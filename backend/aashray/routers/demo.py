from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from aashray.database import get_db
from aashray.deps import require_responder, utcnow
from aashray.models import DemoState, User
from aashray.schemas import DemoPlayRequest, DemoStateOut
from aashray.seed import ensure_demo_state
from aashray.services.clock import apply_tick_actions

router = APIRouter(prefix="/demo", tags=["demo"])


def _out(row: DemoState) -> DemoStateOut:
    return DemoStateOut(
        tick=row.tick,
        rainfall_index=row.rainfall_index,
        playing=row.playing,
        as_of=row.as_of,
    )


@router.post("/tick", response_model=DemoStateOut)
def demo_tick(
    db: Session = Depends(get_db),
    _user: User = Depends(require_responder),
) -> DemoStateOut:
    row = ensure_demo_state(db)
    row.tick += 1
    row.as_of = utcnow()
    db.commit()
    apply_tick_actions(db, row.tick)
    row = ensure_demo_state(db)
    db.refresh(row)
    return _out(row)


@router.post("/play", response_model=DemoStateOut)
def demo_play(
    body: DemoPlayRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(require_responder),
) -> DemoStateOut:
    row = ensure_demo_state(db)
    row.playing = body.playing
    row.as_of = utcnow()
    db.commit()
    db.refresh(row)
    return _out(row)
