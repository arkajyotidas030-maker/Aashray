from tests.conftest import _login


def test_health_llm_down_routing_precomputed(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["db"] == "ok"
    assert body["llm"] == "down"
    assert body["routing"] == "precomputed"


def test_login_ops_and_citizen(client):
    ops = client.post(
        "/api/v1/auth/login", json={"email": "ops@demo", "password": "demo"}
    )
    assert ops.status_code == 200
    assert ops.json()["role"] == "responder"

    citizen = client.post(
        "/api/v1/auth/login", json={"email": "citizen@demo", "password": "demo"}
    )
    assert citizen.status_code == 200
    assert citizen.json()["role"] == "citizen"


def test_login_rejects_bad_password(client):
    res = client.post(
        "/api/v1/auth/login", json={"email": "ops@demo", "password": "wrong"}
    )
    assert res.status_code == 401


def test_snapshot_requires_responder(client):
    assert client.get("/api/v1/ops/snapshot").status_code == 401
    token = _login(client, "citizen@demo")
    res = client.get(
        "/api/v1/ops/snapshot", headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403


def test_snapshot_stub_has_provenance_and_tick_zero(client):
    token = _login(client, "ops@demo")
    res = client.get(
        "/api/v1/ops/snapshot", headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["tick"] == 0
    assert body["incidents"] == []
    assert body["priority_queue"] == []
    assert "unconfirmed_safety_status" in body["visibility"]
    assert "missing" not in body["visibility"]["note"].lower() or "not a missing" in body["visibility"]["note"].lower()
    for name, layer in body["layers"].items():
        assert layer["type"] == "FeatureCollection"
        assert layer["provenance"]["source"] in {"live", "fused", "rule", "simulated"}
        assert "as_of" in layer["provenance"]


def test_demo_tick_advances_snapshot(client):
    token = _login(client, "ops@demo")
    headers = {"Authorization": f"Bearer {token}"}
    tick = client.post("/api/v1/demo/tick", headers=headers)
    assert tick.status_code == 200
    assert tick.json()["tick"] == 1
    snap = client.get("/api/v1/ops/snapshot", headers=headers)
    assert snap.json()["tick"] == 1
