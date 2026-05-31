"""
Pravah — Dataset Validation Suite
=================================
Asserts the generated dataset is INTERNALLY CONSISTENT before any engine reads it.
If any check fails, downstream planning would be garbage — so we fail loudly here.

Run:  python3 tests/test_dataset_integrity.py
Exit code 0 = all good; 1 = at least one failure.
"""
import os
import csv
import sys
from collections import defaultdict

DATA = os.path.join(os.path.dirname(__file__), "..", "datasets")

def load(name):
    with open(os.path.join(DATA, name)) as f:
        return list(csv.DictReader(f))

checks = []
def check(name, condition, detail=""):
    checks.append((name, bool(condition), detail))

# ---- load everything ----
items   = load("items.csv")
locs    = load("locations.csv")
sups    = load("suppliers.csv")
res     = load("resources.csv")
modes   = load("transport_modes.csv")
bom     = load("bom.csv")
routing = load("routing.csv")
sim     = load("supplier_item_mapping.csv")
demand  = load("demand_history.csv")
inv     = load("inventory.csv")
pos     = load("purchase_orders.csv")
pros    = load("production_orders.csv")
sos     = load("sales_orders.csv")
svc     = load("service_levels.csv")
costs   = load("costs.csv")
cons    = load("constraints.csv")

item_codes = {r["item_code"] for r in items}
loc_codes  = {r["location_code"] for r in locs}
sup_codes  = {r["supplier_code"] for r in sups}
res_codes  = {r["resource_code"] for r in res}
fg_codes   = {r["item_code"] for r in items if r["item_type"] == "FG"}
rm_codes   = {r["item_code"] for r in items if r["item_type"] == "RM"}
pm_codes   = {r["item_code"] for r in items if r["item_type"] == "PM"}
sfg_codes  = {r["item_code"] for r in items if r["item_type"] == "SFG"}

# ---- 1. portfolio counts match the brief ----
check("10 finished goods", len(fg_codes) == 10, f"got {len(fg_codes)}")
check("20 raw materials",  len(rm_codes) == 20, f"got {len(rm_codes)}")
check("5 packaging mats",  len(pm_codes) == 5,  f"got {len(pm_codes)}")
check("2 semi-finished",   len(sfg_codes) == 2, f"got {len(sfg_codes)}")

# ---- 2. every tenant_id present and uniform ----
all_rows = items+locs+sups+res+modes+bom+routing+sim+demand+inv+pos+pros+sos+svc+costs+cons
tenants = {r["tenant_id"] for r in all_rows}
check("single tenant_id, present everywhere", tenants == {"apex"}, str(tenants))

# ---- 3. BOM referential integrity: parents and components are real items ----
bad_parents = {r["parent_item"] for r in bom if r["parent_item"] not in item_codes}
bad_comps   = {r["component_item"] for r in bom if r["component_item"] not in item_codes}
check("BOM parents are real items", not bad_parents, str(bad_parents))
check("BOM components are real items", not bad_comps, str(bad_comps))

# ---- 4. every FG has a BOM (can be exploded) ----
bom_parents = {r["parent_item"] for r in bom}
fg_without_bom = fg_codes - bom_parents
check("every FG has a BOM", not fg_without_bom, str(fg_without_bom))

# ---- 5. every SFG used in a BOM also has its own BOM (multi-level closes) ----
sfg_used = {r["component_item"] for r in bom if r["component_item"] in sfg_codes}
sfg_without_bom = sfg_used - bom_parents
check("every used SFG has its own BOM", not sfg_without_bom, str(sfg_without_bom))

# ---- 6. BOM has no cycles (simple DFS) ----
graph = defaultdict(list)
for r in bom:
    graph[r["parent_item"]].append(r["component_item"])
def has_cycle():
    WHITE, GREY, BLACK = 0,1,2
    color = defaultdict(int)
    def dfs(u):
        color[u] = GREY
        for v in graph[u]:
            if color[v] == GREY: return True
            if color[v] == WHITE and dfs(v): return True
        color[u] = BLACK
        return False
    return any(color[n]==0 and dfs(n) for n in list(graph))
check("BOM is acyclic", not has_cycle())

