"""
Pravah — Synthetic Dataset Generator
=====================================
Company: Apex Nutraceuticals (nutraceutical manufacturing)

Design principles
-----------------
1. REPRODUCIBLE: fixed RNG seed -> identical output every run.
2. INTERNALLY CONSISTENT: every foreign key references a real master record;
   BOMs explode to real RMs/PMs/SFGs; demand history covers every FG x DC x month.
3. PLANNING-READY: the numbers are shaped so that forecasting, MRP, capacity and
   optimization all have something meaningful to chew on (trend + seasonality +
   noise in demand; finite capacity; MOQs; lead times; costs; service levels).
4. NOT HARDCODED INTO THE APP: this writes CSVs to /datasets. The app loads those.

Output: one CSV per logical table, all tagged with tenant_id.
"""

import os
import csv
import math
import random
from datetime import date, timedelta

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
SEED = 42
TENANT_ID = "apex"                      # single demo tenant; schema supports many
HISTORY_MONTHS = 36                     # months of demand history (3 years)
HISTORY_START = date(2023, 4, 1)        # FY start (Apr) — Indian fiscal year
PLAN_START = date(2026, 4, 1)           # planning horizon start
PLAN_PERIODS = 6                        # 6 monthly planning buckets
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets")

rng = random.Random(SEED)

# --------------------------------------------------------------------------
# Master data definitions (the "shape" of Apex Nutraceuticals)
# --------------------------------------------------------------------------

# 10 Finished Goods. unit_price = selling price/unit; unit_cost filled later from BOM rollup-ish.
FINISHED_GOODS = [
    # code,     name,             category,      base_demand, trend, season_amp, abc_hint, price
    ("FG001", "Whey Protein 1kg",      "Protein",      900, 0.020, 0.18, "A", 2499),
    ("FG002", "Mass Gainer 3kg",       "Protein",      400, 0.015, 0.22, "A", 2999),
    ("FG003", "Fish Oil 90caps",       "Wellness",     650, 0.008, 0.10, "B", 799),
    ("FG004", "Multivitamin 60tab",    "Wellness",     800, 0.010, 0.08, "A", 599),
    ("FG005", "Creatine 250g",         "Performance",  550, 0.025, 0.15, "B", 1099),
    ("FG006", "Pre Workout 300g",      "Performance",  500, 0.030, 0.20, "B", 1499),
    ("FG007", "BCAA 400g",             "Performance",  350, 0.012, 0.16, "C", 1299),
    ("FG008", "Omega 3 120caps",       "Wellness",     450, 0.009, 0.10, "B", 999),
    ("FG009", "Vitamin D 60tab",       "Wellness",     600, 0.007, 0.30, "C", 399),
    ("FG010", "Electrolyte Mix 500g",  "Hydration",    700, 0.018, 0.35, "B", 699),
]

# 2 Semi-Finished Goods (bulk blends produced in-house, then filled/packed)
SEMI_FINISHED = [
    ("SFG001", "Protein Base Blend (bulk)",   "kg"),
    ("SFG002", "Capsule Oil Base (bulk)",     "L"),
]

# 20 Raw Materials
RAW_MATERIALS = [
    ("RM001", "Whey Protein Concentrate", "kg", 480),
    ("RM002", "Whey Protein Isolate",     "kg", 720),
    ("RM003", "Maltodextrin",             "kg", 95),
    ("RM004", "Cocoa Powder",             "kg", 320),
    ("RM005", "Creatine Monohydrate",     "kg", 1100),
    ("RM006", "Caffeine Anhydrous",       "kg", 1800),
    ("RM007", "Beta Alanine",             "kg", 1500),
    ("RM008", "L-Leucine",                "kg", 1300),
    ("RM009", "L-Isoleucine",             "kg", 1250),
    ("RM010", "L-Valine",                 "kg", 1250),
    ("RM011", "Fish Oil Concentrate",     "L", 640),
    ("RM012", "Vitamin D3 Premix",        "kg", 2200),
    ("RM013", "Multivitamin Premix",      "kg", 980),
    ("RM014", "Citric Acid",              "kg", 110),
    ("RM015", "Sodium/Potassium Salts",   "kg", 130),
    ("RM016", "Natural Flavour Blend",    "kg", 850),
    ("RM017", "Sucralose Sweetener",      "kg", 1400),
    ("RM018", "Gelatin (capsule)",        "kg", 540),
    ("RM019", "Glycerin",                 "L", 180),
    ("RM020", "Anti-caking Agent",        "kg", 240),
]

