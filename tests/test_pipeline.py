"""
Pipeline smoke test — seeds a fresh in-memory DB, runs the full pipeline, and
asserts each stage produced sensible, connected output. Run: python3 tests/test_pipeline.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.seed_loader import load
from planning.run_all import run_pipeline

checks = []
def check(name, cond, detail=""):
    checks.append((name, bool(cond), detail))

# fresh in-memory DB
eng = m.make_engine("sqlite:///:memory:")
m.init_db(eng)
Session = m.make_session_factory(eng)
ssn = Session()
load(ssn)
res = run_pipeline(ssn)

check("segmentation covers 10 FGs", res["Segmentation"] == 10, res["Segmentation"])
check("forecast 30 series x 6 months = 180", res["Forecasting"] == 180, res["Forecasting"])
check("demand plan 180 rows", res["Demand Plan"] == 180)
check("inventory targets 30", res["Inventory Targets"] == 30)
check("handshake 30", res["Handshake"] == 30)
check("netting 60", res["Netting"] == 60)
check("MRP produced rows", res["Supply MRP"] > 0)
check("capacity 36", res["Capacity"] == 36)
check("optimizer produced rows", res["Optimizer (3 scenarios)"] > 0)

# connectedness: every forecast item is a real FG
fgs = {it.item_code for it in ssn.query(m.Item).filter_by(item_type="FG")}
fc_items = {r.item_code for r in ssn.query(m.ForecastOutput)}
check("forecast items are FGs", fc_items <= fgs, str(fc_items - fgs))

# forecast accuracy is reasonable (<25% avg MAPE on 36-mo data)
fc = ssn.query(m.ForecastOutput).all()
avg_mape = sum(r.mape for r in fc) / len(fc)
check(f"avg MAPE < 25% (got {avg_mape:.1f}%)", avg_mape < 25)

# handshake revenue-at-risk is non-negative and computed
hs = ssn.query(m.DemandSupplyHandshake).all()
check("handshake revenue-at-risk >= 0", all(r.revenue_at_risk >= 0 for r in hs))

# MRP multi-level: RM appears (proves SFG exploded further)
mrp_items = {r.item_code for r in ssn.query(m.SupplyRequirement)}
rms = {it.item_code for it in ssn.query(m.Item).filter_by(item_type="RM")}
check("MRP exploded to raw materials", bool(mrp_items & rms), str(mrp_items & rms))

# capacity: at least one resource is TIGHT/OVERLOADED (a real constraint exists)
caps = ssn.query(m.CapacityLoad).all()
check("a binding capacity constraint exists",
      any(c.constraint_status in ("TIGHT", "OVERLOADED") for c in caps))

# optimizer: scenarios differ (min_cost vs max_service produce different totals)
def total(sc):
    return sum(p.quantity for p in ssn.query(m.ProductionPlan).filter_by(scenario=sc))
check("min_cost and max_service differ",
      abs(total("min_cost") - total("max_service")) > 1,
      f"min={total('min_cost'):.0f} maxsvc={total('max_service'):.0f}")

# solver explanations stored for each scenario
expl = {e.scenario for e in ssn.query(m.SolverExplanation)}
check("solver explanations stored", expl >= {"min_cost", "max_service", "balanced"}, str(expl))

passed = sum(1 for _, ok, _ in checks if ok)
print(f"\nPIPELINE SMOKE TEST: {passed}/{len(checks)} passed\n" + "-"*50)
failed = False
for name, ok, detail in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  -> {detail}" if not ok else ""))
    if not ok:
        failed = True
sys.exit(1 if failed else 0)
