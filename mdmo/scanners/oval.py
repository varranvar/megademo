import asyncio
import hashlib
import logging
import tempfile
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from sqlalchemy.ext.asyncio import AsyncSession

from mdmo.config import settings
from mdmo.models import CVE, CVEPackageLink, Package, ScanJob, SyncState
from mdmo.scanners import BaseScanner

logger = logging.getLogger(__name__)

OVAL_BASE_URL = "https://security-metadata.canonical.com/oval"

OVAL_NS = {
    "oval": "http://oval.mitre.org/XMLSchema/oval-definitions-5",
    "oval-def": "http://oval.mitre.org/XMLSchema/oval-definitions-5",
    "unix-def": "http://oval.mitre.org/XMLSchema/oval-definitions-5#unix",
    "linux-def": "http://oval.mitre.org/XMLSchema/oval-definitions-5#linux",
}


class OVALParser:
    @staticmethod
    def parse_oval_file(release: str, filepath: str) -> list[dict]:
        import bz2

        from lxml import etree as ET

        results: list[dict] = []
        ns = OVAL_NS

        try:
            with bz2.open(filepath, "rb") as f:
                tree = ET.parse(f)
        except Exception:
            with open(filepath, "rb") as f:
                tree = ET.parse(f)

        root = tree.getroot()

        tests: dict[str, dict] = {}
        objects: dict[str, dict] = {}
        states: dict[str, dict] = {}

        for child in root:
            test_tag = child.tag
            if "}" in test_tag:
                test_tag = test_tag.split("}", 1)[1]
            if test_tag == "tests":
                for tchild in child:
                    tid = tchild.get("id", "")
                    tc = tchild.get("comment", "")
                    state_ref = None
                    obj_ref = None
                    check_existence = None
                    for subtag in tchild:
                        stag = subtag.tag
                        if "}" in stag:
                            stag = stag.split("}", 1)[1]
                        if stag == "object":
                            obj_ref = subtag.get("object_ref", "")
                        elif stag == "state":
                            state_ref = subtag.get("state_ref", "")
                        elif stag == "check_existence":
                            check_existence = subtag.text
                    tests[tid] = {
                        "id": tid,
                        "comment": tc,
                        "object_ref": obj_ref,
                        "state_ref": state_ref,
                        "check_existence": check_existence,
                    }
            elif test_tag == "objects":
                for ochild in child:
                    oid = ochild.get("id", "")
                    pkg_name = None
                    for subtag in ochild:
                        stag = subtag.tag
                        if "}" in stag:
                            stag = stag.split("}", 1)[1]
                        if stag == "name":
                            pkg_name = subtag.text
                    objects[oid] = {"id": oid, "name": pkg_name}
            elif test_tag == "states":
                for schild in child:
                    sid = schild.get("id", "")
                    sc = schild.get("comment", "")
                    evr = None
                    for subtag in schild:
                        stag = subtag.tag
                        if "}" in stag:
                            stag = stag.split("}", 1)[1]
                        if stag == "evr":
                            evr = subtag.text
                    states[sid] = {"id": sid, "comment": sc, "evr": evr}

        for child in root:
            child_tag = child.tag
            if "}" in child_tag:
                child_tag = child_tag.split("}", 1)[1]
            if child_tag != "definitions":
                continue

            for definition in child:
                def_class = definition.get("class", "")
                if def_class not in ("patch", "vulnerability"):
                    continue
                def_id = definition.get("id", "")

                title = ""
                severity = ""
                cve_refs: list[str] = []
                usn_refs: list[str] = []
                description = ""

                for meta_child in definition:
                    mtag = meta_child.tag
                    if "}" in mtag:
                        mtag = mtag.split("}", 1)[1]

                    if mtag == "metadata":
                        for mdata in meta_child:
                            dt = mdata.tag
                            if "}" in dt:
                                dt = dt.split("}", 1)[1]
                            if dt == "title":
                                title = (mdata.text or "").strip()
                            elif dt == "description":
                                description = (mdata.text or "").strip()

                        for ref in meta_child.iter():
                            rtag = ref.tag
                            if "}" in rtag:
                                rtag = rtag.split("}", 1)[1]
                            if rtag == "reference":
                                ref_id = ref.get("ref_id", "")
                                ref_source = ref.get("source", "")
                                if ref_source == "CVE":
                                    cve_refs.append(ref_id)
                                elif ref_source == "USN":
                                    usn_refs.append(ref_id)

                        for advisory in meta_child.iter():
                            at = advisory.tag
                            if "}" in at:
                                at = at.split("}", 1)[1]
                            if at == "advisory":
                                for sev in advisory:
                                    st = sev.tag
                                    if "}" in st:
                                        st = st.split("}", 1)[1]
                                    if st == "severity":
                                        severity = (sev.text or "").strip()

                    elif mtag == "criteria":
                        criteria_refs = OVALParser._extract_criteria_refs(meta_child)

                for cve_id in cve_refs:
                    for crit in criteria_refs:
                        test_info = tests.get(crit["test_ref"], {})
                        obj_ref = test_info.get("object_ref", "")
                        state_ref = test_info.get("state_ref", "")
                        obj_info = objects.get(obj_ref, {})
                        pkg_name = obj_info.get("name", "")
                        state_info = states.get(state_ref, {})
                        evr = state_info.get("evr", "")

                        if not pkg_name:
                            continue

                        fix_version = None
                        if evr and "le " in evr:
                            fix_version = evr.split("le ", 1)[1].strip()
                        elif evr and "lt " in evr:
                            fix_version = evr.split("lt ", 1)[1].strip()
                        elif evr and not evr.startswith(("le ", "lt ", "ge ", "gt ", "eq ")):
                            fix_version = evr.strip()

                        results.append({
                            "cve_id": cve_id,
                            "usn_id": usn_refs[0] if usn_refs else "",
                            "source_pkg": pkg_name,
                            "binary_packages": [pkg_name],
                            "fix_version": fix_version,
                            "status": "open",
                            "severity": severity,
                            "description": description or title,
                        })

        return results

    @staticmethod
    def _extract_criteria_refs(criteria_element) -> list[dict]:
        refs: list[dict] = []
        for child in criteria_element.iter():
            tag = child.tag
            if "}" in tag:
                tag = tag.split("}", 1)[1]
            if tag in ("criterion", "criteria"):
                test_ref = child.get("test_ref", "")
                if test_ref:
                    refs.append({
                        "test_ref": test_ref,
                        "comment": child.get("comment", ""),
                    })
        return refs


