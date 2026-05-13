from typing import Iterator


def _parse_epoch(version: str) -> tuple[int, str]:
    if ":" in version:
        epoch_str, rest = version.split(":", 1)
        try:
            epoch = int(epoch_str)
        except ValueError:
            epoch = 0
        return epoch, rest
    return 0, version


def _parse_debian_revision(version: str) -> tuple[str, str]:
    idx = version.rfind("-")
    if idx != -1:
        return version[:idx], version[idx:]
    return version, ""


def _char_at(s: str, i: int) -> str:
    return s[i] if i < len(s) else ""


def _is_digit(c: str) -> bool:
    return c.isdigit()


def _order(c: str) -> int:
    if c == "":
        return 0
    if c == "~":
        return -1
    if c.isdigit():
        return 0
    if c.isalpha():
        return ord(c)
    return ord(c) + 256


def _dpkg_compare_versions_raw(a: str, b: str) -> int:
    i = 0
    j = 0
    while i < len(a) or j < len(b):

        while (i < len(a) and not _is_digit(a[i])) or (j < len(b) and not _is_digit(b[j])):
            ac = _order(_char_at(a, i))
            bc = _order(_char_at(b, j))
            if ac != bc:
                return -1 if ac < bc else 1
            i += 1
            j += 1

        while i < len(a) and a[i] == "0":
            i += 1
        while j < len(b) and b[j] == "0":
            j += 1

        num_a = 0
        num_b = 0
        while i < len(a) and _is_digit(a[i]) and j < len(b) and _is_digit(b[j]):
            num_a = num_a * 10 + int(a[i])
            num_b = num_b * 10 + int(b[j])
            i += 1
            j += 1

        while i < len(a) and _is_digit(a[i]):
            num_a = num_a * 10 + int(a[i])
            i += 1
        while j < len(b) and _is_digit(b[j]):
            num_b = num_b * 10 + int(b[j])
            j += 1

        if num_a < num_b:
            return -1
        if num_a > num_b:
            return 1

    return 0


def dpkg_compare_versions(a: str, b: str) -> int:
    """
    Compare two Debian package version strings.

    Returns:
        -1 if a < b (a is older)
         0 if a == b (same version)
         1 if a > b (a is newer)

    Implementation follows Debian Policy Manual section 5.6.12.
    """
    epoch_a, upstream_a = _parse_epoch(a)
    epoch_b, upstream_b = _parse_epoch(b)

    if epoch_a != epoch_b:
        return -1 if epoch_a < epoch_b else 1

    deb_a, deb_rev_a = _parse_debian_revision(upstream_a)
    deb_b, deb_rev_b = _parse_debian_revision(upstream_b)

    cmp_upstream = _dpkg_compare_versions_raw(deb_a, deb_b)
    if cmp_upstream != 0:
        return cmp_upstream

    if deb_rev_a == "" and deb_rev_b != "":
        return 1
    if deb_rev_a != "" and deb_rev_b == "":
        return -1

    return _dpkg_compare_versions_raw(deb_rev_a, deb_rev_b)


def is_version_affected(
    installed: str, fixed: str, operation: str = "less than"
) -> bool:
    """
    Check if an installed version is affected by a vulnerability
    given the fixed version and comparison operation.

    Args:
        installed: The installed version string.
        fixed: The fixed version string (the version that patches the vuln).
        operation: The comparison operation:
            "less than" (default) - affected if installed < fixed
            "less than or equal" - affected if installed <= fixed
            "greater than" - affected if installed > fixed
            "equal" - affected if installed == fixed

    Returns:
        True if the installed version is affected (does NOT have the fix).
    """
    cmp = dpkg_compare_versions(installed, fixed)
    if operation == "less than":
        return cmp < 0
    elif operation == "less than or equal":
        return cmp <= 0
    elif operation == "greater than":
        return cmp > 0
    elif operation == "equal":
        return cmp == 0
    elif operation == "not equal":
        return cmp != 0
    return False
