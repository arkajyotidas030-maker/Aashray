from __future__ import annotations

from shapely.geometry import LineString

from aashray.intelligence.gis import hazard_polygon
from aashray.services.scenario import load_pack


def score_routes_shapely(blocked_edge_ids: set[str]) -> list[dict]:
    pack = load_pack()
    hazard = hazard_polygon()
    roads = {r["edge_id"]: r["coordinates"] for r in pack.get("roads", [])}

    scored: list[dict] = []
    for route in pack.get("routes", []):
        line = LineString(route["coordinates"])
        status = "safest_available"
        reason = None
        if line.intersects(hazard):
            status = "rejected"
            reason = "crosses debris/hazard polygon"
        else:
            for eid in blocked_edge_ids:
                coords = roads.get(eid)
                if not coords or len(coords) < 2:
                    continue
                if line.intersects(LineString(coords)):
                    status = "rejected"
                    reason = f"blocked edge {eid}"
                    break
        scored.append(
            {
                "id": route["id"],
                "label": route["label"],
                "duration_min": route["duration_min"],
                "status": status,
                "reason": reason,
                "coordinates": route["coordinates"],
                "source": "precomputed",
                "method": "shapely_intersection",
            }
        )

    available = [r for r in scored if r["status"] != "rejected"]
    if available:
        best = min(available, key=lambda r: r["duration_min"])
        for r in scored:
            if r["status"] == "rejected":
                continue
            r["status"] = "safest_available" if r["id"] == best["id"] else "alternate"
    return scored
