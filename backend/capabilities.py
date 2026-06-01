"""
Capabilities
============
Decides which planning features are ENABLED for a tenant based on the data that
actually exists — and gives a clear reason when something is disabled. This is
how we honour the rule: never fake a real constraint; instead disable the feature
that needs it and tell the user why.

Returned shape:
{
  "capacity_planning": {"enabled": False, "reason": "No resource/routing data..."},
  "constrained_optimization": {...},
  ...
}
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DEFAULT_TENANT


def compute(session, tenant=DEFAULT_TENANT):
    n_resources = session.query(m.Resource).filter_by(tenant_id=tenant).count()
    n_routing = session.query(m.Routing).filter_by(tenant_id=tenant).count()
    n_demand = session.query(m.DemandHistory).filter_by(tenant_id=tenant).count()
    n_bom = session.query(m.Bom).filter_by(tenant_id=tenant).count()

    caps = {}

    # Forecasting / demand — needs history
    caps["forecasting"] = {
        "enabled": n_demand > 0,
        "reason": "" if n_demand > 0 else "No demand history provided."}

    # MRP — needs a BOM
    caps["mrp"] = {
        "enabled": n_bom > 0,
        "reason": "" if n_bom > 0 else "No BOM provided — cannot explode dependent demand."}

    # Capacity planning — needs BOTH resources and routing, used exactly (never faked)
    has_capacity_data = n_resources > 0 and n_routing > 0
    caps["capacity_planning"] = {
        "enabled": has_capacity_data,
        "reason": "" if has_capacity_data else
                  "Capacity planning disabled — no resource/routing data provided. "
                  "Upload resources (line hours) and routing (hours per unit) to enable "
                  "finite-capacity checks. We do not estimate real line capacity."}

    # Constrained optimization — only meaningful with real capacity to constrain against
    caps["constrained_optimization"] = {
        "enabled": has_capacity_data,
        "reason": "" if has_capacity_data else
                  "Optimizer runs unconstrained (meets demand at min cost) because no "
                  "capacity data was provided. Upload resources + routing to optimise "
                  "against real line limits."}

    return caps


def is_enabled(session, feature, tenant=DEFAULT_TENANT):
    return compute(session, tenant).get(feature, {}).get("enabled", False)
