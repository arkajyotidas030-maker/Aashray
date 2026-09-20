from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from aashray.database import get_db
from aashray.schemas import HealthStatus
from aashray.services.snapshot import health_status

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
def health(db: Session = Depends(get_db)) -> HealthStatus:
    status = health_status()
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        status = status.model_copy(update={"db": "down"})
    return status