# 5 Packaging Materials
PACKAGING = [
    ("PM001", "Jar 1kg (HDPE)",      "ea", 28),
    ("PM002", "Jar 3kg (HDPE)",      "ea", 52),
    ("PM003", "Bottle 90/120 caps",  "ea", 14),
    ("PM004", "Label (printed)",     "ea", 3),
    ("PM005", "Shipper Carton",      "ea", 18),
]

# Locations: 2 plants + 3 warehouses (DCs)
PLANTS = [
    ("PLANT_BDI", "Baddi Plant", "Plant", "Himachal Pradesh", "North"),
    ("PLANT_PUN", "Pune Plant",  "Plant", "Maharashtra",      "West"),
]
WAREHOUSES = [
    ("DC_DEL", "Delhi DC",     "DC", "Delhi",       "North"),
    ("DC_MUM", "Mumbai DC",    "DC", "Maharashtra", "West"),
    ("DC_BLR", "Bangalore DC", "DC", "Karnataka",   "South"),
]
LOCATIONS = PLANTS + WAREHOUSES

# Suppliers (3 ingredient + 2 packaging)
SUPPLIERS = [
    # code, name, type, lead_time_days, moq, reliability, incoterm, payment
    ("SUP_INGA", "Ingredient Supplier A", "Ingredient", 21, 200, 0.95, "FOB", "Net 30"),
    ("SUP_INGB", "Ingredient Supplier B", "Ingredient", 28, 150, 0.90, "CIF", "Net 45"),
    ("SUP_INGC", "Ingredient Supplier C", "Ingredient", 35, 100, 0.88, "FOB", "Net 60"),
    ("SUP_PACKA","Packaging Supplier A",  "Packaging",  14, 500, 0.96, "EXW", "Net 30"),
    ("SUP_PACKB","Packaging Supplier B",  "Packaging",  10, 1000,0.93, "EXW", "Net 30"),
]

# Resources (production lines). capacity = hours available per month per line.
RESOURCES = [
    ("MIX_LINE_01", "Mixing Line 1",    "PLANT_BDI", 480),
    ("MIX_LINE_02", "Mixing Line 2",    "PLANT_PUN", 480),
    ("FILL_LINE_01","Filling Line 1",   "PLANT_BDI", 360),
    ("PACK_LINE_01","Packaging Line 1", "PLANT_BDI", 460),
    ("PACK_LINE_02","Packaging Line 2", "PLANT_PUN", 460),
    ("LABEL_LINE_01","Labeling Line",   "PLANT_PUN", 500),
]

TRANSPORT_MODES = [
    ("ROAD", "Road", 4, 6.0),    # mode, name, lead_time_days, cost_per_kg
    ("AIR",  "Air",  1, 35.0),
]

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def month_iter(start, n):
    """Yield first-of-month dates."""
    y, m = start.year, start.month
    for _ in range(n):
        yield date(y, m, 1)
        m += 1
        if m > 12:
            m = 1
            y += 1

def write_csv(name, header, rows):
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return path, len(rows)

NOW = "2026-05-31T00:00:00Z"

# --------------------------------------------------------------------------
# 1. items  (FG + SFG + RM + PM)
# --------------------------------------------------------------------------
def build_items():
    rows = []
    for code, name, cat, *_ , price in [(*fg,) for fg in FINISHED_GOODS]:
        rows.append([TENANT_ID, code, name, "FG", cat, "ea", price, NOW, NOW])
    for code, name, uom in SEMI_FINISHED:
        rows.append([TENANT_ID, code, name, "SFG", "Intermediate", uom, "", NOW, NOW])
    for code, name, uom, cost in RAW_MATERIALS:
        rows.append([TENANT_ID, code, name, "RM", "Ingredient", uom, cost, NOW, NOW])
    for code, name, uom, cost in PACKAGING:
        rows.append([TENANT_ID, code, name, "PM", "Packaging", uom, cost, NOW, NOW])
    return write_csv("items.csv",
        ["tenant_id","item_code","description","item_type","category","uom","unit_price_or_cost","created_at","updated_at"],
        rows)

