"""
Parameters Registry
===================
The single home for every tunable number in the system. Engines read values via
get_param(); they never hardcode. Each parameter records:
  - source: 'derived' (we computed/defaulted with a stated assumption) or
            'planner' (overridden in the UI) or 'client' (came from upload)
  - assumption: shown in the UI so a planner sees WHY a value is what it is
  - editable: whether the UI may change it

This is what makes the system honest: no magic constants buried in code. If a
value isn't from the client, the app says so and lets the planner change it.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DEFAULT_TENANT

# name -> (default_value, value_type, assumption shown to planner)
# These are STARTING POINTS a planner can review/override — not hidden constants.
DEFAULTS = {
    # ---- forecasting ----
    "forecast_holdout_months":   (3,    "int",   "Months held back to backtest forecast accuracy. Industry-typical 3."),
    "forecast_horizon_months":   (6,    "int",   "How many months forward to forecast. Set to your planning horizon."),
    "forecast_season_length":    (12,   "int",   "Seasonal cycle length in months (12 = annual seasonality)."),
    "ses_alpha":                 (0.4,  "float", "Smoothing factor for Single Exponential Smoothing (0–1)."),
    "hw_alpha":                  (0.3,  "float", "Holt-Winters level smoothing (0–1)."),
    "hw_beta":                   (0.1,  "float", "Holt-Winters trend smoothing (0–1)."),
    "hw_gamma":                  (0.2,  "float", "Holt-Winters seasonal smoothing (0–1)."),
    # ---- inventory ----
    "lead_time_months_dc":       (0.5,  "float", "DC replenishment lead time. Default 0.5 month — override with real values."),
    "default_service_level_A":   (0.98, "float", "Target service level for A-class items if not provided."),
    "default_service_level_B":   (0.95, "float", "Target service level for B-class items if not provided."),
    "default_service_level_C":   (0.90, "float", "Target service level for C-class items if not provided."),
    # ---- costs ----
    "holding_cost_pct_month":    (0.02, "float", "Monthly inventory holding cost as % of value. Default 2% — override with finance's figure."),
    "production_cost_ratio":     (0.5,  "float", "If production cost missing: assume it's this fraction of selling price."),
    # ---- netting ----
    "default_moq":               (50,   "int",   "Default production lot size if item MOQ not given."),
    # ---- segmentation thresholds ----
    "abc_a_cutoff":              (0.80, "float", "Cumulative value share defining A items (top 80%)."),
    "abc_b_cutoff":              (0.95, "float", "Cumulative value share defining B items (to 95%)."),
    "xyz_x_cutoff":              (0.25, "float", "Coefficient-of-variation cutoff for stable (X) items."),
    "xyz_y_cutoff":              (0.50, "float", "CoV cutoff for variable (Y) items; above = erratic (Z)."),
    # ---- optimizer ----
    "shortage_penalty_mult":     (3.0,  "float", "Penalty per unit short = this × unit margin (min-cost scenario)."),
    # ---- constraints ----
    "min_months_cover":          (0.5,  "float", "Default minimum inventory cover if not provided."),
    "max_months_cover":          (3.0,  "float", "Default maximum inventory cover if not provided."),
}

_CASTERS = {"int": int, "float": float, "str": str,
            "bool": lambda x: str(x).lower() in ("1", "true", "yes")}


def seed_parameters(session, tenant=DEFAULT_TENANT, overwrite=False):
    """Ensure every parameter exists in the DB. Existing planner overrides are kept
    unless overwrite=True."""
    existing = {p.name: p for p in session.query(m.Parameter).filter_by(tenant_id=tenant, scope="global")}
    for name, (val, vtype, assumption) in DEFAULTS.items():
        if name in existing and not overwrite:
            continue
        if name in existing:
            p = existing[name]
            p.value = str(val); p.value_type = vtype; p.assumption = assumption; p.source = "derived"
        else:
            session.add(m.Parameter(
                tenant_id=tenant, name=name, scope="global", value=str(val),
                value_type=vtype, source="derived", assumption=assumption, editable=True))
    session.commit()


def get_param(session, name, tenant=DEFAULT_TENANT, scope="global"):
    """Read a parameter's typed value. Falls back to DEFAULTS if not yet seeded."""
    p = (session.query(m.Parameter)
         .filter_by(tenant_id=tenant, name=name, scope=scope).first())
    if p is None and scope != "global":
        p = session.query(m.Parameter).filter_by(tenant_id=tenant, name=name, scope="global").first()
    if p is not None:
        return _CASTERS.get(p.value_type, str)(p.value)
    if name in DEFAULTS:
        val, vtype, _ = DEFAULTS[name]
        return _CASTERS.get(vtype, str)(str(val))
    raise KeyError(f"Unknown parameter '{name}'")


def set_param(session, name, value, tenant=DEFAULT_TENANT, scope="global", source="planner"):
    """Planner override from the UI. Records that a human changed it."""
    p = session.query(m.Parameter).filter_by(tenant_id=tenant, name=name, scope=scope).first()
    if p is None:
        vtype = DEFAULTS.get(name, (None, "float", ""))[1]
        p = m.Parameter(tenant_id=tenant, name=name, scope=scope, value=str(value),
                        value_type=vtype, source=source, assumption="Set by planner.", editable=True)
        session.add(p)
    else:
        p.value = str(value); p.source = source
    session.commit()
    return p


def list_parameters(session, tenant=DEFAULT_TENANT):
    rows = session.query(m.Parameter).filter_by(tenant_id=tenant).order_by(m.Parameter.name).all()
    return [{"name": p.name, "scope": p.scope, "value": p.value, "value_type": p.value_type,
             "source": p.source, "assumption": p.assumption, "editable": p.editable} for p in rows]
