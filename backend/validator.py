"""
Upload Validator — strict gate for client Excel uploads.

Input:  dict {sheet_name: pandas.DataFrame}
Output: {"ok": bool, "errors": [..], "warnings": [..], "summary": {..}}

Hard errors (block the upload):
  - a required sheet is missing
  - a required column is missing
  - a foreign-key value references a non-existent master record
  - duplicate keys
  - non-numeric value in a numeric column
  - invalid enum value
  - BOM has a cycle, or an FG without a BOM
  - demand history not complete (every FG x DC needs the same set of periods)

Soft warnings (don't block; defaults will fill):
  - an optional sheet is missing (we note which default applies)
"""
import math
from collections import defaultdict, deque
from backend.data_contract import CONTRACT, REQUIRED_SHEETS, OPTIONAL_SHEETS, DEFAULTS_DOC


def _is_number(x):
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return False
        float(x)
        return True
    except (ValueError, TypeError):
        return False


def validate(sheets: dict) -> dict:
    errors, warnings = [], []

    def err(sheet, row, msg):
        errors.append({"sheet": sheet, "row": row, "message": msg})

    def warn(sheet, msg):
        warnings.append({"sheet": sheet, "message": msg})

    # normalize: lower-case sheet names
    sheets = {k.strip(): v for k, v in sheets.items()}

    # 1. required sheets present
    for s in REQUIRED_SHEETS:
        if s not in sheets:
            err(s, None, f"Required sheet '{s}' is missing.")
    # 2. optional sheets -> warnings
    for s in OPTIONAL_SHEETS:
        if s not in sheets:
            warn(s, DEFAULTS_DOC.get(s, f"Optional sheet '{s}' absent; defaults applied."))

    # if any required sheet missing, stop early (FK checks would cascade)
    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings,
                "summary": {"sheets_received": list(sheets.keys())}}

    # build master key sets for FK checks
    masters = {}
    for s, df in sheets.items():
        spec = CONTRACT.get(s)
        if not spec:
            warn(s, f"Unknown sheet '{s}' ignored.")
            continue

    # 3. per-sheet structural checks
    for s, df in sheets.items():
        spec = CONTRACT.get(s)
        if not spec:
            continue
        cols = list(df.columns)
        # required columns
        for c in spec["columns"]:
            if c not in cols:
                err(s, None, f"Missing column '{c}'. Expected: {spec['columns']}")
        # if columns missing, skip row checks for this sheet
        if any(c not in cols for c in spec["columns"]):
            continue
        # numeric columns (blanks allowed only where contract marks nullable)
        nullable = set(spec.get("nullable_numeric", []))
        for c in spec.get("numeric_cols", []):
            for ridx, val in df[c].items():
                is_blank = val is None or (isinstance(val, float) and math.isnan(val)) or str(val).strip() == ""
                if is_blank:
                    if c not in nullable:
                        err(s, int(ridx) + 2, f"Column '{c}' is required (blank not allowed).")
                    continue
                if not _is_number(val):
                    err(s, int(ridx) + 2, f"Column '{c}' must be numeric, got '{val}'.")
        # enums
        for c, allowed in spec.get("enums", {}).items():
            for ridx, val in df[c].items():
                if str(val).strip() not in allowed:
                    err(s, int(ridx) + 2, f"Column '{c}' must be one of {allowed}, got '{val}'.")
        # duplicate keys
        kc = spec.get("key_cols", [])
        if kc and all(c in cols for c in kc):
            seen = set()
            for ridx, row in df.iterrows():
                key = tuple(str(row[c]) for c in kc)
                if key in seen:
                    err(s, int(ridx) + 2, f"Duplicate key {kc}={key}.")
                seen.add(key)

    # collect master codes (after structural pass; only if sheets present)
    item_codes = set(sheets["items"]["item_code"].astype(str)) if "items" in sheets else set()
    loc_codes = set(sheets["locations"]["location_code"].astype(str)) if "locations" in sheets else set()
    sup_codes = set(sheets["suppliers"]["supplier_code"].astype(str)) if "suppliers" in sheets else set()
    master_lookup = {"items.item_code": item_codes,
                     "locations.location_code": loc_codes,
                     "suppliers.supplier_code": sup_codes}

    # 4. foreign-key checks
    for s, df in sheets.items():
        spec = CONTRACT.get(s)
        if not spec or "fk" not in spec:
            continue
        for col, target in spec["fk"].items():
            if col not in df.columns:
                continue
            valid = master_lookup.get(target, set())
            for ridx, val in df[col].items():
                if str(val) not in valid:
                    err(s, int(ridx) + 2, f"'{col}'='{val}' not found in {target}.")

    # 5. BOM closure + acyclicity + every FG has a BOM
    if "items" in sheets and "bom" in sheets:
        fg = set(sheets["items"].loc[sheets["items"]["item_type"] == "FG", "item_code"].astype(str))
        bom = sheets["bom"]
        bom_parents = set(bom["parent_item"].astype(str))
        for f in fg - bom_parents:
            err("bom", None, f"Finished good '{f}' has no BOM (cannot be exploded).")
        # cycle check
        graph = defaultdict(list)
        for _, r in bom.iterrows():
            graph[str(r["parent_item"])].append(str(r["component_item"]))
        color = defaultdict(int)
        def dfs(u):
            color[u] = 1
            for v in graph[u]:
                if color[v] == 1: return True
                if color[v] == 0 and dfs(v): return True
            color[u] = 2
            return False
        if any(color[n] == 0 and dfs(n) for n in list(graph)):
            err("bom", None, "BOM contains a cycle (an item depends on itself).")

    # 6. demand completeness: every FG x DC has the same set of periods
    if "demand_history" in sheets and "items" in sheets and "locations" in sheets:
        dh = sheets["demand_history"]
        fg = set(sheets["items"].loc[sheets["items"]["item_type"] == "FG", "item_code"].astype(str))
        dcs = set(sheets["locations"].loc[sheets["locations"]["location_type"] == "DC", "location_code"].astype(str))
        keyper = defaultdict(set)
        for _, r in dh.iterrows():
            keyper[(str(r["item_code"]), str(r["location_code"]))].add(str(r["period"]))
        period_counts = {len(v) for v in keyper.values()}
        if len(period_counts) > 1:
            err("demand_history", None,
                f"Inconsistent history length across FG x DC (period counts: {sorted(period_counts)}). "
                "Every FG/DC pair must have the same months.")
        for f in fg:
            for dc in dcs:
                if (f, dc) not in keyper:
                    err("demand_history", None, f"No demand history for FG '{f}' at DC '{dc}'.")

    ok = len(errors) == 0
    summary = {
        "sheets_received": list(sheets.keys()),
        "required_present": [s for s in REQUIRED_SHEETS if s in sheets],
        "optional_present": [s for s in OPTIONAL_SHEETS if s in sheets],
        "error_count": len(errors),
        "warning_count": len(warnings),
    }
    return {"ok": ok, "errors": errors, "warnings": warnings, "summary": summary}