# --------------------------------------------------------------------------
# 2. locations
# --------------------------------------------------------------------------
def build_locations():
    rows = [[TENANT_ID, c, n, t, st, z, NOW, NOW] for c,n,t,st,z in LOCATIONS]
    return write_csv("locations.csv",
        ["tenant_id","location_code","location_name","location_type","state","zone","created_at","updated_at"],
        rows)

# --------------------------------------------------------------------------
# 3. suppliers
# --------------------------------------------------------------------------
def build_suppliers():
    rows = [[TENANT_ID,c,n,t,lt,moq,rel,inc,pay,NOW,NOW] for c,n,t,lt,moq,rel,inc,pay in SUPPLIERS]
    return write_csv("suppliers.csv",
        ["tenant_id","supplier_code","supplier_name","supplier_type","lead_time_days","moq","reliability","incoterm","payment_terms","created_at","updated_at"],
        rows)

# --------------------------------------------------------------------------
# 4. resources
# --------------------------------------------------------------------------
def build_resources():
    rows = [[TENANT_ID,c,n,p,cap,NOW,NOW] for c,n,p,cap in RESOURCES]
    return write_csv("resources.csv",
        ["tenant_id","resource_code","resource_name","plant_code","hours_per_month","created_at","updated_at"],
        rows)

# --------------------------------------------------------------------------
# 5. transport_modes
# --------------------------------------------------------------------------
def build_transport():
    rows = [[TENANT_ID,c,n,lt,cost,NOW,NOW] for c,n,lt,cost in TRANSPORT_MODES]
    return write_csv("transport_modes.csv",
        ["tenant_id","mode_code","mode_name","lead_time_days","cost_per_kg","created_at","updated_at"],
        rows)

# --------------------------------------------------------------------------
# 6. BOM  — multi-level: FG -> (SFG + PM), SFG -> RM
#    This gives the MRP engine a real explosion to do.
# --------------------------------------------------------------------------
# Map each FG to a recipe. Quantities are per 1 unit of FG.
# We route protein FGs through SFG001 (protein base) and capsule FGs through SFG002.
def build_bom():
    rows = []
    def add(parent, comp, qty):
        rows.append([TENANT_ID, parent, comp, qty, NOW, NOW])

    # SFG recipes (per 1 unit of bulk: 1 kg or 1 L)
    # SFG001 Protein Base Blend (per kg)
    add("SFG001","RM001",0.55)   # WPC
    add("SFG001","RM002",0.25)   # WPI
    add("SFG001","RM003",0.10)   # maltodextrin
    add("SFG001","RM016",0.05)   # flavour
    add("SFG001","RM017",0.02)   # sweetener
    add("SFG001","RM020",0.03)   # anti-caking
    # SFG002 Capsule Oil Base (per L)
    add("SFG002","RM011",0.85)   # fish oil concentrate
    add("SFG002","RM019",0.10)   # glycerin
    add("SFG002","RM018",0.05)   # gelatin (for encapsulation)

    # FG recipes
    # FG001 Whey Protein 1kg: 1.0 kg protein base + jar1kg + label + carton-share
    add("FG001","SFG001",1.00); add("FG001","PM001",1); add("FG001","PM004",1); add("FG001","PM005",0.1)
    # FG002 Mass Gainer 3kg: 2.4 kg base + extra malto + jar3kg
    add("FG002","SFG001",2.40); add("FG002","RM003",0.55); add("FG002","RM004",0.20)
    add("FG002","PM002",1); add("FG002","PM004",1); add("FG002","PM005",0.1)
    # FG003 Fish Oil 90caps: 0.12 L oil base + bottle + label
    add("FG003","SFG002",0.12); add("FG003","PM003",1); add("FG003","PM004",1); add("FG003","PM005",0.05)
    # FG004 Multivitamin 60tab: premix + bottle
    add("FG004","RM013",0.018); add("FG004","RM020",0.002); add("FG004","PM003",1); add("FG004","PM004",1); add("FG004","PM005",0.05)
    # FG005 Creatine 250g
    add("FG005","RM005",0.25); add("FG005","RM016",0.005); add("FG005","PM001",1); add("FG005","PM004",1); add("FG005","PM005",0.08)
    # FG006 Pre Workout 300g
    add("FG006","RM006",0.02); add("FG006","RM007",0.10); add("FG006","RM003",0.12)
    add("FG006","RM016",0.04); add("FG006","RM017",0.02); add("FG006","PM001",1); add("FG006","PM004",1); add("FG006","PM005",0.08)
    # FG007 BCAA 400g: leucine/isoleucine/valine 2:1:1
    add("FG007","RM008",0.20); add("FG007","RM009",0.10); add("FG007","RM010",0.10)
    add("FG007","RM016",0.03); add("FG007","PM001",1); add("FG007","PM004",1); add("FG007","PM005",0.08)
    # FG008 Omega 3 120caps
    add("FG008","SFG002",0.15); add("FG008","PM003",1); add("FG008","PM004",1); add("FG008","PM005",0.05)
    # FG009 Vitamin D 60tab
    add("FG009","RM012",0.004); add("FG009","RM020",0.002); add("FG009","PM003",1); add("FG009","PM004",1); add("FG009","PM005",0.04)
    # FG010 Electrolyte Mix 500g
    add("FG010","RM014",0.05); add("FG010","RM015",0.20); add("FG010","RM003",0.20)
    add("FG010","RM016",0.03); add("FG010","RM017",0.02); add("FG010","PM001",1); add("FG010","PM004",1); add("FG010","PM005",0.08)

    return write_csv("bom.csv",
        ["tenant_id","parent_item","component_item","usage_qty","created_at","updated_at"],
        rows)