# ---- 7. routing references real items + real resources ----
bad_r_items = {r["item_code"] for r in routing if r["item_code"] not in item_codes}
bad_r_res   = {r["resource_code"] for r in routing if r["resource_code"] not in res_codes}
check("routing items are real", not bad_r_items, str(bad_r_items))
check("routing resources are real", not bad_r_res, str(bad_r_res))

# ---- 8. every FG is routed (has at least one resource step) ----
routed = {r["item_code"] for r in routing}
fg_not_routed = fg_codes - routed
check("every FG is routed", not fg_not_routed, str(fg_not_routed))

# ---- 9. supplier_item_mapping integrity + every RM/PM is sourceable ----
bad_sim_sup = {r["supplier_code"] for r in sim if r["supplier_code"] not in sup_codes}
bad_sim_itm = {r["item_code"] for r in sim if r["item_code"] not in item_codes}
check("SIM suppliers real", not bad_sim_sup, str(bad_sim_sup))
check("SIM items real", not bad_sim_itm, str(bad_sim_itm))
sourceable = {r["item_code"] for r in sim}
buy_items = rm_codes | pm_codes
unsourced = buy_items - sourceable
check("every RM and PM is sourceable", not unsourced, str(unsourced))

# ---- 10. demand history completeness: every FG x DC x N months ----
dcs = {r["location_code"] for r in locs if r["location_type"] == "DC"}
demand_keys = defaultdict(set)
for r in demand:
    demand_keys[(r["item_code"], r["location_code"])].add(r["period"])
# infer N = number of distinct periods present (should be uniform)
period_counts = {len(v) for v in demand_keys.values()}
N = max(period_counts) if period_counts else 0
missing = []
for fg in fg_codes:
    for dc in dcs:
        if len(demand_keys[(fg, dc)]) != N:
            missing.append((fg, dc, len(demand_keys[(fg,dc)])))
check(f"demand history complete (FGxDCx{N})", not missing and len(period_counts) == 1, str(missing[:5]))

# ---- 11. no negative or non-numeric demand ----
bad_demand = []
for r in demand:
    try:
        q = float(r["quantity"])
        if q < 0: bad_demand.append(r)
    except ValueError:
        bad_demand.append(r)
check("demand quantities valid (>=0, numeric)", not bad_demand, f"{len(bad_demand)} bad")

# ---- 12. inventory references real items + real locations ----
bad_inv_i = {r["item_code"] for r in inv if r["item_code"] not in item_codes}
bad_inv_l = {r["location_code"] for r in inv if r["location_code"] not in loc_codes}
check("inventory items real", not bad_inv_i, str(bad_inv_i))
check("inventory locations real", not bad_inv_l, str(bad_inv_l))

# ---- 13. orders reference real items/locations/suppliers ----
check("PO items real", all(r["item_code"] in item_codes for r in pos))
check("PO suppliers real", all(r["supplier_code"] in sup_codes for r in pos))
check("ProdOrder items are FG", all(r["item_code"] in fg_codes for r in pros))
check("SO items are FG", all(r["item_code"] in fg_codes for r in sos))
check("SO locations are DCs", all(r["location_code"] in dcs for r in sos))

# ---- 14. parameters cover every FG ----
check("service level per FG", {r["item_code"] for r in svc} >= fg_codes)
check("constraints per FG", {r["item_code"] for r in cons} >= fg_codes)
fg_costed = {r["item_code"] for r in costs}
check("production cost per FG", fg_codes <= fg_costed)

# ---- 15. resources belong to real plants ----
plants = {r["location_code"] for r in locs if r["location_type"] == "Plant"}
check("resources map to real plants", all(r["plant_code"] in plants for r in res))

# ---- report ----
passed = sum(1 for _,ok,_ in checks if ok)
total = len(checks)
print(f"\nDATASET INTEGRITY: {passed}/{total} checks passed\n" + "-"*50)
failed = False
for name, ok, detail in checks:
    flag = "PASS" if ok else "FAIL"
    line = f"[{flag}] {name}"
    if not ok:
        line += f"  -> {detail}"
        failed = True
    print(line)

sys.exit(1 if failed else 0)
