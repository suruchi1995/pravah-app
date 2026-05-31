"""
Pravah FastAPI backend.

Endpoints
  GET  /api/health
  GET  /api/template                      -> download client Excel template
  POST /api/upload?tenant=...             -> validate + (if ok) seed + run pipeline
  POST /api/reset-demo?tenant=...         -> reseed synthetic Apex + run pipeline
  GET  /api/summary?tenant=...            -> KPI cards for dashboard
  GET  /api/segmentation?tenant=...
  GET  /api/forecast?tenant=...&item=...&location=...
  GET  /api/handshake?tenant=...
  GET  /api/inventory-targets?tenant=...
  GET  /api/netting?tenant=...&item=...
  GET  /api/mrp?tenant=...
  GET  /api/capacity?tenant=...
  GET  /api/optimizer?tenant=...          -> 3 scenarios + production plans + explanations
  GET  /api/master/{table}?tenant=...     -> raw master/transaction tables for Data Hub
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend import models as m
from backend.config import DATABASE_URL, DEFAULT_TENANT
from backend.validator import validate
from backend.defaults import apply_defaults
from backend.seed_loader import load as seed_synthetic
from planning.run_all import run_pipeline
from optimization import production_optimizer
from ai import copilot
from pydantic import BaseModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(ROOT, "Pravah_Client_Template.xlsx")

engine = m.make_engine(DATABASE_URL)
m.init_db(engine)
Session = m.make_session_factory(engine)

app = FastAPI(title="Pravah API", version="0.3")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _ensure_seeded(tenant):
    """Self-healing: if a tenant has no items, seed synthetic Apex + run pipeline.
    If items exist but planning outputs are missing/incomplete (e.g. a partial
    earlier run), re-run the pipeline so every screen has data."""
    with Session() as s:
        n_items = s.query(m.Item).filter_by(tenant_id=tenant).count()
        if n_items == 0:
            if tenant == DEFAULT_TENANT:
                seed_synthetic(s)
                run_pipeline(s, tenant)
            return
        # items exist — ensure planning outputs are present
        n_scenarios = s.query(m.SolverExplanation).filter_by(tenant_id=tenant).count()
        n_forecast = s.query(m.ForecastOutput).filter_by(tenant_id=tenant).count()
        if n_scenarios == 0 or n_forecast == 0:
            run_pipeline(s, tenant)


@app.get("/api/health")
def health():
    return {"status": "ok", "db": DATABASE_URL.split("://")[0]}


@app.get("/api/template")
def template():
    if not os.path.exists(TEMPLATE_PATH):
        raise HTTPException(404, "Template not generated yet.")
    return FileResponse(TEMPLATE_PATH, filename="Pravah_Client_Template.xlsx")


@app.post("/api/upload")
async def upload(file: UploadFile = File(...), tenant: str = Query(DEFAULT_TENANT)):
    content = await file.read()
    try:
        xls = pd.read_excel(io.BytesIO(content), sheet_name=None, dtype=object)
    except Exception as e:
        raise HTTPException(400, f"Could not read Excel file: {e}")
    # drop README + bookkeeping cols
    sheets = {k: v for k, v in xls.items() if k.lower() != "readme"}
    for k in sheets:
        sheets[k] = sheets[k].drop(
            columns=[c for c in ["tenant_id", "created_at", "updated_at"] if c in sheets[k].columns])

    result = validate(sheets)
    if not result["ok"]:
        return {"ok": False, "errors": result["errors"], "warnings": result["warnings"],
                "summary": result["summary"]}

    # convert to dict-of-dicts, apply defaults, seed, run
    tables = {name: df.where(pd.notna(df), None).to_dict("records") for name, df in sheets.items()}
    tables = apply_defaults(tables)
    with Session() as s:
        _seed_from_tables(s, tables, tenant)
        run_pipeline(s, tenant)
    return {"ok": True, "warnings": result["warnings"], "summary": result["summary"],
            "message": "Upload validated, loaded, and planned."}


def _seed_from_tables(session, tables, tenant):
    """Load validated client tables into the DB (replacing this tenant's source rows)."""
    from backend.seed_loader import LOADERS
    model_by_file = {f[:-4]: (model, mapping) for f, model, mapping in
                     [(f, mod, mp) for f, mod, mp in LOADERS]}
    for sheet, rows in tables.items():
        if sheet not in model_by_file:
            continue
        model, mapping = model_by_file[sheet]
        session.query(model).filter(model.tenant_id == tenant).delete()
        objs = []
        for r in rows:
            kwargs = {"tenant_id": tenant}
            for col, (attr, caster) in mapping.items():
                kwargs[attr] = caster(r.get(col, ""))
            objs.append(model(**kwargs))
        session.bulk_save_objects(objs)
    session.commit()


@app.post("/api/reset-demo")
def reset_demo(tenant: str = Query(DEFAULT_TENANT)):
    with Session() as s:
        seed_synthetic(s)
        res = run_pipeline(s, tenant)
    return {"ok": True, "pipeline": res}


# ---------------- read endpoints ----------------
def rows_to_dicts(rows, fields):
    return [{f: getattr(r, f) for f in fields} for r in rows]


@app.get("/api/summary")
def summary(tenant: str = Query(DEFAULT_TENANT)):
    _ensure_seeded(tenant)
    with Session() as s:
        n_fg = s.query(m.Item).filter_by(tenant_id=tenant, item_type="FG").count()
        hs = s.query(m.DemandSupplyHandshake).filter_by(tenant_id=tenant).all()
        rev_risk = sum(r.revenue_at_risk for r in hs)
        avg_fill = sum(r.fill_rate for r in hs) / len(hs) if hs else 0
        fc = s.query(m.ForecastOutput).filter_by(tenant_id=tenant).all()
        avg_mape = sum(r.mape for r in fc) / len(fc) if fc else 0
        caps = s.query(m.CapacityLoad).filter_by(tenant_id=tenant).all()
        bottlenecks = len({c.resource_code for c in caps if c.constraint_status in ("TIGHT", "OVERLOADED")})
        expl = s.query(m.SolverExplanation).filter_by(tenant_id=tenant).all()
        scen = {e.scenario: {"status": e.status, "objective_value": e.objective_value} for e in expl}
        return {
            "finished_goods": n_fg,
            "total_revenue_at_risk": round(rev_risk, 2),
            "avg_fill_rate": round(avg_fill, 4),
            "avg_mape": round(avg_mape, 2),
            "capacity_bottlenecks": bottlenecks,
            "scenarios": scen,
        }


@app.get("/api/segmentation")
def segmentation(tenant: str = Query(DEFAULT_TENANT)):
    _ensure_seeded(tenant)
    with Session() as s:
        rows = s.query(m.ProductSegmentation).filter_by(tenant_id=tenant).all()
        return rows_to_dicts(rows, ["item_code", "abc_class", "xyz_class", "abc_xyz",
                                    "annual_value", "cov", "reasoning"])


@app.get("/api/forecast")
def forecast(tenant: str = Query(DEFAULT_TENANT), item: str = None, location: str = None):
    _ensure_seeded(tenant)
    with Session() as s:
        q = s.query(m.ForecastOutput).filter_by(tenant_id=tenant)
        if item: q = q.filter_by(item_code=item)
        if location: q = q.filter_by(location_code=location)
        rows = q.order_by(m.ForecastOutput.item_code, m.ForecastOutput.location_code,
                          m.ForecastOutput.period).all()
        return rows_to_dicts(rows, ["item_code", "location_code", "period", "forecast_qty",
                                    "selected_model", "mape", "bias", "reasoning"])


@app.get("/api/handshake")
def handshake(tenant: str = Query(DEFAULT_TENANT)):
    _ensure_seeded(tenant)
    with Session() as s:
        rows = s.query(m.DemandSupplyHandshake).filter_by(tenant_id=tenant).order_by(
            m.DemandSupplyHandshake.revenue_at_risk.desc()).all()
        return rows_to_dicts(rows, ["item_code", "location_code", "period", "demand_qty",
                                    "available_supply_qty", "gap_qty", "fill_rate",
                                    "revenue_at_risk", "margin_at_risk", "recommendation"])


@app.get("/api/inventory-targets")
def inventory_targets(tenant: str = Query(DEFAULT_TENANT)):
    _ensure_seeded(tenant)
    with Session() as s:
        rows = s.query(m.InventoryTarget).filter_by(tenant_id=tenant).all()
        return rows_to_dicts(rows, ["item_code", "location_code", "avg_monthly_demand",
                                    "safety_stock", "reorder_point", "target_inventory",
                                    "days_cover", "reasoning"])


@app.get("/api/netting")
def netting(tenant: str = Query(DEFAULT_TENANT), item: str = None):
    _ensure_seeded(tenant)
    with Session() as s:
        q = s.query(m.NetRequirement).filter_by(tenant_id=tenant)
        if item: q = q.filter_by(item_code=item)
        rows = q.order_by(m.NetRequirement.item_code, m.NetRequirement.period).all()
        return rows_to_dicts(rows, ["item_code", "period", "gross_requirement", "safety_stock",
                                    "on_hand", "scheduled_receipts", "net_requirement",
                                    "planned_order", "reasoning"])


@app.get("/api/mrp")
def mrp(tenant: str = Query(DEFAULT_TENANT)):
    _ensure_seeded(tenant)
    with Session() as s:
        rows = s.query(m.SupplyRequirement).filter_by(tenant_id=tenant).order_by(
            m.SupplyRequirement.level, m.SupplyRequirement.item_code, m.SupplyRequirement.period).all()
        return rows_to_dicts(rows, ["item_code", "period", "level", "gross_requirement",
                                    "net_requirement", "source"])


@app.get("/api/capacity")
def capacity(tenant: str = Query(DEFAULT_TENANT)):
    _ensure_seeded(tenant)
    with Session() as s:
        rows = s.query(m.CapacityLoad).filter_by(tenant_id=tenant).order_by(
            m.CapacityLoad.period, m.CapacityLoad.resource_code).all()
        return rows_to_dicts(rows, ["resource_code", "period", "load_hours", "available_hours",
                                    "utilization", "constraint_status"])


@app.get("/api/optimizer")
def optimizer(tenant: str = Query(DEFAULT_TENANT)):
    _ensure_seeded(tenant)
    with Session() as s:
        expl = s.query(m.SolverExplanation).filter_by(tenant_id=tenant).all()
        plans = s.query(m.ProductionPlan).filter_by(tenant_id=tenant).all()
        by_scenario = {}
        for e in expl:
            by_scenario[e.scenario] = {
                "objective": e.objective, "objective_value": e.objective_value,
                "status": e.status, "reasoning": e.reasoning, "plan": []}
        for p in plans:
            if p.scenario in by_scenario:
                by_scenario[p.scenario]["plan"].append(
                    {"item_code": p.item_code, "period": p.period, "quantity": p.quantity})
        return by_scenario


@app.get("/api/master/{table}")
def master(table: str, tenant: str = Query(DEFAULT_TENANT)):
    _ensure_seeded(tenant)
    table_map = {
        "items": (m.Item, ["item_code", "description", "item_type", "category", "uom", "unit_price_or_cost"]),
        "locations": (m.Location, ["location_code", "location_name", "location_type", "state", "zone"]),
        "suppliers": (m.Supplier, ["supplier_code", "supplier_name", "supplier_type", "lead_time_days", "moq", "reliability"]),
        "resources": (m.Resource, ["resource_code", "resource_name", "plant_code", "hours_per_month"]),
        "bom": (m.Bom, ["parent_item", "component_item", "usage_qty"]),
        "inventory": (m.Inventory, ["item_code", "location_code", "on_hand_qty"]),
        "demand_history": (m.DemandHistory, ["item_code", "location_code", "period", "quantity"]),
    }
    if table not in table_map:
        raise HTTPException(404, f"Unknown table '{table}'.")
    model, fields = table_map[table]
    with Session() as s:
        rows = s.query(model).filter_by(tenant_id=tenant).all()
        return rows_to_dicts(rows, fields)


class CopilotQuery(BaseModel):
    question: str
    tenant: str = DEFAULT_TENANT


@app.post("/api/copilot")
def copilot_ask(q: CopilotQuery):
    _ensure_seeded(q.tenant)
    with Session() as s:
        return copilot.ask(s, q.question, q.tenant)
