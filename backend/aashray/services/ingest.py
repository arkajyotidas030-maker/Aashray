from pathlib import Path

from sqlalchemy.orm import Session

from aashray.config import get_settings
from aashray.deps import utcnow
from aashray.models import Checkin, Evidence, User
from aashray.schemas import CheckinCreate, EvidenceCreate
from aashray.services.fusion import fuse_evidence, maybe_run_decision_engine

_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("landslide", ("landslide", "debris", "slope", "hillside")),
    ("blocked_road", ("blocked", "road blocked", "debris on road")),
    ("trapped", ("trapped", "vehicle trapped", "stuck")),
]


def classify_keywords(text: str | None) -> str | None:
    if not text:
        return None
    low = text.lower()
    for label, words in _KEYWORDS:
        if any(w in low for w in words):
            return label
    return None


def persist_checkin(db: Session, user: User, body: CheckinCreate) -> Checkin:
    now = utcnow()
    row = Checkin(
        user_id=user.id,
        status=body.status,
        lat=body.lat,
        lon=body.lon,
        t=now,
        source=body.source,
    )
    db.add(row)
    user.last_lat = body.lat
    user.last_lon = body.lon
    db.commit()
    db.refresh(row)
    return row


def persist_evidence(db: Session, user: User, body: EvidenceCreate) -> tuple[Evidence, str]:
    """Write the row first (SOS 201 path), then fuse in-process."""
    now = utcnow()
    emergency = body.emergency_type
    severity = body.severity
    people = body.people_count
    if not emergency or severity is None or people is None:
        try:
            from aashray.intelligence.classify import classify

            got = classify(body.raw_text)
        except ImportError:
            got = {"emergency_type": classify_keywords(body.raw_text)}
        emergency = emergency or got.get("emergency_type")
        if severity is None and got.get("severity") is not None:
            severity = got.get("severity")
        if people is None and got.get("people_count") is not None:
            people = got.get("people_count")
    ev = Evidence(
        user_id=user.id,
        kind=body.kind,
        lat=body.lat,
        lon=body.lon,
        t=now,
        raw_text=body.raw_text,
        emergency_type=emergency,
        people_count=people,
        severity=severity,
        trapped=body.trapped,
        injury=body.injury,
        source=body.source,
        as_of=now,
    )
    db.add(ev)
    user.last_lat = body.lat
    user.last_lon = body.lon
    db.flush()
    incident = fuse_evidence(db, ev)
    maybe_run_decision_engine(db)
    db.commit()
    db.refresh(ev)
    db.refresh(incident)
    return ev, incident.code


def save_media(db: Session, evidence: Evidence, filename: str, data: bytes) -> str:
    settings = get_settings()
    folder = Path(settings.media_dir)
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename).suffix.lower() or ".bin"
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".bin"
    dest = folder / f"{evidence.id}{suffix}"
    dest.write_bytes(data)
    evidence.media_path = str(dest)
    db.commit()
    db.refresh(evidence)
    return evidence.media_path
