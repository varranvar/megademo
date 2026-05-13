# MDMO — Ubuntu Package Hygiene Dashboard

## Overview

MDMO is a FastAPI-based server/dashboard that analyzes Ubuntu package hygiene. It scans Launchpad for upstream bugs, matches NVD CVEs and Ubuntu OVAL vulnerability data against installed packages, computes a weighted hygiene score per package, and displays results in an interactive HTMX-powered dashboard.

**Stack:** FastAPI + Jinja2 + HTMX + Alpine.js + Chart.js, SQLite (aiosqlite), SQLAlchemy 2.0 async, APScheduler  
**Python:** >=3.11  
**Framework pattern:** Server-rendered HTML with HTMX partials (no SPA, no JS build step)

---

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run server (creates data/mdmo.db on first start)
uvicorn mdmo.main:app --reload

# Run tests
pytest tests/ -v

# Lint
ruff check mdmo/ tests/

# Docker
docker-compose up
```

Open http://localhost:8000 for the dashboard. API docs at http://localhost:8000/api/docs.

Set `NVD_API_KEY` env var to increase NVD API rate limits (optional, works without).

---

## Project Structure

```
mdmo/
├── pyproject.toml              # Dependencies, ruff + pytest config
├── config.yaml                 # Runtime settings (releases, scan intervals, scoring weights)
├── Dockerfile / docker-compose.yml
│
├── mdmo/                       # Python package root
│   ├── main.py                 # FastAPI app, lifespan, static files mount
│   ├── config.py               # Pydantic Settings + YAML loader → `settings` global
│   ├── database.py             # aiosqlite engine, `init_db()`, `get_db()` async generator
│   ├── models.py               # All SQLAlchemy 2.0 ORM models
│   ├── scheduler.py            # APScheduler jobs: scan_launchpad/nvd/oval + score_all
│   ├── version_compare.py      # dpkg --compare-versions reimplementation
│   │
│   ├── api/
│   │   ├── router.py           # APIRouter aggregation
│   │   └── packages.py         # Routes: /, /package/{name}, HTMX partials, API endpoints
│   │
│   ├── scanners/               # Data ingestion layer
│   │   ├── base.py             # BaseScanner ABC
│   │   ├── launchpad.py        # LaunchpadClient + LaunchpadScanner
│   │   ├── nvd.py              # NVDClient + CVEParser + NVDScanner
│   │   └── oval.py             # OVALParser + OVALScanner
│   │
│   ├── plugins/                # Extensible hygiene checks
│   │   ├── base.py             # HygieneCheck ABC, HygieneResult, PluginRegistry
│   │   └── builtin/
│   │       ├── bug_check.py    # Bug severity/scoring check
│   │       ├── cve_check.py    # CVE CVSS² + KEV check
│   │       └── freshness_check.py  # Version age check
│   │
│   ├── scoring/
│   │   └── engine.py           # ScoringEngine: runs plugins, aggregates, persists scores
│   │
│   ├── templates/              # Jinja2 templates (server-rendered HTML)
│   │   ├── layout.html         # Base layout with navbar, HTMX/Chart.js/Alpine imports
│   │   ├── dashboard.html      # Main list view with search/filter/sort
│   │   ├── package_detail.html # Per-package detail with tabs
│   │   └── partials/           # HTMX swap fragments
│   │       ├── package_table.html, summary_cards.html
│   │       ├── bugs_table.html, cves_table.html
│   │       ├── score_badge.html, severity_badge.html
│   │
│   └── static/
│       ├── css/dashboard.css   # 726 lines, complete component styles
│       └── js/app.js           # Chart.js init, HTMX swap animations
│
└── tests/
    ├── conftest.py
    ├── test_config.py          # Config loading tests
    └── test_version_compare.py # 22 parametrized dpkg comparison cases