# --------------------------------------------------------------------------
# 7. routing — which resources each FG/SFG consumes, hours per unit
# --------------------------------------------------------------------------
def build_routing():
    rows = []
    def add(item, res, hrs):
        rows.append([TENANT_ID, item, res, hrs, NOW, NOW])
    # SFG production = mixing (bulk, slower per unit)
    add("SFG001","MIX_LINE_01",0.060); add("SFG001","MIX_LINE_02",0.060)
    add("SFG002","MIX_LINE_01",0.100)
    # Powder FGs: fill + pack + label (~min/unit on each line)
    for fg in ["FG001","FG002","FG005","FG006","FG007","FG010"]:
        add(fg,"FILL_LINE_01",0.050); add(fg,"PACK_LINE_01",0.040); add(fg,"LABEL_LINE_01",0.020)
    # Capsule/tablet FGs: fill + pack + label (bottle line)
    for fg in ["FG003","FG004","FG008","FG009"]:
        add(fg,"FILL_LINE_01",0.030); add(fg,"PACK_LINE_02",0.030); add(fg,"LABEL_LINE_01",0.020)
    return write_csv("routing.csv",
        ["tenant_id","item_code","resource_code","runtime_hr_per_unit","created_at","updated_at"],
        rows)

# --------------------------------------------------------------------------
# 8. supplier_item_mapping — who supplies which RM/PM, price, MOQ
# --------------------------------------------------------------------------
def build_supplier_item_mapping():
    rows = []
    def add(sup, item, price, moq, lt):
        rows.append([TENANT_ID, sup, item, price, moq, lt, NOW, NOW])
    rm_cost = {c: cost for c,_,_,cost in RAW_MATERIALS}
    pm_cost = {c: cost for c,_,_,cost in PACKAGING}
    # Ingredients: spread across A/B/C; some dual-sourced
    ing_items = [c for c,_,_,_ in RAW_MATERIALS]
    for i, item in enumerate(ing_items):
        primary = ["SUP_INGA","SUP_INGB","SUP_INGC"][i % 3]
        add(primary, item, rm_cost[item], 100 + (i%3)*50, [21,28,35][i%3])
        # dual-source a few key high-value items
        if item in ["RM001","RM002","RM005","RM006","RM011","RM013"]:
            secondary = "SUP_INGB" if primary != "SUP_INGB" else "SUP_INGC"
            add(secondary, item, round(rm_cost[item]*1.06,2), 150, 30)
    # Packaging
    for j, item in enumerate([c for c,_,_,_ in PACKAGING]):
        sup = "SUP_PACKA" if j % 2 == 0 else "SUP_PACKB"
        add(sup, item, pm_cost[item], 500 if sup=="SUP_PACKA" else 1000, 14 if sup=="SUP_PACKA" else 10)
    return write_csv("supplier_item_mapping.csv",
        ["tenant_id","supplier_code","item_code","unit_price","moq","lead_time_days","created_at","updated_at"],
        rows)

