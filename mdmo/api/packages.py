from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import case, func, select, or_

from mdmo.database import get_db
from mdmo.models import CVE, Bug, Package, PackageScore, ScanJob, Heuristic
from mdmo.plugins.base import PluginRegistry
from mdmo.scoring.engine import ScoringEngine

router = APIRouter()

_templates_dir = Path(__file__).parent.parent / "templates"
_templates = Jinja2Templates(directory=str(_templates_dir))


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    async for session in get_db():
        stmt = select(Package)
        result = await session.execute(stmt)
        packages = result.scalars().all()

        scores_by_pkg: dict[int, float] = {}
        grades_by_pkg: dict[int, str] = {}

        scores_result = await session.execute(
            select(
                PackageScore.package_id,
                func.avg(PackageScore.score).label("avg_score"),
            ).group_by(PackageScore.package_id)
        )
        engine = ScoringEngine.from_config()
        for row in scores_result:
            pkg_id, avg = row.package_id, row.avg_score
            scores_by_pkg[pkg_id] = avg
            grades_by_pkg[pkg_id] = engine.get_grade(avg)

        total = len(packages)
        critical = sum(1 for g in grades_by_pkg.values() if g == "critical")
        warning = sum(1 for g in grades_by_pkg.values() if g == "warning")
        fair = sum(1 for g in grades_by_pkg.values() if g == "fair")
        healthy = sum(1 for g in grades_by_pkg.values() if g == "healthy")
        unscored = total - len(scores_by_pkg)
        healthy += unscored

        return _templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "packages": packages,
                "scores": scores_by_pkg,
                "grades": grades_by_pkg,
                "stats": {
                    "total": total,
                    "critical": critical,
                    "warning": warning,
                    "fair": fair,
                    "healthy": healthy,
                },
            },
        )


@router.get("/package/{name}", response_class=HTMLResponse)
async def package_detail(request: Request, name: str):
    async for session in get_db():
        result = await session.execute(
            select(Package).where(Package.name == name).order_by(Package.updated_at.desc())
        )
        package = result.scalars().first()
        if not package:
            return HTMLResponse("<h2>Package not found</h2>", status_code=404)

        pkg_result = await session.execute(
            select(Package).where(Package.id == package.id)
        )
        package = pkg_result.scalar_one()

        engine = ScoringEngine.from_config()
        score_data = await engine.score_package(package, session)

        score_trend = await _get_score_trend(session, package.id)

        return _templates.TemplateResponse(
            "package_detail.html",
            {
                "request": request,
                "package": package,
                "score_data": score_data,
                "score_trend": score_trend,
                "bug_count": len(package.bugs),
                "cve_count": len(package.cves),
            },
        )


@router.get("/package/{name}/bugs", response_class=HTMLResponse)
async def package_bugs(request: Request, name: str):
    async for session in get_db():
        result = await session.execute(
            select(Package).where(Package.name == name).order_by(Package.updated_at.desc())
        )
        package = result.scalars().first()
        if not package:
            return HTMLResponse("<p>Package not found</p>", status_code=404)

        pkg_result = await session.execute(
            select(Package).where(Package.id == package.id)
        )
        package = pkg_result.scalar_one()

        bugs = package.bugs or []
        return _templates.TemplateResponse(
            "partials/bugs_table.html",
            {"request": request, "package": package, "bugs": bugs},
        )


@router.get("/package/{name}/cves", response_class=HTMLResponse)
async def package_cves(request: Request, name: str):
    async for session in get_db():
        result = await session.execute(
            select(Package).where(Package.name == name).order_by(Package.updated_at.desc())
        )
        package = result.scalars().first()
        if not package:
            return HTMLResponse("<p>Package not found</p>", status_code=404)

        pkg_result = await session.execute(
            select(Package).where(Package.id == package.id)
        )
        package = pkg_result.scalar_one()

        cves = sorted(
            package.cves or [],
            key=lambda c: c.cvss_score or 0,
            reverse=True,
        )
        return _templates.TemplateResponse(
            "partials/cves_table.html",
            {"request": request, "package": package, "cves": cves},
        )


