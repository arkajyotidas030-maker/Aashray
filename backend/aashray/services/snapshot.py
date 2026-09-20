import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from aashray.config import get_settings
from aashray.models import Checkin, DemoState, Evidence, Incident, IncidentEvidence, User
from aashray.schemas import (
    CheckinOut,
    CitizenSnapshot,
    EvidenceOut,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    HealthStatus,
    IncidentOut,
    IsolationState,
    LayerMap,
    PriorityWeights,
    Provenance,
    Snapshot,
    Source,
    VisibilitySummary,
)
from aashray.services.decision import effective_zone, run_decision_engine
from aashray.services.scenario import load_pack
from aashray.services.serialize import evidence_to_out


def health_status() -> HealthStatus:
    settings = get_settings()
    return HealthStatus(
        db="ok",
        llm="ok" if settings.llm_configured else "down",
        routing="precomputed",
    )


def _empty_layer(source: Source, as_of: datetime) -> GeoJSONFeatureCollection:
    return GeoJSONFeatureCollection(
        features=[],
        provenance=Provenance(source=source, as_of=as_of),
    )


def _aware(dt: datetime | None, fallback: datetime) -> datetime:
    if dt is None:
        return fallback
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _point_feature(lat: float, lon: float, properties: dict) -> GeoJSONFeature:
    return GeoJSONFeature(
        geometry={"type": "Point", "coordinates": [lon, lat]},
        properties=properties,
    )


def _poly_feature(ring: list[list[float]], properties: dict) -> GeoJSONFeature:
    return GeoJSONFeature(
        geometry={"type": "Polygon", "coordinates": [ring]},
        properties=properties,
    )


def _line_feature(line: list[list[float]], properties: dict) -> GeoJSONFeature:
    return GeoJSONFeature(
        geometry={"type": "LineString", "coordinates": line},
        properties=properties,
    )


def _centroid_latlon(inc: Incident) -> tuple[float, float] | None:
    if not inc.centroid:
        return None
    try:
        geom = json.loads(inc.centroid)
        coords = geom.get("coordinates") or []
        return float(coords[1]), float(coords[0])
    except Exception:
        return None


def _visibility(db: Session) -> VisibilitySummary:
    citizens = list(db.scalars(select(User).where(User.role == "citizen")).all())
    checked = {
        row.user_id
        for row in db.scalars(select(Checkin)).all()
    }
    n = len(citizens)
    confirmed = len({u.id for u in citizens if u.id in checked})
    unconfirmed = n - confirmed
    coverage = (100.0 * confirmed / n) if n else 0.0
    return VisibilitySummary(
        coverage_pct=round(coverage, 1),
        unconfirmed_safety_status=unconfirmed,
        simulated_registered_users=n,
    )


