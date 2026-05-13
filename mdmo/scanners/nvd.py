import asyncio
import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from sqlalchemy.ext.asyncio import AsyncSession

from mdmo.config import settings
from mdmo.models import CVE, CVEPackageLink, Package, ScanJob
from mdmo.scanners import BaseScanner

logger = logging.getLogger(__name__)

NVD_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

CPE_PRODUCT_MAP = {
    "openssl": "openssl",
    "apache": "apache2",
    "http_server": "apache2",
    "apache/http_server": "apache2",
    "python": "python3",
    "linux": "linux",
    "linux_kernel": "linux",
    "linux/linux_kernel": "linux",
    "nodejs": "nodejs",
    "node.js": "nodejs",
    "nodejs/node.js": "nodejs",
    "bind": "bind9",
    "php": "php",
    "postgresql": "postgresql",
    "mysql": "mysql",
    "nginx": "nginx",
    "curl": "curl",
    "libcurl": "curl",
    "curl/libcurl": "curl",
    "zlib": "zlib",
    "sqlite": "sqlite3",
    "expat": "expat",
    "libxml2": "libxml2",
    "systemd": "systemd",
}


class NVDClient:
    def __init__(self) -> None:
        headers = {}
        if settings.nvd.api_key:
            headers["apiKey"] = settings.nvd.api_key
        self._headers = headers
        self._has_api_key = bool(settings.nvd.api_key)

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=NVD_BASE_URL,
            headers=self._headers,
            timeout=60.0,
        )

    def _sleep_between_pages(self) -> float:
        return 0.6 if self._has_api_key else 6.0

    async def poll_delta(self, since: datetime) -> list[dict]:
        _since = since.replace(microsecond=0)
        _end = datetime.now(timezone.utc).replace(microsecond=0)

        all_cves: list[dict] = []
        start_index = 0
        page_size = 2000
        sleep_seconds = self._sleep_between_pages()

        async with self._client() as client:
            while True:
                params: dict = {
                    "lastModStartDate": _since.strftime("%Y-%m-%dT%H:%M:%S.000"),
                    "lastModEndDate": _end.strftime("%Y-%m-%dT%H:%M:%S.000"),
                    "startIndex": start_index,
                    "resultsPerPage": page_size,
                }
                resp = await client.get("/", params=params)
                resp.raise_for_status()
                data = resp.json()

                vulnerabilities = data.get("vulnerabilities", [])
                all_cves.extend(vulnerabilities)

                total_results = data.get("totalResults", 0)
                logger.info(
                    "NVD poll_delta: fetched %d/%d (since=%s)",
                    len(all_cves),
                    total_results,
                    _since.isoformat(),
                )

                if start_index + page_size >= total_results:
                    break

                start_index += page_size
                await asyncio.sleep(sleep_seconds)

        return all_cves

    async def get_cve(self, cve_id: str) -> dict | None:
        async with self._client() as client:
            params = {"cveId": cve_id}
            resp = await client.get("/", params=params)
            resp.raise_for_status()
            data = resp.json()
            vulns = data.get("vulnerabilities", [])
            return vulns[0] if vulns else None

    async def search_cves(self, keyword: str, limit: int = 100) -> list[dict]:
        all_cves: list[dict] = []
        start_index = 0
        page_size = min(limit, 2000)
        sleep_seconds = self._sleep_between_pages()

        async with self._client() as client:
            while len(all_cves) < limit:
                params: dict = {
                    "keywordSearch": keyword,
                    "startIndex": start_index,
                    "resultsPerPage": page_size,
                }
                resp = await client.get("/", params=params)
                resp.raise_for_status()
                data = resp.json()

                vulnerabilities = data.get("vulnerabilities", [])
                all_cves.extend(vulnerabilities)

                total_results = data.get("totalResults", 0)
                if start_index + page_size >= total_results or len(all_cves) >= limit:
                    break

                start_index += page_size
                await asyncio.sleep(sleep_seconds)

        return all_cves[:limit]


