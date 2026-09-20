from __future__ import annotations

import math
from typing import Any


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def point_in_ring(lat: float, lon: float, ring: list[list[float]]) -> bool:
    """Ray casting. ring vertices are [lon, lat] GeoJSON order."""
    inside = False
    n = len(ring)
    if n < 4:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        intersect = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-16) + xi
        )
        if intersect:
            inside = not inside
        j = i
    return inside


def _orient(ax: float, ay: float, bx: float, by: float, cx: float, cy: float) -> float:
    return (by - ay) * (cx - bx) - (bx - ax) * (cy - by)


def _on_seg(ax: float, ay: float, bx: float, by: float, cx: float, cy: float) -> bool:
    return min(ax, bx) - 1e-12 <= cx <= max(ax, bx) + 1e-12 and min(ay, by) - 1e-12 <= cy <= max(
        ay, by
    ) + 1e-12


def segments_intersect(a: list[float], b: list[float], c: list[float], d: list[float]) -> bool:
    o1 = _orient(a[0], a[1], b[0], b[1], c[0], c[1])
    o2 = _orient(a[0], a[1], b[0], b[1], d[0], d[1])
    o3 = _orient(c[0], c[1], d[0], d[1], a[0], a[1])
    o4 = _orient(c[0], c[1], d[0], d[1], b[0], b[1])
    if o1 == 0 and _on_seg(a[0], a[1], b[0], b[1], c[0], c[1]):
        return True
    if o2 == 0 and _on_seg(a[0], a[1], b[0], b[1], d[0], d[1]):
        return True
    if o3 == 0 and _on_seg(c[0], c[1], d[0], d[1], a[0], a[1]):
        return True
    if o4 == 0 and _on_seg(c[0], c[1], d[0], d[1], b[0], b[1]):
        return True
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def line_hits_polygon(line: list[list[float]], ring: list[list[float]]) -> bool:
    for lon, lat in line:
        if point_in_ring(lat, lon, ring):
            return True
    for i in range(len(line) - 1):
        for j in range(len(ring) - 1):
            if segments_intersect(line[i], line[i + 1], ring[j], ring[j + 1]):
                return True
    return False


def feature(geometry: dict[str, Any], properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "Feature", "geometry": geometry, "properties": properties}
