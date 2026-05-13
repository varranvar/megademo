from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession


class BaseScanner(ABC):
    name: str

    @abstractmethod
    async def scan_package(self, package_name: str, release: str, session: AsyncSession) -> dict:
        ...

    @abstractmethod
    async def scan_all(self, packages: list, session: AsyncSession) -> dict:
        ...
