import tempfile
from pathlib import Path

import yaml
import pytest

from mdmo.config import AppSettings


class TestConfig:
    def test_defaults(self):
        cfg = AppSettings()
        assert cfg.database.path == "data/mdmo.db"
        assert cfg.ubuntu.releases == ["jammy", "noble"]
        assert cfg.scan.intervals.launchpad == 86400
        assert cfg.scoring.weights.cve == 0.35

    def test_from_yaml(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
database:
  path: /tmp/test.db
ubuntu:
  releases:
    - focal
    - jammy
scoring:
  weights:
    bugs: 0.30
    cve: 0.40
    freshness: 0.15
    plugins: 0.15
""")
            f.flush()
            cfg = AppSettings.from_yaml(f.name)
            Path(f.name).unlink()

        assert cfg.database.path == "/tmp/test.db"
        assert cfg.ubuntu.releases == ["focal", "jammy"]
        assert cfg.scoring.weights.bugs == 0.30
