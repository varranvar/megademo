import gzip
import json
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

import cachetools
import httpx
from launchpadlib.launchpad import Launchpad
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ubuntu-archive")

ARCHIVE_BASE = "https://archive.ubuntu.com/ubuntu"
CHANGES_BASE = "https://changelogs.ubuntu.com/changelogs"
AUTOPKGTEST_API = "https://autopkgtest.ubuntu.com"
LAUNCHPAD_CACHE = os.path.join(os.path.dirname(__file__), ".launchpad_cache")
DATA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "frontend", "data", "ubuntu-archive"
)

SERIES_ALIASES: dict[str, str] = {
    "14.04": "trusty",
    "16.04": "xenial",
    "18.04": "bionic",
    "20.04": "focal",
    "22.04": "jammy",
    "24.04": "noble",
    "24.10": "oracular",
    "25.04": "plucky",
    "26.04": "resolute",
}

_package_cache: cachetools.TTLCache = cachetools.TTLCache(maxsize=256, ttl=300)
_http_client: httpx.AsyncClient | None = None
_lp: Launchpad | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
    return _http_client


def _get_lp() -> Launchpad:
    global _lp
    if _lp is None:
        _lp = Launchpad.login_anonymously("ubuntu-archive-mcp", "production", launchpadlib_dir=LAUNCHPAD_CACHE)
    return _lp


