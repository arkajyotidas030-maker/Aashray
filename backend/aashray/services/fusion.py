from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from aashray.deps import utcnow
from aashray.models import Evidence, Incident, IncidentEvidence

GEO_RADIUS_M = 500.0
TIME_WINDOW = timedelta(minutes=45)
ATTACH_THRESHOLD = 0.65
W_GEO, W_TIME, W_CAT, W_TEXT = 0.40, 0.25, 0.20, 0.15
RELATED = {
    "landslide": "mass_movement",
    "blocked_road": "mass_movement",
    "trapped": "mass_movement",
    "debris": "mass_movement",
}


def category_match(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 1.0
    la, lb = a.strip().lower(), b.strip().lower()
    if la == lb:
        return 1.0
    if RELATED.get(la) and RELATED.get(la) == RELATED.get(lb):
        return 0.7
    return 0.0


def categories_compatible(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return True
    la, lb = a.strip().lower(), b.strip().lower()
    if la == lb:
        return True
    if RELATED.get(la) and RELATED.get(la) == RELATED.get(lb):
        return True
    return False


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def geo_score(dist_m: float) -> float:
    if dist_m >= GEO_RADIUS_M:
        return 0.0
    return 1.0 - dist_m / GEO_RADIUS_M


def time_score(seconds: float) -> float:
    window = TIME_WINDOW.total_seconds()
    if seconds < 0 or seconds >= window:
        return 0.0
    return 1.0 - seconds / window


def jaccard_text(a: str | None, b: str | None) -> float:
    """Offline text_sim until Person 3 embeddings/TF-IDF land."""
    try:
        from aashray.intelligence.textsim import text_similarity  # type: ignore

        return float(text_similarity(a or "", b or ""))
    except Exception:
        wa = set((a or "").lower().split())
        wb = set((b or "").lower().split())
        if not wa or not wb:
            return 0.0
        return len(wa & wb) / len(wa | wb)


def _aware(dt: datetime | None) -> datetime:
    if dt is None:
        return utcnow()
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def pair_score(ev: Evidence, other: Evidence) -> float:
    dist = haversine_m(ev.lat, ev.lon, other.lat, other.lon)
    dt = abs((_aware(ev.t) - _aware(other.t)).total_seconds())
    return (
        W_GEO * geo_score(dist)
        + W_TIME * time_score(dt)
        + W_CAT * category_match(ev.emergency_type, other.emergency_type)
        + W_TEXT * jaccard_text(ev.raw_text, other.raw_text)
    )


def _centroid_json(lat: float, lon: float) -> str:
    return json.dumps({"type": "Point", "coordinates": [lon, lat]})


def _next_code(db: Session) -> str:
    n = db.scalar(select(Incident.id).order_by(Incident.id.desc())) or 0
    return f"A{2719 + n}"


def _incident_types(incident: Incident) -> set[str]:
    types: set[str] = set()
    for m in incident.members:
        t = m.evidence.emergency_type
        if t:
            types.add(t.lower())
    return types


def fuse_evidence(db: Session, evidence: Evidence) -> Incident:
    """Attach to an open incident or create one. Person 3 may replace pair_score."""
    open_incidents = db.scalars(
        select(Incident)
        .where(Incident.status != "dismissed")
        .options(selectinload(Incident.members).selectinload(IncidentEvidence.evidence))
    ).all()

    best: tuple[float, Incident, Evidence] | None = None
    for inc in open_incidents:
        for member in inc.members:
            other = member.evidence
            if not categories_compatible(evidence.emergency_type, other.emergency_type):
                continue
            if haversine_m(evidence.lat, evidence.lon, other.lat, other.lon) > GEO_RADIUS_M:
                continue
            if abs((_aware(evidence.t) - _aware(other.t)).total_seconds()) > TIME_WINDOW.total_seconds():
                continue
            s = pair_score(evidence, other)
            if best is None or s > best[0]:
                best = (s, inc, other)

    if best and best[0] >= ATTACH_THRESHOLD:
        score, inc, _ = best
        db.add(
            IncidentEvidence(
                incident_id=inc.id,
                evidence_id=evidence.id,
                contribution_score=score,
            )
        )
        inc.confidence = score
        inc.centroid = _centroid_json(evidence.lat, evidence.lon)
        inc.as_of = utcnow()
        existing = _incident_types(inc)
        if evidence.emergency_type and existing:
            if not any(categories_compatible(evidence.emergency_type, t) for t in existing):
                inc.disagreement = True
        db.flush()
        db.refresh(inc)
        return inc

    inc = Incident(
        code=_next_code(db),
        centroid=_centroid_json(evidence.lat, evidence.lon),
        geometry=_centroid_json(evidence.lat, evidence.lon),
        confidence=0.40,
        status="open",
        as_of=utcnow(),
    )
    db.add(inc)
    db.flush()
    db.add(
        IncidentEvidence(
            incident_id=inc.id,
            evidence_id=evidence.id,
            contribution_score=0.40,
        )
    )
    db.flush()
    return inc


def maybe_run_decision_engine(db: Session) -> None:
    from aashray.services.decision import run_decision_engine

    run_decision_engine(db)