# --------------------------------------------------------------------------
# 9. demand_history — FG x DC x month, trend + seasonality + noise
#    Split total FG demand across the 3 DCs by fixed share.
# --------------------------------------------------------------------------
DC_SHARE = {"DC_DEL": 0.40, "DC_MUM": 0.35, "DC_BLR": 0.25}

def build_demand_history():
    rows = []
    months = list(month_iter(HISTORY_START, HISTORY_MONTHS))
    for code, name, cat, base, trend, amp, abc, price in FINISHED_GOODS:
        for t, mdate in enumerate(months):
            # trend grows month over month; seasonality is a sine over 12 months
            trend_factor = (1 + trend) ** t
            season = 1 + amp * math.sin(2 * math.pi * (mdate.month) / 12.0)
            total = base * trend_factor * season
            for dc, share in DC_SHARE.items():
                noise = rng.uniform(0.92, 1.08)
                qty = max(0, int(round(total * share * noise)))
                rows.append([TENANT_ID, code, dc, mdate.isoformat(), qty, NOW, NOW])
    return write_csv("demand_history.csv",
        ["tenant_id","item_code","location_code","period","quantity","created_at","updated_at"],
        rows)

# --------------------------------------------------------------------------
# 10. inventory — opening on-hand for FG (at DCs) and RM/PM/SFG (at plants)
# --------------------------------------------------------------------------
def build_inventory():
    rows = []
    # FG inventory at DCs: ~ 0.3–0.6 months of recent demand
    last_month_total = {}
    for code, name, cat, base, trend, amp, abc, price in FINISHED_GOODS:
        last = base * ((1+trend)**(HISTORY_MONTHS-1))
        last_month_total[code] = last
        for dc, share in DC_SHARE.items():
            cover = rng.uniform(0.3, 0.6)
            qty = int(round(last * share * cover))
            rows.append([TENANT_ID, code, dc, qty, NOW, NOW])
    # RM/PM/SFG inventory at plants (held at Baddi mainly)
    for code, name, uom, cost in RAW_MATERIALS:
        rows.append([TENANT_ID, code, "PLANT_BDI", int(rng.uniform(200, 1500)), NOW, NOW])
    for code, name, uom, cost in PACKAGING:
        rows.append([TENANT_ID, code, "PLANT_BDI", int(rng.uniform(2000, 8000)), NOW, NOW])
    for code, name, uom in SEMI_FINISHED:
        rows.append([TENANT_ID, code, "PLANT_BDI", int(rng.uniform(100, 400)), NOW, NOW])
    return write_csv("inventory.csv",
        ["tenant_id","item_code","location_code","on_hand_qty","created_at","updated_at"],
        rows)

# --------------------------------------------------------------------------
# 11. open purchase orders (in transit) — a few RMs/PMs arriving in plan window
# --------------------------------------------------------------------------
def build_purchase_orders():
    rows = []
    pid = 1
    sample_items = ["RM001","RM002","RM005","RM011","PM001","PM003","PM004"]
    for item in sample_items:
        sup = "SUP_INGA" if item.startswith("RM") else "SUP_PACKA"
        qty = int(rng.uniform(300, 1200))
        eta = (PLAN_START + timedelta(days=int(rng.uniform(5, 40)))).isoformat()
        rows.append([TENANT_ID, f"PO{pid:04d}", sup, item, qty, eta, "OPEN", NOW, NOW])
        pid += 1
    return write_csv("purchase_orders.csv",
        ["tenant_id","po_number","supplier_code","item_code","quantity","expected_receipt","status","created_at","updated_at"],
        rows)

