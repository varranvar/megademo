"""Launchpad API client for bug triage.

Uses launchpadlib with anonymous read-only access to query bugs,
search for similar bugs, and find upstream project info.
"""

import re
from dataclasses import dataclass, field
from launchpadlib.launchpad import Launchpad


LP_SERVICE_ROOT = "production"
LP_APP_NAME = "lp-bug-triage"
LP_VERSION = "devel"


@dataclass
class BugInfo:
    id: int
    title: str
    description: str
    tags: list[str]
    status: str
    importance: str
    package_name: str | None
    heat: int
    date_created: str
    web_link: str


@dataclass
class UpstreamInfo:
    project_name: str | None = None
    homepage_url: str | None = None
    bug_tracker_url: str | None = None
    bug_watch_urls: list[str] = field(default_factory=list)


def _get_lp():
    return Launchpad.login_anonymously(LP_APP_NAME, LP_SERVICE_ROOT, version=LP_VERSION)


def get_bug(bug_id: int) -> BugInfo:
    """Fetch a bug by ID and return structured info."""
    lp = _get_lp()
    bug = lp.bugs[bug_id]

    # Get all bug tasks - prefer non-Fix Released tasks for package name
    tasks = list(bug.bug_tasks)
    first_task = tasks[0] if tasks else None
    
    # Find the most relevant task (prefer non-closed statuses)
    preferred_task = first_task
    closed_statuses = {"Fix Released", "Invalid", "Won't Fix", "Expired"}
    for task in tasks:
        if task.status not in closed_statuses:
            preferred_task = task
            break

    package_name = None
    if preferred_task:
        target_name = preferred_task.bug_target_display_name or ""
        # Format is typically "packagename (Ubuntu)" or "projectname"
        match = re.match(r"^(\S+)", target_name)
        if match:
            package_name = match.group(1).lower()

    return BugInfo(
        id=bug.id,
        title=bug.title,
        description=bug.description or "",
        tags=list(bug.tags),
        status=preferred_task.status if preferred_task else "Unknown",
        importance=preferred_task.importance if preferred_task else "Unknown",
        package_name=package_name,
        heat=bug.heat or 0,
        date_created=str(bug.date_created),
        web_link=bug.web_link,
    )


def search_similar_bugs(bug_info: BugInfo, max_results: int = 20) -> list[BugInfo]:
    """Search for bugs similar to the given bug.

    Strategy:
    1. Search same package for bugs with overlapping tags
    2. Search same package with keywords from the title
    """
    lp = _get_lp()
    results: dict[int, BugInfo] = {}

    if not bug_info.package_name:
        return []

    ubuntu = lp.distributions["ubuntu"]

    try:
        pkg = ubuntu.getSourcePackage(name=bug_info.package_name)
    except Exception:
        # Package might not exist or might be a project, not a distro package
        try:
            project = lp.projects[bug_info.package_name]
            pkg = project
        except Exception:
            return []

    # Search by tags if the bug has any
    if bug_info.tags:
        try:
            tasks = pkg.searchTasks(
                tags=bug_info.tags[:5],
                tags_combinator="Any",
                status=["New", "Confirmed", "Triaged", "In Progress", "Fix Committed"],
                omit_duplicates=True,
            )
            for task in tasks[:max_results]:
                b = task.bug
                if b.id == bug_info.id:
                    continue
                target_name = task.bug_target_display_name or ""
                match = re.match(r"^(\S+)", target_name)
                pname = match.group(1) if match else None
                results[b.id] = BugInfo(
                    id=b.id,
                    title=b.title,
                    description=(b.description or "")[:500],
                    tags=list(b.tags),
                    status=task.status,
                    importance=task.importance,
                    package_name=pname,
                    heat=b.heat or 0,
                    date_created=str(b.date_created),
                    web_link=b.web_link,
                )
        except Exception:
            pass

    # Search by title keywords
    title_words = [w for w in bug_info.title.split() if len(w) > 3]
    if title_words:
        search_text = " ".join(title_words[:5])
        try:
            tasks = pkg.searchTasks(
                search_text=search_text,
                status=["New", "Confirmed", "Triaged", "In Progress", "Fix Committed"],
                omit_duplicates=True,
            )
            for task in tasks[:max_results]:
                b = task.bug
                if b.id == bug_info.id or b.id in results:
                    continue
                target_name = task.bug_target_display_name or ""
                match = re.match(r"^(\S+)", target_name)
                pname = match.group(1) if match else None
                results[b.id] = BugInfo(
                    id=b.id,
                    title=b.title,
                    description=(b.description or "")[:500],
                    tags=list(b.tags),
                    status=task.status,
                    importance=task.importance,
                    package_name=pname,
                    heat=b.heat or 0,
                    date_created=str(b.date_created),
                    web_link=b.web_link,
                )
        except Exception:
            pass

    return list(results.values())[:max_results]


def get_upstream_info(bug_id: int) -> UpstreamInfo:
    """Find upstream project information for a bug.

    Checks:
    1. upstream_product_link on the source package
    2. bug_watch_link entries on bug tasks (direct upstream issue URLs)
    """
    lp = _get_lp()
    bug = lp.bugs[bug_id]
    info = UpstreamInfo()

    tasks = list(bug.bug_tasks)
    if not tasks:
        return info

    # Find the most relevant task (prefer non-closed statuses)
    closed_statuses = {"Fix Released", "Invalid", "Won't Fix", "Expired"}
    preferred_task = tasks[0]
    for task in tasks:
        if task.status not in closed_statuses:
            preferred_task = task
            break

    target_name = preferred_task.bug_target_display_name or ""
    match = re.match(r"^(\S+)", target_name)
    package_name = match.group(1) if match else None

    # Try to get upstream from the source package
    if package_name:
        try:
            ubuntu = lp.distributions["ubuntu"]
            pkg = ubuntu.getSourcePackage(name=package_name)
            upstream = pkg.upstream_product
            if upstream:
                info.project_name = upstream.name
                info.homepage_url = upstream.homepage_url
                # Try to get bug tracker
                try:
                    if upstream.bug_tracker_link:
                        tracker = lp.load(upstream.bug_tracker_link)
                        info.bug_tracker_url = getattr(tracker, "base_url", None)
                except Exception:
                    pass
        except Exception:
            pass

    # Collect bug watch URLs (direct upstream issue links)
    for task in tasks:
        try:
            if task.bug_watch_link:
                watch = lp.load(task.bug_watch_link)
                if hasattr(watch, "url") and watch.url:
                    info.bug_watch_urls.append(watch.url)
        except Exception:
            pass

    # Also check bug watches collection directly
    try:
        for watch in bug.bug_watches:
            if hasattr(watch, "url") and watch.url:
                url = watch.url
                if url not in info.bug_watch_urls:
                    info.bug_watch_urls.append(url)
    except Exception:
        pass

    return info
