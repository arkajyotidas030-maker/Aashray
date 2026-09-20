from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from aashray.database import get_db
from aashray.deps import get_current_user, require_responder, utcnow
from aashray.models import Incident, IncidentEvidence, User
from aashray.schemas import IncidentActionOut, IncidentDetail, IncidentOut, LockerMember, Provenance
from aashray.services.serialize import evidence_to_out

router = APIRouter(tags=["incidents"])


@router.get("/incidents", response_model=list[IncidentOut])
def list_incidents(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[IncidentOut]:
    rows = db.scalars(
        select(Incident)
        .options(selectinload(Incident.members).selectinload(IncidentEvidence.evidence))
        .order_by(Incident.id)
    ).all()
    out: list[IncidentOut] = []
    for inc in rows:
        if user.role != "responder":
            if not any(m.evidence.user_id == user.id for m in inc.members):
                continue
        out.append(
            IncidentOut(
                id=inc.id,
                code=inc.code,
                confidence=inc.confidence,
                status=inc.status,
                isolated=inc.isolated,
                disagreement=inc.disagreement,
                sitrep=inc.sitrep_cache,
                member_evidence_ids=[m.evidence_id for m in inc.members],
                provenance=Provenance(source="fused", as_of=inc.as_of),
            )
        )
    return out


def _detail(inc: Incident) -> IncidentDetail:
    locker = [
        LockerMember(
            **evidence_to_out(m.evidence, inc.code).model_dump(),
            contribution_score=m.contribution_score,
        )
        for m in inc.members
    ]
    return IncidentDetail(
        id=inc.id,
        code=inc.code,
        confidence=inc.confidence,
        status=inc.status,
        isolated=inc.isolated,
        disagreement=inc.disagreement,
        sitrep=inc.sitrep_cache,
        member_evidence_ids=[m.evidence_id for m in inc.members],
        provenance=Provenance(source="fused", as_of=inc.as_of),
        locker=locker,
    )


def _load(db: Session, incident_id: int) -> Incident | None:
    return db.scalar(
        select(Incident)
        .where(Incident.id == incident_id)
        .options(selectinload(Incident.members).selectinload(IncidentEvidence.evidence))
    )


@router.get("/incidents/{incident_id}", response_model=IncidentDetail)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IncidentDetail:
    inc = _load(db, incident_id)
    if inc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Incident not found")
    if user.role != "responder":
        if not any(m.evidence.user_id == user.id for m in inc.members):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not linked to this incident")
        locker = [
            LockerMember(
                **evidence_to_out(m.evidence, inc.code).model_dump(),
                contribution_score=m.contribution_score,
            )
            for m in inc.members
            if m.evidence.user_id == user.id
        ]
        detail = _detail(inc)
        detail.locker = locker
        return detail
    return _detail(inc)


@router.post("/ops/incidents/{incident_id}/assign", response_model=IncidentActionOut)
def assign_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_responder),
) -> IncidentActionOut:
    inc = db.get(Incident, incident_id)
    if inc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Incident not found")
    inc.status = "assigned"
    inc.as_of = utcnow()
    db.commit()
    return IncidentActionOut(code=inc.code, status=inc.status)


@router.post("/ops/incidents/{incident_id}/dismiss", response_model=IncidentActionOut)
def dismiss_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_responder),
) -> IncidentActionOut:
    inc = db.get(Incident, incident_id)
    if inc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Incident not found")
    inc.status = "dismissed"
    inc.as_of = utcnow()
    db.commit()
    return IncidentActionOut(code=inc.code, status=inc.status)
