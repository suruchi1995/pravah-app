"""
Demand Planning — statistical forecast + overrides -> consensus.

NOTHING hardcoded. Overrides come from the demand_overrides table, which is
populated either by a planner in the UI or by an uploaded overrides sheet.
  statistical_qty = forecast_output.forecast_qty
  override_qty    = demand_overrides row, if one exists for (item, loc, period)
  consensus_qty   = override_qty if present else statistical_qty
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DEFAULT_TENANT


def run(session, tenant=DEFAULT_TENANT):
    fc = session.query(m.ForecastOutput).filter_by(tenant_id=tenant).all()
    if not fc:
        return 0

    # load overrides keyed by (item, loc, period) — from UI or upload, never code
    overrides = {}
    for o in session.query(m.DemandOverride).filter_by(tenant_id=tenant):
        overrides[(o.item_code, o.location_code, o.period)] = (o.override_qty, o.override_type)

    session.query(m.DemandPlan).filter_by(tenant_id=tenant).delete()
    rows = []
    for r in fc:
        stat = r.forecast_qty
        ov_entry = overrides.get((r.item_code, r.location_code, r.period))
        if ov_entry is not None:
            ov_val, ov_type = ov_entry
            if ov_type == "uplift_pct":
                ov = round(stat * (1 + ov_val / 100.0), 2)   # +X% on the statistical forecast
            else:
                ov = ov_val                                   # absolute set
        else:
            ov = None
        consensus = ov if ov is not None else stat
        rows.append(m.DemandPlan(
            tenant_id=tenant, item_code=r.item_code, location_code=r.location_code,
            period=r.period, statistical_qty=stat, override_qty=ov,
            consensus_qty=consensus))
    session.bulk_save_objects(rows)
    session.commit()
    return len(rows)


if __name__ == "__main__":
    from backend.config import DATABASE_URL
    eng = m.make_engine(DATABASE_URL); Session = m.make_session_factory(eng)
    with Session() as ssn:
        n = run(ssn)
        ov = ssn.query(m.DemandPlan).filter(m.DemandPlan.override_qty.isnot(None)).count()
        print(f"Demand plan rows: {n} | overrides applied: {ov}")
