# Running Pravah locally

## Backend (FastAPI + engines + OR-Tools)
```bash
pip install -r requirements.txt
python3 scripts/generate_dataset.py        # writes /datasets/*.csv (seed=42)
python3 scripts/make_template.py            # writes client Excel template
uvicorn backend.main:app --port 8000        # API at http://localhost:8000
# first request auto-seeds Apex + runs the full pipeline
```

## Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev                                 # http://localhost:5173 (proxies /api -> :8000)
```

## Tests
```bash
python3 tests/test_dataset_integrity.py     # 29/29
python3 tests/test_pipeline.py              # 16/16
python3 tests/test_validator.py             # 7/7
```

## Client upload flow
1. Data Hub → download Template → fill the GREEN required sheets.
2. Upload → strict validation. If rejected, every error names sheet/row/problem.
3. If accepted, the pipeline re-runs and all screens reflect the new data.
4. Reset demo restores synthetic Apex data.

## Deploy targets (BP4)
- Backend → Render (set DATABASE_URL to Neon Postgres, ANTHROPIC_API_KEY as secret)
- Frontend → Netlify (set VITE proxy / API base to the Render URL)