def build_snapshot(db: Session) -> Snapshot:
    picture = run_decision_engine(db)
    state = db.get(DemoState, 1)
    now = datetime.now(timezone.utc)
    as_of = _aware(state.as_of if state else None, now)
    pack = load_pack()

    incidents = db.scalars(
        select(Incident)
        .options(selectinload(Incident.members).selectinload(IncidentEvidence.evidence))
        .order_by(Incident.id)
    ).all()
    evidence_rows = db.scalars(
        select(Evidence)
        .options(selectinload(Evidence.memberships).selectinload(IncidentEvidence.incident))
        .order_by(Evidence.id)
    ).all()
    checkins = db.scalars(select(Checkin).order_by(Checkin.id)).all()

    incidents_out: list[IncidentOut] = []
    incident_features: list[GeoJSONFeature] = []
    for inc in incidents:
        member_ids = [m.evidence_id for m in inc.members]
        incidents_out.append(
            IncidentOut(
                id=inc.id,
                code=inc.code,
                confidence=inc.confidence,
                status=inc.status,
                isolated=inc.isolated,
                disagreement=inc.disagreement,
                sitrep=inc.sitrep_cache,
                member_evidence_ids=member_ids,
                provenance=Provenance(source="fused", as_of=_aware(inc.as_of, as_of)),
            )
        )
        ll = _centroid_latlon(inc)
        if ll:
            incident_features.append(
                _point_feature(
                    ll[0],
                    ll[1],
                    {
                        "code": inc.code,
                        "confidence": inc.confidence,
                        "status": inc.status,
                        "source": "fused",
                        "as_of": _aware(inc.as_of, as_of).isoformat(),
                    },
                )
            )

    evidence_out: list[EvidenceOut] = [evidence_to_out(ev) for ev in evidence_rows]
    safety_features = [
        _point_feature(
            c.lat,
            c.lon,
            {"status": c.status, "source": c.source, "unconfirmed_safety_status": False},
        )
        for c in checkins
    ]
    poi_features = [
        _point_feature(
            p["lat"],
            p["lon"],
            {
                "name": p["name"],
                "kind": p["kind"],
                "availability_source": "simulated",
                "source": "rule",
                "label": "SIMULATED availability",
            },
        )
        for p in pack.get("pois", [])
    ]
    allow_critical = any(picture.corroborated.values())
    if picture.zone_features:
        zone_features = []
        for z in picture.zone_features:
            if z["level"] == "critical" and not allow_critical:
                continue
            zone_features.append(
                GeoJSONFeature(
                    geometry=z["geometry"],
                    properties={
                        "level": z["level"],
                        "source": z.get("source", "rule"),
                        "method": z.get("method"),
                        "critical_requires_corroboration": z["level"] == "critical",
                        "corroborated": allow_critical if z["level"] == "critical" else True,
                    },
                )
            )
    else:
        zone_features = [
            _poly_feature(
                z["coordinates"],
                {
                    "level": z["level"],
                    "source": "rule",
                    "critical_requires_corroboration": z["level"] == "critical",
                    "corroborated": allow_critical if z["level"] == "critical" else True,
                },
            )
            for z in pack.get("zones", [])
        ]
        if not allow_critical:
            zone_features = [f for f in zone_features if f.properties.get("level") != "critical"]

    risk_features = []
    if state and state.rainfall_index >= 1 and pack.get("hazard"):
        risk_features.append(
            _poly_feature(
                pack["hazard"]["coordinates"],
                {
                    "layer": "risk",
                    "source": "simulated",
                    "label": "SIMULATED rainfall/slope estimation — not IMD",
                },
            )
        )
    route_features = [
        _line_feature(
            r["coordinates"],
            {"id": r["id"], "status": r["status"], "reason": r.get("reason"), "source": r.get("source", "precomputed")},
        )
        for r in picture.routes
    ]
    blocked_features = []
    from aashray.models import BlockedEdge

    blocked_rows = list(db.scalars(select(BlockedEdge)).all())
    roads = {r["edge_id"]: r["coordinates"] for r in pack.get("roads", [])}
    for row in blocked_rows:
        geom = roads.get(row.edge_id)
        if geom:
            blocked_features.append(
                _line_feature(geom, {"edge_id": row.edge_id, "source": row.source})
            )

    vis_features = []
    if picture.visibility_features:
        vis_features = [
            GeoJSONFeature(geometry=f["geometry"], properties=f.get("properties") or {})
            for f in picture.visibility_features
        ]

    layers = LayerMap(
        incidents=GeoJSONFeatureCollection(
            features=incident_features, provenance=Provenance(source="fused", as_of=as_of)
        ),
        risk=GeoJSONFeatureCollection(
            features=risk_features, provenance=Provenance(source="simulated", as_of=as_of)
        ),
        infrastructure=GeoJSONFeatureCollection(
            features=poi_features, provenance=Provenance(source="rule", as_of=as_of)
        ),
        human_safety=GeoJSONFeatureCollection(
            features=safety_features, provenance=Provenance(source="live", as_of=as_of)
        ),
        visibility=GeoJSONFeatureCollection(
            features=vis_features, provenance=Provenance(source="rule", as_of=as_of)
        ),
        evacuation=GeoJSONFeatureCollection(
            features=route_features, provenance=Provenance(source="rule", as_of=as_of)
        ),
        alert_zones=GeoJSONFeatureCollection(
            features=zone_features, provenance=Provenance(source="rule", as_of=as_of)
        ),
        blocked_roads=GeoJSONFeatureCollection(
            features=blocked_features, provenance=Provenance(source="simulated", as_of=as_of)
        ),
    )

    sitrep = next((i.sitrep_cache for i in incidents if i.sitrep_cache), None)
    isolation = IsolationState(
        isolated_settlements=picture.isolation_settlements,
        cascade=picture.cascade,
    )

    return Snapshot(
        tick=state.tick if state else 0,
        rainfall_index=state.rainfall_index if state else 0,
        playing=bool(state.playing) if state else False,
        as_of=as_of,
        health=health_status(),
        incidents=incidents_out,
        evidence=evidence_out,
        layers=layers,
        visibility=_visibility(db),
        priority_weights=PriorityWeights(),
        priority_queue=picture.priority_queue,
        isolation=isolation,
        sitrep=sitrep,
        resources=picture.resources,
        routes=picture.routes,
        alerts=picture.alerts,
        corroborated=picture.corroborated,
    )


