"""Validator tests — clean Apex passes; deliberately broken data fails with clear errors."""
import os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.validator import validate

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets")

def load_sheets():
    sheets = {}
    for f in os.listdir(DATA):
        if f.endswith(".csv"):
            df = pd.read_csv(os.path.join(DATA, f), dtype=object)  # object dtype so we can inject bad values
            df = df.drop(columns=[c for c in ["tenant_id", "created_at", "updated_at"] if c in df.columns])
            sheets[f[:-4]] = df
    return sheets

checks = []
def check(name, cond, detail=""):
    checks.append((name, bool(cond), detail))

# 1. clean data passes
clean = load_sheets()
r = validate(clean)
check("clean Apex data passes", r["ok"], str(r["errors"][:3]))

# 2. missing required sheet
b = load_sheets(); del b["inventory"]
r = validate(b)
check("missing required sheet rejected", not r["ok"] and any("inventory" in e["message"] for e in r["errors"]))

# 3. dangling BOM FK
b = load_sheets()
bom = b["bom"]
bom.loc[len(bom)] = {"parent_item": "FG001", "component_item": "RM999", "usage_qty": "2"}
r = validate(b)
check("dangling BOM reference rejected", not r["ok"] and any("RM999" in e["message"] for e in r["errors"]))

# 4. non-numeric in numeric column
b = load_sheets()
b["bom"].iloc[0, b["bom"].columns.get_loc("usage_qty")] = "abc"
r = validate(b)
check("non-numeric usage_qty rejected", not r["ok"] and any("numeric" in e["message"] for e in r["errors"]))

# 5. invalid enum
b = load_sheets()
b["items"].iloc[0, b["items"].columns.get_loc("item_type")] = "WIDGET"
r = validate(b)
check("invalid item_type enum rejected", not r["ok"] and any("item_type" in e["message"] for e in r["errors"]))

# 6. incomplete demand history (drop one FG/DC's rows)
b = load_sheets()
dh = b["demand_history"]
b["demand_history"] = dh[~((dh["item_code"] == "FG001") & (dh["location_code"] == "DC_DEL"))]
r = validate(b)
check("incomplete demand history rejected", not r["ok"] and any("FG001" in e["message"] for e in r["errors"]))

# 7. optional sheet missing -> warning not error (transport_modes is still optional)
b = load_sheets(); del b["transport_modes"]
r = validate(b)
check("missing optional sheet -> warning only", r["ok"] and any(w["sheet"] == "transport_modes" for w in r["warnings"]))

passed = sum(1 for _, ok, _ in checks if ok)
print(f"\nVALIDATOR TESTS: {passed}/{len(checks)} passed\n" + "-"*50)
failed = False
for name, ok, detail in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  -> {detail}" if not ok else ""))
    if not ok: failed = True
sys.exit(1 if failed else 0)
