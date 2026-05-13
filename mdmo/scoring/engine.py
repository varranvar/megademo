import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from mdmo.config import settings
from mdmo.database import async_session_factory
from mdmo.models import CVE, Bug, Package, PackageScore, Heuristic
from mdmo.plugins.base import PluginRegistry

logger = logging.getLogger(__name__)


class ScoringEngine:
    def __init__(self, config: dict | None = None):
        scoring_cfg = (config or {}).get("scoring", {}) if config else {}
        weights_cfg = scoring_cfg.get("weights", {})
        self.weights = {
            "bugs": weights_cfg.get("bugs", 0.25),
            "cve": weights_cfg.get("cve", 0.35),
            "freshness": weights_cfg.get("freshness", 0.20),
            "plugins": weights_cfg.get("plugins", 0.20),
        }
        self.plugins = PluginRegistry.get_all()
        self.freshness_plugin = PluginRegistry.get("version_freshness")

    async def score_package(self, package: Package, session) -> dict:
        bug_score = _compute_bug_score(package)
        cve_score = _compute_cve_score(package)

        plugin_results = {}
        plugin_total = 0.0
        plugin_count = 0

        if self.plugins:
            tasks = [p.check(package) for p in self.plugins]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for plugin, result in zip(self.plugins, results):
                if isinstance(result, Exception):
                    plugin_results[plugin.name] = {
                        "score": 0.5,
                        "label": f"{plugin.name}: error",
                        "details": {"error": str(result)},
                    }
                    plugin_total += 0.5
                elif result.error:
                    plugin_results[plugin.name] = {
                        "score": 0.5,
                        "label": result.label or plugin.name,
                        "details": result.details,
                    }
                    plugin_total += 0.5
                else:
                    plugin_results[plugin.name] = {
                        "score": result.score,
                        "label": result.label or plugin.name,
                        "details": result.details,
                    }
                    plugin_total += result.score
                plugin_count += 1

        avg_plugin = plugin_total / max(plugin_count, 1) if plugin_count > 0 else 0.5

        total = (
            self.weights["bugs"] * bug_score
            + self.weights["cve"] * cve_score
            + self.weights["plugins"] * avg_plugin
        )

        norm_factor = self.weights["bugs"] + self.weights["cve"] + self.weights["plugins"]
        if norm_factor > 0:
            total = total / norm_factor

        total_score = round(total * 100, 1)
        grade = self.get_grade(total_score)

        return {
            "total_score": total_score,
            "grade": grade,
            "components": {
                "bugs": {
                    "score": round(bug_score * 100),
                    "label": f"Open Bugs ({len(package.bugs)})",
                    "details": {"open_bugs": len(package.bugs)},
                },
                "cve": {
                    "score": round(cve_score * 100),
                    "label": f"CVEs ({len(package.cves)})",
                    "details": {"cve_count": len(package.cves)},
                },
                **plugin_results,
            },
        }

    async def score_all_packages(self, session) -> int:
        result = await session.execute(select(Package))
        packages = result.scalars().all()

        if not packages:
            return 0

        scored = 0
        for package in packages:
            score_data = await self.score_package(package, session)
            await _persist_scores(session, package, score_data)
            scored += 1

        await session.commit()
        return scored

    def get_grade(self, score: float) -> str:
        if score <= 30:
            return "critical"
        elif score <= 55:
            return "warning"
        elif score <= 75:
            return "fair"
        else:
            return "healthy"

    @classmethod
    def from_config(cls) -> "ScoringEngine":
        return cls(settings.model_dump())


def _compute_bug_score(package: Package) -> float:
    bug_count = len(package.bugs) if package.bugs else 0
    if bug_count == 0:
        return 1.0
    elif bug_count == 1:
        return 0.8
    elif bug_count <= 5:
        return 0.6
    elif bug_count <= 10:
        return 0.4
    elif bug_count <= 20:
        return 0.2
    else:
        return 0.0


def _compute_cve_score(package: Package) -> float:
    cves = package.cves or []
    if not cves:
        return 1.0

    scores = [c.cvss_score for c in cves if c.cvss_score is not None]
    if not scores:
        return 0.5

    avg = sum(scores) / len(scores)
    if avg >= 9.0 or any(s >= 9.0 for s in scores):
        return 0.0
    elif avg > 7.0:
        return 0.3
    elif avg > 4.0:
        return 0.5
    else:
        return 0.7


async def _persist_scores(session, package: Package, score_data: dict) -> None:
    now = datetime.now(timezone.utc)

    for component_name, component_data in score_data.get("components", {}).items():
        heuristic = await _get_or_create_heuristic(session, component_name)

        existing = await session.execute(
            select(PackageScore).where(
                PackageScore.package_id == package.id,
                PackageScore.heuristic_id == heuristic.id,
            )
        )
        existing_score = existing.scalar_one_or_none()

        if existing_score:
            existing_score.score = component_data["score"]
            existing_score.details = component_data.get("details")
            existing_score.calculated_at = now
        else:
            new_score = PackageScore(
                package_id=package.id,
                heuristic_id=heuristic.id,
                score=component_data["score"],
                details=component_data.get("details"),
                calculated_at=now,
            )
            session.add(new_score)


async def _get_or_create_heuristic(session, name: str) -> Heuristic:
    result = await session.execute(select(Heuristic).where(Heuristic.name == name))
    heuristic = result.scalar_one_or_none()
    if not heuristic:
        heuristic = Heuristic(
            name=name,
            label=name.replace("_", " ").title(),
            weight=1.0,
            enabled=True,
        )
        session.add(heuristic)
        await session.flush()
    return heuristic