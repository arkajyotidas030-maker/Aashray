from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from aashray import models as _models  # noqa: F401
from aashray.config import get_settings
from aashray.database import Base, SessionLocal, get_engine
from aashray.limiter import limiter
from aashray.routers import auth, checkins, citizen, demo, evidence, health, incidents, media, ops, routes
from aashray.seed import seed_if_demo

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=get_engine())
    Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        seed_if_demo(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="AASHRAY API",
    version="0.1.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(ops.router, prefix="/api/v1")
app.include_router(demo.router, prefix="/api/v1")
app.include_router(evidence.router, prefix="/api/v1")
app.include_router(checkins.router, prefix="/api/v1")
app.include_router(incidents.router, prefix="/api/v1")
app.include_router(media.router, prefix="/api/v1")
app.include_router(routes.router, prefix="/api/v1")
app.include_router(citizen.router, prefix="/api/v1")
