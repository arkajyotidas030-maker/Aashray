from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from aashray.database import get_db
from aashray.deps import get_current_user
from aashray.models import User
from aashray.schemas import CitizenSnapshot
from aashray.services.snapshot import build_citizen_snapshot

router = APIRouter(prefix="/citizen", tags=["citizen"])


@router.get("/snapshot", response_model=CitizenSnapshot)
def citizen_snapshot(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CitizenSnapshot:
    return build_citizen_snapshot(db, user)
