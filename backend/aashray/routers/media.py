from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from aashray.database import get_db
from aashray.deps import require_responder
from aashray.models import Evidence, User

router = APIRouter(tags=["media"])


@router.get("/media/{evidence_id}")
def get_media(
    evidence_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_responder),
) -> FileResponse:
    ev = db.get(Evidence, evidence_id)
    if ev is None or not ev.media_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No media")
    path = Path(ev.media_path)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Media missing on disk")
    return FileResponse(path)
