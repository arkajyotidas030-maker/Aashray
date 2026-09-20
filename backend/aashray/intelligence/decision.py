from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from aashray.deps import utcnow
from aashray.models import AlertEvent, BlockedEdge, Checkin, DemoState, Incident, User
from aashray.intelligence.gis import geofence_zones, settlement_containing, zone_level_for
from aashray.intelligence.isolation import cascade_text, isolated_settlements, last_access_blocked, poi_reachable
from aashray.intelligence.routes import score_routes_shapely
from aashray.intelligence.visibility import score_visibility
from aashray.services.decision import DecisionPicture, _load_incidents, corroborated, priority_for, rank_resources


def enhance(db: Session, picture: DecisionPicture) -> DecisionPicture:
    """Shapely zones, networkx isolation, visibility grid, safest-of-N."""
    blocked = {row.edge_id for row in db.scalars(select(BlockedEdge)).all()}
    isolated_names = isolated_settlements(blocked)
    picture.isolation_settlements = isolated_names
    picture.cascade = cascade_text() if isolated_names else None
    picture.routes = score_routes_shapely(blocked)

    incidents = _load_incidents(db)
    checkins = list(db.scalars(select(Checkin)).all())
    citizens = list(db.scalars(select(User).where(User.role == "citizen")).all())
    checked_ids = {c.user_id for c in checkins}
    state = db.get(DemoState, 1)
    rain = state.rainfall_index if state else 0

    picture.priority_queue = []
    picture.resources = []
    zone_bank: list[dict] = []

    for inc in incidents:
        centroid = _latlon(inc)
        place = settlement_containing(*centroid) if centroid else None
        isolated = bool(place and place in isolated_names)
        if last_access_blocked(blocked) and place == "Gahar hamlet":
            isolated = True
        inc.isolated = isolated
        if centroid:
            zone_bank = geofence_zones(*centroid)
        allow = corroborated(inc, rain)
        picture.corroborated[inc.code] = allow
        item = priority_for(inc, checkins, isolated)
        picture.priority_queue.append(item)
        res = rank_resources(inc, isolated)
        for r in res:
            r["incident_code"] = inc.code
            r["reachable"] = poi_reachable(r["id"], blocked)
            r["access"] = "graph"
        picture.resources.extend(res[:3])

        if zone_bank:
            for user in citizens:
                if user.last_lat is None or user.last_lon is None:
                    continue
                level = zone_level_for(user.last_lat, user.last_lon, zone_bank, allow)
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
    picture.zone_features = zone_bank
    user_triples = [
        (u.last_lat, u.last_lon, u.id in checked_ids)
        for u in citizens
        if u.last_lat is not None and u.last_lon is not None
    ]
    picture.visibility_features = score_visibility(
        user_triples, hazard_nearby=bool(incidents) or rain >= 1
    )
    return picture


def _latlon(inc: Incident) -> tuple[float, float] | None:
    if not inc.centroid:
        return None
    try:
        coords = json.loads(inc.centroid)["coordinates"]
        return float(coords[1]), float(coords[0])
    except Exception:
        return None
