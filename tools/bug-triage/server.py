"""Launchpad Bug Triage MCP Server.

An MCP server that provides tools for finding similar Launchpad bugs
and exploring upstream issue trackers.
"""

import json
import os
import re
from dataclasses import asdict
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP

import lp_client
import upstream_search

DATA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "frontend", "data", "bug-triage"
)


def _write_result(package_name: str, result: dict) -> str | None:
    """Write analysis result to the frontend data directory."""
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

STOP_WORDS = {
    "the", "and", "for", "with", "from", "this", "that", "have", "has",
    "was", "were", "been", "being", "will", "would", "could", "should",
    "not", "but", "are", "can", "does", "into", "when", "where", "which",
    "their", "there", "then", "than", "also", "just", "only", "very",
    "some", "other", "about", "after", "before", "between", "under",
    "over", "more", "most", "such", "each", "every",
}


def extract_keywords(text: str, max_keywords: int = 6) -> list[str]:
    """Extract meaningful keywords from text for search queries."""
    # Remove punctuation, keep alphanumeric and hyphens
    words = re.findall(r"[a-zA-Z0-9][\w.-]*[a-zA-Z0-9]|[a-zA-Z0-9]", text)
    keywords = []
    for w in words:
        if len(w) < 3:
            continue
        if w.lower() in STOP_WORDS:
            continue
        keywords.append(w)
        if len(keywords) >= max_keywords:
            break
    return keywords

server = FastMCP("lp-bug-triage", log_level="WARNING")


@server.tool()
def get_bug_details(bug_id: int) -> str:
    """Get detailed information about a Launchpad bug by its ID.

    Returns the bug's title, description, tags, status, importance,
    package name, and upstream project info.
    """
    bug = lp_client.get_bug(bug_id)
    upstream = lp_client.get_upstream_info(bug_id)

    result = {
        "bug": asdict(bug),
        "upstream": asdict(upstream),
    }
    return json.dumps(result, indent=2, default=str)


@server.tool()
def search_similar_bugs(bug_id: int) -> str:
    """Find bugs similar to the given Launchpad bug.

    Searches Launchpad for bugs in the same package with overlapping
    tags or matching title keywords. Also finds upstream project info
    and searches the upstream issue tracker for related issues.

    Returns a structured report with:
    - The input bug's details
    - Similar Launchpad bugs
    - Upstream project information
    - Similar upstream issues (if upstream repo is found)
    """
    # 1. Fetch the input bug
    bug = lp_client.get_bug(bug_id)

    # 2. Search for similar Launchpad bugs
    similar = lp_client.search_similar_bugs(bug)

    # 3. Get upstream info
    upstream = lp_client.get_upstream_info(bug_id)

    # 4. Search upstream issue trackers
    title_keywords = extract_keywords(bug.title)

    upstream_issues = []

    # Search using bug watch URLs (direct upstream links)
    searched_repos = set()
    for watch_url in upstream.bug_watch_urls:
        parsed = upstream_search.parse_issue_url(watch_url)
        if parsed:
            platform, project, _ = parsed
            if platform == "github" and project not in searched_repos:
                searched_repos.add(project)
                owner, repo = project.split("/", 1)
                issues = upstream_search.search_github_issues(
                    owner, repo, title_keywords
                )
                upstream_issues.extend(issues)
            elif platform.startswith("gitlab:"):
                host = platform.split(":", 1)[1]
                if project not in searched_repos:
                    searched_repos.add(project)
                    issues = upstream_search.search_gitlab_issues(
                        host, project, title_keywords
                    )
                    upstream_issues.extend(issues)

    # Search using homepage URL or bug tracker URL
    search_urls = []
    if upstream.homepage_url:
        search_urls.append(upstream.homepage_url)
    if upstream.bug_tracker_url:
        search_urls.append(upstream.bug_tracker_url)
    
    for url in search_urls:
        if upstream_issues:
            break
        issues = upstream_search.search_upstream(url, title_keywords)
        upstream_issues.extend(issues)

    result = {
        "input_bug": asdict(bug),
        "similar_launchpad_bugs": [asdict(b) for b in similar],
        "upstream_info": asdict(upstream),
        "upstream_issues": [asdict(i) for i in upstream_issues],
        "summary": {
            "total_similar_lp_bugs": len(similar),
            "total_upstream_issues": len(upstream_issues),
            "upstream_found": bool(upstream.project_name or upstream.bug_watch_urls),
        },
        "triage_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    _write_result(bug.package_name, result)

    return json.dumps(result, indent=2, default=str)


def main():
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
