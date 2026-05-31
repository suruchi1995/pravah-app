# Pravah — AI-Native Supply Chain Planning Platform

Pravah is a cloud planning operating system for SMB/mid-market manufacturers.
It runs the full planning cycle on real, connected data — segmentation → forecasting →
demand planning → demand-supply handshake → inventory → netting → supply (MRP) →
capacity → OR-Tools optimization → control tower → AI copilot.

Demo tenant: **Apex Nutraceuticals** (nutraceutical manufacturing).

## Architecture

| Layer | Tech | Host |
| --- | --- | --- |
| Frontend | React + TypeScript + Vite + Tailwind + shadcn + AG Grid + Recharts | Netlify |
| Backend | FastAPI + Pydantic + SQLAlchemy + Alembic | Render |
| Engines | pandas, statsmodels, Google OR-Tools | (in backend) |
| Database | Postgres (`tenant_id` on every table) | Neon |
| AI | Anthropic API via backend proxy (key = server secret) | Render env |

**Data flow (fully connected, no hardcoding):**

```
scripts/generate_dataset.py  (reproducible, seed=42)
  -> /datasets/*.csv
  -> loaded into Postgres (tenant-scoped)
  -> planning engines read from DB, write results back to DB
  -> FastAPI serves results as JSON
  -> React renders live
  -> AI Copilot reads the SAME stored planning outputs
```

## Repo layout

```
backend/        FastAPI app, models, services
frontend/       React app
datasets/       Generated CSVs (the seed source of truth)
planning/       Planning engines (forecast, netting, inventory, capacity...)
optimization/   OR-Tools models
ai/             Copilot / RAG / explainability
infra/          Docker, Render, CI
tests/          Unit, integration, validation tests
docs/           Technical docs (mirrored to Notion)
scripts/        Data generation + utilities
```

## Build status

- [x] **BP1 — Foundation**: repo structure, synthetic Apex dataset generator, integrity suite (29/29 passing)
- [x] **BP2 — Engines**: Postgres-first schema + seed loader + 9 planning engines + OR-Tools optimizer; pipeline smoke test 16/16
- [x] **BP3 — API + Frontend**: data contract + strict validator (7/7), client Excel template, FastAPI (all engine endpoints + upload/validate/seed/run), full React app (10 screens, Vite/Tailwind/AG Grid/Recharts) — builds clean; API E2E 18/18
- [ ] BP4 — AI Copilot + Control Tower + deploy + Notion sync

### Test suites (70 checks total)
```
tests/test_dataset_integrity.py   29/29   dataset referential integrity
tests/test_pipeline.py            16/16   engine chain produces connected output
tests/test_validator.py            7/7    strict upload validation both directions
tests/test_api.py                 18/18   every endpoint + upload accept/reject
```

### Run the app locally
```bash
# backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
# frontend (separate terminal)
cd frontend && npm install && npm run dev   # proxies /api -> :8000
```

### Data architecture (client-upload driven)
Clients upload their own Excel (7 required sheets, 9 optional with documented defaults).
Flow: **upload → strict validate → seed DB → run pipeline → screens render**.
Synthetic Apex data is the default demo seed. See `backend/data_contract.py` and `backend/validator.py`.

## Reproduce BP1 locally

```bash
pip install -r requirements.txt
python3 scripts/generate_dataset.py      # writes /datasets/*.csv
python3 tests/test_dataset_integrity.py   # must print 29/29 passed
```

## Security

Secrets (Anthropic API key, GitHub/Neon/Render tokens) are **never** committed and
**never** shipped to the browser. They live only as environment variables on the
backend host. See `.env.example` for the variable names.
