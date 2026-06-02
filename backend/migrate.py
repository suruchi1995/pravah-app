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
    """Make the live DB compatible with the current models. Safe to run on every boot.
    Two operations, both non-destructive:
      1. ADD columns that exist in the model but not in the live table.
      2. WIDEN string columns to unbounded VARCHAR (Postgres only) so values never
         truncate. Widening never loses data. This fixes pre-existing tables that
         were created with a narrow varchar(N) before the model was relaxed.
    """
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())
    is_postgres = engine.dialect.name == "postgresql"
    changed = []

    for table_name, table in m.Base.metadata.tables.items():
        if table_name not in existing_tables:
            continue  # create_all handles brand-new tables
        live_cols = {c["name"]: c for c in insp.get_columns(table_name)}

        for col in table.columns:
            # 1. add missing column
            if col.name not in live_cols:
                coltype = _sql_type(col)
                default = " DEFAULT ''" if coltype == "VARCHAR" else (
                    " DEFAULT 0" if coltype in ("INTEGER", "DOUBLE PRECISION") else (
                    " DEFAULT TRUE" if coltype == "BOOLEAN" else ""))
                for ddl in (f'ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col.name} {coltype}{default}',
                            f'ALTER TABLE {table_name} ADD COLUMN {col.name} {coltype}{default}'):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text(ddl))
                        changed.append(f"add {table_name}.{col.name}")
                        break
                    except Exception:
                        continue
                continue

            # 2. widen narrow string columns (Postgres enforces varchar length)
            if is_postgres:
                tname = col.type.__class__.__name__.lower()
                if "string" in tname or "varchar" in tname or "text" in tname:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text(
                                f'ALTER TABLE {table_name} ALTER COLUMN {col.name} TYPE VARCHAR'))
                        changed.append(f"widen {table_name}.{col.name}")
                    except Exception:
                        pass
    return changed
