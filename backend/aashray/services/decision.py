from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from aashray.deps import utcnow
from aashray.models import AlertEvent, BlockedEdge, Checkin, DemoState, Incident, IncidentEvidence, User
from aashray.schemas import PriorityItem, PriorityWeights
from aashray.services.geo import haversine_m, point_in_ring
from aashray.services.routes import score_routes_with_blocked
from aashray.services.scenario import load_pack

ZONE_RANK = {"critical": 3, "warning": 2, "nearby": 1}


def _aware(dt: datetime | None) -> datetime:
    if dt is None:
        return utcnow()
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _centroid(inc: Incident) -> tuple[float, float] | None:
    import json

    if not inc.centroid:
        return None
    try:
        coords = json.loads(inc.centroid)["coordinates"]
        return float(coords[1]), float(coords[0])
    except Exception:
        return None


def _load_incidents(db: Session) -> list[Incident]:
    return list(
        db.scalars(
            select(Incident)
            .where(Incident.status != "dismissed")
            .options(selectinload(Incident.members).selectinload(IncidentEvidence.evidence))
        ).all()
    )


def corroborated(inc: Incident, rainfall_index: int) -> bool:
    members = inc.members
    if len(members) >= 2:
        return True
    has_sos = any(m.evidence.kind == "sos" for m in members)
    return has_sos and rainfall_index >= 1


def zone_for_point(lat: float, lon: float) -> str | None:
    best = None
    best_rank = 0
    for zone in load_pack().get("zones", []):
        if point_in_ring(lat, lon, zone["coordinates"]):
            rank = ZONE_RANK.get(zone["level"], 0)
            if rank > best_rank:
                best_rank = rank
                best = zone["level"]
    return best


def effective_zone(lat: float, lon: float, allow_critical: bool) -> str | None:
    level = zone_for_point(lat, lon)
    if level == "critical" and not allow_critical:
        if point_in_ring(lat, lon, _zone_ring("warning")):
            return "warning"
        if point_in_ring(lat, lon, _zone_ring("nearby")):
            return "nearby"
        return None
    return level


def _zone_ring(level: str) -> list[list[float]]:
    for zone in load_pack().get("zones", []):
        if zone["level"] == level:
            return zone["coordinates"]
    return []


def _need_kinds(inc: Incident) -> list[str]:
    types = { (m.evidence.emergency_type or "").lower() for m in inc.members }
    if "trapped" in types or any(m.evidence.injury for m in inc.members):
        return ["hospital", "fire"]
    if "landslide" in types:
        return ["fire", "hospital"]
    if "blocked_road" in types:
        return ["fire", "hospital"]
    return ["hospital", "shelter"]


def rank_resources(inc: Incident, isolated: bool) -> list[dict]:
    ll = _centroid(inc)
    if not ll:
        return []
    kinds = _need_kinds(inc)
    ranked: list[dict] = []
    for poi in load_pack().get("pois", []):
        dist = haversine_m(ll[0], ll[1], poi["lat"], poi["lon"])
        type_match = 1 if poi["kind"] in kinds else 0
        reachable = not (isolated and poi["id"] == "hospital-valley")
        ranked.append(
            {
                "id": poi["id"],
                "name": poi["name"],
                "kind": poi["kind"],
                "lat": poi["lat"],
                "lon": poi["lon"],
                "distance_m": round(dist),
                "type_match": bool(type_match),
                "available": bool(poi.get("available", True)),
                "availability_source": "simulated",
                "reachable": reachable,
                "score": type_match * 1_000_000 - dist + (0 if reachable else -5_000_000),
            }
        )
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked


def priority_for(inc: Incident, checkins: list[Checkin], isolated: bool) -> PriorityItem:
    w = PriorityWeights()
    members = [m.evidence for m in inc.members]
    severity = max((e.severity or 0) for e in members) if members else 0
    people = sum((e.people_count or 0) for e in members)
    ll = _centroid(inc)
    critical_n = 0
    if ll:
        for c in checkins:
            if c.status in {"assist", "danger"} and haversine_m(ll[0], ll[1], c.lat, c.lon) <= 500:
                critical_n += 1
    latest = max((_aware(e.t) for e in members), default=utcnow())
    hours = max(0.0, (utcnow() - latest).total_seconds() / 3600.0)
    resources = rank_resources(inc, isolated)
    km = (resources[0]["distance_m"] / 1000.0) if resources else 0.0
    breakdown = {
        "severity": w.severity * severity,
        "people": w.people * people,
        "critical_checkins": w.critical_checkins * critical_n,
        "hours_since_report": w.hours_since_report * hours,
        "km": w.km * km,
    }
    score = sum(breakdown.values())
    if isolated:
        score *= w.isolation_multiplier
        breakdown["isolation_multiplier"] = w.isolation_multiplier
    nearest = None
    reason = None
    if resources:
        nearest = resources[0]["name"]
        reason = f"{resources[0]['kind']} · {resources[0]['distance_m']}m · availability simulated"
        if not resources[0]["reachable"]:
            reason += " · road access uncertain"
    return PriorityItem(
        incident_code=inc.code,
        score=round(score, 3),
        breakdown={k: round(v, 3) for k, v in breakdown.items()},
        nearest_resource=nearest,
        reason=reason,
    )


