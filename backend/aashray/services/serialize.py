from aashray.models import Evidence
from aashray.schemas import EvidenceOut


def evidence_to_out(ev: Evidence, incident_code: str | None = None) -> EvidenceOut:
    if incident_code is None and ev.memberships:
        incident_code = ev.memberships[0].incident.code
    return EvidenceOut(
        id=ev.id,
        kind=ev.kind,
        lat=ev.lat,
        lon=ev.lon,
        t=ev.t,
        raw_text=ev.raw_text,
        emergency_type=ev.emergency_type,
        people_count=ev.people_count,
        severity=ev.severity,
        trapped=ev.trapped,
        injury=ev.injury,
        source=ev.source,
        as_of=ev.as_of,
        incident_code=incident_code,
        has_media=bool(ev.media_path),
    )
