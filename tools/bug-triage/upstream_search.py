"""Search upstream issue trackers (GitHub, GitLab) for similar issues."""

import re
from dataclasses import dataclass
import requests


@dataclass
class UpstreamIssue:
    title: str
    url: str
    state: str
    source: str  # "github" or "gitlab"
    labels: list[str]
    created_at: str


def parse_repo_url(url: str) -> tuple[str, str, str] | None:
    """Parse a URL into (platform, owner, repo).

    Returns None if the URL can't be parsed.
    Supports GitHub and GitLab URLs.
    """
    # GitHub: https://github.com/owner/repo
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)", url)
    if m:
        return ("github", m.group(1), m.group(2))

    # GitLab (gitlab.com or self-hosted): https://gitlab.example.com/group/project
    m = re.match(r"https?://(gitlab\.[^/]+)/(.+?)(?:\.git)?$", url)
    if m:
        host = m.group(1)
        path = m.group(2).rstrip("/")
        # Remove trailing /-/... paths (issues, merge_requests, etc.)
        path = re.sub(r"/-/.*$", "", path)
        return ("gitlab:" + host, path, "")

    return None


def parse_issue_url(url: str) -> tuple[str, str, str] | None:
    """Parse an issue URL to extract platform and project info.

    Returns (platform, project_identifier, issue_number) or None.
    """
    # GitHub issue: https://github.com/owner/repo/issues/123
    m = re.match(r"https?://github\.com/([^/]+/[^/]+)/issues/(\d+)", url)
    if m:
        return ("github", m.group(1), m.group(2))

    # GitLab issue: https://gitlab.example.com/group/project/-/issues/123
    m = re.match(r"https?://(gitlab\.[^/]+)/(.+?)/-/issues/(\d+)", url)
    if m:
        return ("gitlab:" + m.group(1), m.group(2), m.group(3))

    return None


def search_github_issues(owner: str, repo: str, keywords: list[str],
                         max_results: int = 15) -> list[UpstreamIssue]:
    """Search GitHub Issues API for matching issues."""
    query = " ".join(keywords)
    search_query = f"{query} repo:{owner}/{repo} is:issue"

    try:
        resp = requests.get(
            "https://api.github.com/search/issues",
            params={"q": search_query, "per_page": max_results, "sort": "relevance"},
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    results = []
    for item in data.get("items", []):
        results.append(UpstreamIssue(
            title=item["title"],
            url=item["html_url"],
            state=item["state"],
            source="github",
            labels=[l["name"] for l in item.get("labels", [])],
            created_at=item["created_at"],
        ))

    return results


def search_gitlab_issues(host: str, project_path: str, keywords: list[str],
                         max_results: int = 15) -> list[UpstreamIssue]:
    """Search GitLab Issues API for matching issues."""
    import urllib.parse
    encoded_path = urllib.parse.quote(project_path, safe="")
    query = " ".join(keywords)

    try:
        resp = requests.get(
            f"https://{host}/api/v4/projects/{encoded_path}/issues",
            params={"search": query, "per_page": max_results, "state": "all"},
            timeout=15,
        )
        resp.raise_for_status()
        items = resp.json()
    except Exception:
        return []

    results = []
    for item in items:
        results.append(UpstreamIssue(
            title=item["title"],
            url=item["web_url"],
            state=item["state"],
            source="gitlab",
            labels=item.get("labels", []),
            created_at=item["created_at"],
        ))

    return results


def search_upstream(url: str, keywords: list[str],
                    max_results: int = 15) -> list[UpstreamIssue]:
    """Search for issues on an upstream repo given its URL.

    Automatically detects GitHub vs GitLab and calls the right API.
    """
    parsed = parse_repo_url(url)
    if not parsed:
        return []

    platform, owner_or_path, repo = parsed

    if platform == "github":
        return search_github_issues(owner_or_path, repo, keywords, max_results)
    elif platform.startswith("gitlab:"):
        host = platform.split(":", 1)[1]
        return search_gitlab_issues(host, owner_or_path, keywords, max_results)

    return []