def build_citizen_snapshot(db: Session, user: User) -> CitizenSnapshot:
    snap = build_snapshot(db)
    lat, lon = user.last_lat, user.last_lon
    allow = any(snap.corroborated.values())
    level = None
    if lat is not None and lon is not None:
        level = _level_from_zone_features(lat, lon, snap.layers.alert_zones.features)
        if level is None:
            level = effective_zone(lat, lon, allow)
    messages = {
        "critical": "You are in a Critical zone after corroborated reports. Avoid travel toward the slope.",
        "warning": "Warning zone. Avoid travelling toward the incident.",
        "nearby": "Nearby zone. Do not travel toward the reported slope failure.",
    }
    safest = next((r for r in snap.routes if r.get("status") == "safest_available"), None)
    rejected = [r for r in snap.routes if r.get("status") == "rejected"]
    shelters = [p for p in load_pack().get("pois", []) if p["kind"] in {"shelter", "hospital"}]
    own_checkin = db.scalars(
        select(Checkin).where(Checkin.user_id == user.id).order_by(Checkin.id.desc())
    ).first()
    own_ids = [e.id for e in db.scalars(select(Evidence).where(Evidence.user_id == user.id)).all()]
    checkin_out = None
    if own_checkin:
        checkin_out = CheckinOut(
            id=own_checkin.id,
            status=own_checkin.status,  # type: ignore[arg-type]
            lat=own_checkin.lat,
            lon=own_checkin.lon,
            t=own_checkin.t,
            source=own_checkin.source,
        )
    return CitizenSnapshot(
        tick=snap.tick,
        rainfall_index=snap.rainfall_index,
        as_of=snap.as_of,
        zone_level=level,
        zone_message=messages.get(level or "", None),
        safest_route=safest,
        rejected_routes=rejected,
        shelters=shelters,
        isolation=snap.isolation,
        own_checkin=checkin_out,
        own_evidence_ids=own_ids,
        alert_zones=snap.layers.alert_zones,
        evacuation=snap.layers.evacuation,
    )


def _level_from_zone_features(lat: float, lon: float, features: list) -> str | None:
    from shapely.geometry import Point, shape

    rank = {"critical": 3, "warning": 2, "nearby": 1}
    best, best_r = None, 0
    pt = Point(lon, lat)
    for feat in features:
        geom = feat.geometry
        if not geom:
            continue
        try:
            poly = shape(geom)
        except Exception:
            continue
        if poly.contains(pt) or poly.touches(pt):
            level = (feat.properties or {}).get("level")
            r = rank.get(level, 0)
            if r > best_r:
                best, best_r = level, r
    return best
