from __future__ import annotations

from shapely.geometry import box, mapping

from aashray.intelligence.gis import point_in_poly

# Demo bbox. Denominator = seeded scenario users whose last pin falls in the cell.
WEST, SOUTH, EAST, NORTH = 77.1830, 32.2360, 77.1950, 32.2480
NX, NY = 4, 4


def grid_cells() -> list[dict]:
    dx = (EAST - WEST) / NX
    dy = (NORTH - SOUTH) / NY
    cells: list[dict] = []
    n = 0
    for iy in range(NY):
        for ix in range(NX):
            minx = WEST + ix * dx
            miny = SOUTH + iy * dy
            poly = box(minx, miny, minx + dx, miny + dy)
            cells.append({"id": f"cell-{n}", "poly": poly, "geometry": mapping(poly)})
            n += 1
    return cells


def score_visibility(
    users: list[tuple[float, float, bool]],
    *,
    hazard_nearby: bool,
) -> list[dict]:
    """users: (lat, lon, has_checkin). Unconfirmed ≠ missing."""
    cells = grid_cells()
    features: list[dict] = []
    for cell in cells:
        expected = 0
        checked = 0
        for lat, lon, ok in users:
            if point_in_poly(lat, lon, cell["poly"]):
                expected += 1
                if ok:
                    checked += 1
        if expected == 0:
            vis = 0.0
        else:
            vis = checked / expected
        copy = "Safety status uncertain — information-gathering recommended." if (
            vis < 0.5 and hazard_nearby and expected > 0
        ) else None
        features.append(
            {
                "type": "Feature",
                "geometry": cell["geometry"],
                "properties": {
                    "cell_id": cell["id"],
                    "visibility": round(vis, 3),
                    "expected_scenario_users": expected,
                    "checked_in": checked,
                    "unconfirmed_safety_status": max(0, expected - checked),
                    "copy": copy,
                    "source": "rule",
                    "note": "unconfirmed_safety_status is not a missing-person count",
                },
            }
        )
    return features
