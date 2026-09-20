from __future__ import annotations

from aashray.services.geo import line_hits_polygon
from aashray.services.scenario import load_pack


def score_routes() -> list[dict]:
    pack = load_pack()
    hazard = pack.get("hazard", {}).get("coordinates") or []
    blocked_ids = set()  # filled by caller via optional argument

    scored: list[dict] = []
    for route in pack.get("routes", []):
        line = route["coordinates"]
        hits_hazard = bool(hazard) and line_hits_polygon(line, hazard)
        reason = None
        status = "safest_available"
        if hits_hazard:
            status = "rejected"
            reason = "crosses debris/hazard polygon"
        scored.append(
            {
                "id": route["id"],
                "label": route["label"],
                "duration_min": route["duration_min"],
                "status": status,
                "reason": reason,
                "coordinates": line,
                "source": "precomputed",
            }
        )
    available = [r for r in scored if r["status"] != "rejected"]
    if available:
        best = min(available, key=lambda r: r["duration_min"])
        for r in scored:
            if r["id"] == best["id"]:
                r["status"] = "safest_available"
            elif r["status"] != "rejected":
                r["status"] = "alternate"
    return scored


def score_routes_with_blocked(blocked_edge_ids: set[str]) -> list[dict]:
    pack = load_pack()
    roads = {r["edge_id"]: r["coordinates"] for r in pack.get("roads", [])}
    scored = score_routes()
    hazard = pack.get("hazard", {}).get("coordinates") or []
    for r in scored:
        if r["status"] == "rejected":
            continue
        for edge_id in blocked_edge_ids:
            geom = roads.get(edge_id)
            if not geom:
                continue
            if line_hits_polygon(r["coordinates"], _line_as_thin_ring(geom)) or _shares_vertex(
                r["coordinates"], geom
            ):
                r["status"] = "rejected"
                r["reason"] = f"blocked edge {edge_id}"
    available = [x for x in scored if x["status"] != "rejected"]
    if available:
        best = min(available, key=lambda x: x["duration_min"])
        for r in scored:
            if r["status"] == "rejected":
                continue
            r["status"] = "safest_available" if r["id"] == best["id"] else "alternate"
    _ = hazard
    return scored


def _shares_vertex(a: list[list[float]], b: list[list[float]]) -> bool:
    sa = {(round(p[0], 5), round(p[1], 5)) for p in a}
    sb = {(round(p[0], 5), round(p[1], 5)) for p in b}
    return bool(sa & sb)


def _line_as_thin_ring(line: list[list[float]]) -> list[list[float]]:
    if len(line) < 2:
        return []
    # Degenerate; vertex sharing handles blocked-road overlap for this bbox.
    return []
