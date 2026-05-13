import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from mdmo.database import async_session_factory
from mdmo.models import CVE, CVEPackageLink
from mdmo.plugins.base import HygieneCheck, HygieneResult

logger = logging.getLogger(__name__)


class CVECheck(HygieneCheck):
    name = "cve_severity"
    description = "Unpatched CVEs weighted by CVSS severity"
    weight = 0.35

    async def check(self, package: Any) -> HygieneResult:
        async with async_session_factory() as session:
            cve_links = await session.execute(
                select(CVEPackageLink, CVE)
                .join(CVE, CVEPackageLink.cve_id == CVE.id)
                .where(
                    CVEPackageLink.package_id == package.id,
                    CVEPackageLink.status != "patched",
                )
            )
            rows = cve_links.all()

        now = datetime.now(timezone.utc)
        raw_score = 0.0
        details: list[dict] = []

        for link, cve in rows:
            cvss = cve.cvss_score or cve.cvss_v30_score or 0.0
            if cvss == 0.0:
                cvss = 5.0

            severity_weight = (cvss ** 2) / 100.0

            multiplier = 1.0

            if cve.kev:
                multiplier *= 2.5

            if cve.published_date:
                pub_dt = cve.published_date
                if pub_dt.tzinfo is None:
                    pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                age_days = (now - pub_dt).days
                if age_days <= 30:
                    multiplier *= 1.5
                elif age_days <= 90:
                    multiplier *= 1.2
                elif age_days <= 365:
                    multiplier *= 1.0
                else:
                    multiplier *= 0.7

            weighted = severity_weight * multiplier
            raw_score += weighted

            details.append({
                "cve_id": cve.cve_id,
                "cvss_score": cvss,
                "severity_weight": round(severity_weight, 4),
                "multiplier": round(multiplier, 2),
                "weighted": round(weighted, 4),
                "kev": cve.kev,
            })

        normalized = max(0.0, 1.0 - raw_score / 10.0)
        normalized = min(1.0, normalized)

        return HygieneResult(
            score=round(normalized, 4),
            label=self.name.replace("_", " ").title(),
            details={
                "raw_sum": round(raw_score, 4),
                "normalized": round(normalized, 4),
                "cve_count": len(rows),
                "cves": details,
            },
        )
