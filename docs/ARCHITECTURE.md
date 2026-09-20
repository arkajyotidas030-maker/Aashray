# Architecture (as implemented)

One **FastAPI** process, one **SQLite** file, two **React** surfaces. Polling (~2s), not WebSockets. No Kafka, PostGIS, Firebase, or Kubernetes.

```
Citizen / Ops SPA  --JSON-->  FastAPI /api/v1
                               | persist evidence/check-ins
                               | fuse (geo/time/category/TF-IDF)
                               | decision: zones, isolation, routes, priority
                               v
                             SQLite + scenario pack (GeoJSON/JSON)
```

## Ingest

`POST /evidence` (rate-limited) writes an **evidence** row, then `fuse_and_decide` in-process. Citizens receive `201` with an incident code immediately. Fusion score:

`0.40·geo + 0.25·time + 0.20·category + 0.15·text_sim` — attach if ≥ 0.65.

Provenance on rows: `live` | `simulated` (demo clock).

## Decision (RULE)

- **Corroboration:** Critical zone only if ≥2 members **or** SOS + rainfall_index ≥ 1.  
- **Zones:** Shapely buffer clipped to `valley_mask.geojson` (not a circle).  
- **Isolation:** networkx BFS; blocking `edge-14` isolates Gahar hamlet.  
- **Routes:** packed polylines scored with line∩hazard (**PRECOMPUTED**).  
- **Priority:** visible weights on ops (severity, people, check-ins, recency, distance, isolation multiplier).  
- **Resources:** nearest POI by type; availability **SIMULATED**.  
- **Sitrep:** `compose_sitrep()` from structured fields; LLM may replace wording if configured.

## Snapshot

`GET /ops/snapshot` — full ops document (incidents, locker evidence, layers, priority, visibility, sitrep).  
`GET /citizen/snapshot` — own zone, own check-in, safest/rejected routes, shelters. No other citizens’ SOS or photos.

Every GeoJSON layer has `provenance.source` + `as_of`.

## Auth

PyJWT + bcrypt. Roles `citizen` | `responder`. Photos: `GET /media/{id}` responder-only.

## What is not in the process

No live IMD, no NDMA SMS, no OSRM HTTP client, no vision model, no offline IndexedDB SOS queue (PWA manifest only).
