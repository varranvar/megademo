import asyncio
import datetime
import logging
import re
import time
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mdmo.config import settings
from mdmo.models import Bug, Package, ScanJob
from mdmo.scanners.base import BaseScanner

logger = logging.getLogger(__name__)

LAUNCHPAD_STATUSES = [
    "New",
    "Confirmed",
    "Triaged",
    "In Progress",
    "Incomplete",
    "Fix Committed",
]

LAUNCHPAD_BASE_URL = settings.launchpad.api_base_url


def _parse_link_id(url: str | None) -> int | None:
    if not url:
        return None
    match = re.search(r"/bugs/(\d+)$", url.rstrip("/"))
    return int(match.group(1)) if match else None


def _parse_datetime(val: str | None) -> datetime.datetime | None:
    if not val:
        return None
    try:
        return datetime.datetime.fromisoformat(val.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


class ETagCache:
    def __init__(self, ttl_seconds: int = 21600):
        self._cache: dict[str, tuple[str, Any, float]] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> tuple[str | None, Any | None]:
        entry = self._cache.get(key)
        if entry is None:
            return None, None
        etag, payload, expiry = entry
        if time.monotonic() > expiry:
            del self._cache[key]
            return None, None
        return etag, payload

    def set(self, key: str, etag: str, payload: Any) -> None:
        self._cache[key] = (etag, payload, time.monotonic() + self._ttl)

    def clear(self) -> None:
        self._cache.clear()


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time: float = 0.0
        self._open = False

    @property
    def is_open(self) -> bool:
        if not self._open:
            return False
        if time.monotonic() - self._last_failure_time >= self._recovery_timeout:
            self._open = False
            self._failure_count = 0
            return False
        return True

    def record_success(self) -> None:
        self._failure_count = 0
        self._open = False

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self._failure_threshold:
            self._open = True


class LaunchpadClient:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._bug_cache = ETagCache(ttl_seconds=43200)
        self._tasks_cache = ETagCache(ttl_seconds=21600)
        self._circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=300)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=LAUNCHPAD_BASE_URL,
                headers={"Accept": "application/json"},
                timeout=60.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self, url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None
    ) -> httpx.Response:
        if self._circuit.is_open:
            raise RuntimeError("Circuit breaker is open")

        merged_headers = {**(headers or {})}
        last_exception = None
        for attempt in range(3):
            try:
                async with self._lock:
                    client = await self._get_client()
                    response = await client.get(url, params=params, headers=merged_headers)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "10"))
                    await asyncio.sleep(retry_after)
                    continue

                if response.status_code == 404:
                    self._circuit.record_success()
                    return response

                if response.status_code >= 500:
                    self._circuit.record_failure()
                    wait = 2 ** attempt
                    await asyncio.sleep(wait)
                    continue

                self._circuit.record_success()
                return response

            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                logger.warning("Launchpad request attempt %d failed: %s", attempt + 1, exc)
                last_exception = exc
                self._circuit.record_failure()
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)

        raise last_exception or RuntimeError("Launchpad request failed after 3 attempts")

    async def _follow_pagination(self, total_entry: dict) -> list[dict]:
        entries = list(total_entry.get("entries", []))
        next_link = total_entry.get("next_collection_link")
        while next_link:
            async with self._lock:
                client = await self._get_client()
                response = await client.get(next_link)
            if response.status_code != 200:
                break
            page = response.json()
            entries.extend(page.get("entries", []))
            next_link = page.get("next_collection_link")
        return entries

    async def get_source_tasks(self, package: str) -> list[dict]:
        cache_key = f"tasks:{package}"
        etag, cached = self._tasks_cache.get(cache_key)
        response_headers: dict[str, str] = {}
        if etag:
            response_headers["If-None-Match"] = etag

        url = "/+source-packages"
        params: dict[str, Any] = {
            "ws.op": "searchTasks",
            "source_name": package,
            "order_by": "-importance",
        }

        resp = await self._request(url, params=params, headers=response_headers)
        if resp.status_code == 404:
            return []
        if resp.status_code == 304:
            if cached is not None:
                return cached
            return []

        resp.raise_for_status()
        data = resp.json()
        entries = await self._follow_pagination(data)

        filtered = [
            e
            for e in entries
            if e.get("bug_target_name") == package
            and e.get("status") in LAUNCHPAD_STATUSES
        ]
        new_etag = resp.headers.get("ETag", "")
        if new_etag:
            self._tasks_cache.set(cache_key, new_etag, filtered)

        return filtered

    async def get_bug_details(self, bug_id: int) -> dict | None:
        cache_key = f"bug:{bug_id}"
        etag, cached = self._bug_cache.get(cache_key)
        if cached is not None:
            return cached

        response_headers: dict[str, str] = {}
        if etag:
            response_headers["If-None-Match"] = etag

        url = f"/bugs/{bug_id}"
        resp = await self._request(url, headers=response_headers)
        if resp.status_code == 404:
            return None
        if resp.status_code == 304:
            return cached

        resp.raise_for_status()
        data = resp.json()
        new_etag = resp.headers.get("ETag", "")
        if new_etag:
            self._bug_cache.set(cache_key, new_etag, data)

        return data

    async def search_source_packages(
        self, release: str, query: str = "", limit: int = 100
    ) -> list[dict]:
        distro = f"ubuntu/{release}"
        url = f"/{distro}/+source-packages"
        params: dict[str, Any] = {
            "ws.op": "search",
            "text": query,
        }
        resp = await self._request(url, params=params)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        entries = await self._follow_pagination(data)
        return entries[:limit]


