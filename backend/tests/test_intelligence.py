from aashray.intelligence.gis import geofence_zones, settlement_containing
from aashray.intelligence.isolation import isolated_settlements, last_access_blocked
from aashray.intelligence.routes import score_routes_shapely
from aashray.intelligence.textsim import text_similarity
from aashray.intelligence.visibility import score_visibility


def test_tfidf_links_paraphrase_reports():
    sim = text_similarity(
        "Landslide on the hill road, rocks on the slope",
        "Road blocked by debris, cannot pass",
    )
    assert sim > 0.05


def test_bfs_isolates_hamlet_when_last_edge_blocked():
    assert isolated_settlements(set()) == []
    cut = isolated_settlements({"edge-14"})
    assert "Gahar hamlet" in cut
    assert last_access_blocked({"edge-14"}) is True


def test_incident_point_is_in_gahar():
    assert settlement_containing(32.2395, 77.1880) == "Gahar hamlet"
    assert settlement_containing(32.2462, 77.1914) == "Tehsil town"


def test_shapely_geofence_is_not_a_full_disk():
    zones = geofence_zones(32.2395, 77.1880)
    levels = {z["level"] for z in zones}
    assert {"critical", "warning", "nearby"} <= levels
    crit = next(z for z in zones if z["level"] == "critical")
    geom = crit["geometry"]
    if geom["type"] == "Polygon":
        coords = geom["coordinates"][0]
    else:
        coords = geom["coordinates"][0][0]
    lons = [c[0] for c in coords]
    assert max(lons) - min(lons) < 0.02


def test_shapely_rejects_fast_route():
    routes = {r["id"]: r for r in score_routes_shapely(set())}
    assert routes["fast"]["status"] == "rejected"
    assert routes["fast"]["method"] == "shapely_intersection"
    assert any(r["status"] == "safest_available" for r in routes.values())


def test_visibility_grid_marks_unchecked_hamlet():
    users = [
        (32.2462, 77.1914, True),
        (32.2390, 77.1875, False),
        (32.2388, 77.1873, False),
    ]
    feats = score_visibility(users, hazard_nearby=True)
    assert len(feats) == 16
    hamlet_cells = [f for f in feats if f["properties"]["expected_scenario_users"] and f["properties"]["visibility"] < 1]
    assert hamlet_cells
    assert any(f["properties"]["copy"] for f in hamlet_cells)