@dataclass
class DecisionPicture:
    priority_queue: list[PriorityItem] = field(default_factory=list)
    isolation_settlements: list[str] = field(default_factory=list)
    cascade: str | None = None
    routes: list[dict] = field(default_factory=list)
    resources: list[dict] = field(default_factory=list)
    alerts: list[dict] = field(default_factory=list)
    corroborated: dict[str, bool] = field(default_factory=dict)
    zone_features: list[dict] = field(default_factory=list)
    visibility_features: list[dict] = field(default_factory=list)


def run_decision_engine(db: Session) -> DecisionPicture:
    """Deterministic rules Person 2 owns. Person 3 may overlay GIS later."""
    pack = load_pack()
    access = pack.get("access", {})
    last_edge = access.get("last_access_edge")
    blocked = {row.edge_id for row in db.scalars(select(BlockedEdge)).all()}
    isolated = bool(last_edge and last_edge in blocked)

    state = db.get(DemoState, 1)
    rain = state.rainfall_index if state else 0
    incidents = _load_incidents(db)
    checkins = list(db.scalars(select(Checkin)).all())
    citizens = list(db.scalars(select(User).where(User.role == "citizen")).all())

    picture = DecisionPicture()
    if isolated:
        picture.isolation_settlements = [access.get("settlement", "settlement")]
        picture.cascade = access.get("cascade")

    all_resources: list[dict] = []
    for inc in incidents:
        inc.isolated = isolated
        picture.corroborated[inc.code] = corroborated(inc, rain)
        item = priority_for(inc, checkins, isolated)
        picture.priority_queue.append(item)
        res = rank_resources(inc, isolated)
        for r in res:
            r["incident_code"] = inc.code
        all_resources.extend(res[:3])
        allow_critical = picture.corroborated[inc.code]
        for user in citizens:
            if user.last_lat is None or user.last_lon is None:
                continue
            level = effective_zone(user.last_lat, user.last_lon, allow_critical)
            if not level:
                continue
            exists = db.scalar(
                select(AlertEvent).where(
                    AlertEvent.user_id == user.id,
                    AlertEvent.incident_id == inc.id,
                    AlertEvent.zone_level == level,
                )
            )
            if exists:
                continue
            db.add(
                AlertEvent(
                    user_id=user.id,
                    incident_id=inc.id,
                    zone_level=level,
                    t=utcnow(),
                )
            )
            db.flush()
    picture.priority_queue.sort(key=lambda p: p.score, reverse=True)
    picture.resources = all_resources
    picture.routes = score_routes_with_blocked(blocked)

    alerts = db.scalars(select(AlertEvent)).all()
    by_id = {i.id: i for i in incidents}
    users = {u.id: u for u in citizens}
    for a in alerts:
        inc = by_id.get(a.incident_id)
        user = users.get(a.user_id)
        picture.alerts.append(
            {
                "user_email": user.email if user else "",
                "incident_code": inc.code if inc else "",
                "zone_level": a.zone_level,
                "t": _aware(a.t).isoformat(),
            }
        )

    try:
        from aashray.intelligence.decision import enhance

        enhance(db, picture)
    except ImportError:
        pass

    _write_sitrep(incidents)
    db.commit()
    return picture


def compose_sitrep(inc: Incident) -> str:
    """Deterministic sitrep from fused fields. Never blank; never invents geometry."""
    n = len(inc.members)
    kinds = sorted({(m.evidence.kind or "?") for m in inc.members if m.evidence})
    people = sum((m.evidence.people_count or 0) for m in inc.members if m.evidence)
    iso = " Isolation RULE: last access cut; medical delay estimated." if inc.isolated else ""
    dis = " Category disagreement on this cluster." if inc.disagreement else ""
    kinds_s = ", ".join(kinds) if kinds else "n/a"
    return (
        f"{inc.code} FUSED from {n} evidence ({kinds_s}). "
        f"Cluster confidence {inc.confidence:.2f} (not field accuracy). "
        f"Status {inc.status}. People mentioned ~{people}.{iso}{dis} "
        "Sitrep RULE."
    )[:240]


def _write_sitrep(incidents: list[Incident]) -> None:
    from aashray.services.llm import draft_sitrep

    for inc in incidents:
        fallback = compose_sitrep(inc)
        enhanced = draft_sitrep(
            {
                "code": inc.code,
                "confidence": inc.confidence,
                "isolated": inc.isolated,
                "status": inc.status,
                "members": len(inc.members),
            }
        )
        inc.sitrep_cache = (enhanced or fallback)[:240]
