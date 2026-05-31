"""
Inventory Planning — safety stock, reorder point, target inventory, days of cover.

Per (FG, DC):
  avg_monthly_demand = mean of consensus demand plan
  sigma              = std of recent demand history (monthly)
  z                  = service-level z-factor from target_service_level
  lead_time_months   = DC lead time assumption (network) -> here 0.5 month default
  safety_stock = z * sigma * sqrt(lead_time_months)
  reorder_point = avg_monthly_demand * lead_time_months + safety_stock
  target_inventory = reorder_point + avg_monthly_demand   (order-up-to)
  days_cover = target_inventory / (avg_monthly_demand/30)
Reasoning stored per row.
"""
import os, sys, math, statistics
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DEFAULT_TENANT

LEAD_TIME_MONTHS = 0.5   # DC replenishment lead time assumption

# inverse normal CDF (Acklam approximation) for service-level -> z
def z_from_service(p):
    if p <= 0: return 0.0
    if p >= 0.9999: p = 0.9999
    a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00]
    b=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,6.680131188771972e+01,-1.328068155288572e+01]
    c=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,-2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00]
    d=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,3.754408661907416e+00]
    pl=0.02425
    if p < pl:
        q=math.sqrt(-2*math.log(p)); return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p <= 1-pl:
        q=p-0.5; r=q*q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    q=math.sqrt(-2*math.log(1-p)); return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)


def run(session, tenant=DEFAULT_TENANT):
    svc = {r.item_code: r.target_service_level for r in session.query(m.ServiceLevel).filter_by(tenant_id=tenant)}

    # recent demand history std per (item, loc)
    hist = defaultdict(list)
    for d in session.query(m.DemandHistory).filter_by(tenant_id=tenant):
        hist[(d.item_code, d.location_code)].append((d.period, d.quantity))

    # avg consensus demand per (item, loc)
    plan = defaultdict(list)
    for r in session.query(m.DemandPlan).filter_by(tenant_id=tenant):
        plan[(r.item_code, r.location_code)].append(r.consensus_qty)

    session.query(m.InventoryTarget).filter_by(tenant_id=tenant).delete()
    rows = []
    for key, consensus in plan.items():
        item, loc = key
        avg = statistics.mean(consensus) if consensus else 0.0
        series = [q for _, q in sorted(hist.get(key, []))][-12:]   # last 12 months
        sigma = statistics.pstdev(series) if len(series) > 1 else 0.0
        z = z_from_service(svc.get(item, 0.95))
        ss = z * sigma * math.sqrt(LEAD_TIME_MONTHS)
        rop = avg * LEAD_TIME_MONTHS + ss
        target = rop + avg
        days = (target / (avg / 30)) if avg else 0.0
        reason = (f"z={z:.2f} (SL {svc.get(item,0.95):.0%}), sigma={sigma:.0f}/mo, "
                  f"LT={LEAD_TIME_MONTHS}mo -> SS={ss:.0f}; ROP={rop:.0f}; "
                  f"target(order-up-to)={target:.0f} ~ {days:.0f} days cover.")
        rows.append(m.InventoryTarget(
            tenant_id=tenant, item_code=item, location_code=loc,
            avg_monthly_demand=round(avg,2), safety_stock=round(ss,2),
            reorder_point=round(rop,2), target_inventory=round(target,2),
            days_cover=round(days,1), reasoning=reason))
    session.bulk_save_objects(rows)
    session.commit()
    return len(rows)


if __name__ == "__main__":
    from backend.config import DATABASE_URL
    eng = m.make_engine(DATABASE_URL); Session = m.make_session_factory(eng)
    with Session() as ssn:
        n = run(ssn)
        print(f"Inventory targets: {n}")
        for r in ssn.query(m.InventoryTarget).filter_by(tenant_id="apex", item_code="FG001").order_by(m.InventoryTarget.location_code):
            print(f"  FG001 {r.location_code}: avg={r.avg_monthly_demand:.0f} SS={r.safety_stock:.0f} ROP={r.reorder_point:.0f} target={r.target_inventory:.0f} ({r.days_cover:.0f}d)")
