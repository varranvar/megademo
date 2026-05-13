import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, func

from mdmo.config import settings
from mdmo.database import async_session_factory
from mdmo.models import Package, ScanJob
from mdmo.scanners.launchpad import LaunchpadScanner
from mdmo.scanners.nvd import NVDScanner
from mdmo.scanners.oval import OVALScanner
from mdmo.scoring.engine import ScoringEngine

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _discover_packages(session) -> list[Package]:
    result = await session.execute(select(Package))
    packages = list(result.scalars().all())
    if packages:
        return packages

    logger.info("No packages in DB yet, discovering from Launchpad...")
    scanner = LaunchpadScanner()
    discovered: list[Package] = []
    try:
        client = scanner.client
        for release in settings.ubuntu.releases:
            try:
                pkgs = await client.search_source_packages(release, limit=100)
                for p in pkgs:
                    discovered.append(
                        Package(name=p.get("name", ""), release=release)
                    )
            except Exception:
                logger.exception("Failed to search packages for %s", release)
    finally:
        await scanner.close()

    if discovered:
        session.add_all(discovered)
        await session.commit()
        logger.info("Discovered %d packages", len(discovered))

    result = await session.execute(select(Package))
    return list(result.scalars().all())


async def scan_launchpad() -> None:
    logger.info("Launchpad scan started")
    scanner = LaunchpadScanner()
    try:
        async with async_session_factory() as session:
            packages = await _discover_packages(session)
            if not packages:
                logger.warning("No packages discovered, aborting launchpad scan")
                return

            summary = await scanner.scan_all(packages, session)
            logger.info("Launchpad scan complete: %s", summary)
    except Exception:
        logger.exception("Launchpad scan failed")
    finally:
        await scanner.close()


async def scan_nvd() -> None:
    logger.info("NVD scan started")
    scanner = NVDScanner()
    try:
        async with async_session_factory() as session:
            packages = await _discover_packages(session)
            summary = await scanner.scan_all(packages, session)
            logger.info("NVD scan complete: %s", summary)
    except Exception:
        logger.exception("NVD scan failed")


async def scan_oval() -> None:
    logger.info("OVAL scan started")
    scanner = OVALScanner()
    try:
        async with async_session_factory() as session:
            summary = await scanner.scan_all([], session)
            logger.info("OVAL scan complete: %s", summary)
    except Exception:
        logger.exception("OVAL scan failed")


async def score_all() -> None:
    logger.info("Scoring run started")
    try:
        async with async_session_factory() as session:
            engine = ScoringEngine.from_config()
            count = await engine.score_all_packages(session)
            logger.info("Scoring run complete: %d packages scored", count)

            scored = await session.execute(
                select(func.count()).select_from(Package)
            )
            total = scored.scalar() or 0
            job = ScanJob(
                scanner="scoring",
                status="completed",
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
                total_packages=total,
                packages_scanned=count,
            )
            session.add(job)
            await session.commit()
    except Exception:
        logger.exception("Scoring run failed")


def init_scheduler() -> None:
    intervals = settings.scan.intervals

    scheduler.add_job(
        scan_launchpad,
        trigger=IntervalTrigger(seconds=intervals.launchpad),
        id="scan_launchpad",
        name="Launchpad Bug Scanner",
        replace_existing=True,
    )

    scheduler.add_job(
        scan_nvd,
        trigger=IntervalTrigger(seconds=intervals.nvd),
        id="scan_nvd",
        name="NVD CVE Scanner",
        replace_existing=True,
    )

    scheduler.add_job(
        scan_oval,
        trigger=IntervalTrigger(seconds=intervals.oval),
        id="scan_oval",
        name="Ubuntu OVAL Scanner",
        replace_existing=True,
    )

    scheduler.add_job(
        score_all,
        trigger=IntervalTrigger(seconds=3600),
        id="score_all",
        name="Hygiene Scoring Engine",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Scheduler initialized: launchpad=%ds, nvd=%ds, oval=%ds, scoring=3600s",
        intervals.launchpad,
        intervals.nvd,
        intervals.oval,
    )
