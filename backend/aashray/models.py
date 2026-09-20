from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aashray.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32))  # citizen | responder
    last_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evidence: Mapped[list["Evidence"]] = relationship(back_populates="user")
    checkins: Mapped[list["Checkin"]] = relationship(back_populates="user")


class Evidence(Base):
    """Atomic signal. Not an operational incident until fusion writes membership."""

    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))  # sos | report | photo_meta
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    t: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    emergency_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    people_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0–5
    trapped: Mapped[bool] = mapped_column(default=False)
    injury: Mapped[bool] = mapped_column(default=False)
    media_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list when P3 fills it
    source: Mapped[str] = mapped_column(String(32), default="live")  # live | simulated
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="evidence")
    memberships: Mapped[list["IncidentEvidence"]] = relationship(back_populates="evidence")


class Incident(Base):
    """Operational object after fusion. Geometry stored as GeoJSON text."""

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    centroid: Mapped[str | None] = mapped_column(Text, nullable=True)  # GeoJSON Point
    geometry: Mapped[str | None] = mapped_column(Text, nullable=True)  # GeoJSON Geometry
    confidence: Mapped[float] = mapped_column(Float, default=0.0)  # cluster confidence, not field accuracy
    status: Mapped[str] = mapped_column(String(32), default="open")  # open | assigned | dismissed
    isolated: Mapped[bool] = mapped_column(default=False)
    disagreement: Mapped[bool] = mapped_column(default=False)
    sitrep_cache: Mapped[str | None] = mapped_column(Text, nullable=True)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    members: Mapped[list["IncidentEvidence"]] = relationship(back_populates="incident")


class IncidentEvidence(Base):
    __tablename__ = "incident_evidence"
    __table_args__ = (UniqueConstraint("incident_id", "evidence_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("evidence.id"), index=True)
    contribution_score: Mapped[float] = mapped_column(Float, default=0.0)

    incident: Mapped[Incident] = relationship(back_populates="members")
    evidence: Mapped[Evidence] = relationship(back_populates="memberships")


class Checkin(Base):
    __tablename__ = "checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(32))  # safe | assist | danger
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    t: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source: Mapped[str] = mapped_column(String(32), default="live")

    user: Mapped[User] = relationship(back_populates="checkins")


class BlockedEdge(Base):
    __tablename__ = "blocked_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edge_id: Mapped[str] = mapped_column(String(64), index=True)
    t: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(32), default="simulated")


class AlertEvent(Base):
    """One alert per (user, incident, zone_level) until the level changes."""

    __tablename__ = "alert_events"
    __table_args__ = (UniqueConstraint("user_id", "incident_id", "zone_level"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    zone_level: Mapped[str] = mapped_column(String(32))  # critical | warning | nearby
    t: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DemoState(Base):
    __tablename__ = "demo_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tick: Mapped[int] = mapped_column(Integer, default=0)
    rainfall_index: Mapped[int] = mapped_column(Integer, default=0)
    playing: Mapped[bool] = mapped_column(default=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