class LaunchpadScanner(BaseScanner):
    name = "launchpad"

    def __init__(self):
        self._client: LaunchpadClient | None = None

    @property
    def client(self) -> LaunchpadClient:
        if self._client is None:
            self._client = LaunchpadClient()
        return self._client

    def _parse_task_to_bug(self, task: dict, package_id: int) -> Bug:
        bug_link = task.get("bug_link")
        bug_id = _parse_link_id(bug_link)
        return Bug(
            bug_id=bug_id or 0,
            package_id=package_id,
            title=task.get("title"),
            status=task.get("status"),
            importance=task.get("importance"),
            assignee=task.get("assignee_link"),
            created_date=_parse_datetime(task.get("date_created")),
            last_updated=_parse_datetime(task.get("date_last_updated")),
            bug_link=bug_link,
            tags=task.get("tags", []),
        )

    def _enrich_bug_from_details(self, bug: Bug, details: dict) -> None:
        bug.heat = details.get("heat")
        bug.users_affected_count = details.get("users_affected_count")
        bug.message_count = details.get("message_count")
        bug.number_of_duplicates = details.get("number_of_duplicates")
        bug.security_related = details.get("security_related", False)
        if details.get("tags"):
            bug.tags = details["tags"]

    async def scan_package(
        self, package_name: str, release: str, session: AsyncSession
    ) -> dict:
        try:
            tasks = await self.client.get_source_tasks(package_name)

            if not tasks:
                logger.info("No open tasks found for %s", package_name)
                return {"status": "ok", "items_fetched": 0}

            result = await session.execute(
                select(Package).where(
                    Package.name == package_name, Package.release == release
                )
            )
            pkg = result.scalar_one_or_none()
            if pkg is None:
                pkg = Package(name=package_name, release=release)
                session.add(pkg)
                await session.flush()

            parsed_bugs: dict[int, Bug] = {}
            for task in tasks:
                bug = self._parse_task_to_bug(task, pkg.id)
                if bug.bug_id and bug.bug_id not in parsed_bugs:
                    parsed_bugs[bug.bug_id] = bug

            enrichment_bugs = sorted(
                parsed_bugs.values(),
                key=lambda b: (b.last_updated or datetime.datetime.min),
                reverse=True,
            )[:20]

            for bug in enrichment_bugs:
                try:
                    details = await self.client.get_bug_details(bug.bug_id)
                    if details:
                        self._enrich_bug_from_details(bug, details)
                except Exception:
                    logger.warning(
                        "Failed to fetch details for bug %d on package %s",
                        bug.bug_id,
                        package_name,
                    )

            for bug in parsed_bugs.values():
                existing = await session.execute(
                    select(Bug).where(
                        Bug.bug_id == bug.bug_id, Bug.package_id == pkg.id
                    )
                )
                existing_bug = existing.scalar_one_or_none()
                if existing_bug:
                    for key, value in bug.__dict__.items():
                        if key not in ("id", "_sa_instance_state"):
                            setattr(existing_bug, key, value)
                else:
                    session.add(bug)

            await session.commit()
            return {"status": "ok", "items_fetched": len(parsed_bugs)}

        except Exception as exc:
            logger.error("Error scanning package %s: %s", package_name, exc)
            await session.rollback()
            return {"status": "error", "items_fetched": 0, "error": str(exc)}

    async def scan_all(self, packages: list, session: AsyncSession) -> dict:
        now = datetime.datetime.now(datetime.timezone.utc)
        scan_job = ScanJob(
            scanner=self.name,
            status="running",
            started_at=now,
            created_at=now,
            total_packages=len(packages),
        )
        session.add(scan_job)
        await session.commit()

        semaphore = asyncio.Semaphore(3)
        scanned = 0
        items = 0
        errors: list[str] = []

        async def _scan_one(pkg: Package) -> None:
            nonlocal scanned, items
            async with semaphore:
                result = await self.scan_package(pkg.name, pkg.release, session)
                scanned += 1
                items += result.get("items_fetched", 0)
                if result.get("status") == "error":
                    errors.append(result.get("error", "unknown"))
                scan_job.packages_scanned = scanned
                scan_job.items_fetched = items

        coros = [_scan_one(p) for p in packages]
        await asyncio.gather(*coros, return_exceptions=True)

        scan_job.status = "completed"
        scan_job.finished_at = datetime.datetime.now(datetime.timezone.utc)
        scan_job.completed_at = datetime.datetime.now(datetime.timezone.utc)
        scan_job.packages_scanned = scanned
        scan_job.items_fetched = items
        if errors:
            scan_job.error = "; ".join(errors[:5])

        await session.commit()

        return {
            "status": "completed",
            "packages_scanned": scanned,
            "items_fetched": items,
        }

    async def close(self) -> None:
        if self._client:
            await self._client.close()