@router.get("/api/v1/packages/table", response_class=HTMLResponse)
async def packages_table(
    request: Request,
    search: str = Query(""),
    filter: str = Query("all"),
    sort: str = Query("score"),
    page: int = Query(1),
):
    async for session in get_db():
        stmt = select(Package)
        if search:
            stmt = stmt.where(
                or_(
                    Package.name.ilike(f"%{search}%"),
                    Package.version.ilike(f"%{search}%"),
                )
            )
        result = await session.execute(stmt)
        all_packages = result.scalars().all()

        scored_packages = []
        engine = ScoringEngine.from_config()

        for pkg in all_packages:
            scores_result = await session.execute(
                select(func.avg(PackageScore.score))
                .where(PackageScore.package_id == pkg.id)
            )
            avg = scores_result.scalar()
            grade = engine.get_grade(avg) if avg is not None else "healthy"
            scored_packages.append((pkg, avg, grade))

        if filter == "critical":
            scored_packages = [(p, s, g) for p, s, g in scored_packages if g == "critical"]
        elif filter == "warning":
            scored_packages = [(p, s, g) for p, s, g in scored_packages if g == "warning"]
        elif filter == "fair":
            scored_packages = [(p, s, g) for p, s, g in scored_packages if g == "fair"]
        elif filter == "healthy":
            scored_packages = [(p, s, g) for p, s, g in scored_packages if g == "healthy"]

        if sort == "score":
            scored_packages.sort(key=lambda x: x[1] if x[1] is not None else 100, reverse=True)
        elif sort == "name":
            scored_packages.sort(key=lambda x: x[0].name.lower())
        elif sort == "cves":
            scored_packages.sort(key=lambda x: len(x[0].cves or []), reverse=True)
        elif sort == "bugs":
            scored_packages.sort(key=lambda x: len(x[0].bugs or []), reverse=True)

        per_page = 20
        total_pages = max(1, (len(scored_packages) + per_page - 1) // per_page)
        start = (page - 1) * per_page
        page_packages = scored_packages[start : start + per_page]

        return _templates.TemplateResponse(
            "partials/package_table.html",
            {
                "request": request,
                "packages": page_packages,
                "page": page,
                "total_pages": total_pages,
            },
        )


@router.get("/api/v1/stats/summary", response_class=HTMLResponse)
async def stats_summary(request: Request):
    async for session in get_db():
        result = await session.execute(select(Package))
        all_packages = result.scalars().all()

        total = len(all_packages)
        engine = ScoringEngine.from_config()
        grades_count = {"critical": 0, "warning": 0, "fair": 0, "healthy": 0}

        for pkg in all_packages:
            scores_result = await session.execute(
                select(func.avg(PackageScore.score))
                .where(PackageScore.package_id == pkg.id)
            )
            avg = scores_result.scalar()
            grade = engine.get_grade(avg) if avg is not None else "healthy"
            grades_count[grade] += 1

        stats = {
            "total": total,
            "critical": grades_count["critical"],
            "warning": grades_count["warning"],
            "fair": grades_count["fair"],
            "healthy": grades_count["healthy"],
        }

        return _templates.TemplateResponse(
            "partials/summary_cards.html",
            {"request": request, "stats": stats},
        )


@router.get("/api/v1/scans/latest-status", response_class=HTMLResponse)
async def latest_scan_status(request: Request):
    async for session in get_db():
        result = await session.execute(
            select(ScanJob).order_by(ScanJob.created_at.desc()).limit(1)
        )
        job = result.scalar_one_or_none()

        if not job:
            return HTMLResponse('<span class="status-text status-idle">No scans yet</span>')

        status_class = "status-success" if job.status == "completed" else (
            "status-error" if job.status == "failed" else "status-running"
        )
        status_text = job.status.title()
        scanner = job.scanner.title()

        return HTMLResponse(
            f'<span class="status-text {status_class}">{scanner} scan: {status_text}</span>'
        )


async def _get_score_trend(session, package_id: int) -> list[dict]:
    result = await session.execute(
        select(
            PackageScore.calculated_at,
            func.avg(PackageScore.score).label("avg_score"),
        )
        .where(PackageScore.package_id == package_id)
        .group_by(func.date(PackageScore.calculated_at))
        .order_by(PackageScore.calculated_at.asc())
        .limit(30)
    )
    rows = result.all()
    return [
        {
            "date": row.calculated_at.strftime("%Y-%m-%d") if row.calculated_at else "",
            "score": round(row.avg_score, 1) if row.avg_score else 0,
        }
        for row in rows
    ]