class CVEParser:
    @staticmethod
    def parse_cve(cve_item: dict) -> dict:
        cve_data = cve_item.get("cve", {})
        cve_id = cve_data.get("id", "")

        description = ""
        for desc in cve_data.get("descriptions", []):
            if desc.get("lang") == "en":
                description = desc.get("value", "")
                break

        published_date = None
        if cve_data.get("published"):
            try:
                published_date = datetime.fromisoformat(
                    cve_data["published"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        last_modified = None
        if cve_data.get("lastModified"):
            try:
                last_modified = datetime.fromisoformat(
                    cve_data["lastModified"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        cvss_v31_score, cvss_v31_severity, cvss_v31_vector = None, None, None
        cvss_v30_score, cvss_v30_severity, cvss_v30_vector = None, None, None

        metrics = cve_data.get("metrics", {})
        for metric_key, metric_list in metrics.items():
            if not isinstance(metric_list, list) or not metric_list:
                continue
            for entry in metric_list:
                cvss_data = entry.get("cvssData", {})
                if not cvss_data:
                    continue
                if metric_key == "cvssMetricV31":
                    cvss_v31_score = cvss_data.get("baseScore")
                    cvss_v31_severity = cvss_data.get("baseSeverity")
                    cvss_v31_vector = cvss_data.get("vectorString")
                    if cvss_v31_severity:
                        cvss_v31_severity = cvss_v31_severity.upper()
                    break
                elif metric_key == "cvssMetricV30":
                    cvss_v30_score = cvss_data.get("baseScore")
                    cvss_v30_severity = cvss_data.get("baseSeverity")
                    cvss_v30_vector = cvss_data.get("vectorString")
                    if cvss_v30_severity:
                        cvss_v30_severity = cvss_v30_severity.upper()
                    break

        for metric_key, metric_list in metrics.items():
            if not isinstance(metric_list, list) or not metric_list:
                continue
            if metric_key not in ("cvssMetricV31", "cvssMetricV30"):
                continue
            for entry in metric_list:
                cvss_data = entry.get("cvssData", {})
                if not cvss_data:
                    continue
                if metric_key == "cvssMetricV31":
                    cvss_v31_score = cvss_data.get("baseScore")
                    cvss_v31_severity = cvss_data.get("baseSeverity")
                    cvss_v31_vector = cvss_data.get("vectorString")
                    if cvss_v31_severity:
                        cvss_v31_severity = cvss_v31_severity.upper()
                elif metric_key == "cvssMetricV30":
                    cvss_v30_score = cvss_data.get("baseScore")
                    cvss_v30_severity = cvss_data.get("baseSeverity")
                    cvss_v30_vector = cvss_data.get("vectorString")
                    if cvss_v30_severity:
                        cvss_v30_severity = cvss_v30_severity.upper()

        cwe_ids: list[str] = []
        for weakness in cve_data.get("weaknesses", []):
            for desc_data in weakness.get("description", []):
                value = desc_data.get("value", "")
                if value.startswith("CWE-"):
                    cwe_ids.append(value)

        kev = False
        kev_date_added = None
        if cve_data.get("cisaExploitAdd"):
            kev_date_added_str = cve_data["cisaExploitAdd"]
            if kev_date_added_str:
                kev = True
                try:
                    kev_date_added = datetime.fromisoformat(
                        kev_date_added_str.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

        rejected = cve_data.get("vulnStatus", "") == "Rejected"

        return {
            "cve_id": cve_id,
            "description": description,
            "published_date": published_date,
            "last_modified": last_modified,
            "cvss_v31_score": cvss_v31_score,
            "cvss_v31_severity": cvss_v31_severity,
            "cvss_v31_vector": cvss_v31_vector,
            "cvss_v30_score": cvss_v30_score,
            "cvss_v30_severity": cvss_v30_severity,
            "cvss_v30_vector": cvss_v30_vector,
            "cwe_ids": cwe_ids,
            "kev": kev,
            "kev_date_added": kev_date_added,
            "rejected": rejected,
        }


class NVDScanner(BaseScanner):
    name = "nvd"

    def __init__(self) -> None:
        self.client = NVDClient()

    @staticmethod
    def _extract_products(cve_item: dict) -> list[dict]:
        products: list[dict] = []
        cve_data = cve_item.get("cve", {})
        for config in cve_data.get("configurations", []):
            for node in config.get("nodes", []):
                for match in node.get("cpeMatch", []):
                    criteria = match.get("criteria", "")
                    if not criteria:
                        continue
                    parts = criteria.split(":")
                    if len(parts) >= 5:
                        vendor = parts[3]
                        product = parts[4]
                        products.append({
                            "vendor": vendor,
                            "product": product,
                            "criteria": criteria,
                            "vulnerable": match.get("vulnerable", True),
                        })
        return products

    @staticmethod
    def _match_product_to_package(product_name: str, known_packages: set[str]) -> str | None:
        product_lower = product_name.lower()
        if product_lower in CPE_PRODUCT_MAP:
            return CPE_PRODUCT_MAP[product_lower]
        for cpe_key, pkg_name in CPE_PRODUCT_MAP.items():
            if product_lower == cpe_key.split("/")[-1]:
                return pkg_name
        if product_lower in known_packages:
            return product_lower
        return None

    async def _upsert_cve(self, session: AsyncSession, parsed: dict) -> CVE | None:
        stmt = sqlite_upsert(CVE).values(
            cve_id=parsed["cve_id"],
            description=parsed["description"],
            cvss_score=parsed["cvss_v31_score"],
            cvss_severity=parsed["cvss_v31_severity"],
            vector_string=parsed["cvss_v31_vector"],
            cvss_v30_score=parsed["cvss_v30_score"],
            cvss_v30_severity=parsed["cvss_v30_severity"],
            cvss_v30_vector=parsed["cvss_v30_vector"],
            cwe_ids=parsed["cwe_ids"],
            kev=parsed["kev"],
            kev_date_added=parsed["kev_date_added"],
            rejected=parsed["rejected"],
            published_date=parsed["published_date"],
            last_modified=parsed["last_modified"],
            status="open",
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["cve_id"],
            set_={
                "description": stmt.excluded.description,
                "cvss_score": stmt.excluded.cvss_score,
                "cvss_severity": stmt.excluded.cvss_severity,
                "vector_string": stmt.excluded.vector_string,
                "cvss_v30_score": stmt.excluded.cvss_v30_score,
                "cvss_v30_severity": stmt.excluded.cvss_v30_severity,
                "cvss_v30_vector": stmt.excluded.cvss_v30_vector,
                "cwe_ids": stmt.excluded.cwe_ids,
                "kev": stmt.excluded.kev,
                "kev_date_added": stmt.excluded.kev_date_added,
                "rejected": stmt.excluded.rejected,
                "published_date": stmt.excluded.published_date,
                "last_modified": stmt.excluded.last_modified,
            },
        )
        result = await session.execute(stmt)
        await session.commit()

        sel = select(CVE).where(CVE.cve_id == parsed["cve_id"])
        row = await session.execute(sel)
        return row.scalar_one_or_none()

    async def _link_cve_to_package(
        self, session: AsyncSession, cve_db: CVE, package_id: int
    ) -> None:
        stmt = sqlite_upsert(CVEPackageLink).values(
            cve_id=cve_db.id,
            package_id=package_id,
            status="open",
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["cve_id", "package_id"],
            set_={"status": stmt.excluded.status},
        )
        await session.execute(stmt)
        await session.commit()

    async def scan_package(
        self, package_name: str, release: str, session: AsyncSession
    ) -> dict[str, Any]:
        cves = await self.client.search_cves(package_name, limit=200)
        parsed_cves = [CVEParser.parse_cve(item) for item in cves]

        stmt = select(Package).where(Package.name == package_name, Package.release == release)
        row = await session.execute(stmt)
        package = row.scalar_one_or_none()

        stored_count = 0
        for parsed in parsed_cves:
            cve_db = await self._upsert_cve(session, parsed)
            if cve_db and package:
                await self._link_cve_to_package(session, cve_db, package.id)
            stored_count += 1

        return {
            "scanner": "nvd",
            "package": package_name,
            "release": release,
            "cves_found": len(cves),
            "cves_stored": stored_count,
        }

    async def scan_all(
        self, packages: list[Any], session: AsyncSession
    ) -> dict[str, Any]:
        scan_job = ScanJob(
            scanner="nvd",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        session.add(scan_job)
        await session.commit()
        await session.refresh(scan_job)

        last_sync = None
        result = await session.execute(
            select(ScanJob)
            .where(ScanJob.scanner == "nvd", ScanJob.status == "completed")
            .order_by(ScanJob.finished_at.desc())
            .limit(1)
        )
        last_job = result.scalar_one_or_none()
        if last_job and last_job.finished_at:
            last_sync = last_job.finished_at
        else:
            last_sync = datetime.now(timezone.utc) - timedelta(days=7)

        logger.info("NVD scan_all: polling delta since %s", last_sync.isoformat())
        cve_items = await self.client.poll_delta(last_sync)

        known_package_names: set[str] = set()
        if packages:
            for pkg in packages:
                if hasattr(pkg, "name"):
                    known_package_names.add(pkg.name)
        else:
            result = await session.execute(select(Package.name).distinct())
            known_package_names = {row[0] for row in result if row[0]}

        stored = 0
        linked = 0
        for item in cve_items:
            parsed = CVEParser.parse_cve(item)
            if parsed["rejected"]:
                continue

            cve_db = await self._upsert_cve(session, parsed)
            if cve_db:
                stored += 1

            products = self._extract_products(item)
            for prod in products:
                pkg_name = self._match_product_to_package(
                    prod["product"], known_package_names
                )
                if pkg_name and cve_db:
                    row = await session.execute(
                        select(Package.id).where(Package.name == pkg_name)
                    )
                    pkg_ids = row.scalars().all()
                    for pkg_id in pkg_ids:
                        await self._link_cve_to_package(session, cve_db, pkg_id)
                        linked += 1

        scan_job.status = "completed"
        scan_job.items_fetched = len(cve_items)
        scan_job.packages_scanned = stored
        scan_job.finished_at = datetime.now(timezone.utc)
        await session.commit()

        return {
            "scanner": "nvd",
            "status": "completed",
            "total_cves_fetched": len(cve_items),
            "cves_stored": stored,
            "cves_linked": linked,
        }
