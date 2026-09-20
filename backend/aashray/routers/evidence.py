from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from aashray.database import get_db
from aashray.deps import get_current_user
from aashray.limiter import limiter
from aashray.models import Evidence, User
from aashray.schemas import EvidenceCreate, EvidenceCreated
from aashray.services.ingest import persist_evidence, save_media

router = APIRouter(tags=["evidence"])


@router.post("/evidence", response_model=EvidenceCreated, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_evidence(
    request: Request,
    body: EvidenceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EvidenceCreated:
    if user.role != "responder":
        body = body.model_copy(update={"source": "live"})
    ev, code = persist_evidence(db, user, body)
    conf = 0.4
    if ev.memberships:
        conf = ev.memberships[0].incident.confidence
    return EvidenceCreated(
        evidence_id=ev.id,
        incident_code=code,
        cluster_confidence=conf,
    )


@router.post("/evidence/{evidence_id}/media", response_model=EvidenceCreated)
@limiter.limit("10/minute")
def upload_evidence_media(
    request: Request,
    evidence_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    file: UploadFile = File(...),
) -> EvidenceCreated:
    ev = db.get(Evidence, evidence_id)
    if ev is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evidence not found")
    if ev.user_id != user.id and user.role != "responder":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your evidence")
    data = file.file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "Max 5MB")
    save_media(db, ev, file.filename or "upload.bin", data)
    code = ev.memberships[0].incident.code if ev.memberships else ""
    conf = ev.memberships[0].incident.confidence if ev.memberships else 0.4
    return EvidenceCreated(evidence_id=ev.id, incident_code=code, cluster_confidence=conf)
