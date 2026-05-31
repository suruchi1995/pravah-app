"""
Capacity Planning — finite capacity load per resource per period.

load_hours = sum over items routed to the resource of (planned production qty * runtime_hr)
available_hours = resource.hours_per_month
utilization = load / available
constraint_status = OK (<85%), TIGHT (85-100%), OVERLOADED (>100%)

Planned production = FG planned orders (netting) + SFG net requirements (MRP),
since both consume resource time via routing.
"""
import os, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DEFAULT_TENANT


def run(session, tenant=DEFAULT_TENANT):
    resources = {r.resource_code: r for r in session.query(m.Resource).filter_by(tenant_id=tenant)}
    routing = defaultdict(list)   # item -> [(resource, hr_per_unit)]
    for rt in session.query(m.Routing).filter_by(tenant_id=tenant):
        routing[rt.item_code].append((rt.resource_code, rt.runtime_hr_per_unit))

    # planned production qty by item x period
    prod = defaultdict(lambda: defaultdict(float))
    for nr in session.query(m.NetRequirement).filter_by(tenant_id=tenant):
        prod[nr.item_code][nr.period] += nr.planned_order
    for sr in session.query(m.SupplyRequirement).filter_by(tenant_id=tenant):
        if sr.source == "make":   # SFGs are produced -> consume capacity
            prod[sr.item_code][sr.period] += sr.net_requirement
    periods = sorted({p for it in prod for p in prod[it]})

    # accumulate load
    load = defaultdict(lambda: defaultdict(float))   # resource -> period -> hours
    for it, pmap in prod.items():
        for res, hr in routing.get(it, []):
            for p, q in pmap.items():
                load[res][p] += q * hr

    session.query(m.CapacityLoad).filter_by(tenant_id=tenant).delete()
    rows = []
    for res, rinfo in resources.items():
        avail = rinfo.hours_per_month
        for p in periods:
            lh = load[res].get(p, 0.0)
            util = (lh / avail) if avail else 0.0
            status = "OK" if util < 0.85 else ("TIGHT" if util <= 1.0 else "OVERLOADED")
            rows.append(m.CapacityLoad(
                tenant_id=tenant, resource_code=res, period=p,
                load_hours=round(lh,2), available_hours=round(avail,2),
                utilization=round(util,4), constraint_status=status))
    session.bulk_save_objects(rows)
    session.commit()
    return len(rows)


if __name__ == "__main__":
    from backend.config import DATABASE_URL
    eng = m.make_engine(DATABASE_URL); Session = m.make_session_factory(eng)
    with Session() as ssn:
        n = run(ssn)
        print(f"Capacity load rows: {n}")
        first = ssn.query(m.CapacityLoad).filter_by(tenant_id="apex").order_by(m.CapacityLoad.period).first()
        p0 = first.period
        print(f"Resource utilization, {p0}:")
        for r in ssn.query(m.CapacityLoad).filter_by(tenant_id="apex", period=p0).order_by(m.CapacityLoad.utilization.desc()):
            print(f"  {r.resource_code:14s} load={r.load_hours:7.0f}h / {r.available_hours:.0f}h = {r.utilization:5.0%}  [{r.constraint_status}]")
