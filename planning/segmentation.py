"""
Segmentation — 3-axis model at item-location level (lowest granularity).

Axis 1: ABC  — annual value contribution at item-location
Axis 2: Predictability (formerly XYZ) — CoV of demand at item-location
Axis 3: Supply Criticality (CI) — fill rate + revenue at risk + supplier reliability

Result: one row per (item, location) giving full picture of where to focus.
Also writes a summary row at item level (location='ALL') for the ABC×Predictability matrix.

The item-level ABC/XYZ rows (location=ALL) are kept for backward compatibility
with the existing matrix view. Item-location rows are the new addition.
"""
import os, sys, statistics, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DEFAULT_TENANT
from backend.parameters import get_param


def run(session, tenant=DEFAULT_TENANT):
    A_CUT = get_param(session, "abc_a_cutoff", tenant)
    B_CUT = get_param(session, "abc_b_cutoff", tenant)
    X_CUT = get_param(session, "xyz_x_cutoff", tenant)
    Y_CUT = get_param(session, "xyz_y_cutoff", tenant)

    # --- build demand series per (item, loc) ---
    demand = {}  # (item, loc) -> [monthly qty]
    for d in session.query(m.DemandHistory).filter_by(tenant_id=tenant):
        key = (d.item_code, d.location_code)
        demand.setdefault(key, []).append(d.quantity)

    items = {i.item_code: i for i in session.query(m.Item).filter_by(tenant_id=tenant)}
    fgs = [i for i in items.values() if i.item_type == 'FG']
    fg_codes = {fg.item_code for fg in fgs}

    # --- supplier reliability per item (from supplier_item_mapping via suppliers) ---
    sups = {s.supplier_code: s for s in session.query(m.Supplier).filter_by(tenant_id=tenant)}
    sim = session.query(m.SupplierItemMapping).filter_by(tenant_id=tenant).all()
    item_reliability = {}  # item_code -> avg reliability of its suppliers
    for r in sim:
        rel = sups[r.supplier_code].reliability if r.supplier_code in sups else 0.8
        item_reliability.setdefault(r.item_code, []).append(rel)
    item_rel = {k: statistics.mean(v) for k, v in item_reliability.items()}

    # --- handshake data for supply criticality ---
    hs_rows = session.query(m.DemandSupplyHandshake).filter_by(tenant_id=tenant).all()
    hs_by_il = {}  # (item, loc) -> list of handshake rows
    for h in hs_rows:
        hs_by_il.setdefault((h.item_code, h.location_code), []).append(h)

    # ---- ITEM-LEVEL summary (location = 'ALL') — for backward compat matrix ----
    # annual value per item (sum across all locations)
    item_annual = {}
    for (item, loc), series in demand.items():
        if item not in fg_codes: continue
        price = items[item].unit_price_or_cost or 0
        item_annual[item] = item_annual.get(item, 0) + statistics.mean(series) * price * 12

    total_value = sum(item_annual.values())
    sorted_items = sorted(item_annual, key=lambda x: -item_annual[x])
    cum = 0
    abc_item = {}
    for fg in sorted_items:
        cum += item_annual[fg]
        share = cum / total_value if total_value else 0
        abc_item[fg] = 'A' if share <= A_CUT else ('B' if share <= B_CUT else 'C')

    item_cov = {}
    for (item, loc), series in demand.items():
        if item not in fg_codes: continue
        avg = statistics.mean(series) if series else 0
        std = statistics.pstdev(series) if len(series) > 1 else 0
        item_cov.setdefault(item, []).append((std/avg) if avg else 0)
    item_cov_avg = {k: statistics.mean(v) for k, v in item_cov.items()}

    def xyz_of(c): return 'X' if c <= X_CUT else ('Y' if c <= Y_CUT else 'Z')
    def ci_of(fill, rel): # supply criticality: low fill + low reliability = HIGH
        score = (1-fill) * 0.6 + (1-rel) * 0.4
        return 'HIGH' if score >= 0.4 else ('MEDIUM' if score >= 0.2 else 'LOW')

    session.query(m.ProductSegmentation).filter_by(tenant_id=tenant).delete()
    rows = []

    # item-level summary rows (for matrix)
    for fg in fg_codes:
        ann = item_annual.get(fg, 0)
        cov = item_cov_avg.get(fg, 0)
        abc = abc_item.get(fg, 'C')
        xyz = xyz_of(cov)
        rel = item_rel.get(fg, 0.8)
        # avg fill across all locations
        hs_all = [h for key, hs in hs_by_il.items() if key[0]==fg for h in hs]
        avg_fill = statistics.mean(h.fill_rate for h in hs_all) if hs_all else 1.0
        ci = ci_of(avg_fill, rel)
        reason = (f"{abc} by annual value ₹{ann:,.0f}. "
                  f"CoV={cov:.2f} → {xyz} (predictability). "
                  f"Supply CI={ci} (fill={avg_fill:.0%}, supplier_rel={rel:.0%}).")
        rows.append(m.ProductSegmentation(
            tenant_id=tenant, item_code=fg, location_code='ALL',
            abc_class=abc, xyz_class=xyz, abc_xyz=abc+xyz,
            annual_value=round(ann, 2), cov=round(cov, 4),
            supply_ci=ci, avg_fill_rate=round(avg_fill, 4),
            supplier_reliability=round(rel, 4), reasoning=reason))

    # item-location level rows (new)
    locs = {l.location_code for l in session.query(m.Location).filter_by(tenant_id=tenant, location_type='DC')}
    for loc in locs:
        # annual value at this location, ranked
        loc_annual = {}
        for fg in fg_codes:
            series = demand.get((fg, loc), [])
            price = items[fg].unit_price_or_cost or 0
            loc_annual[fg] = statistics.mean(series) * price * 12 if series else 0
        loc_total = sum(loc_annual.values())
        loc_sorted = sorted(loc_annual, key=lambda x: -loc_annual[x])
        cum = 0
        abc_loc = {}
        for fg in loc_sorted:
            cum += loc_annual[fg]
            share = cum/loc_total if loc_total else 0
            abc_loc[fg] = 'A' if share <= A_CUT else ('B' if share <= B_CUT else 'C')
        for fg in fg_codes:
            series = demand.get((fg, loc), [])
            if not series: continue
            avg = statistics.mean(series)
            std = statistics.pstdev(series) if len(series) > 1 else 0
            cov = (std/avg) if avg else 0
            xyz = xyz_of(cov)
            abc = abc_loc.get(fg, 'C')
            hs_il = hs_by_il.get((fg, loc), [])
            fill = statistics.mean(h.fill_rate for h in hs_il) if hs_il else 1.0
            risk = sum(h.revenue_at_risk for h in hs_il)
            rel = item_rel.get(fg, 0.8)
            ci = ci_of(fill, rel)
            ann = loc_annual.get(fg, 0)
            reason = (f"At {loc}: ABC={abc} (₹{ann:,.0f}/yr), "
                      f"Predictability={xyz} (CoV={cov:.2f}), "
                      f"Supply CI={ci} (fill={fill:.0%}, risk=₹{risk:,.0f}).")
            rows.append(m.ProductSegmentation(
                tenant_id=tenant, item_code=fg, location_code=loc,
                abc_class=abc, xyz_class=xyz, abc_xyz=abc+xyz,
                annual_value=round(ann,2), cov=round(cov,4),
                supply_ci=ci, avg_fill_rate=round(fill,4),
                supplier_reliability=round(rel,4), reasoning=reason))

    session.bulk_save_objects(rows)
    session.commit()
    return len(rows)


if __name__ == "__main__":
    from backend.config import DATABASE_URL
    eng = m.make_engine(DATABASE_URL); S = m.make_session_factory(eng)
    with S() as ssn: print("Segmentation rows:", run(ssn))
