from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("JWT_SECRET", "test-secret-must-be-at-least-32b")
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("OSRM_URL", "")
    monkeypatch.setenv("SEED_PASSWORD", "demo")
    monkeypatch.setenv("MEDIA_DIR", str(tmp_path / "media"))

    from aashray.config import get_settings
    from aashray.database import get_engine, get_session_factory

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    from aashray.main import app

    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


def _login(client: TestClient, email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "demo"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]
