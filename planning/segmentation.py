"""
Segmentation engine — ABC (value) + XYZ (variability) from real demand history.

ABC: rank FGs by annual value (avg monthly demand x unit price x 12), cumulative
     share -> A (<=80%), B (<=95%), C (rest).
XYZ: coefficient of variation (CoV = std/mean) of monthly demand ->
     X (CoV<=0.25 stable), Y (<=0.5 variable), Z (>0.5 erratic).
Writes product_segmentation with reasoning per item.
"""
import os, sys, statistics
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DEFAULT_TENANT


def run(session, tenant=DEFAULT_TENANT):
    # gather FG monthly totals (sum across DCs)
    items = {it.item_code: it for it in session.query(m.Item).filter_by(tenant_id=tenant)}
    fgs = [c for c, it in items.items() if it.item_type == "FG"]

    monthly = defaultdict(lambda: defaultdict(float))   # item -> period -> qty
    for d in session.query(m.DemandHistory).filter_by(tenant_id=tenant):
        if d.item_code in fgs:
            monthly[d.item_code][d.period] += d.quantity

    # ABC value
    values = {}
    cov = {}
    for fg in fgs:
        series = list(monthly[fg].values())
        avg = statistics.mean(series) if series else 0.0
        std = statistics.pstdev(series) if len(series) > 1 else 0.0
        price = items[fg].unit_price_or_cost or 0.0
        values[fg] = avg * price * 12
        cov[fg] = (std / avg) if avg else 0.0

    total_value = sum(values.values()) or 1.0
    ranked = sorted(fgs, key=lambda x: values[x], reverse=True)
    cum = 0.0
    abc = {}
    for fg in ranked:
        cum += values[fg]
        share = cum / total_value
        abc[fg] = "A" if share <= 0.80 else ("B" if share <= 0.95 else "C")

    def xyz_of(c):
        return "X" if c <= 0.25 else ("Y" if c <= 0.50 else "Z")

    # wipe + write
    session.query(m.ProductSegmentation).filter_by(tenant_id=tenant).delete()
    rows = []
    for fg in fgs:
        a, x = abc[fg], xyz_of(cov[fg])
        reason = (f"Annual value ~{values[fg]:,.0f} (rank by value -> {a}); "
                  f"CoV={cov[fg]:.2f} -> {x} "
                  f"({'stable' if x=='X' else 'variable' if x=='Y' else 'erratic'} demand).")
        rows.append(m.ProductSegmentation(
            tenant_id=tenant, item_code=fg, abc_class=a, xyz_class=x,
            abc_xyz=a + x, annual_value=round(values[fg], 2),
            cov=round(cov[fg], 4), reasoning=reason))
    session.bulk_save_objects(rows)
    session.commit()
    return len(rows)


if __name__ == "__main__":
    from backend.config import DATABASE_URL
    eng = m.make_engine(DATABASE_URL); m.init_db(eng)
    Session = m.make_session_factory(eng)
    with Session() as ssn:
        n = run(ssn)
        print(f"Segmentation written: {n} FGs")
        for r in ssn.query(m.ProductSegmentation).filter_by(tenant_id="apex").order_by(m.ProductSegmentation.annual_value.desc()):
            print(f"  {r.item_code}  {r.abc_xyz}  value={r.annual_value:>12,.0f}  CoV={r.cov:.2f}")
