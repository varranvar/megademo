import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Package(Base):
    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    release: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    component: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    architecture: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    last_scan: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    hygiene_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    cve_links: Mapped[list["CVEPackageLink"]] = relationship(
        back_populates="package", cascade="all, delete-orphan"
    )
    bugs: Mapped[list["Bug"]] = relationship(
        back_populates="package", cascade="all, delete-orphan"
    )

    @property
    def cves(self) -> list["CVE"]:
        return [link.cve for link in self.cve_links if link.cve is not None]


class Bug(Base):
    __tablename__ = "bugs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bug_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    package_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    importance: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    assignee: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    last_updated: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    bug_link: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    heat: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    users_affected_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    message_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    number_of_duplicates: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    security_related: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    tags: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    package: Mapped[Optional["Package"]] = relationship(back_populates="bugs")


class CVE(Base):
    __tablename__ = "cves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cve_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cvss_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cvss_severity: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    vector_string: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    cvss_v30_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cvss_v30_severity: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    cvss_v30_vector: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    cwe_ids: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    kev: Mapped[bool] = mapped_column(Boolean, default=False)
    kev_date_added: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    rejected: Mapped[bool] = mapped_column(Boolean, default=False)
    published_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    last_modified: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    usn_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    package_links: Mapped[list["CVEPackageLink"]] = relationship(
        back_populates="cve", cascade="all, delete-orphan"
    )


class CVEPackageLink(Base):
    __tablename__ = "cve_package_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cve_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cves.id", ondelete="CASCADE"), nullable=False, index=True
    )
    package_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fix_version: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, default="open")

    cve: Mapped[Optional["CVE"]] = relationship(back_populates="package_links")
    package: Mapped[Optional["Package"]] = relationship(back_populates="cve_links")


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scanner: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    packages_scanned: Mapped[int] = mapped_column(Integer, default=0)
    items_fetched: Mapped[int] = mapped_column(Integer, default=0)
    total_packages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)


class PackageScore(Base):
    __tablename__ = "package_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    heuristic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("heuristics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, default=0.0)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    calculated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)


class Heuristic(Base):
    __tablename__ = "heuristics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class SyncState(Base):
    __tablename__ = "sync_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    value: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)