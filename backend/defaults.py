"""
Apply documented defaults for any OPTIONAL sheet the client didn't provide.
Operates on a dict of {sheet: list-of-dicts} and returns it completed.
Defaults are intentionally conservative and flagged in their reasoning downstream.
"""
from collections import defaultdict


def apply_defaults(tables: dict) -> dict:
    items = tables.get("items", [])
    fgs = [r for r in items if r.get("item_type") == "FG"]
    sfgs = [r for r in items if r.get("item_type") == "SFG"]
    plants = [r for r in tables.get("locations", []) if r.get("location_type") == "Plant"]

    # service_levels: default by ABC unknown at this point -> use 0.95 baseline
    if not tables.get("service_levels"):
        tables["service_levels"] = [
            {"item_code": r["item_code"], "target_service_level": 0.95} for r in fgs]

    # costs: production_cost = 50% of price; holding 2%/mo
    if not tables.get("costs"):
        rows = []
        for r in fgs + sfgs:
            price = r.get("unit_price_or_cost") or 0
            try:
                price = float(price)
            except (TypeError, ValueError):
                price = 0.0
            rows.append({"item_code": r["item_code"],
                         "production_cost": round(price * 0.5, 2) if price else 100.0,
                         "holding_cost_pct_month": 0.02})
        tables["costs"] = rows

    # constraints: 0.5 - 3.0 months cover
    if not tables.get("constraints"):
        tables["constraints"] = [
            {"item_code": r["item_code"], "min_months_cover": 0.5, "max_months_cover": 3.0}
            for r in fgs]

    # transport_modes
    if not tables.get("transport_modes"):
        tables["transport_modes"] = [
            {"mode_code": "ROAD", "mode_name": "Road", "lead_time_days": 4, "cost_per_kg": 6.0},
            {"mode_code": "AIR", "mode_name": "Air", "lead_time_days": 1, "cost_per_kg": 35.0}]

    # resources / routing: NEVER faked. If absent, capacity planning is disabled
    # downstream (see capabilities). We do not invent a line or its hours.

    # open orders default empty (safe — absence genuinely means none open)
    for opt in ("purchase_orders", "production_orders", "sales_orders"):
        tables.setdefault(opt, [])

    return tables
