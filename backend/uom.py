"""
UOM Conversion Engine
=====================
Converts quantities between units of measure using a conversion table.
The table is seeded with standard conversions and clients can add their own.

Rule: if a BOM component UOM doesn't match the parent's UOM, look up the
conversion and apply it. If no conversion exists, log a warning and use
the raw number (with a flag so the planner knows it's unverified).

Convention: conversions are directional (from_uom -> to_uom = multiply by factor).
The reverse is automatically derived (1/factor).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DEFAULT_TENANT

# Standard seed conversions — client can add their own in the template
STANDARD_CONVERSIONS = [
    # Weight
    ("g",   "kg",  0.001),
    ("mg",  "kg",  0.000001),
    ("ton", "kg",  1000.0),
    ("lb",  "kg",  0.453592),
    ("oz",  "kg",  0.028350),
    # Volume
    ("ml",  "L",   0.001),
    ("cl",  "L",   0.01),
    ("dl",  "L",   0.1),
    ("gal", "L",   3.78541),
    ("fl_oz", "L", 0.029574),
    # Count (ea, pcs, unit — all equivalent)
    ("pcs", "ea",  1.0),
    ("unit","ea",  1.0),
    ("pc",  "ea",  1.0),
]


def seed_conversions(session, tenant=DEFAULT_TENANT):
    """Seed standard conversions if not already present."""
    existing = {(c.from_uom, c.to_uom) for c in
                session.query(m.UomConversion).filter_by(tenant_id=tenant)}
    new = []
    for from_uom, to_uom, factor in STANDARD_CONVERSIONS:
        if (from_uom, to_uom) not in existing:
            new.append(m.UomConversion(tenant_id=tenant, from_uom=from_uom,
                                        to_uom=to_uom, factor=factor))
        # also seed the reverse if not present
        if (to_uom, from_uom) not in existing:
            new.append(m.UomConversion(tenant_id=tenant, from_uom=to_uom,
                                        to_uom=from_uom, factor=round(1/factor, 8)))
    session.bulk_save_objects(new)
    session.commit()
    return len(new)


def build_conversion_map(session, tenant=DEFAULT_TENANT):
    """Return dict {(from_uom, to_uom): factor} for fast lookup."""
    rows = session.query(m.UomConversion).filter_by(tenant_id=tenant).all()
    return {(r.from_uom, r.to_uom): r.factor for r in rows}


def convert(qty, from_uom, to_uom, conv_map):
    """Convert qty from from_uom to to_uom. Returns (converted_qty, ok, warning)."""
    if from_uom == to_uom:
        return qty, True, None
    key = (from_uom, to_uom)
    if key in conv_map:
        return qty * conv_map[key], True, None
    # try 2-step via a common base
    for mid in ("kg", "L", "ea"):
        k1 = (from_uom, mid); k2 = (mid, to_uom)
        if k1 in conv_map and k2 in conv_map:
            return qty * conv_map[k1] * conv_map[k2], True, None
    return qty, False, f"No conversion found: {from_uom} → {to_uom}. Using raw value."
