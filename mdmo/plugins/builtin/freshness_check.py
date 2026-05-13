from datetime import datetime, timezone
from typing import Any

from mdmo.plugins.base import HygieneCheck, HygieneResult


class FreshnessCheck(HygieneCheck):
    name = "version_freshness"
    description = "How current the package version is compared to upstream"
    weight = 0.20

    async def check(self, package: Any) -> HygieneResult:
        ref_date = package.updated_at or package.created_at
        if ref_date is None:
            return HygieneResult(
                score=0.5,
                details={"age_days": None, "version": package.version, "status": "unknown"},
                label="Freshness Unknown",
            )

        now = datetime.now(timezone.utc)
        if ref_date.tzinfo is None:
            ref_date = ref_date.replace(tzinfo=timezone.utc)

        age_days = (now - ref_date).days
        score = max(0.0, 1.0 - age_days / 730.0)

        if score >= 0.8:
            status = "recent"
        elif score >= 0.5:
            status = "aging"
        elif score >= 0.2:
            status = "stale"
        else:
            status = "outdated"

        return HygieneResult(
            score=score,
            details={
                "age_days": age_days,
                "version": package.version,
                "status": status,
                "updated_at": ref_date.isoformat() if ref_date else None,
            },
            label=f"Version Freshness: {status.title()} ({age_days}d old)",
        )
