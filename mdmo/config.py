import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    path: str = "data/mdmo.db"


class ScanIntervals(BaseModel):
    launchpad: int = 86400
    nvd: int = 21600
    oval: int = 86400


class ScoringWeights(BaseModel):
    bugs: float = 0.25
    cve: float = 0.35
    freshness: float = 0.20
    plugins: float = 0.20


class NVDConfig(BaseModel):
    api_key: str = ""


class LaunchpadConfig(BaseModel):
    api_base_url: str = "https://api.launchpad.net/devel"


class OVALConfig(BaseModel):
    base_url: str = "https://security-metadata.canonical.com/oval"


class ScanConfig(BaseModel):
    intervals: ScanIntervals = ScanIntervals()


class ScoringConfig(BaseModel):
    weights: ScoringWeights = ScoringWeights()


class UbuntuConfig(BaseModel):
    releases: list[str] = ["jammy", "noble"]


class AppSettings(BaseModel):
    database: DatabaseConfig = DatabaseConfig()
    ubuntu: UbuntuConfig = UbuntuConfig()
    scan: ScanConfig = ScanConfig()
    scoring: ScoringConfig = ScoringConfig()
    nvd: NVDConfig = NVDConfig()
    launchpad: LaunchpadConfig = LaunchpadConfig()
    oval: OVALConfig = OVALConfig()

    @classmethod
    def from_yaml(cls, config_path: str = "config.yaml") -> "AppSettings":
        path = Path(config_path)
        if not path.exists():
            return cls()

        raw = path.read_text()
        raw = os.path.expandvars(raw)
        data = yaml.safe_load(raw) or {}
        return cls(**data)


_settings: AppSettings | None = None


def _init_settings(config_path: str = "config.yaml") -> AppSettings:
    global _settings
    _settings = AppSettings.from_yaml(config_path)
    return _settings


class SettingsProxy:
    def __init__(self, wrapped: AppSettings) -> None:
        self._wrapped = wrapped

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)

    def model_dump(self) -> dict:
        return self._wrapped.model_dump()


def get_settings() -> AppSettings:
    global _settings
    if _settings is None:
        _settings = _init_settings()
    return _settings


settings = get_settings()