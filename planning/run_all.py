"""
Run the full planning pipeline in dependency order against the current DB.
Usage: python3 -m planning.run_all
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DATABASE_URL, DEFAULT_TENANT
from planning import (segmentation, forecasting, demand_plan, inventory_planning,
                      handshake, netting, supply_mrp, capacity)
from optimization import production_optimizer


def run_pipeline(session, tenant=DEFAULT_TENANT):
    from backend.parameters import seed_parameters
    from backend.uom import seed_conversions
    seed_parameters(session, tenant)
    seed_conversions(session, tenant)   # ensure all tunables exist as data first
    steps = [
        ("Segmentation",      segmentation.run),
        ("Forecasting",       forecasting.run),
        ("Demand Plan",       demand_plan.run),
        ("Inventory Targets", inventory_planning.run),
        ("Handshake",         handshake.run),
        ("Netting",           netting.run),
        ("Supply MRP",        supply_mrp.run),
        ("Capacity",          capacity.run),
    ]
    results = {}
    for name, fn in steps:
        results[name] = fn(session, tenant)
    opt = production_optimizer.run(session, tenant)
    results["Optimizer (3 scenarios)"] = sum(v["rows"] for v in opt.values())
    return results


if __name__ == "__main__":
    eng = m.make_engine(DATABASE_URL); m.init_db(eng)
    Session = m.make_session_factory(eng)
    with Session() as ssn:
        res = run_pipeline(ssn)
    print("Pipeline complete:")
    for k, v in res.items():
        print(f"  {k:20s} {v:5d} rows")
