# Pravah — Deployment Guide

This repo deploys as three pieces: **Postgres on Neon**, **backend on Render**, **frontend on Netlify**.
Secrets (DB URL, Anthropic key) live ONLY as env vars in the host dashboards — never in Git.

## 0. Push to GitHub
```bash
cd pravah
git init && git add . && git commit -m "Pravah BP1-BP3: data, engines, API, frontend"
git branch -M main
git remote add origin https://github.com/suruchi1995/pravah-app.git
git push -u origin main        # use your fine-grained token as the password
```
The `.gitignore` already excludes `.env`, `node_modules`, `pravah.db`, build output.

## 1. Database — Neon (free)
1. Create a project at neon.tech → copy the connection string
   (`postgresql://user:pass@host/dbname?sslmode=require`).
2. You'll paste it into Render as `DATABASE_URL` (step 2). No code change — the app is
   Postgres-ready; it falls back to SQLite only when `DATABASE_URL` is unset.
3. First boot auto-creates tables and (for tenant `apex`) seeds synthetic data + runs the pipeline.

## 2. Backend — Render (free)
1. New → **Blueprint**, point at this repo. Render reads `render.yaml`.
2. In the service's **Environment**, set (sync:false means you set them here, not in Git):
   - `DATABASE_URL` = your Neon string
   - `ANTHROPIC_API_KEY` = your key (only needed once the Copilot ships in BP4)
3. Deploy. Health check: `https://<your-service>.onrender.com/api/health` → `{"status":"ok"}`.

## 3. Frontend — Netlify
1. In `netlify.toml`, replace `REPLACE_WITH_RENDER_URL` with your Render host
   (e.g. `pravah-api.onrender.com`).
2. New site from Git → pick this repo. Netlify reads `netlify.toml` (base `frontend`,
   build `npm run build`, publish `frontend/dist`), and proxies `/api/*` to Render.
3. Open the Netlify URL — the app loads, pre-seeded with Apex.

## 4. CI
`.github/workflows/ci.yml` runs all four test suites + the frontend build on every push.

## Local development
```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
cd frontend && npm install && npm run dev   # http://localhost:5173, proxies /api
```

## Security checklist
- [ ] No `.env`, key, or token committed (check `git log -p` before first push)
- [ ] Anthropic key set only in Render env, never in frontend
- [ ] GitHub token is fine-grained, scoped to `pravah-app`, short expiry
