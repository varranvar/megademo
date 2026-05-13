import pytest


@pytest.fixture
def app_settings():
    from mdmo.config import AppSettings

    return AppSettings(
        database={"path": ":memory:"},
        ubuntu={"releases": ["jammy"]},
    )
