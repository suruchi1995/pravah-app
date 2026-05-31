"""
Demand-Supply Handshake — the core differentiator.

Per (FG, DC, first plan period):
  demand_qty           = consensus demand plan
  available_supply_qty = on-hand inventory (DC) + open production orders (allocated)
                         + open POs of the FG (rare for FG, included for completeness)
  gap_qty              = max(0, demand - available)
  fill_rate            = min(1, available / demand)
  revenue_at_risk      = gap_qty * selling_price
  margin_at_risk       = gap_qty * (selling_price - production_cost)
  recommendation       = action text driven by the numbers
Stores explanation for the AI copilot to read.
"""
import os, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DEFAULT_TENANT


def run(session, tenant=DEFAULT_TENANT):
    items = {it.item_code: it for it in session.query(m.Item).filter_by(tenant_id=tenant)}
    cost = {c.item_code: c for c in session.query(m.Cost).filter_by(tenant_id=tenant)}

    # first plan period
    periods = sorted({r.period for r in session.query(m.DemandPlan).filter_by(tenant_id=tenant)})
    if not periods:
        return 0
    p0 = periods[0]

    # demand for first period per (item, loc)
    demand = {}
    for r in session.query(m.DemandPlan).filter_by(tenant_id=tenant, period=p0):
        demand[(r.item_code, r.location_code)] = r.consensus_qty

    # on-hand FG inventory at DCs
    onhand = defaultdict(float)
    for inv in session.query(m.Inventory).filter_by(tenant_id=tenant):
        onhand[(inv.item_code, inv.location_code)] += inv.on_hand_qty

    # open production orders (made at plant; treat as supply available to network)
    prod_supply = defaultdict(float)
    for po in session.query(m.ProductionOrder).filter_by(tenant_id=tenant):
        prod_supply[po.item_code] += po.quantity

    # distribute plant production proportionally to each DC's demand share for that FG
    fg_demand_total = defaultdict(float)
    for (it, loc), q in demand.items():
        fg_demand_total[it] += q

    session.query(m.DemandSupplyHandshake).filter_by(tenant_id=tenant).delete()
    rows = []
    for (it, loc), dq in demand.items():
        price = items[it].unit_price_or_cost or 0.0
        prod_cost = cost[it].production_cost if it in cost else price * 0.5
        share = (dq / fg_demand_total[it]) if fg_demand_total[it] else 0.0
        supply = onhand[(it, loc)] + prod_supply[it] * share
        gap = max(0.0, dq - supply)
        fill = min(1.0, supply / dq) if dq else 1.0
        rev_risk = gap * price
        margin_risk = gap * max(0.0, price - prod_cost)
        if gap <= 0:
            rec = "Supply covers demand. No action."
        elif fill >= 0.85:
            rec = f"Minor gap ({gap:.0f}u). Pull a small production lot or transfer from another DC."
        else:
            rec = f"Material shortfall ({gap:.0f}u, fill {fill:.0%}). Schedule production and/or expedite components."
        rows.append(m.DemandSupplyHandshake(
            tenant_id=tenant, item_code=it, location_code=loc, period=p0,
            demand_qty=round(dq,2), available_supply_qty=round(supply,2),
            gap_qty=round(gap,2), fill_rate=round(fill,4),
            revenue_at_risk=round(rev_risk,2), margin_at_risk=round(margin_risk,2),
            recommendation=rec))
    session.bulk_save_objects(rows)
    session.commit()
    return len(rows)


if __name__ == "__main__":
    from backend.config import DATABASE_URL
    eng = m.make_engine(DATABASE_URL); Session = m.make_session_factory(eng)
    with Session() as ssn:
        n = run(ssn)
        rows = ssn.query(m.DemandSupplyHandshake).filter_by(tenant_id="apex").all()
        tot_rev = sum(r.revenue_at_risk for r in rows)
        gaps = [r for r in rows if r.gap_qty > 0]
        print(f"Handshake rows: {n} | rows with gap: {len(gaps)} | total revenue-at-risk: ₹{tot_rev:,.0f}")
        for r in sorted(rows, key=lambda x: -x.revenue_at_risk)[:5]:
            print(f"  {r.item_code} {r.location_code}: demand={r.demand_qty:.0f} supply={r.available_supply_qty:.0f} gap={r.gap_qty:.0f} fill={r.fill_rate:.0%} rev@risk=₹{r.revenue_at_risk:,.0f}")
