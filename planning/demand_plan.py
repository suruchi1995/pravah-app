"""
Demand Planning — turns statistical forecast into a consensus demand plan.

statistical_qty = forecast_output.forecast_qty
override_qty    = optional manual adjustment (here: a sample promo uplift on FG006
                  pre-workout for the first plan month, to show the override path works)
consensus_qty   = override_qty if present else statistical_qty

In production, overrides come from the UI. We seed one realistic override so the
consensus logic is demonstrably exercised, not just a copy of the forecast.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DEFAULT_TENANT

# sample promotional uplifts: (item, period_index_from_start, uplift_factor)
PROMO = {("FG006", 0): 1.25, ("FG006", 1): 1.15}   # pre-workout launch campaign


def run(session, tenant=DEFAULT_TENANT):
    fc = session.query(m.ForecastOutput).filter_by(tenant_id=tenant).all()
    if not fc:
        return 0
    periods = sorted({r.period for r in fc})
    pidx = {p: i for i, p in enumerate(periods)}

    session.query(m.DemandPlan).filter_by(tenant_id=tenant).delete()
    rows = []
    for r in fc:
        stat = r.forecast_qty
        override = None
        key = (r.item_code, pidx[r.period])
        if key in PROMO:
            override = round(stat * PROMO[key], 2)
        consensus = override if override is not None else stat
        rows.append(m.DemandPlan(
            tenant_id=tenant, item_code=r.item_code, location_code=r.location_code,
            period=r.period, statistical_qty=stat, override_qty=override,
            consensus_qty=consensus))
    session.bulk_save_objects(rows)
    session.commit()
    return len(rows)


if __name__ == "__main__":
    from backend.config import DATABASE_URL
    eng = m.make_engine(DATABASE_URL); Session = m.make_session_factory(eng)
    with Session() as ssn:
        n = run(ssn)
        print(f"Demand plan rows: {n}")
        overrides = ssn.query(m.DemandPlan).filter(m.DemandPlan.override_qty.isnot(None)).all()
        print(f"Rows with override applied: {len(overrides)} (sample promo on FG006)")
        for r in overrides[:3]:
            print(f"  {r.item_code} {r.location_code} {r.period}: stat={r.statistical_qty:.0f} -> consensus={r.consensus_qty:.0f}")
