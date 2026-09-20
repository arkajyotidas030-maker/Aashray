# AASHRAY

Student prototype for **VBYLD Hack for Social Cause** (Sept 2026).  
Situation awareness for **one hill-district landslide scenario** — not official NDMA/SDRF software.

Thesis: fuse citizen **evidence** into **incidents**, show GIS + rules (zones, isolation, safer-not-faster routes, explainable priority), and mark where the picture is **incomplete**. Unconfirmed check-ins are **not** missing persons. The demo still runs with the language model **down**.

## What is live vs simulated

| Layer | Label |
|---|---|
| Citizen SOS / check-in (this session) | **LIVE** |
| Demo-clock injected reports / blocked road | **SIMULATED** |
| Fused incident cluster | **FUSED** |
| Alert zones, isolation BFS, visibility grid, priority | **RULE** |
| Rainfall / slope risk polygon | **SIMULATED** (not IMD) |
| Hospital / shelter availability | **SIMULATED** |
| Candidate routes | **PRECOMPUTED** (Shapely vs hazard). Live OSRM is not wired |
| Sitrep | **RULE** text; **OPTIONAL LLM** only if `LLM_API_KEY` is set |
| Assign / dismiss | **SIMULATED** status on the incident row |
| SMS card | Copy-paste payload only — **no SMS sent** |
| Map tiles | Third-party basemap imagery, **not** a disaster feed |

## Run locally

Needs Python 3.12+ (3.14 works with wheels) and Node 20+.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\uvicorn aashray.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm install
npx vite --host 127.0.0.1 --port 5173
```

Open http://127.0.0.1:5173  

| Role | Email | Password |
|---|---|---|
| Citizen | `citizen@demo` | `demo` |
| Responder | `ops@demo` | `demo` |

Also: `hamlet.a@demo`, `hamlet.b@demo`, `town.b@demo` (same password).

API docs: http://127.0.0.1:8000/docs  
Health: http://127.0.0.1:8000/api/v1/health → `llm: down`, `routing: precomputed` with the default `.env`.

## Demo clock (Advance clock)

Same ingest path as live SOS (`source=simulated` for scripted rows). Empty ticks still increment the integer clock.

| Tick | What happens |
|---|---|
| 1 | SIMULATED rainfall index = 1 (risk polygon may appear) |
| 2 | Four scripted reports → one FUSED incident if they match |
| 5 | Town check-in (visibility) |
| 7 | Block `edge-14` → Gahar hamlet **isolation** (RULE / graph) |

`POST /api/v1/demo/play` only stores a `playing` flag; the UI uses **Advance clock** (`POST /demo/tick`).

## Tests

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q
```

```powershell
cd frontend
npx playwright install chromium
npm run test:e2e
```

## Repository layout

- `backend/aashray/` — FastAPI, SQLite, fusion, GIS/rules  
- `backend/aashray/scenario/` — packed graph, GeoJSON, `ticks.json`, route polylines  
- `frontend/src/` — citizen + ops (React, Leaflet)  
- `docs/ARCHITECTURE.md` — data flow as implemented  
- `docs/CLAIMS.md` — statements we will and will not make  
- `LICENSE` — MIT  

## Environment

See `backend/.env.example`. No third-party keys are required. Optional: `LLM_API_KEY` + `LLM_BASE_URL` (OpenAI-compatible) to enhance sitrep language only.
