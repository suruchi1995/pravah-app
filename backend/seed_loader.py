"""
Seed loader — load /datasets/*.csv into the DB (idempotent: wipes source tables first).
Run:  python3 -m backend.seed_loader
"""
import os
import csv
import sys

# allow running as `python3 backend/seed_loader.py` or `-m backend.seed_loader`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import models as m
from backend.config import DATABASE_URL, DEFAULT_TENANT

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets")

# CSV file -> (model, column mapping {csv_col: (attr, caster)})
def i(x):  # int
    return int(float(x)) if x not in ("", None) else 0
def f(x):  # float
    return float(x) if x not in ("", None) else None
def s(x):  # str
    return x

LOADERS = [
    ("items.csv", m.Item, {
        "item_code": ("item_code", s), "description": ("description", s),
        "item_type": ("item_type", s), "category": ("category", s),
        "uom": ("uom", s), "unit_price_or_cost": ("unit_price_or_cost", f)}),
    ("locations.csv", m.Location, {
        "location_code": ("location_code", s), "location_name": ("location_name", s),
        "location_type": ("location_type", s), "state": ("state", s), "zone": ("zone", s)}),
    ("suppliers.csv", m.Supplier, {
        "supplier_code": ("supplier_code", s), "supplier_name": ("supplier_name", s),
        "supplier_type": ("supplier_type", s), "lead_time_days": ("lead_time_days", i),
        "moq": ("moq", i), "reliability": ("reliability", f),
        "incoterm": ("incoterm", s), "payment_terms": ("payment_terms", s)}),
    ("resources.csv", m.Resource, {
        "resource_code": ("resource_code", s), "resource_name": ("resource_name", s),
        "plant_code": ("plant_code", s), "hours_per_month": ("hours_per_month", f)}),
    ("transport_modes.csv", m.TransportMode, {
        "mode_code": ("mode_code", s), "mode_name": ("mode_name", s),
        "lead_time_days": ("lead_time_days", i), "cost_per_kg": ("cost_per_kg", f)}),
    ("bom.csv", m.Bom, {
        "parent_item": ("parent_item", s), "component_item": ("component_item", s),
        "usage_qty": ("usage_qty", f)}),
    ("routing.csv", m.Routing, {
        "item_code": ("item_code", s), "resource_code": ("resource_code", s),
        "runtime_hr_per_unit": ("runtime_hr_per_unit", f)}),
    ("supplier_item_mapping.csv", m.SupplierItemMapping, {
        "supplier_code": ("supplier_code", s), "item_code": ("item_code", s),
        "unit_price": ("unit_price", f), "moq": ("moq", i), "lead_time_days": ("lead_time_days", i)}),
    ("demand_history.csv", m.DemandHistory, {
        "item_code": ("item_code", s), "location_code": ("location_code", s),
        "period": ("period", s), "quantity": ("quantity", f)}),
    ("inventory.csv", m.Inventory, {
        "item_code": ("item_code", s), "location_code": ("location_code", s),
        "on_hand_qty": ("on_hand_qty", f)}),
    ("purchase_orders.csv", m.PurchaseOrder, {
        "po_number": ("po_number", s), "supplier_code": ("supplier_code", s),
        "item_code": ("item_code", s), "quantity": ("quantity", f),
        "expected_receipt": ("expected_receipt", s), "status": ("status", s)}),
    ("production_orders.csv", m.ProductionOrder, {
        "pro_number": ("pro_number", s), "item_code": ("item_code", s),
        "plant_code": ("plant_code", s), "quantity": ("quantity", f),
        "expected_completion": ("expected_completion", s), "status": ("status", s)}),
    ("sales_orders.csv", m.SalesOrder, {
        "so_number": ("so_number", s), "item_code": ("item_code", s),
        "location_code": ("location_code", s), "quantity": ("quantity", f),
        "required_date": ("required_date", s), "priority": ("priority", s), "status": ("status", s)}),
    ("supply_lanes.csv", m.SupplyLane, {
        "lane_code": ("lane_code", s), "from_location": ("from_location", s),
        "to_location": ("to_location", s), "item_code": ("item_code", lambda x: x if x else None),
        "transport_mode": ("transport_mode", s), "lead_time_days": ("lead_time_days", f),
        "min_lot_size": ("min_lot_size", f), "min_lot_uom": ("min_lot_uom", s),
        "cost_per_unit": ("cost_per_unit", f)}),
    ("demand_overrides.csv", m.DemandOverride, {
        "item_code": ("item_code", s), "location_code": ("location_code", s),
        "period": ("period", s), "override_qty": ("override_qty", f),
        "override_type": ("override_type", s), "reason": ("reason", s), "source": ("source", s)}),
    ("service_levels.csv", m.ServiceLevel, {
        "item_code": ("item_code", s), "target_service_level": ("target_service_level", f)}),
    ("costs.csv", m.Cost, {
        "item_code": ("item_code", s), "production_cost": ("production_cost", f),
        "holding_cost_pct_month": ("holding_cost_pct_month", f)}),
    ("constraints.csv", m.Constraint, {
        "item_code": ("item_code", s), "min_months_cover": ("min_months_cover", f),
        "max_months_cover": ("max_months_cover", f)}),
]


def load(session):
    counts = {}
    for fname, model, mapping in LOADERS:
        # wipe existing source rows for this tenant (idempotent reseed)
        session.query(model).filter(model.tenant_id == DEFAULT_TENANT).delete()
        path = os.path.join(DATA, fname)
        if not os.path.exists(path):
            # optional CSVs (e.g. demand_overrides) may be absent — that's fine,
            # never crash the seed because a non-required file is missing.
            counts[fname] = 0
            continue
        rows = []
        with open(path) as fh:
            for r in csv.DictReader(fh):
                kwargs = {"tenant_id": r.get("tenant_id", DEFAULT_TENANT)}
                for col, (attr, caster) in mapping.items():
                    raw = r.get(col, "")
                    kwargs[attr] = caster(raw)
                rows.append(model(**kwargs))
        session.bulk_save_objects(rows)
        counts[fname] = len(rows)
    session.commit()
    return counts


def main():
    engine = m.make_engine(DATABASE_URL)
    m.init_db(engine)
    Session = m.make_session_factory(engine)
    with Session() as session:
        counts = load(session)
    print(f"Seeded into {DATABASE_URL}")
    for fname, n in counts.items():
        print(f"  {fname:32s} {n:5d} rows")


if __name__ == "__main__":
    main()
