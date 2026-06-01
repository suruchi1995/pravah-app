"""
Pravah — Data Contract
======================
Defines what a client upload MUST contain, what is OPTIONAL (auto-defaulted),
and the column schema for each sheet. The validator and the template generator
both import from here so they can never drift apart.

REQUIRED sheets: data a real manufacturer genuinely has in their ERP/purchasing.
OPTIONAL sheets: if absent, we generate documented defaults (flagged as assumptions).
"""

# sheet -> {required: bool, columns: [..], key_cols: [..], numeric_cols: [..]}
CONTRACT = {
    "items": {
        "required": True,
        "columns": ["item_code", "description", "item_type", "category", "uom", "unit_price_or_cost"],
        "key_cols": ["item_code"],
        "numeric_cols": ["unit_price_or_cost"],
        "nullable_numeric": ["unit_price_or_cost"],  # SFG/intermediates may have blank price
        "enums": {"item_type": ["FG", "SFG", "RM", "PM"]},
    },
    "locations": {
        "required": True,
        "columns": ["location_code", "location_name", "location_type", "state", "zone"],
        "key_cols": ["location_code"],
        "numeric_cols": [],
        "enums": {"location_type": ["Plant", "DC"]},
    },
    "suppliers": {
        "required": True,
        "columns": ["supplier_code", "supplier_name", "supplier_type", "lead_time_days",
                    "moq", "reliability", "incoterm", "payment_terms"],
        "key_cols": ["supplier_code"],
        "numeric_cols": ["lead_time_days", "moq", "reliability"],
        "enums": {},
    },
    "bom": {
        "required": True,
        "columns": ["parent_item", "component_item", "usage_qty"],
        "key_cols": ["parent_item", "component_item"],
        "numeric_cols": ["usage_qty"],
        "fk": {"parent_item": "items.item_code", "component_item": "items.item_code"},
    },
    "demand_history": {
        "required": True,
        "columns": ["item_code", "location_code", "period", "quantity"],
        "key_cols": ["item_code", "location_code", "period"],
        "numeric_cols": ["quantity"],
        "fk": {"item_code": "items.item_code", "location_code": "locations.location_code"},
    },
    "inventory": {
        "required": True,
        "columns": ["item_code", "location_code", "on_hand_qty"],
        "key_cols": ["item_code", "location_code"],
        "numeric_cols": ["on_hand_qty"],
        "fk": {"item_code": "items.item_code", "location_code": "locations.location_code"},
    },
    "supplier_item_mapping": {
        "required": True,
        "columns": ["supplier_code", "item_code", "unit_price", "moq", "lead_time_days"],
        "key_cols": ["supplier_code", "item_code"],
        "numeric_cols": ["unit_price", "moq", "lead_time_days"],
        "fk": {"supplier_code": "suppliers.supplier_code", "item_code": "items.item_code"},
    },
    # -------- strongly recommended: real constraints (used if given, NEVER faked) --------
    # If absent, capacity planning + constrained optimization are DISABLED and flagged,
    # rather than invented. Everything upstream still runs.
    "resources": {
        "required": False,
        "recommended": True,
        "columns": ["resource_code", "resource_name", "plant_code", "hours_per_month"],
        "key_cols": ["resource_code"], "numeric_cols": ["hours_per_month"],
    },
    "routing": {
        "required": False,
        "recommended": True,
        "columns": ["item_code", "resource_code", "runtime_hr_per_unit"],
        "key_cols": ["item_code", "resource_code"], "numeric_cols": ["runtime_hr_per_unit"],
    },
    "transport_modes": {
        "required": False,
        "columns": ["mode_code", "mode_name", "lead_time_days", "cost_per_kg"],
        "key_cols": ["mode_code"], "numeric_cols": ["lead_time_days", "cost_per_kg"],
    },
    "service_levels": {
        "required": False,
        "columns": ["item_code", "target_service_level"],
        "key_cols": ["item_code"], "numeric_cols": ["target_service_level"],
    },
    "costs": {
        "required": False,
        "columns": ["item_code", "production_cost", "holding_cost_pct_month"],
        "key_cols": ["item_code"], "numeric_cols": ["production_cost", "holding_cost_pct_month"],
    },
    "constraints": {
        "required": False,
        "columns": ["item_code", "min_months_cover", "max_months_cover"],
        "key_cols": ["item_code"], "numeric_cols": ["min_months_cover", "max_months_cover"],
    },
    "demand_overrides": {
        "required": False,
        "columns": ["item_code", "location_code", "period", "override_qty", "override_type", "reason", "source"],
        "key_cols": ["item_code", "location_code", "period"], "numeric_cols": ["override_qty"],
    },
    "purchase_orders": {
        "required": False,
        "columns": ["po_number", "supplier_code", "item_code", "quantity", "expected_receipt", "status"],
        "key_cols": ["po_number"], "numeric_cols": ["quantity"],
    },
    "production_orders": {
        "required": False,
        "columns": ["pro_number", "item_code", "plant_code", "quantity", "expected_completion", "status"],
        "key_cols": ["pro_number"], "numeric_cols": ["quantity"],
    },
    "sales_orders": {
        "required": False,
        "columns": ["so_number", "item_code", "location_code", "quantity", "required_date", "priority", "status"],
        "key_cols": ["so_number"], "numeric_cols": ["quantity"],
    },
}

REQUIRED_SHEETS = [s for s, c in CONTRACT.items() if c["required"]]
OPTIONAL_SHEETS = [s for s, c in CONTRACT.items() if not c["required"]]

DEFAULTS_DOC = {
    "service_levels": "If absent: A=98%, B=95%, C=90% by ABC class (computed after segmentation).",
    "costs": "If absent: production_cost = 50% of unit price; holding = 2%/month.",
    "constraints": "If absent: min 0.5, max 3.0 months of cover.",
    "resources": "If absent: a single default line with ample capacity; capacity planning becomes non-binding.",
    "routing": "If absent: nominal runtime per unit so capacity load is computed but rarely binds.",
    "transport_modes": "If absent: Road (4d) + Air (1d) defaults.",
    "purchase_orders": "If absent: treated as none open.",
    "production_orders": "If absent: treated as none open.",
    "sales_orders": "If absent: treated as none open.",
}