class OVALScanner(BaseScanner):
    name = "oval"

    def _oval_url(self, release: str) -> str:
        return f"{OVAL_BASE_URL}/com.ubuntu.{release}.usn.oval.xml.bz2"

    def _oval_meta_url(self, release: str) -> str:
        return f"{OVAL_BASE_URL}/com.ubuntu.{release}.usn.oval.xml.bz2.meta"

    async def _get_meta_checksum(self, release: str) -> str | None:
        url = self._oval_meta_url(release)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                text = resp.text
                for line in text.splitlines():
                    if line.startswith("sha256="):
                        return line.split("=", 1)[1].strip()
        except Exception:
            logger.warning("Failed to fetch OVAL meta for %s", release)
        return None

    async def download_oval(self, release: str) -> str | None:
        meta_checksum = await self._get_meta_checksum(release)
        if meta_checksum:
            last = await self._get_sync_state(f"oval_checksum_{release}")
            if last == meta_checksum:
                logger.info("OVAL %s unchanged (checksum match), skipping download", release)
                return None

        url = self._oval_url(release)
        tmp = tempfile.NamedTemporaryFile(suffix=".xml.bz2", delete=False)
        filepath = tmp.name
        tmp.close()

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(resp.content)

            if meta_checksum:
                computed = hashlib.sha256()
                with open(filepath, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        computed.update(chunk)
                actual = computed.hexdigest()
                if actual != meta_checksum:
                    logger.warning(
                        "OVAL %s checksum mismatch: expected %s, got %s",
                        release,
                        meta_checksum,
                        actual,
                    )

            await self._set_sync_state(f"oval_checksum_{release}", meta_checksum or "")
            return filepath
        except Exception:
            import os

            if os.path.exists(filepath):
                os.remove(filepath)
            raise

    async def _get_sync_state(self, key: str) -> str | None:
        from mdmo.database import async_session_factory

        async with async_session_factory() as session:
            result = await session.execute(select(SyncState).where(SyncState.key == key))
            row = result.scalar_one_or_none()
            return row.value if row else None

    async def _set_sync_state(self, key: str, value: str) -> None:
        from mdmo.database import async_session_factory

        async with async_session_factory() as session:
            stmt = sqlite_upsert(SyncState).values(key=key, value=value)
            stmt = stmt.on_conflict_do_update(
                index_elements=["key"],
                set_={"value": stmt.excluded.value},
            )
            await session.execute(stmt)
            await session.commit()

    async def _upsert_cve_oval(
        self, session: AsyncSession, data: dict, package_id: int
    ) -> CVE | None:
        stmt = sqlite_upsert(CVE).values(
            cve_id=data["cve_id"],
            description=data.get("description", ""),
            published_date=None,
            last_modified=datetime.now(timezone.utc),
            status="open",
            usn_id=data.get("usn_id", ""),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["cve_id"],
            set_={
                "description": stmt.excluded.description,
                "last_modified": stmt.excluded.last_modified,
                "usn_id": stmt.excluded.usn_id,
            },
        )
        await session.execute(stmt)
        await session.flush()

        sel = select(CVE).where(CVE.cve_id == data["cve_id"])
        row = await session.execute(sel)
        cve_db = row.scalar_one_or_none()

        if cve_db:
            link_stmt = sqlite_upsert(CVEPackageLink).values(
                cve_id=cve_db.id,
                package_id=package_id,
                fix_version=data.get("fix_version"),
                status="open",
            )
            link_stmt = link_stmt.on_conflict_do_update(
                index_elements=["cve_id", "package_id"],
                set_={
                    "fix_version": link_stmt.excluded.fix_version,
                    "status": link_stmt.excluded.status,
                },
            )
            await session.execute(link_stmt)

        return cve_db

    async def _ensure_package(
        self, session: AsyncSession, package_name: str, release: str
    ) -> Package:
        result = await session.execute(
            select(Package).where(
                Package.name == package_name,
                Package.release == release,
            )
        )
        pkg = result.scalar_one_or_none()
        if pkg:
            return pkg

        pkg = Package(
            name=package_name,
            release=release,
            component="main",
            architecture="amd64",
        )
        session.add(pkg)
        await session.flush()
        return pkg

    async def scan_release(self, release: str, session: AsyncSession) -> dict[str, Any]:
        filepath = await self.download_oval(release)
        if filepath is None:
            return {"release": release, "status": "skipped", "cves_processed": 0}

        try:
            parsed = OVALParser.parse_oval_file(release, filepath)
        finally:
            import os

            if os.path.exists(filepath):
                os.remove(filepath)

        processed = 0
        for entry in parsed:
            pkg = await self._ensure_package(session, entry["source_pkg"], release)
            await self._upsert_cve_oval(session, entry, pkg.id)
            processed += 1

        await session.commit()

        logger.info(
            "OVAL scan_release %s: processed %d CVE entries",
            release,
            processed,
        )
        return {"release": release, "status": "complete", "cves_processed": processed}

    async def scan_package(
        self, package_name: str, release: str, session: AsyncSession
    ) -> dict[str, Any]:
        result = {"scanner": "oval", "package": package_name, "release": release}

        row = await session.execute(
            select(Package.id).where(
                Package.name == package_name,
                Package.release == release,
            )
        )
        pkg_id = row.scalar_one_or_none()
        if not pkg_id:
            result["error"] = "Package not found"
            return result

        link_rows = await session.execute(
            select(CVEPackageLink).join(CVE).where(
                CVEPackageLink.package_id == pkg_id
            )
        )
        links = link_rows.scalars().all()
        result["cve_count"] = len(links)
        return result

    async def scan_all(
        self, packages: list[Any], session: AsyncSession
    ) -> dict[str, Any]:
        scan_job = ScanJob(
            scanner="oval",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        session.add(scan_job)
        await session.commit()

        total_cves = 0
        for release in settings.ubuntu.releases:
            release_result = await self.scan_release(release, session)
            total_cves += release_result.get("cves_processed", 0)

        scan_job.status = "completed"
        scan_job.items_fetched = total_cves
        scan_job.packages_scanned = total_cves
        scan_job.finished_at = datetime.now(timezone.utc)
        await session.commit()

        return {
            "scanner": "oval",
            "status": "completed",
            "releases_scanned": settings.ubuntu.releases,
            "cves_processed": total_cves,
        }