# --------------------------------------------------------------------------
# 12. open production orders — a couple of FGs already scheduled
# --------------------------------------------------------------------------
def build_production_orders():
    rows = []
    pid = 1
    for fg in ["FG001","FG004","FG010"]:
        qty = int(rng.uniform(200, 600))
        eta = (PLAN_START + timedelta(days=int(rng.uniform(3, 25)))).isoformat()
        rows.append([TENANT_ID, f"PRO{pid:04d}", fg, "PLANT_BDI", qty, eta, "OPEN", NOW, NOW])
        pid += 1
    return write_csv("production_orders.csv",
        ["tenant_id","pro_number","item_code","plant_code","quantity","expected_completion","status","created_at","updated_at"],
        rows)

# --------------------------------------------------------------------------
# 13. sales orders — open customer orders against FGs at DCs
# --------------------------------------------------------------------------
def build_sales_orders():
    rows = []
    sid = 1
    for code, name, cat, base, trend, amp, abc, price in FINISHED_GOODS:
        n_orders = rng.randint(1, 3)
        for _ in range(n_orders):
            dc = rng.choice(list(DC_SHARE.keys()))
            qty = int(base * rng.uniform(0.05, 0.20))
            req = (PLAN_START + timedelta(days=int(rng.uniform(2, 30)))).isoformat()
            prio = rng.choice(["High","Medium","Low"])
            rows.append([TENANT_ID, f"SO{sid:05d}", code, dc, qty, req, prio, "OPEN", NOW, NOW])
            sid += 1
    return write_csv("sales_orders.csv",
        ["tenant_id","so_number","item_code","location_code","quantity","required_date","priority","status","created_at","updated_at"],
        rows)

# --------------------------------------------------------------------------
# 14. service_levels, lead_times, moq, costs, constraints (parameters)
# --------------------------------------------------------------------------
def build_parameters():
    paths = []
    # demand overrides — a sample promo, as DATA (planner-editable), not hardcoded in engine
    # FG006 pre-workout launch campaign: uplift first two plan months at each DC.
    months = list(month_iter(PLAN_START, 2))
    rows = []
    for i, mdate in enumerate(months):
        uplift = 25 if i == 0 else 15   # +25% then +15% on the statistical forecast
        for dc in DC_SHARE:
            rows.append([TENANT_ID, "FG006", dc, mdate.isoformat(),
                         uplift, "uplift_pct", "Pre-workout launch campaign", "upload"])
    paths.append(write_csv("demand_overrides.csv",
        ["tenant_id","item_code","location_code","period","override_qty","override_type","reason","source"], rows))

    # service levels per FG (drives safety stock z-factor downstream)
    rows = []
    for code, name, cat, base, trend, amp, abc, price in FINISHED_GOODS:
        target = {"A": 0.98, "B": 0.95, "C": 0.90}[abc]
        rows.append([TENANT_ID, code, target, NOW, NOW])
    paths.append(write_csv("service_levels.csv",
        ["tenant_id","item_code","target_service_level","created_at","updated_at"], rows))

    # costs: production cost/unit (FG/SFG), holding cost % per month
    rows = []
    for code, name, cat, base, trend, amp, abc, price in FINISHED_GOODS:
        prod_cost = round(price * rng.uniform(0.45, 0.60), 2)
        rows.append([TENANT_ID, code, prod_cost, 0.02, NOW, NOW])
    for code, name, uom in SEMI_FINISHED:
        rows.append([TENANT_ID, code, round(rng.uniform(150, 400),2), 0.02, NOW, NOW])
    paths.append(write_csv("costs.csv",
        ["tenant_id","item_code","production_cost","holding_cost_pct_month","created_at","updated_at"], rows))

    # constraints: min/max inventory bounds for FGs (weeks of cover -> units later)
    rows = []
    for code, name, cat, base, trend, amp, abc, price in FINISHED_GOODS:
        rows.append([TENANT_ID, code, 0.5, 3.0, NOW, NOW])  # min/max months cover
    paths.append(write_csv("constraints.csv",
        ["tenant_id","item_code","min_months_cover","max_months_cover","created_at","updated_at"], rows))

    return paths

