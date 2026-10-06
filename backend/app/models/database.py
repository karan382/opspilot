from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class IncidentDB(Base):
    __tablename__ = "incidents"

    incident_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    service: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    symptoms: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    investigations: Mapped[list["InvestigationRunDB"]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
    )


class InvestigationRunDB(Base):
    __tablename__ = "investigation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.incident_id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    claim_level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    incident: Mapped["IncidentDB"] = relationship(
        back_populates="investigations",
    )

    evidence: Mapped[list["InvestigationEvidenceDB"]] = relationship(
        back_populates="investigation",
        cascade="all, delete-orphan",
    )


class InvestigationEvidenceDB(Base):
    __tablename__ = "investigation_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_runs.id"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    service: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timestamp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    observation: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int | None] = mapped_column(Integer, nullable=True)

    investigation: Mapped["InvestigationRunDB"] = relationship(
        back_populates="evidence",
    )