from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Source = Literal["live", "fused", "rule", "simulated"]
Role = Literal["citizen", "responder"]
CheckinStatus = Literal["safe", "assist", "danger"]
ZoneLevel = Literal["critical", "warning", "nearby"]


class Provenance(BaseModel):
    source: Source
    as_of: datetime


class HealthStatus(BaseModel):
    db: Literal["ok", "down"]
    llm: Literal["ok", "down"]
    routing: Literal["live", "precomputed"]


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
    user_id: int
    email: str


class GeoJSONFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any] | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class GeoJSONFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[GeoJSONFeature] = Field(default_factory=list)
    provenance: Provenance


class LayerMap(BaseModel):
    incidents: GeoJSONFeatureCollection
    risk: GeoJSONFeatureCollection
    infrastructure: GeoJSONFeatureCollection
    human_safety: GeoJSONFeatureCollection
    visibility: GeoJSONFeatureCollection
    evacuation: GeoJSONFeatureCollection
    alert_zones: GeoJSONFeatureCollection
    blocked_roads: GeoJSONFeatureCollection


class PriorityWeights(BaseModel):
    """Shown on ops cards so a juror can recompute by hand. Not a learned model."""

    severity: float = 3.0
    people: float = 0.15
    critical_checkins: float = 2.0
    hours_since_report: float = 0.4
    km: float = -0.05
    isolation_multiplier: float = 1.5


class PriorityItem(BaseModel):
    incident_code: str
    score: float
    breakdown: dict[str, float] = Field(default_factory=dict)
    nearest_resource: str | None = None
    reason: str | None = None


class VisibilitySummary(BaseModel):
    """Denominator is simulated registered users. Unconfirmed ≠ missing."""

    coverage_pct: float = 0.0
    unconfirmed_safety_status: int = 0
    simulated_registered_users: int = 0
    note: str = (
        "unconfirmed_safety_status counts scenario users who have not checked in. "
        "It is not a missing-person count."
    )


class IsolationState(BaseModel):
    isolated_settlements: list[str] = Field(default_factory=list)
    cascade: str | None = None


class EvidenceOut(BaseModel):
    id: int
    kind: str
    lat: float
    lon: float
    t: datetime
    raw_text: str | None
    emergency_type: str | None
    people_count: int | None
    severity: int | None
    trapped: bool
    injury: bool
    source: str
    as_of: datetime
    incident_code: str | None = None
    has_media: bool = False


class EvidenceCreated(BaseModel):
    evidence_id: int
    incident_code: str
    cluster_confidence: float
    confidence_label: str = "cluster confidence, not field-validated accuracy"


class CheckinOut(BaseModel):
    id: int
    status: CheckinStatus
    lat: float
    lon: float
    t: datetime
    source: str


class LockerMember(EvidenceOut):
    contribution_score: float


class IncidentOut(BaseModel):
    id: int
    code: str
    confidence: float
    status: str
    isolated: bool
    disagreement: bool
    sitrep: str | None = None
    member_evidence_ids: list[int] = Field(default_factory=list)
    provenance: Provenance


class IncidentDetail(IncidentOut):
    locker: list[LockerMember] = Field(default_factory=list)


class IncidentActionOut(BaseModel):
    code: str
    status: str


class Snapshot(BaseModel):
    """Single document Person 1 polls about every 2 seconds."""

    tick: int
    rainfall_index: int
    playing: bool
    as_of: datetime
    health: HealthStatus
    incidents: list[IncidentOut]
    evidence: list[EvidenceOut]
    layers: LayerMap
    visibility: VisibilitySummary
    priority_weights: PriorityWeights
    priority_queue: list[PriorityItem]
    isolation: IsolationState
    sitrep: str | None = None
    resources: list[dict] = Field(default_factory=list)
    routes: list[dict] = Field(default_factory=list)
    alerts: list[dict] = Field(default_factory=list)
    corroborated: dict[str, bool] = Field(default_factory=dict)


class CitizenSnapshot(BaseModel):
    """Citizen view: never other people's exact SOS or photos."""

    tick: int
    rainfall_index: int
    as_of: datetime
    zone_level: str | None = None
    zone_message: str | None = None
    safest_route: dict | None = None
    rejected_routes: list[dict] = Field(default_factory=list)
    shelters: list[dict] = Field(default_factory=list)
    isolation: IsolationState
    own_checkin: CheckinOut | None = None
    own_evidence_ids: list[int] = Field(default_factory=list)
    note: str = "Other citizens' exact SOS and photos are not shown."
    alert_zones: GeoJSONFeatureCollection | None = None
    evacuation: GeoJSONFeatureCollection | None = None


class DemoStateOut(BaseModel):
    tick: int
    rainfall_index: int
    playing: bool
    as_of: datetime


class DemoPlayRequest(BaseModel):
    playing: bool = True


# Unused until Person 2 Phase 2 ingest; kept here so Person 1 can type against the contract.
class EvidenceCreate(BaseModel):
    kind: Literal["sos", "report", "photo_meta"] = "sos"
    lat: float
    lon: float
    raw_text: str | None = None
    emergency_type: str | None = None
    people_count: int | None = None
    severity: int | None = Field(default=None, ge=0, le=5)
    trapped: bool = False
    injury: bool = False
    source: Literal["live", "simulated"] = "live"


class CheckinCreate(BaseModel):
    status: CheckinStatus
    lat: float
    lon: float
    source: Literal["live", "simulated"] = "live"
