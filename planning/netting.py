"""
Netting Engine — classic MRP netting for finished goods, per (FG, period).

  net_requirement = gross_requirement + safety_stock - on_hand - scheduled_receipts
  planned_order   = round up to MOQ multiple if net_requirement > 0 else 0

Projected on-hand carries forward period to period (running balance), so the
plan is time-phased, not single-bucket. Full reasoning stored per row.
"""
import os, sys, math
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DEFAULT_TENANT

DEFAULT_MOQ = 50


def run(session, tenant=DEFAULT_TENANT):
    items = {it.item_code: it for it in session.query(m.Item).filter_by(tenant_id=tenant)}
    fgs = [c for c, it in items.items() if it.item_type == "FG"]

    # consensus demand by FG x period (sum across DCs -> plant-level gross requirement)
    gross = defaultdict(lambda: defaultdict(float))
    for r in session.query(m.DemandPlan).filter_by(tenant_id=tenant):
        gross[r.item_code][r.period] += r.consensus_qty
    periods = sorted({p for fg in fgs for p in gross[fg]})

    # safety stock per FG (sum DC targets)
    ss = defaultdict(float)
    for t in session.query(m.InventoryTarget).filter_by(tenant_id=tenant):
        ss[t.item_code] += t.safety_stock

    # opening on-hand per FG (sum DCs)
    onhand0 = defaultdict(float)
    for inv in session.query(m.Inventory).filter_by(tenant_id=tenant):
        if inv.item_code in fgs:
            onhand0[inv.item_code] += inv.on_hand_qty

    # scheduled receipts: open production orders by FG, mapped to first period
    receipts = defaultdict(lambda: defaultdict(float))
    for po in session.query(m.ProductionOrder).filter_by(tenant_id=tenant):
        if po.item_code in fgs and periods:
            receipts[po.item_code][periods[0]] += po.quantity

    session.query(m.NetRequirement).filter_by(tenant_id=tenant).delete()
    rows = []
    for fg in fgs:
        proj = onhand0[fg]              # running projected on-hand
        safety = ss[fg]
        moq = items[fg].unit_price_or_cost and DEFAULT_MOQ or DEFAULT_MOQ
        for p in periods:
            gr = gross[fg].get(p, 0.0)
            sr = receipts[fg].get(p, 0.0)
            net = gr + safety - proj - sr
            if net > 0:
                planned = math.ceil(net / DEFAULT_MOQ) * DEFAULT_MOQ
            else:
                planned = 0.0
            reason = (f"Gross {gr:.0f} + SS {safety:.0f} - on-hand {proj:.0f} "
                      f"- receipts {sr:.0f} = net {net:.0f}; "
                      f"planned order (CEIL to MOQ {DEFAULT_MOQ}) = {planned:.0f}.")
            rows.append(m.NetRequirement(
                tenant_id=tenant, item_code=fg, location_code="ALL", period=p,
                gross_requirement=round(gr,2), safety_stock=round(safety,2),
                on_hand=round(proj,2), scheduled_receipts=round(sr,2),
                net_requirement=round(net,2), planned_order=round(planned,2),
                reasoning=reason))
            # carry projected on-hand forward
            proj = proj + sr + planned - gr
            if proj < 0:
                proj = 0.0
    session.bulk_save_objects(rows)
    session.commit()
    return len(rows)


if __name__ == "__main__":
    from backend.config import DATABASE_URL
    eng = m.make_engine(DATABASE_URL); Session = m.make_session_factory(eng)
    with Session() as ssn:
        n = run(ssn)
        print(f"Net requirement rows: {n}")
        print("FG001 time-phased netting:")
        for r in ssn.query(m.NetRequirement).filter_by(tenant_id="apex", item_code="FG001").order_by(m.NetRequirement.period):
            print(f"  {r.period}: gross={r.gross_requirement:.0f} onhand={r.on_hand:.0f} net={r.net_requirement:.0f} -> planned={r.planned_order:.0f}")
