import pytest
from mdmo.version_compare import dpkg_compare_versions


class TestVersionCompare:
    @pytest.mark.parametrize(
        "a,b,expected",
        [
            ("1.0", "1.0", 0),
            ("2.0", "1.0", 1),
            ("1.0", "2.0", -1),
            ("1:2.0", "2.0", 1),
            ("1:1.0", "2:1.0", -1),
            ("1.0~rc1", "1.0", -1),
            ("1.0", "1.0~rc1", 1),
            ("1.0~beta1", "1.0~beta2", -1),
            ("1.0.0", "1.0", 1),
            ("3.0.2-0ubuntu1.18", "3.0.2-0ubuntu1.17", 1),
            ("3.0.2-0ubuntu1.18", "3.0.2-0ubuntu1.18", 0),
            ("1:9.11.3+dfsg-1ubuntu1", "1:9.11.3+dfsg-1ubuntu2", -1),
            ("2.35-0ubuntu3.8", "2.35-0ubuntu3.7", 1),
            ("0.9.8", "0.9.8a", -1),
            ("1.0pre1", "1.0", -1),
            ("1.0.1", "1.0.10", -1),
            ("2.0", "10.0", -1),
            ("10.0", "2.0", 1),
            ("1.10", "1.2", 1),
            ("1.9", "1.10", -1),
            ("1.0.0", "1.0", 1),
            ("1.0-1", "1.0-2", -1),
            ("3.0.2-0ubuntu1.18", "3.0.2-0ubuntu1.17", 1),
        ],
    )
    def test_compare(self, a, b, expected):
        result = dpkg_compare_versions(a, b)
        assert result == expected, f"{a} vs {b}: expected {expected}, got {result}"
