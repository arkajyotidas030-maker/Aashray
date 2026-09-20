from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from aashray.database import get_db
from aashray.deps import require_responder
from aashray.models import User
from aashray.schemas import Snapshot
from aashray.services.snapshot import build_snapshot

router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/snapshot", response_model=Snapshot)
def ops_snapshot(
    db: Session = Depends(get_db),
    _user: User = Depends(require_responder),
) -> Snapshot:
    return build_snapshot(db)
