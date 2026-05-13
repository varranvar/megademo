import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from server import (
    get_series_info,
    get_package_version,
    search_packages,
    get_package_details,
    get_build_status,
    get_bug_list,
    _resolve_series,
)


async def test_series_resolution():
    assert _resolve_series("24.04") == "noble"
    assert _resolve_series("noble") == "noble"
    assert _resolve_series("22.04") == "jammy"
    assert _resolve_series("unknown") == "unknown"
    print("PASS: series resolution")


async def test_get_series_info():
    result = await get_series_info()
    assert isinstance(result, list)
    names = {s["name"] for s in result}
    assert "noble" in names or "jammy" in names, f"Expected known series, got: {names}"
    print(f"PASS: get_series_info returned {len(result)} series")


async def test_get_package_version():
    result = await get_package_version("cargo", "noble")
    if "error" in result:
        print(f"SKIP: get_package_version cargo/noble: {result['error']}")
        return
    assert "version" in result
    assert result["package"] == "cargo"
    print(f"PASS: get_package_version cargo={result['version']} on noble")


async def test_search_packages():
    result = await search_packages("rustc", series="noble", search_field="name")
    assert "source_matches" in result or "binary_matches" in result
    total = result.get("total_source", 0) + result.get("total_binary", 0)
    print(f"PASS: search_packages 'rustc' found {total} matches on noble")


async def test_get_package_details():
    result = await get_package_details("cargo", series="noble")
    if "error" in result:
        print(f"SKIP: get_package_details cargo: {result['error']}")
        return
    assert "type" in result
    print(f"PASS: get_package_details cargo type={result['type']}")


async def test_get_build_status():
    result = await get_build_status("rustc", "noble")
    if "error" in result:
        print(f"SKIP: get_build_status rustc: {result['error']}")
        return
    assert "builds" in result
    print(f"PASS: get_build_status rustc: {len(result['builds'])} builds")


async def test_get_bug_list():
    result = await get_bug_list("rustc", status="New", limit=5)
    if "error" in result:
        print(f"SKIP: get_bug_list rustc: {result['error']}")
        return
    assert "bugs" in result
    print(f"PASS: get_bug_list rustc: {len(result['bugs'])} bugs")


async def main():
    tests = [
        test_series_resolution,
        test_get_series_info,
        test_get_package_version,
        test_search_packages,
        test_get_package_details,
        test_get_build_status,
        test_get_bug_list,
    ]
    for t in tests:
        try:
            await t()
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")

    from server import _http_client
    if _http_client:
        await _http_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
