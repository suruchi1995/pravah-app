"""
Lightweight schema reconciliation.
=================================
SQLAlchemy's create_all() creates MISSING TABLES but never alters EXISTING ones
to add new columns. When we add a column to a model (e.g. demand_overrides.override_type)
and deploy against a database that already has the old table, queries 500.

This module, run on startup after create_all(), inspects each mapped table and
ADDs any columns that exist in the model but not in the live DB. It is conservative:
it only ADDs columns (never drops or alters types), so it is safe to run every boot.

For SQLite (local/tests) this is a no-op-ish safety net; it primarily matters for
Postgres in production.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import inspect, text
from backend import models as m


# Map SQLAlchemy column types to a portable SQL type for ALTER TABLE ADD COLUMN.
def _sql_type(col):
    t = col.type.__class__.__name__.lower()
    if "int" in t and "tinyint" not in t:
        return "INTEGER"
    if "float" in t or "numeric" in t or "real" in t:
        return "DOUBLE PRECISION"
    if "bool" in t:
        return "BOOLEAN"
    if "datetime" in t or "timestamp" in t:
        return "TIMESTAMP"
    # String / Text / everything else
    return "VARCHAR"


def reconcile_schema(engine):
    """Add any model columns missing from existing tables. Safe to run on every boot."""
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())
    added = []

    for table_name, table in m.Base.metadata.tables.items():
        if table_name not in existing_tables:
            # create_all handles brand-new tables; skip here
            continue
        live_cols = {c["name"] for c in insp.get_columns(table_name)}
        for col in table.columns:
            if col.name not in live_cols:
                coltype = _sql_type(col)
                default = ""
                # give a safe default for NOT NULL-ish additions
                if coltype == "VARCHAR":
                    default = " DEFAULT ''"
                elif coltype in ("INTEGER", "DOUBLE PRECISION"):
                    default = " DEFAULT 0"
                elif coltype == "BOOLEAN":
                    default = " DEFAULT TRUE"
                ddl = f'ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col.name} {coltype}{default}'
                try:
                    with engine.begin() as conn:
                        conn.execute(text(ddl))
                    added.append(f"{table_name}.{col.name}")
                except Exception as e:
                    # SQLite doesn't support ADD COLUMN IF NOT EXISTS; try without it
                    try:
                        with engine.begin() as conn:
                            conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {col.name} {coltype}{default}'))
                        added.append(f"{table_name}.{col.name}")
                    except Exception:
                        pass  # column likely already exists or dialect limitation
    return added
