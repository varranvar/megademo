from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HygieneResult:
    score: float
    details: dict[str, Any] = field(default_factory=dict)
    label: str = ""
    error: str | None = None


class HygieneCheck(ABC):
    name: str
    description: str
    weight: float = 0.05

    @abstractmethod
    async def check(self, package: Any) -> HygieneResult:
        ...

    def render_html(self, result: HygieneResult) -> str:
        return ""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "name", None):
            return
        PluginRegistry.register(cls())


class PluginRegistry:
    _checks: dict[str, HygieneCheck] = {}

    @classmethod
    def register(cls, check: HygieneCheck) -> None:
        cls._checks[check.name] = check

    @classmethod
    def get_all(cls) -> list[HygieneCheck]:
        return list(cls._checks.values())

    @classmethod
    def get(cls, name: str) -> HygieneCheck | None:
        return cls._checks.get(name)

    @classmethod
    def clear(cls) -> None:
        cls._checks.clear()