def _write_result(package_name: str, result: dict) -> str | None:
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except Exception:
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    safe_name = re.sub(r"[^\w-]", "_", package_name or "unknown")
    filename = f"{safe_name}-{timestamp}.json"
    filepath = os.path.join(DATA_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    except Exception:
        return None

    manifest_path = os.path.join(DATA_DIR, "manifest.json")
    manifest = []
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            manifest = []

    if filename not in manifest:
        manifest.append(filename)
        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        except Exception:
            pass

    return filename


def _resolve_series(series: str) -> str:
    return SERIES_ALIASES.get(series, series)


def _parse_deb822(text: str) -> list[dict[str, str]]:
    paragraphs: list[dict[str, str]] = []
    current: dict[str, str] = {}
    last_key = ""
    for line in text.splitlines():
        if not line.strip():
            if current:
                paragraphs.append(current)
                current = {}
                last_key = ""
            continue
        if line.startswith(" ") or line.startswith("\t"):
            if last_key and last_key in current:
                current[last_key] += "\n" + line.strip()
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            current[key] = value.strip()
            last_key = key
    if current:
        paragraphs.append(current)
    return paragraphs


async def _fetch_packages_index(series: str, component: str = "main", arch: str = "amd64") -> list[dict[str, str]]:
    cache_key = f"packages:{series}:{component}:{arch}"
    if cache_key in _package_cache:
        return _package_cache[cache_key]
    client = _get_http_client()
    for pocket in ["", "-updates", "-security"]:
        url = f"{ARCHIVE_BASE}/dists/{series}{pocket}/{component}/binary-{arch}/Packages.gz"
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                break
        except httpx.HTTPError:
            continue
    else:
        return []
    decompressed = gzip.decompress(resp.content).decode("utf-8")
    paragraphs = _parse_deb822(decompressed)
    _package_cache[cache_key] = paragraphs
    return paragraphs


async def _fetch_sources_index(series: str, component: str = "main") -> list[dict[str, str]]:
    cache_key = f"sources:{series}:{component}"
    if cache_key in _package_cache:
        return _package_cache[cache_key]
    client = _get_http_client()
    for pocket in ["", "-updates", "-security"]:
        url = f"{ARCHIVE_BASE}/dists/{series}{pocket}/{component}/source/Sources.gz"
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                break
        except httpx.HTTPError:
            continue
    else:
        return []
    decompressed = gzip.decompress(resp.content).decode("utf-8")
    paragraphs = _parse_deb822(decompressed)
    _package_cache[cache_key] = paragraphs
    return paragraphs


@mcp.tool()
async def get_series_info() -> list[dict[str, Any]]:
    """List all Ubuntu series with version, status, and active state."""
    lp = _get_lp()
    ubuntu = lp.distributions["ubuntu"]
    result = []
    for s in ubuntu.series:
        result.append({
            "name": s.name,
            "version": s.version,
            "status": s.status,
            "active": s.active,
        })
    return result


@mcp.tool()
async def get_package_version(
    package: str,
    series: str,
    pocket: str = "Release",
    component: str = "main",
) -> dict[str, Any]:
    """Get the latest published version of a source package in a given series and pocket.

    Args:
        package: Source package name (e.g., 'rustc', 'cargo')
        series: Ubuntu series name or version (e.g., 'noble', '24.04')
        pocket: Archive pocket - Release, Security, Updates, Proposed, Backports
        component: Archive component - main, universe, multiverse, restricted
    """
    series = _resolve_series(series)
    lp = _get_lp()
    ubuntu = lp.distributions["ubuntu"]
    try:
        ds = ubuntu.getSeries(name_or_version=series)
    except Exception:
        return {"error": f"Series '{series}' not found."}
    try:
        pubs = ubuntu.main_archive.getPublishedSources(
            source_name=package, distro_series=ds, pocket=pocket, status="Published"
        )
        pubs = list(pubs)
    except Exception as exc:
        return {"error": f"Launchpad query failed: {exc}"}
    if not pubs:
        return {"error": f"No published version of '{package}' found in {series}/{pocket}."}
    pub = pubs[0]
    return {
        "package": package,
        "version": pub.source_package_version,
        "series": series,
        "pocket": pocket,
        "component": pub.component_name,
        "date_published": str(pub.date_published) if pub.date_published else None,
    }


@mcp.tool()
async def search_packages(
    query: str,
    series: str = "noble",
    component: str = "main",
    search_field: str = "name",
    limit: int = 20,
) -> dict[str, Any]:
    """Search for packages in the Ubuntu Archive by name or description.

    Args:
        query: Search term (supports wildcards like 'rust-*')
        series: Ubuntu series name or version
        component: Archive component to search
        search_field: 'name' to search package names, 'description' to search descriptions
        limit: Maximum number of results
    """
    series = _resolve_series(series)
    sources = await _fetch_sources_index(series, component)
    binaries = await _fetch_packages_index(series, component)

    pattern = query.replace("*", ".*").replace("?", ".")
    regex = re.compile(f"^{pattern}$", re.IGNORECASE) if "*" in query else re.compile(pattern, re.IGNORECASE)

    src_matches = []
    for p in sources:
        name = p.get("Package", "")
        desc = p.get("Description", "").split("\n")[0] if "Description" in p else ""
        if search_field == "name" and regex.search(name):
            src_matches.append({"name": name, "version": p.get("Version", ""), "description": desc, "type": "source"})
        elif search_field == "description" and regex.search(desc):
            src_matches.append({"name": name, "version": p.get("Version", ""), "description": desc, "type": "source"})

    bin_matches = []
    for p in binaries:
        name = p.get("Package", "")
        desc = p.get("Description", "").split("\n")[0] if "Description" in p else ""
        if search_field == "name" and regex.search(name):
            bin_matches.append({"name": name, "version": p.get("Version", ""), "description": desc, "type": "binary"})
        elif search_field == "description" and regex.search(desc):
            bin_matches.append({"name": name, "version": p.get("Version", ""), "description": desc, "type": "binary"})

    return {
        "query": query,
        "series": series,
        "component": component,
        "source_matches": src_matches[:limit],
        "binary_matches": bin_matches[:limit],
        "total_source": len(src_matches),
        "total_binary": len(bin_matches),
    }


@mcp.tool()
async def get_package_details(
    package: str,
    series: str = "noble",
    component: str = "main",
    arch: str = "amd64",
) -> dict[str, Any]:
    """Get detailed metadata for a package: dependencies, maintainer, section, description.

    Args:
        package: Binary or source package name
        series: Ubuntu series name or version
        component: Archive component
        arch: Architecture
    """
    series = _resolve_series(series)
    binaries = await _fetch_packages_index(series, component, arch)
    sources = await _fetch_sources_index(series, component)

    for p in binaries:
        if p.get("Package") == package:
            return {"type": "binary", "data": p}

    for p in sources:
        if p.get("Package") == package:
            return {"type": "source", "data": p}

    return {"error": f"Package '{package}' not found in {series}/{component}/{arch}."}


@mcp.tool()
async def get_changelog(
    package: str,
    version: str | None = None,
    component: str = "main",
) -> dict[str, Any]:
    """Fetch the Debian changelog for a package.

    If version is omitted, looks up the latest published version via Launchpad first.

    Args:
        package: Source package name
        version: Specific version (latest if omitted)
        component: Archive component
    """
    if not version:
        lp = _get_lp()
        ubuntu = lp.distributions["ubuntu"]
        try:
            pubs = ubuntu.main_archive.getPublishedSources(source_name=package, status="Published")
            pubs = list(pubs)
            if pubs:
                version = pubs[0].source_package_version
        except Exception:
            pass
        if not version:
            return {"error": f"Could not determine latest version for '{package}'."}

    letter = package[0] if package else "z"
    url = f"{CHANGES_BASE}/pool/{component}/{letter}/{package}/{package}_{version}/changelog"
    client = _get_http_client()
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        return {"package": package, "version": version, "changelog": resp.text[:10000]}
    except httpx.HTTPError:
        return {
            "error": f"Changelog not found for {package}={version} at changelogs.ubuntu.com.",
            "instruction": "Download the source package and read debian/changelog directly.",
        }


@mcp.tool()
async def get_build_status(
    package: str,
    series: str = "noble",
) -> dict[str, Any]:
    """Get build status for a source package across architectures.

    Args:
        package: Source package name
        series: Ubuntu series name or version
    """
    series = _resolve_series(series)
    lp = _get_lp()
    ubuntu = lp.distributions["ubuntu"]
    try:
        builds = ubuntu.main_archive.getBuildRecords(source_name=package)
    except Exception as exc:
        return {"error": f"Launchpad query failed: {exc}"}
    result = []
    count = 0
    for b in builds:
        if count >= 50:
            break
        series_name = b.distro_series.name if b.distro_series else "unknown"
        if series_name != series:
            continue
        result.append({
            "series": series_name,
            "arch": b.arch_tag,
            "status": b.buildstate,
            "date_built": str(b.datebuilt) if b.datebuilt else None,
            "build_log_url": b.build_log_url,
            "duration": str(b.datebuilt - b.date_first_dispatched) if b.datebuilt and b.date_first_dispatched else None,
        })
        count += 1
    return {"package": package, "series": series, "builds": result}


@mcp.tool()
async def get_build_log(
    package: str,
    series: str = "noble",
    arch: str = "amd64",
) -> dict[str, Any]:
    """Fetch the build log for a package on a specific architecture.

    Args:
        package: Source package name
        series: Ubuntu series name or version
        arch: Architecture
    """
    series = _resolve_series(series)
    lp = _get_lp()
    ubuntu = lp.distributions["ubuntu"]
    try:
        builds = ubuntu.main_archive.getBuildRecords(source_name=package)
    except Exception:
        return {"error": f"Could not fetch builds for '{package}'."}
    for b in builds:
        if b.distro_series and b.distro_series.name != series:
            continue
        if b.arch_tag != arch:
            continue
        log_url = b.build_log_url
        if not log_url:
            continue
        client = _get_http_client()
        try:
            resp = await client.get(log_url)
            resp.raise_for_status()
            return {
                "package": package,
                "series": series,
                "arch": arch,
                "log_url": log_url,
                "log_tail": resp.text[-8000:],
            }
        except httpx.HTTPError:
            return {"error": f"Could not fetch build log from {log_url}"}
    return {"error": f"No build found for '{package}' on {series}/{arch}."}


@mcp.tool()
async def get_autopkgtest_results(
    package: str,
    series: str = "noble",
    arch: str = "amd64",
) -> dict[str, Any]:
    """Query autopkgtest results for a package.

    Args:
        package: Source package name
        series: Ubuntu series name or version
        arch: Architecture
    """
    series = _resolve_series(series)
    client = _get_http_client()
    try:
        resp = await client.get(
            f"{AUTOPKGTEST_API}/results",
            params={"release": series, "package": package, "arch": arch},
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as exc:
        return {"error": f"Could not fetch autopkgtest results: {exc}"}
    results = []
    for entry in data[:20]:
        results.append({
            "release": entry.get("release"),
            "package": entry.get("package"),
            "version": entry.get("version"),
            "arch": entry.get("arch"),
            "status": entry.get("status"),
            "test_names": entry.get("test_names", []),
            "run_id": entry.get("run_id"),
        })
    return {"package": package, "series": series, "arch": arch, "results": results}


@mcp.tool()
async def get_reverse_dependencies(
    package: str,
    series: str = "noble",
    component: str = "main",
    arch: str = "amd64",
) -> dict[str, Any]:
    """Find packages that depend on a given package.

    Args:
        package: Binary package name
        series: Ubuntu series name or version
        component: Archive component
        arch: Architecture
    """
    series = _resolve_series(series)
    binaries = await _fetch_packages_index(series, component, arch)
    rdeps: dict[str, list[str]] = defaultdict(list)
    dep_fields = ["Depends", "Pre-Depends", "Recommends", "Suggests"]
    for p in binaries:
        name = p.get("Package", "")
        for field in dep_fields:
            raw = p.get(field, "")
            if not raw:
                continue
            for dep_clause in raw.split(","):
                dep_name = dep_clause.strip().split()[0]
                if dep_name == package:
                    rdeps[field].append(name)
                    break
    return {
        "package": package,
        "series": series,
        "reverse_dependencies": {k: v for k, v in rdeps.items() if v},
    }


@mcp.tool()
async def get_bug_list(
    package: str,
    status: str | None = None,
    importance: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Search Launchpad bugs for a source package.

    Args:
        package: Source package name
        status: Bug status filter (New, Confirmed, Triaged, In Progress, Fix Committed, Fix Released, Invalid, Won't Fix, Opinionated, Expired)
        importance: Bug importance filter (Critical, High, Medium, Low, Wishlist, Undecided)
        limit: Maximum number of results
    """
    lp = _get_lp()
    ubuntu = lp.distributions["ubuntu"]
    try:
        srcpkg = ubuntu.getSourcePackage(name=package)
    except Exception:
        return {"error": f"Package '{package}' not found."}
    kwargs: dict[str, Any] = {}
    if status:
        kwargs["status"] = status
    if importance:
        kwargs["importance"] = importance
    try:
        tasks = srcpkg.searchTasks(**kwargs)
    except Exception as exc:
        return {"error": f"Bug search failed: {exc}"}
    bugs = []
    for t in tasks:
        if len(bugs) >= limit:
            break
        bug = t.bug
        assignee_link = getattr(t, "assignee_link", None)
        assignee = assignee_link.rsplit("/", 1)[-1] if assignee_link else None
        bugs.append({
            "id": bug.id,
            "title": bug.title,
            "status": t.status,
            "importance": t.importance,
            "assignee": assignee,
            "url": f"https://bugs.launchpad.net/bugs/{bug.id}",
        })
    return {"package": package, "bugs": bugs}


@mcp.tool()
async def run_lintian(
    changes_file: str,
    severity: str = "warning",
) -> dict[str, Any]:
    """Run lintian on a .changes or .deb file and return structured results.

    If lintian is not available in the environment, returns instructions
    for the user to run it locally and paste results back.

    Args:
        changes_file: Path to .changes or .deb file
        severity: Minimum severity to report - error, warning, info, pedantic
    """
    severity_map = {"error": "E", "warning": "W", "info": "I", "pedantic": "P"}
    min_severity = severity_map.get(severity, "W")
    try:
        result = subprocess.run(
            ["lintian", "--output-format=json", changes_file],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode not in (0, 1):
            return {"error": f"lintian failed: {result.stderr}"}
        tags = json.loads(result.stdout) if result.stdout.strip() else []
    except FileNotFoundError:
        return {
            "error": "lintian is not installed in this environment.",
            "instruction": (
                f"Install lintian (`sudo apt install lintian`) and run: "
                f"`lintian --output-format=json {changes_file}`. "
                f"Then paste the JSON output back for analysis."
            ),
        }
    except subprocess.TimeoutExpired:
        return {"error": "lintian timed out after 120 seconds."}
    order = "EWIPOX"
    min_idx = order.index(min_severity) if min_severity in order else 1
    filtered = [t for t in tags if order.index(t.get("code", "W")) <= min_idx]
    return {"file": changes_file, "tags": filtered, "total": len(tags), "filtered": len(filtered)}


@mcp.tool()
async def get_source_package(
    package: str,
    series: str = "noble",
    dest_dir: str | None = None,
) -> dict[str, Any]:
    """Download and extract a source package. Returns instructions if not run locally.

    Args:
        package: Source package name
        series: Ubuntu series name or version
        dest_dir: Directory to download into (default: /tmp/<package>)
    """
    series = _resolve_series(series)
    dest = dest_dir or f"/tmp/{package}"
    try:
        result = subprocess.run(
            ["apt-get", "source", f"{package}/{series}"],
            capture_output=True, text=True, timeout=300,
            cwd=dest,
        )
        if result.returncode != 0:
            return {"error": f"apt-get source failed: {result.stderr}"}
    except FileNotFoundError:
        return {
            "error": "apt-get is not available in this environment.",
            "instruction": (
                f"Run locally: `mkdir -p {dest} && cd {dest} && apt-get source {package}/{series}`. "
                f"Then point the agent at the extracted source directory."
            ),
        }
    return {
        "package": package,
        "series": series,
        "dest_dir": dest,
        "instruction": f"Source extracted to {dest}. Use the files there for analysis.",
    }


@mcp.tool()
async def get_copyright_file(
    package: str,
    version: str | None = None,
    component: str = "main",
) -> dict[str, Any]:
    """Fetch the debian/copyright file for a package.

    If version is omitted, looks up the latest published version via Launchpad.

    Args:
        package: Source package name
        version: Specific version (latest if omitted)
        component: Archive component
    """
    if not version:
        lp = _get_lp()
        ubuntu = lp.distributions["ubuntu"]
        try:
            pubs = ubuntu.main_archive.getPublishedSources(source_name=package, status="Published")
            pubs = list(pubs)
            if pubs:
                version = pubs[0].source_package_version
        except Exception:
            pass
        if not version:
            return {"error": f"Could not determine latest version for '{package}'."}

    letter = package[0] if package else "z"
    url = f"{CHANGES_BASE}/pool/{component}/{letter}/{package}/{package}_{version}/copyright"
    client = _get_http_client()
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        return {"package": package, "version": version, "copyright": resp.text[:15000]}
    except httpx.HTTPError:
        return {
            "error": "Could not fetch copyright file from changelogs.ubuntu.com.",
            "instruction": "Download the source package and read debian/copyright directly.",
        }


@mcp.tool()
async def get_package_files(
    package: str,
    series: str = "noble",
    component: str = "main",
    arch: str = "amd64",
) -> dict[str, Any]:
    """List files installed by a binary package using the Contents index.

    Args:
        package: Binary package name
        series: Ubuntu series name or version
        component: Archive component
        arch: Architecture
    """
    series = _resolve_series(series)
    client = _get_http_client()
    contents_url = f"{ARCHIVE_BASE}/dists/{series}/{component}/Contents-{arch}.gz"
    try:
        resp = await client.get(contents_url)
        resp.raise_for_status()
        decompressed = gzip.decompress(resp.content).decode("utf-8", errors="replace")
    except httpx.HTTPError:
        return {"error": f"Could not fetch Contents index for {series}/{component}/{arch}."}
    files: list[str] = []
    for line in decompressed.splitlines():
        parts = line.rsplit(None, 1)
        if len(parts) == 2 and parts[1] == package:
            files.append(parts[0])
        if len(files) >= 200:
            break
    return {"package": package, "series": series, "arch": arch, "files": files, "truncated": len(files) >= 200}


@mcp.tool()
async def analyze_package(
    package: str,
    series: str = "noble",
    component: str = "main",
    arch: str = "amd64",
) -> str:
    """Perform a comprehensive analysis of a package in the Ubuntu Archive.

    Aggregates version info, build status, autopkgtest results, reverse
    dependencies, open bugs, and package details into a single report
    and writes it to the frontend data directory for display.

    Args:
        package: Source or binary package name (e.g., 'rustc', 'cargo')
        series: Primary Ubuntu series to analyse
        component: Archive component (main, universe, etc.)
        arch: Architecture for build/test results
    """
    resolved = _resolve_series(series)

    versions = {}
    for alias, codename in [("resolute (26.04 LTS)", "resolute"), ("plucky (25.04)", "plucky"), ("noble (24.04 LTS)", "noble"), ("jammy (22.04 LTS)", "jammy")]:
        try:
            v = await get_package_version(package, codename)
            if "error" not in v:
                versions[alias] = v.get("version", "N/A")
        except Exception:
            pass
    if not versions:
        versions[resolved] = "N/A"

    build_data = {}
    for alias, codename in [("resolute (26.04 LTS)", "resolute"), ("noble (24.04 LTS)", "noble")]:
        try:
            bs = await get_build_status(package, codename)
            if "error" not in bs:
                build_data[alias] = bs.get("builds", [])
        except Exception:
            pass

    adt_data = {}
    for alias, codename in [("noble (24.04 LTS)", "noble"), ("jammy (22.04 LTS)", "jammy")]:
        try:
            adt = await get_autopkgtest_results(package, codename, arch)
            if "error" not in adt:
                adt_data[alias] = adt.get("results", [])
        except Exception:
            pass

    rdep_data = {}
    try:
        rdeps = await get_reverse_dependencies(package, resolved, component, arch)
        if "error" not in rdeps:
            rdep_data[f"{resolved} ({series})"] = rdeps.get("reverse_dependencies", {})
    except Exception:
        pass

    bug_data = []
    try:
        bl = await get_bug_list(package)
        if "error" not in bl:
            bug_data = bl.get("bugs", [])
    except Exception:
        pass

    details = {}
    try:
        d = await get_package_details(package, resolved, component, arch)
        if "error" not in d:
            details = d
    except Exception:
        pass

    total_builds = sum(len(v) for v in build_data.values())
    succeeded = sum(1 for builds in build_data.values() for b in builds if "Successfully" in b.get("status", ""))
    failed = sum(1 for builds in build_data.values() for b in builds if "Failed" in b.get("status", ""))
    in_progress = sum(1 for builds in build_data.values() for b in builds if "building" in b.get("status", "").lower())
    adt_pass = sum(1 for results in adt_data.values() for r in results if r.get("status") == "pass")
    adt_fail = sum(1 for results in adt_data.values() for r in results if r.get("status") == "fail")
    rdep_count = sum(len(pkgs) for deps in rdep_data.values() for pkgs in deps.values())
    open_bugs = len(bug_data)
    critical_bugs = sum(1 for b in bug_data if b.get("importance") == "Critical")
    high_bugs = sum(1 for b in bug_data if b.get("importance") == "High")

    result = {
        "package": package,
        "scan_date": datetime.now(timezone.utc).isoformat(),
        "versions": versions,
        "build_status": build_data,
        "autopkgtest_results": adt_data,
        "reverse_dependencies": rdep_data,
        "bugs": bug_data,
        "package_details": details,
        "summary": {
            "series_count": len(versions),
            "architectures_built": total_builds,
            "builds_succeeded": succeeded,
            "builds_failed": failed,
            "builds_in_progress": in_progress,
            "autopkgtest_pass": adt_pass,
            "autopkgtest_fail": adt_fail,
            "reverse_dep_count": rdep_count,
            "open_bugs": open_bugs,
            "critical_bugs": critical_bugs,
            "high_bugs": high_bugs,
        },
    }

    _write_result(package, result)

    return json.dumps(result, indent=2, default=str)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
