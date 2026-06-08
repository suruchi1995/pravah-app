"""
Supply Planning (MRP material explosion) — multi-level BOM explosion.

Takes FG planned orders (from netting), explodes them through the BOM to compute
dependent demand for SFG, RM and PM. Handles multi-level (FG -> SFG -> RM) by
processing items in topological order (FG level 0, then their components, etc.).

For each component:
  gross_requirement = sum over parents of (parent planned qty * usage_qty)
  net_requirement   = max(0, gross - on_hand - open_PO_receipts)
  source            = make (has its own BOM, e.g. SFG) or buy (RM/PM)

SFG net requirements themselves become parents and explode further to RM.
"""
import os, sys
from collections import defaultdict, deque
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DEFAULT_TENANT


def _topo_levels(bom_parents, all_items):
    """Assign BOM levels: items that are nobody's component except via FG chain.
    Level 0 = items that are never a component (FGs). Higher = deeper."""
    parents_of = defaultdict(set)   # component -> set(parents)
    children_of = defaultdict(set)  # parent -> set(components)
    for parent, comp in bom_parents:
        parents_of[comp].add(parent)
        children_of[parent].add(comp)
    level = {}
    # FGs = items that are never a component
    roots = [it for it in all_items if it not in parents_of]
    for r in roots:
        level[r] = 0
    q = deque(roots)
    while q:
        u = q.popleft()
        for c in children_of.get(u, ()):
            lv = level[u] + 1
            if c not in level or lv > level[c]:
                level[c] = lv
                q.append(c)
    return level


def run(session, tenant=DEFAULT_TENANT):
    items = {it.item_code: it for it in session.query(m.Item).filter_by(tenant_id=tenant)}
    bom = session.query(m.Bom).filter_by(tenant_id=tenant).all()
    bom_pairs = [(b.parent_item, b.component_item) for b in bom]
    usage = defaultdict(dict)  # parent -> {component: qty}
    # build item UOM map and conversion map for checking
    item_uom = {i.item_code: i.uom for i in session.query(m.Item).filter_by(tenant_id=tenant)}
    from backend.uom import build_conversion_map
    conv_map = build_conversion_map(session, tenant)
    uom_warnings = []
    for b in bom:
        qty = b.usage_qty
        p_uom = item_uom.get(b.parent_item, 'ea')
        c_uom = item_uom.get(b.component_item, 'ea')
        # BOM quantities are in component UOM per 1 parent unit — no conversion needed
        # BUT flag if parent and component are in incompatible UOM families
        if p_uom != c_uom:
            from backend.uom import convert
            _, ok, warn = convert(1.0, c_uom, p_uom, conv_map)
            if not ok:
                uom_warnings.append(f"BOM {b.parent_item}({p_uom}) -> {b.component_item}({c_uom}): {warn}")
        usage[b.parent_item][b.component_item] = qty

    levels = _topo_levels(bom_pairs, list(items.keys()))
    max_level = max(levels.values()) if levels else 0

    # FG planned orders by item x period (from netting)
    planned = defaultdict(lambda: defaultdict(float))
    for nr in session.query(m.NetRequirement).filter_by(tenant_id=tenant):
        planned[nr.item_code][nr.period] += nr.planned_order
    periods = sorted({p for it in planned for p in planned[it]})

    # on-hand for components (at plants)
    onhand = defaultdict(float)
    for inv in session.query(m.Inventory).filter_by(tenant_id=tenant):
        onhand[inv.item_code] += inv.on_hand_qty
    # open PO receipts for components (first period)
    po_receipt = defaultdict(float)
    for po in session.query(m.PurchaseOrder).filter_by(tenant_id=tenant):
        po_receipt[po.item_code] += po.quantity

    # requirement[item][period] accumulates as we descend levels
    req = defaultdict(lambda: defaultdict(float))
    for it in planned:
        for p in periods:
            req[it][p] += planned[it][p]

    session.query(m.SupplyRequirement).filter_by(tenant_id=tenant).delete()
    rows = []

    # process level by level; explode each level's requirement to its components
    for lvl in range(0, max_level + 1):
        level_items = [it for it, l in levels.items() if l == lvl]
        for parent in level_items:
            for comp, qty_per in usage.get(parent, {}).items():
                for p in periods:
                    req[comp][p] += req[parent][p] * qty_per
        # after FGs (lvl 0) we don't emit a supply row (FGs handled by netting);
        # emit rows for components at lvl>=1
        if lvl >= 1:
            for it in level_items:
                # consume on-hand + PO once (apply against earliest period)
                avail = onhand[it] + po_receipt[it]
                src = "make" if it in usage else "buy"   # SFG=make, RM/PM=buy
                for p in periods:
                    gr = req[it][p]
                    net = max(0.0, gr - avail)
                    avail = max(0.0, avail - gr)
                    if gr > 0:
                        rows.append(m.SupplyRequirement(
                            tenant_id=tenant, item_code=it, period=p, level=lvl,
                            gross_requirement=round(gr,2), net_requirement=round(net,2),
                            source=src))
    session.bulk_save_objects(rows)
    session.commit()
    return len(rows)


if __name__ == "__main__":
    from backend.config import DATABASE_URL
    eng = m.make_engine(DATABASE_URL); Session = m.make_session_factory(eng)
    with Session() as ssn:
        n = run(ssn)
        print(f"Supply requirement rows: {n}")
        # show SFG001 (make) and a couple RMs (buy) for first period
        first = ssn.query(m.SupplyRequirement).filter_by(tenant_id="apex").order_by(m.SupplyRequirement.period).first()
        p0 = first.period if first else None
        print(f"First period {p0} dependent demand (top by gross):")
        rows = ssn.query(m.SupplyRequirement).filter_by(tenant_id="apex", period=p0).all()
        for r in sorted(rows, key=lambda x:-x.gross_requirement)[:8]:
            print(f"  L{r.level} {r.item_code:8s} [{r.source}] gross={r.gross_requirement:.0f} net={r.net_requirement:.0f}")
