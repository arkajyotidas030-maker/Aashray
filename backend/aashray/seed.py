from sqlalchemy import select
from sqlalchemy.orm import Session

from aashray.config import get_settings
from aashray.models import DemoState, User
from aashray.security import hash_password

TOWN = (32.2462, 77.1914)
HAMLET_A = (32.2390, 77.1875)
HAMLET_B = (32.2388, 77.1873)


def ensure_demo_state(db: Session) -> DemoState:
    row = db.get(DemoState, 1)
    if row is None:
        row = DemoState(id=1, tick=0, rainfall_index=0, playing=False)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def seed_if_demo(db: Session) -> None:
    settings = get_settings()
    if not settings.demo_mode:
        ensure_demo_state(db)
        return

    def upsert_user(email: str, role: str, lat: float | None = None, lon: float | None = None) -> None:
        existing = db.scalar(select(User).where(User.email == email))
        if existing:
            if lat is not None and existing.last_lat is None:
                existing.last_lat = lat
                existing.last_lon = lon
            if (
                email == settings.seed_citizen_email
                and existing.last_lat is not None
                and abs(existing.last_lat - TOWN[0]) < 1e-4
                and existing.last_lon is not None
                and abs(existing.last_lon - TOWN[1]) < 1e-4
            ):
                existing.last_lat, existing.last_lon = 32.2395, 77.1880
            return
        db.add(
            User(
                email=email,
                password_hash=hash_password(settings.seed_password),
                role=role,
                last_lat=lat,
                last_lon=lon,
            )
        )

    upsert_user(settings.seed_citizen_email, "citizen", 32.2395, 77.1880)
    upsert_user(settings.seed_ops_email, "responder", *TOWN)
    upsert_user("hamlet.a@demo", "citizen", *HAMLET_A)
    upsert_user("hamlet.b@demo", "citizen", *HAMLET_B)
    upsert_user("town.b@demo", "citizen", 32.2455, 77.1908)
    db.commit()
    ensure_demo_state(db)
