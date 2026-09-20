from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from aashray.database import get_db
from aashray.deps import get_current_user
from aashray.models import BlockedEdge, User
from aashray.services.routes import score_routes_with_blocked
from sqlalchemy import select

router = APIRouter(tags=["routes"])


@router.get("/routes/safest")
def safest_routes(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    incident_id: int | None = Query(default=None),
) -> dict:
    blocked = {row.edge_id for row in db.scalars(select(BlockedEdge)).all()}
    routes = score_routes_with_blocked(blocked)
    return {
        "routing": "precomputed",
        "incident_id": incident_id,
        "routes": routes,
        "note": "Safety ranking of candidate geometries. Not a custom router.",
    }
