import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from aashray.config import get_settings
from aashray.deps import utcnow
from aashray.models import BlockedEdge, User
from aashray.schemas import CheckinCreate, EvidenceCreate
from aashray.seed import ensure_demo_state
from aashray.services.ingest import persist_checkin, persist_evidence

TICKS_PATH = Path(__file__).resolve().parent.parent / "scenario" / "ticks.json"


def _load_ticks() -> dict:
    if not TICKS_PATH.exists():
        return {}
    return json.loads(TICKS_PATH.read_text(encoding="utf-8"))


def _demo_citizen(db: Session) -> User:
    settings = get_settings()
    user = db.scalar(select(User).where(User.email == settings.seed_citizen_email))
    if user is None:
        raise RuntimeError("Demo citizen missing; seed DEMO_MODE users")
    return user


def apply_tick_actions(db: Session, tick: int) -> None:
    """Inject scripted inputs through the same persist/check-in functions as live users."""
    spec = _load_ticks().get(str(tick), {})
    if not spec:
        return
    citizen = _demo_citizen(db)
    now = utcnow()

    if "rainfall_index" in spec:
        state = ensure_demo_state(db)
        state.rainfall_index = int(spec["rainfall_index"])
        db.commit()

    for raw in spec.get("evidence", []):
        body = EvidenceCreate.model_validate({**raw, "source": "simulated"})
        persist_evidence(db, citizen, body)

    for raw in spec.get("checkins", []):
        body = CheckinCreate.model_validate({**raw, "source": "simulated"})
        persist_checkin(db, citizen, body)

    for raw in spec.get("blocked_edges", []):
        db.add(
            BlockedEdge(
                edge_id=raw["edge_id"],
                t=now,
                source=raw.get("source", "simulated"),
            )
        )
        db.commit()

    from aashray.services.decision import run_decision_engine

    run_decision_engine(db)
