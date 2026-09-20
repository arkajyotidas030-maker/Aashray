from tests.conftest import _login

NEAR = {"lat": 32.2395, "lon": 77.1880}


def _auth(client, email: str) -> dict:
    return {"Authorization": f"Bearer {_login(client, email)}"}


def test_single_sos_does_not_create_critical_alert(client):
    headers = _auth(client, "citizen@demo")
    res = client.post(
        "/api/v1/evidence",
        headers=headers,
        json={**NEAR, "kind": "sos", "raw_text": "Landslide", "emergency_type": "landslide"},
    )
    assert res.status_code == 201
    ops = _auth(client, "ops@demo")
    snap = client.get("/api/v1/ops/snapshot", headers=ops).json()
    assert snap["corroborated"][snap["incidents"][0]["code"]] is False
    assert all(a["zone_level"] != "critical" for a in snap["alerts"])


def test_fused_incident_has_priority_resources_and_critical_after_corroboration(client):
    headers = _auth(client, "citizen@demo")
    for extra in (
        {"emergency_type": "landslide", "raw_text": "Landslide on the hill road", "severity": 4, "people_count": 3},
        {
            "lat": 32.2398,
            "lon": 77.1884,
            "emergency_type": "blocked_road",
            "raw_text": "Road blocked by debris",
        },
    ):
        body = {**NEAR, "kind": "sos", **extra}
        assert client.post("/api/v1/evidence", headers=headers, json=body).status_code == 201

    ops = _auth(client, "ops@demo")
    snap = client.get("/api/v1/ops/snapshot", headers=ops).json()
    assert len(snap["incidents"]) == 1
    assert snap["corroborated"][snap["incidents"][0]["code"]] is True
    assert snap["priority_queue"]
    item = snap["priority_queue"][0]
    assert "severity" in item["breakdown"]
    assert item["nearest_resource"]
    assert snap["resources"]
    assert any(a["zone_level"] == "critical" for a in snap["alerts"])
    assert any(f["properties"]["level"] == "critical" for f in snap["layers"]["alert_zones"]["features"])
    assert snap["visibility"]["simulated_registered_users"] >= 4
    assert "missing-person" in snap["visibility"]["note"]


def test_safest_route_rejects_hazard_path(client):
    ops = _auth(client, "ops@demo")
    res = client.get("/api/v1/routes/safest", headers=ops)
    assert res.status_code == 200
    routes = {r["id"]: r for r in res.json()["routes"]}
    assert routes["fast"]["status"] == "rejected"
    assert any(r["status"] == "safest_available" for r in routes.values())
    assert routes["safe"]["status"] != "rejected"


def test_citizen_snapshot_hides_ops_feed(client):
    citizen = _auth(client, "citizen@demo")
    client.post(
        "/api/v1/evidence",
        headers=citizen,
        json={**NEAR, "raw_text": "Landslide", "emergency_type": "landslide"},
    )
    pic = client.get("/api/v1/citizen/snapshot", headers=citizen).json()
    assert "evidence" not in pic
    assert "priority_queue" not in pic
    assert pic["own_evidence_ids"]
    assert "not shown" in pic["note"].lower()


def test_demo_t7_marks_isolation_and_t5_checkin_visibility(client):
    ops = _auth(client, "ops@demo")
    for _ in range(7):
        assert client.post("/api/v1/demo/tick", headers=ops).status_code == 200
    snap = client.get("/api/v1/ops/snapshot", headers=ops).json()
    assert snap["tick"] == 7
    assert snap["incidents"]
    assert snap["incidents"][0]["isolated"] is True
    assert snap["isolation"]["isolated_settlements"]
    assert snap["priority_queue"][0]["breakdown"].get("isolation_multiplier") == 1.5
    assert snap["visibility"]["unconfirmed_safety_status"] >= 1
    listed = client.get("/api/v1/incidents", headers=ops)
    assert listed.status_code == 200
    assert listed.json()


def test_sitrep_is_rule_text_when_llm_down(client):
    headers = _auth(client, "citizen@demo")
    res = client.post(
        "/api/v1/evidence",
        headers=headers,
        json={**NEAR, "kind": "sos", "raw_text": "Landslide on the hill road", "emergency_type": "landslide"},
    )
    assert res.status_code == 201
    ops = _auth(client, "ops@demo")
    snap = client.get("/api/v1/ops/snapshot", headers=ops).json()
    assert snap["sitrep"]
    assert "FUSED" in snap["sitrep"]
    assert "Sitrep RULE" in snap["sitrep"]
    assert snap["health"]["llm"] == "down"
