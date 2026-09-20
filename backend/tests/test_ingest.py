from tests.conftest import _login

NEAR = {"lat": 32.2395, "lon": 77.1880}


def _auth(client, email: str) -> dict:
    return {"Authorization": f"Bearer {_login(client, email)}"}


def test_sos_returns_201_and_incident_code(client):
    headers = _auth(client, "citizen@demo")
    res = client.post(
        "/api/v1/evidence",
        headers=headers,
        json={**NEAR, "kind": "sos", "raw_text": "Landslide on the slope", "severity": 4},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["evidence_id"] >= 1
    assert body["incident_code"].startswith("A")
    assert "cluster confidence" in body["confidence_label"]


def test_four_nearby_reports_fuse_to_one_incident(client):
    headers = _auth(client, "citizen@demo")
    payloads = [
        {**NEAR, "kind": "sos", "raw_text": "Landslide on the hill road", "emergency_type": "landslide"},
        {
            "lat": 32.2398,
            "lon": 77.1884,
            "kind": "report",
            "raw_text": "Road blocked by debris",
            "emergency_type": "blocked_road",
        },
        {
            "lat": 32.2392,
            "lon": 77.1877,
            "kind": "sos",
            "raw_text": "Vehicle trapped under debris",
            "emergency_type": "trapped",
            "trapped": True,
        },
        {
            "lat": 32.2396,
            "lon": 77.1881,
            "kind": "photo_meta",
            "raw_text": "Debris photo after landslide on blocked road",
            "emergency_type": "landslide",
        },
    ]
    codes = []
    for p in payloads:
        res = client.post("/api/v1/evidence", headers=headers, json=p)
        assert res.status_code == 201, res.text
        codes.append(res.json()["incident_code"])
    assert len(set(codes)) == 1

    ops = _auth(client, "ops@demo")
    snap = client.get("/api/v1/ops/snapshot", headers=ops)
    assert snap.status_code == 200
    assert len(snap.json()["incidents"]) == 1
    assert len(snap.json()["evidence"]) == 4
    assert len(snap.json()["incidents"][0]["member_evidence_ids"]) == 4
    assert snap.json()["layers"]["incidents"]["features"]


def test_distant_report_starts_new_incident(client):
    headers = _auth(client, "citizen@demo")
    a = client.post(
        "/api/v1/evidence",
        headers=headers,
        json={**NEAR, "raw_text": "Landslide here", "emergency_type": "landslide"},
    )
    b = client.post(
        "/api/v1/evidence",
        headers=headers,
        json={
            "lat": 28.61,
            "lon": 77.21,
            "raw_text": "Different city flood",
            "emergency_type": "flood",
        },
    )
    assert a.json()["incident_code"] != b.json()["incident_code"]


def test_checkin_and_media_role_gate(client):
    citizen = _auth(client, "citizen@demo")
    chk = client.post(
        "/api/v1/checkins",
        headers=citizen,
        json={"status": "safe", **NEAR},
    )
    assert chk.status_code == 201

    ev = client.post(
        "/api/v1/evidence",
        headers=citizen,
        json={**NEAR, "kind": "photo_meta", "raw_text": "debris photo"},
    )
    eid = ev.json()["evidence_id"]
    up = client.post(
        f"/api/v1/evidence/{eid}/media",
        headers=citizen,
        files={"file": ("debris.png", b"\x89PNG\r\nfake", "image/png")},
    )
    assert up.status_code == 200

    assert client.get(f"/api/v1/media/{eid}", headers=citizen).status_code == 403
    ops = _auth(client, "ops@demo")
    assert client.get(f"/api/v1/media/{eid}", headers=ops).status_code == 200


def test_demo_clock_tick2_injects_four_fused_reports(client):
    ops = _auth(client, "ops@demo")
    t1 = client.post("/api/v1/demo/tick", headers=ops)
    assert t1.json()["tick"] == 1
    assert t1.json()["rainfall_index"] == 1
    snap1 = client.get("/api/v1/ops/snapshot", headers=ops).json()
    assert snap1["evidence"] == []

    t2 = client.post("/api/v1/demo/tick", headers=ops)
    assert t2.json()["tick"] == 2
    snap2 = client.get("/api/v1/ops/snapshot", headers=ops).json()
    assert len(snap2["evidence"]) == 4
    assert len(snap2["incidents"]) == 1
    assert all(e["source"] == "simulated" for e in snap2["evidence"])


def test_assign_and_dismiss(client):
    citizen = _auth(client, "citizen@demo")
    created = client.post(
        "/api/v1/evidence",
        headers=citizen,
        json={**NEAR, "raw_text": "Landslide", "emergency_type": "landslide"},
    )
    ops = _auth(client, "ops@demo")
    snap = client.get("/api/v1/ops/snapshot", headers=ops).json()
    iid = snap["incidents"][0]["id"]
    assert client.post(f"/api/v1/ops/incidents/{iid}/assign", headers=ops).json()["status"] == "assigned"
    assert client.post(f"/api/v1/ops/incidents/{iid}/dismiss", headers=ops).json()["status"] == "dismissed"
    assert client.post(f"/api/v1/ops/incidents/{iid}/assign", headers=citizen).status_code == 403
