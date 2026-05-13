import datetime
import logging
import math
from typing import Any

from sqlalchemy import select

from mdmo.database import async_session_factory
from mdmo.models import Bug, Package
from mdmo.plugins.base import HygieneCheck, HygieneResult

logger = logging.getLogger(__name__)

IMPORTANCE_WEIGHTS = {
    "Critical": 5,
    "High": 3,
    "Medium": 1,
    "Low": 0.5,
    "Wishlist": 0.1,
    "Undecided": 1,
}

STALENESS_THRESHOLD_YEARS_2 = 730
STALENESS_THRESHOLD_YEARS_1 = 365
STALENESS_PENALTY_2YR = 0.10
STALENESS_PENALTY_1YR = 0.05


def sigmoid(x: float, midpoint: float = 50, steepness: float = 0.05) -> float:
    return 1.0 / (1.0 + math.exp(steepness * (x - midpoint)))


class BugCheck(HygieneCheck):
    name = "bug_count"
    description = "Open Launchpad bugs, weighted by severity and age"
    weight = 0.25

    async def check(self, package: Any) -> HygieneResult:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Bug).where(Bug.package_id == package.id)
            )
            bugs = result.scalars().all()

        if not bugs:
            return HygieneResult(
                score=1.0,
                label="No Bugs",
                details={"open_bugs": 0, "message": "No open bugs"},
            )

        open_bugs = [b for b in bugs if b.status not in ("Fix Committed", "Won't Fix", "Invalid")]
        if not open_bugs:
            return HygieneResult(
                score=1.0,
                label="All Resolved",
                details={
                    "open_bugs": 0,
                    "total_bugs": len(bugs),
                    "message": "All bugs resolved",
                },
            )

        weighted_count: float = 0.0
        security_count = 0
        now = datetime.datetime.now(datetime.timezone.utc)
        oldest_date: datetime.datetime | None = None

        for bug in open_bugs:
            imp = bug.importance or "Undecided"
            w = IMPORTANCE_WEIGHTS.get(imp, 1.0)
            weighted_count += w

            if bug.security_related:
                security_count += 1

            if bug.created_date:
                if oldest_date is None or bug.created_date < oldest_date:
                    oldest_date = bug.created_date

        raw_score = sigmoid(weighted_count, midpoint=50, steepness=0.05)
        penalty = 0.0

        if oldest_date:
            if oldest_date.tzinfo is None:
                oldest_date = oldest_date.replace(tzinfo=datetime.timezone.utc)
            age_days = (now - oldest_date).days
            if age_days > STALENESS_THRESHOLD_YEARS_2:
                penalty += STALENESS_PENALTY_2YR
            elif age_days > STALENESS_THRESHOLD_YEARS_1:
                penalty += STALENESS_PENALTY_1YR

        if security_count > 0:
            penalty += 0.05 * security_count

        final_score = max(0.0, min(1.0, raw_score - penalty))
        final_score = round(final_score, 4)

        if final_score >= 0.8:
            label = f"Healthy ({len(open_bugs)} bugs)"
        elif final_score >= 0.5:
            label = f"Fair ({len(open_bugs)} bugs)"
        elif final_score >= 0.2:
            label = f"Concerning ({len(open_bugs)} bugs)"
        else:
            label = f"Critical ({len(open_bugs)} bugs)"

        return HygieneResult(
            score=final_score,
            label=label,
            details={
                "open_bugs": len(open_bugs),
                "total_bugs": len(bugs),
                "weighted_count": weighted_count,
                "security_bugs": security_count,
                "oldest_bug_days": (now - oldest_date).days if oldest_date else None,
                "staleness_penalty": penalty,
                "raw_sigmoid": round(raw_score, 4),
            },
        )