```

---

## Conventions

### Imports
- Always use `from mdmo.X import Y` style (absolute imports within the package).
- Third-party imports first, then `mdmo` imports, separated by blank line.

### Database Access
- Use `async for session in get_db():` for route handlers (generator yields one session).
- Use `async with async_session_factory() as session:` for scanners/scheduler (manual session management).
- All sessions are `AsyncSession` from SQLAlchemy 2.0.
- Models use the new `Mapped[]` + `mapped_column()` style (DeclarativeBase 2.0).

### Config Access
- `from mdmo.config import settings` gives a `SettingsProxy` singleton.
- Access nested config: `settings.database.path`, `settings.ubuntu.releases`, `settings.scan.intervals.nvd`, etc.
- `settings.model_dump()` returns the full config dict (used by `ScoringEngine.from_config()`).

### Templates
- All templates extend `layout.html` (provides navbar, JS/CSS imports).
- HTMX attributes: `hx-get`, `hx-target`, `hx-trigger`, `hx-swap` for partial page updates.
- Macros in `partials/score_badge.html` and `partials/severity_badge.html` for reusable components.
- Template responses use `_templates.TemplateResponse(name, {"request": request, ...})`.

### Adding a New Hygiene Check
1. Create `mdmo/plugins/builtin/my_check.py` (or anywhere that gets imported).
2. Subclass `HygieneCheck`, set `name`, `description`, `weight`.
3. Implement `async def check(self, package) -> HygieneResult` — return score 0.0–1.0.
4. The `__init_subclass__` hook auto-registers it with `PluginRegistry`. Zero wiring needed.
5. Optionally configure weight in `config.yaml` under `scoring.weights.plugins`.

### Scoring
- `ScoringEngine.score_package()` runs all registered plugins concurrently via `asyncio.gather`.
- Weighted sum: `Σ(weight_i × score_i)`, normalized to 0–100.
- Grades: 0–30 = critical (red), 31–55 = warning (orange), 56–75 = fair (yellow), 76–100 = healthy (green).
- Results persisted to `PackageScore` and `Heuristic` tables.

### Scan Lifecycle
- APScheduler runs 4 jobs on startup: `scan_launchpad` (24h), `scan_nvd` (6h), `scan_oval` (24h), `score_all` (1h).
- Each scan creates a `ScanJob` record tracking status/progress.
- On first run with empty DB, Launchpad scanner auto-discovers packages for tracked releases.
- NVD scanner does delta polling using `lastModStartDate`/`lastModEndDate`.
- OVAL scanner uses checksum comparison (`.meta` files) to skip unchanged data.

### Version Comparison
- `dpkg_compare_versions(a, b)` returns -1/0/1 per Debian Policy 5.6.12.
- Handles epochs (`1:2.0`), debian revisions (`-0ubuntu1`), tildes (`~rc1`), numeric segments.
- `is_version_affected(installed, fixed, operation)` for vulnerability checking.

---

## Key Commands

| Command | Purpose |
|---------|---------|
| `uvicorn mdmo.main:app --reload` | Start development server |
| `pytest tests/ -v` | Run all tests |
| `ruff check mdmo/ tests/` | Lint |
| `ruff format mdmo/ tests/` | Format (if needed) |
| `docker-compose up` | Production Docker deployment |

---

## Configuration

Edit `config.yaml` to change:
- `ubuntu.releases` — which Ubuntu releases to track
- `scan.intervals.*` — scan frequency in seconds
- `scoring.weights.*` — component weights in aggregate score
- `nvd.api_key` — set to `${NVD_API_KEY}` to read from env var

---

## Data Sources

| Source | URL | Rate Limit | Caching |
|--------|-----|-----------|---------|
| Launchpad API | `api.launchpad.net/devel` | ~200 req/day (anon) | In-memory ETag (6h tasks, 12h bugs) |
| NVD CVE API 2.0 | `services.nvd.nist.gov/rest/json/cves/2.0` | 5 req/30s (no key), 50/30s (with key) | Delta-based polling |
| Ubuntu OVAL XML | `security-metadata.canonical.com/oval` | Unrestricted | SHA256 checksum comparison |

---

## Labels for Future Work

When adding new features, use the following branch/tag conventions:
- `feat/<description>` for new features
- `fix/<description>` for bug fixes
- `refactor/<description>` for refactoring
- New scanners go in `mdmo/scanners/` and subclass `BaseScanner`
- New hygiene checks go in `mdmo/plugins/builtin/` and subclass `HygieneCheck`
- New API endpoints go in `mdmo/api/` and are included via `mdmo/api/router.py`
- New templates go in `mdmo/templates/` (full pages) or `mdmo/templates/partials/` (HTMX fragments)
