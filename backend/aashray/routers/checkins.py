from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from aashray.database import get_db
from aashray.deps import get_current_user
from aashray.models import User
from aashray.schemas import CheckinCreate, CheckinOut
from aashray.services.ingest import persist_checkin

router = APIRouter(tags=["checkins"])


@router.post("/checkins", response_model=CheckinOut, status_code=status.HTTP_201_CREATED)
def create_checkin(
    body: CheckinCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CheckinOut:
    if user.role != "responder":
        body = body.model_copy(update={"source": "live"})
    row = persist_checkin(db, user, body)
    return CheckinOut(
        id=row.id,
        status=row.status,  # type: ignore[arg-type]
        lat=row.lat,
        lon=row.lon,
        t=row.t,
        source=row.source,
    )