# --------------------------------------------------------------------------
# Orchestrate
# --------------------------------------------------------------------------
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    results = []
    results.append(build_items())
    results.append(build_locations())
    results.append(build_suppliers())
    results.append(build_resources())
    results.append(build_transport())
    results.append(build_bom())
    results.append(build_routing())
    results.append(build_supplier_item_mapping())
    results.append(build_demand_history())
    results.append(build_inventory())
    results.append(build_purchase_orders())
    results.append(build_production_orders())
    results.append(build_sales_orders())
    results.extend(build_parameters())
    results.append(write_csv("supply_lanes.csv",
        ["tenant_id","lane_code","from_location","to_location","item_code",
         "transport_mode","lead_time_days","min_lot_size","min_lot_uom","cost_per_unit"],
        build_supply_lanes()))
    print("Generated datasets (seed={}):".format(SEED))
    for path, n in results:
        print("  {:32s} {:5d} rows".format(os.path.basename(path), n))
    print("\nOutput dir:", os.path.abspath(OUT_DIR))


def build_supply_lanes():
    """
    Explicit origin-destination lanes.
    Two tiers:
      1. Supplier → Plant  (for every RM/PM supplier, to the plant that uses it)
      2. Plant → DC        (for every FG, from the plant that makes it)
    This is the missing 'where does each item flow' data.
    """
    rows = []
    # Tier 1: Supplier → Plant lanes (RM and PM)
    # SUP_INGA/B/C supply ingredients → Baddi Plant (RM001-RM010, RM016-RM020)
    # SUP_PKGA/B   supply packaging → both plants (PM001-PM005)
    sup_plant_lanes = [
        ("LANE_INGA_BDI","SUP_INGA","PLANT_BDI",None,"ROAD",21,100,"kg",None),
        ("LANE_INGB_BDI","SUP_INGB","PLANT_BDI",None,"ROAD",28,150,"kg",None),
        ("LANE_INGB_PUN","SUP_INGB","PLANT_PUN",None,"ROAD",28,150,"kg",None),
        ("LANE_INGC_BDI","SUP_INGC","PLANT_BDI",None,"ROAD",35,200,"kg",None),
        ("LANE_INGC_PUN","SUP_INGC","PLANT_PUN",None,"ROAD",35,200,"kg",None),
        ("LANE_INGD_BDI","SUP_INGD","PLANT_BDI",None,"ROAD",25,100,"kg",None),
        ("LANE_INGD_PUN","SUP_INGD","PLANT_PUN",None,"ROAD",25,100,"kg",None),
        ("LANE_INGE_BDI","SUP_INGE","PLANT_BDI",None,"ROAD",30,200,"kg",None),
        ("LANE_PKGA_BDI","SUP_PKGA","PLANT_BDI",None,"ROAD",14,500,"ea",None),
        ("LANE_PKGA_PUN","SUP_PKGA","PLANT_PUN",None,"ROAD",14,500,"ea",None),
        ("LANE_PKGB_BDI","SUP_PKGB","PLANT_BDI",None,"ROAD",21,300,"ea",None),
        ("LANE_PKGB_PUN","SUP_PKGB","PLANT_PUN",None,"ROAD",21,300,"ea",None),
    ]
    # Tier 2: Plant → DC lanes (FG, per item)
    # FG001-FG005 made at Baddi; FG006-FG010 made at Pune (split by capacity)
    fg_plant = {f"FG00{i}":"PLANT_BDI" for i in range(1,6)}
    fg_plant.update({f"FG0{i:02d}":"PLANT_PUN" for i in range(6,11)})
    dcs = ["DC_DEL","DC_MUM","DC_BLR"]
    dc_modes = {"DC_DEL":"ROAD","DC_MUM":"ROAD","DC_BLR":"ROAD"}
    dc_lt   = {"DC_DEL":3,"DC_MUM":4,"DC_BLR":5}   # Baddi-origin lead times
    dc_lt_p = {"DC_DEL":5,"DC_MUM":2,"DC_BLR":3}   # Pune-origin lead times
    for fg,plant in fg_plant.items():
        lt_map = dc_lt if plant=="PLANT_BDI" else dc_lt_p
        for dc in dcs:
            rows.append([
                TENANT_ID, f"LANE_{plant.replace('PLANT_','')}_{dc}_{fg}",
                plant, dc, fg, dc_modes[dc], lt_map[dc], 50, "ea", None
            ])
    for row in sup_plant_lanes:
        rows.append([TENANT_ID] + list(row))
    return rows

if __name__ == "__main__":
    main()
