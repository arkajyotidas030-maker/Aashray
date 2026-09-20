from __future__ import annotations

from shapely.geometry import LineString, Point, Polygon, mapping, shape

from aashray.intelligence.data import load_fc
from aashray.services.scenario import load_pack

# ~500 m / ~1500 m / ~3500 m in degrees at this latitude (geometric, not hydrology)
BUF_CRITICAL = 0.0016
BUF_WARNING = 0.0035
BUF_NEARBY = 0.008


def valley_mask() -> Polygon:
    feat = load_fc("valley_mask.geojson")["features"][0]
    return shape(feat["geometry"])


def ring_polygon(coords: list[list[float]]) -> Polygon:
    return Polygon(coords)


def point_in_poly(lat: float, lon: float, poly: Polygon) -> bool:
    return poly.contains(Point(lon, lat)) or poly.touches(Point(lon, lat))


def line_hits(line_coords: list[list[float]], poly: Polygon) -> bool:
    if poly.is_empty or len(line_coords) < 2:
        return False
    return LineString(line_coords).intersects(poly)


def hazard_polygon() -> Polygon:
    pack = load_pack()
    return Polygon(pack["hazard"]["coordinates"])


def settlement_containing(lat: float, lon: float) -> str | None:
    for feat in load_fc("settlements.geojson")["features"]:
        poly = shape(feat["geometry"])
        if point_in_poly(lat, lon, poly):
            return feat["properties"]["name"]
    return None


def geofence_zones(lat: float, lon: float) -> list[dict]:
    """Buffer incident point, clip to valley mask so Critical is not a circle."""
    origin = Point(lon, lat)
    mask = valley_mask()
    specs = [
        ("critical", BUF_CRITICAL),
        ("warning", BUF_WARNING),
        ("nearby", BUF_NEARBY),
    ]
    out: list[dict] = []
    for level, buf in specs:
        geom = origin.buffer(buf).intersection(mask)
        if geom.is_empty:
            continue
        gj = mapping(geom)
        out.append(
            {
                "level": level,
                "geometry": gj,
                "source": "rule",
                "method": "shapely_buffer_clip_valley",
            }
        )
    return out


def zone_level_for(lat: float, lon: float, zones: list[dict], allow_critical: bool) -> str | None:
    rank = {"critical": 3, "warning": 2, "nearby": 1}
    best, best_r = None, 0
    pt = Point(lon, lat)
    for z in zones:
        geom = shape(z["geometry"])
        if geom.contains(pt) or geom.touches(pt):
            r = rank.get(z["level"], 0)
            if r > best_r:
                best, best_r = z["level"], r
    if best == "critical" and not allow_critical:
        return zone_level_for(lat, lon, [z for z in zones if z["level"] != "critical"], True)
    return best
