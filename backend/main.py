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
from backend import auth as authmod
from pydantic import BaseModel
from fastapi import Depends, Header

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(ROOT, "Pravah_Client_Template.xlsx")

engine = m.make_engine(DATABASE_URL)
m.init_db(engine)
from backend.migrate import reconcile_schema
reconcile_schema(engine)   # add any columns missing from pre-existing tables (prevents 500s on deploy)
Session = m.make_session_factory(engine)

# bootstrap admin + tenant so the app is never locked out (same tenant as the demo data)
with Session() as _s:
    authmod.seed_admin(_s, tenant_id=DEFAULT_TENANT,
                       email="admin@pravah.app", password="changeme123", name="Admin")

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


# ---------------- auth ----------------
def current_user(authorization: str = Header(None)):
    """Resolve the logged-in user from the Bearer token. Returns the JWT payload
    dict (sub, tenant, roles, name) or raises 401."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Not authenticated")
    token = authorization.split(" ", 1)[1]
    payload = authmod.verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    return payload


def require_roles(*allowed):
    def dep(user=Depends(current_user)):
        if not (set(user.get("roles", [])) & set(allowed)):
            raise HTTPException(403, f"Requires one of roles: {allowed}")
        return user
    return dep


class LoginBody(BaseModel):
    email: str
    password: str


@app.post("/api/login")
def login(body: LoginBody):
    with Session() as s:
        u = authmod.authenticate(s, body.email, body.password)
        if not u:
            raise HTTPException(401, "Invalid email or password")
        s.add(m.AuditLog(tenant_id=u.tenant_id, user_email=u.email, action="login", detail=""))
        s.commit()
        return {"token": authmod.make_token(u),
                "user": {"email": u.email, "name": u.full_name, "roles": u.roles, "tenant": u.tenant_id}}


@app.get("/api/me")
def me(user=Depends(current_user)):
    return user


class NewUserBody(BaseModel):
    email: str
    password: str
    full_name: str
    roles: list[str]
    tenant: str = None


@app.get("/api/users")
def list_users(user=Depends(require_roles("admin"))):
    with Session() as s:
        rows = s.query(m.User).filter_by(tenant_id=user["tenant"]).all()
        return [{"email": u.email, "full_name": u.full_name, "roles": u.roles,
                 "is_active": u.is_active, "tenant": u.tenant_id} for u in rows]


@app.post("/api/users")
def create_user(body: NewUserBody, user=Depends(require_roles("admin"))):
    tenant = body.tenant or user["tenant"]
    with Session() as s:
        if s.query(m.User).filter_by(email=body.email.lower().strip()).first():
            raise HTTPException(400, "A user with that email already exists.")
        s.add(m.User(tenant_id=tenant, email=body.email.lower().strip(),
                     password_hash=authmod.hash_password(body.password),
                     full_name=body.full_name, roles_csv=",".join(body.roles), is_active=True))
        s.add(m.AuditLog(tenant_id=user["tenant"], user_email=user["sub"],
                         action="create_user", detail=f"{body.email} roles={body.roles}"))
        s.commit()
        return {"ok": True, "email": body.email}


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


import threading

# tracks long-running jobs per tenant: 'running' | 'done' | 'error: ...'
_JOB_STATUS = {}

def _run_reset(tenant):
    try:
        with Session() as s:
            seed_synthetic(s)
            run_pipeline(s, tenant)
        _JOB_STATUS[tenant] = "done"
    except Exception as e:
        _JOB_STATUS[tenant] = f"error: {type(e).__name__}: {str(e)[:200]}"


@app.post("/api/reset-demo")
def reset_demo(tenant: str = Query(DEFAULT_TENANT)):
    # kick off the heavy reseed+pipeline in the background and return immediately,
    # so the request never times out on free-tier hardware.
    if _JOB_STATUS.get(tenant) == "running":
        return {"ok": True, "status": "running", "message": "A reset is already in progress."}
    _JOB_STATUS[tenant] = "running"
    threading.Thread(target=_run_reset, args=(tenant,), daemon=True).start()
    return {"ok": True, "status": "running",
            "message": "Reset started. This rebuilds all plans and the optimizer — about 30-90s. Refresh the screens shortly."}


@app.get("/api/reset-status")
def reset_status(tenant: str = Query(DEFAULT_TENANT)):
    return {"tenant": tenant, "status": _JOB_STATUS.get(tenant, "idle")}


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
        "items": (m.Item, ["item_code", "description", "item_type", "category", "uom",
                           "unit_price_or_cost"]),
        "items_fg": None,   # special filtered views
        "items_rm": None,
        "items_pm": None,
        "items_sfg": None,
        "locations": (m.Location, ["location_code", "location_name", "location_type",
                                   "state", "zone"]),
        "suppliers": (m.Supplier, ["supplier_code", "supplier_name", "supplier_type",
                                   "lead_time_days", "moq", "reliability"]),
        "resources": (m.Resource, ["resource_code", "resource_name", "plant_code",
                                   "hours_per_month"]),
        "bom": (m.Bom, ["parent_item", "component_item", "usage_qty"]),
        "inventory": (m.Inventory, ["item_code", "location_code", "on_hand_qty"]),
        "demand_history": (m.DemandHistory, ["item_code", "location_code", "period",
                                             "quantity"]),
        "supplier_item_mapping": (m.SupplierItemMapping, ["supplier_code", "item_code",
                                                          "unit_price", "moq",
                                                          "lead_time_days"]),
        "supply_lanes": (m.SupplyLane, ["lane_code", "from_location", "to_location",
                                        "item_code", "transport_mode", "lead_time_days",
                                        "min_lot_size", "min_lot_uom"]),
    }
    if table not in table_map:
        raise HTTPException(404, f"Unknown table '{table}'.")

    # Special filtered item views
    if table.startswith("items_"):
        type_map = {"items_fg": "FG", "items_rm": "RM", "items_pm": "PM", "items_sfg": "SFG"}
        itype = type_map[table]
        with Session() as s:
            rows = s.query(m.Item).filter_by(tenant_id=tenant, item_type=itype).all()
            return rows_to_dicts(rows, ["item_code", "description", "item_type",
                                        "category", "uom", "unit_price_or_cost"])

    model, fields = table_map[table]
    with Session() as s:
        rows = s.query(model).filter_by(tenant_id=tenant).all()
        return rows_to_dicts(rows, fields)


@app.get("/api/capabilities")
def capabilities(tenant: str = Query(DEFAULT_TENANT)):
    _ensure_seeded(tenant)
    from backend import capabilities as cap
    with Session() as s:
        return cap.compute(s, tenant)


class CopilotQuery(BaseModel):
    question: str
    tenant: str = DEFAULT_TENANT


# ---------------- parameters (view; edits go through approval) ----------------
@app.get("/api/parameters")
def get_parameters(user=Depends(current_user)):
    from backend.parameters import list_parameters
    with Session() as s:
        return list_parameters(s, user["tenant"])


# ---------------- change requests (approval workflow) ----------------
import json as _json
from datetime import datetime as _dt


class ChangeBody(BaseModel):
    change_type: str            # "parameter" | "demand_override"
    target: str                 # human-readable
    payload: dict               # the proposed change
    old_value: str = ""
    new_value: str = ""


@app.post("/api/change-requests")
def submit_change(body: ChangeBody, user=Depends(require_roles("planner", "admin"))):
    with Session() as s:
        cr = m.ChangeRequest(
            tenant_id=user["tenant"], requested_by=user["sub"], change_type=body.change_type,
            target=body.target, payload_json=_json.dumps(body.payload),
            old_value=body.old_value, new_value=body.new_value, status="submitted")
        s.add(cr)
        s.add(m.AuditLog(tenant_id=user["tenant"], user_email=user["sub"],
                         action="submit_change", detail=f"{body.change_type}: {body.target}"))
        s.commit()
        return {"ok": True, "id": cr.id, "status": "submitted"}


@app.get("/api/change-requests")
def list_changes(status: str = None, user=Depends(current_user)):
    with Session() as s:
        q = s.query(m.ChangeRequest).filter_by(tenant_id=user["tenant"])
        if status:
            q = q.filter_by(status=status)
        rows = q.order_by(m.ChangeRequest.id.desc()).all()
        return [{"id": c.id, "requested_by": c.requested_by, "change_type": c.change_type,
                 "target": c.target, "old_value": c.old_value, "new_value": c.new_value,
                 "status": c.status, "reviewed_by": c.reviewed_by, "review_note": c.review_note}
                for c in rows]


def _apply_change(s, cr, tenant):
    """Apply an approved change to live data."""
    payload = _json.loads(cr.payload_json)
    if cr.change_type == "parameter":
        from backend.parameters import set_param
        set_param(s, payload["name"], payload["value"], tenant=tenant,
                  scope=payload.get("scope", "global"), source="planner")
    elif cr.change_type == "demand_override":
        # upsert a demand override row
        existing = s.query(m.DemandOverride).filter_by(
            tenant_id=tenant, item_code=payload["item_code"],
            location_code=payload["location_code"], period=payload["period"]).first()
        if existing:
            existing.override_qty = payload["override_qty"]
            existing.override_type = payload.get("override_type", "absolute")
            existing.reason = payload.get("reason", "")
            existing.source = "planner"
        else:
            s.add(m.DemandOverride(
                tenant_id=tenant, item_code=payload["item_code"],
                location_code=payload["location_code"], period=payload["period"],
                override_qty=payload["override_qty"],
                override_type=payload.get("override_type", "absolute"),
                reason=payload.get("reason", ""), source="planner"))
    s.commit()


class ReviewBody(BaseModel):
    note: str = ""


@app.post("/api/change-requests/{cr_id}/approve")
def approve_change(cr_id: int, body: ReviewBody, user=Depends(require_roles("approver", "management", "admin"))):
    with Session() as s:
        cr = s.query(m.ChangeRequest).filter_by(id=cr_id, tenant_id=user["tenant"]).first()
        if not cr:
            raise HTTPException(404, "Change request not found")
        if cr.status != "submitted":
            raise HTTPException(400, f"Already {cr.status}")
        _apply_change(s, cr, user["tenant"])
        cr.status = "approved"; cr.reviewed_by = user["sub"]; cr.review_note = body.note
        cr.reviewed_at = _dt.utcnow()
        s.add(m.AuditLog(tenant_id=user["tenant"], user_email=user["sub"],
                         action="approve_change", detail=f"CR#{cr_id}: {cr.target}"))
        s.commit()
        # re-run pipeline so approved change flows into the plan
        run_pipeline(s, user["tenant"])
        return {"ok": True, "status": "approved", "replanned": True}


@app.post("/api/change-requests/{cr_id}/reject")
def reject_change(cr_id: int, body: ReviewBody, user=Depends(require_roles("approver", "management", "admin"))):
    with Session() as s:
        cr = s.query(m.ChangeRequest).filter_by(id=cr_id, tenant_id=user["tenant"]).first()
        if not cr:
            raise HTTPException(404, "Change request not found")
        cr.status = "rejected"; cr.reviewed_by = user["sub"]; cr.review_note = body.note
        cr.reviewed_at = _dt.utcnow()
        s.add(m.AuditLog(tenant_id=user["tenant"], user_email=user["sub"],
                         action="reject_change", detail=f"CR#{cr_id}: {cr.target}"))
        s.commit()
        return {"ok": True, "status": "rejected"}


@app.get("/api/audit-log")
def audit_log(user=Depends(require_roles("admin", "management", "approver"))):
    with Session() as s:
        rows = s.query(m.AuditLog).filter_by(tenant_id=user["tenant"]).order_by(m.AuditLog.id.desc()).limit(200).all()
        return [{"user": r.user_email, "action": r.action, "detail": r.detail,
                 "at": r.created_at.isoformat() if r.created_at else None} for r in rows]


@app.post("/api/copilot")
def copilot_ask(q: CopilotQuery):
    _ensure_seeded(q.tenant)
    with Session() as s:
        return copilot.ask(s, q.question, q.tenant)
