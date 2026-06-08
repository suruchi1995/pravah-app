"""
Pravah — Database schema (SQLAlchemy 2.0, Postgres-first, SQLite-runnable)
=========================================================================
Every table carries tenant_id + created_at + updated_at.

Two groups:
  1. SOURCE tables  — mirror the generated CSVs (master / network / transactions / params)
  2. OUTPUT tables  — written by the planning engines (segmentation, forecast, ... , plans)

The same models run on Postgres (Neon) and SQLite (local tests). We avoid
Postgres-only types so the schema is portable; on Neon it deploys unchanged.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, String, Integer, Float, Date, DateTime, ForeignKey, Index, text
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TenantMixin:
    """Every row is tenant-scoped and timestamped."""
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, default="apex")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


# ----------------------------------------------------------------------------
# 1. SOURCE TABLES (mirror CSVs)
# ----------------------------------------------------------------------------
class Item(TenantMixin, Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    description: Mapped[str] = mapped_column(String(128))
    item_type: Mapped[str] = mapped_column(String(8))     # FG/SFG/RM/PM
    category: Mapped[str] = mapped_column(String(32))
    uom: Mapped[str] = mapped_column(String(8))
    unit_price_or_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    expiry_days: Mapped[int | None] = mapped_column(Integer, nullable=True)  # shelf life; null = non-perishable


class Location(TenantMixin, Base):
    __tablename__ = "locations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_code: Mapped[str] = mapped_column(String(32), index=True)
    location_name: Mapped[str] = mapped_column(String(64))
    location_type: Mapped[str] = mapped_column(String(16))   # Plant/DC
    state: Mapped[str] = mapped_column(String(48))
    zone: Mapped[str] = mapped_column(String(16))


class Supplier(TenantMixin, Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_code: Mapped[str] = mapped_column(String(32), index=True)
    supplier_name: Mapped[str] = mapped_column(String(64))
    supplier_type: Mapped[str] = mapped_column(String(16))
    lead_time_days: Mapped[int] = mapped_column(Integer)
    moq: Mapped[int] = mapped_column(Integer)
    reliability: Mapped[float] = mapped_column(Float)
    incoterm: Mapped[str] = mapped_column(String(8))
    payment_terms: Mapped[str] = mapped_column(String(16))


class Resource(TenantMixin, Base):
    __tablename__ = "resources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resource_code: Mapped[str] = mapped_column(String(32), index=True)
    resource_name: Mapped[str] = mapped_column(String(64))
    plant_code: Mapped[str] = mapped_column(String(32))
    hours_per_month: Mapped[float] = mapped_column(Float)


class TransportMode(TenantMixin, Base):
    __tablename__ = "transport_modes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mode_code: Mapped[str] = mapped_column(String(16), index=True)
    mode_name: Mapped[str] = mapped_column(String(32))
    lead_time_days: Mapped[int] = mapped_column(Integer)
    cost_per_kg: Mapped[float] = mapped_column(Float)


class Bom(TenantMixin, Base):
    __tablename__ = "bom"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_item: Mapped[str] = mapped_column(String(32), index=True)
    component_item: Mapped[str] = mapped_column(String(32), index=True)
    usage_qty: Mapped[float] = mapped_column(Float)


class Routing(TenantMixin, Base):
    __tablename__ = "routing"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    resource_code: Mapped[str] = mapped_column(String(32), index=True)
    runtime_hr_per_unit: Mapped[float] = mapped_column(Float)


class SupplierItemMapping(TenantMixin, Base):
    __tablename__ = "supplier_item_mapping"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_code: Mapped[str] = mapped_column(String(32), index=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    unit_price: Mapped[float] = mapped_column(Float)
    moq: Mapped[int] = mapped_column(Integer)
    lead_time_days: Mapped[int] = mapped_column(Integer)


class DemandHistory(TenantMixin, Base):
    __tablename__ = "demand_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    location_code: Mapped[str] = mapped_column(String(32), index=True)
    period: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD (1st)
    quantity: Mapped[float] = mapped_column(Float)


class Inventory(TenantMixin, Base):
    __tablename__ = "inventory"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    location_code: Mapped[str] = mapped_column(String(32), index=True)
    on_hand_qty: Mapped[float] = mapped_column(Float)


class PurchaseOrder(TenantMixin, Base):
    __tablename__ = "purchase_orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    po_number: Mapped[str] = mapped_column(String(16), index=True)
    supplier_code: Mapped[str] = mapped_column(String(32))
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    expected_receipt: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(16))


class ProductionOrder(TenantMixin, Base):
    __tablename__ = "production_orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pro_number: Mapped[str] = mapped_column(String(16), index=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    plant_code: Mapped[str] = mapped_column(String(32))
    quantity: Mapped[float] = mapped_column(Float)
    expected_completion: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(16))


class SalesOrder(TenantMixin, Base):
    __tablename__ = "sales_orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    so_number: Mapped[str] = mapped_column(String(16), index=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    location_code: Mapped[str] = mapped_column(String(32), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    required_date: Mapped[str] = mapped_column(String(10))
    priority: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(16))


class ServiceLevel(TenantMixin, Base):
    __tablename__ = "service_levels"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    target_service_level: Mapped[float] = mapped_column(Float)


class Cost(TenantMixin, Base):
    __tablename__ = "costs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    production_cost: Mapped[float] = mapped_column(Float)
    holding_cost_pct_month: Mapped[float] = mapped_column(Float)


class Constraint(TenantMixin, Base):
    __tablename__ = "constraints"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    min_months_cover: Mapped[float] = mapped_column(Float)
    max_months_cover: Mapped[float] = mapped_column(Float)


# ----------------------------------------------------------------------------
# 2. OUTPUT TABLES (written by engines)
# ----------------------------------------------------------------------------
class ProductSegmentation(TenantMixin, Base):
    __tablename__ = "product_segmentation"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    location_code: Mapped[str] = mapped_column(String(32), default="ALL", index=True)
    abc_class: Mapped[str] = mapped_column(String(4))
    xyz_class: Mapped[str] = mapped_column(String(4))
    abc_xyz: Mapped[str] = mapped_column(String(8))
    annual_value: Mapped[float] = mapped_column(Float)
    cov: Mapped[float] = mapped_column(Float)
    supply_ci: Mapped[str] = mapped_column(String(8), default="LOW")
    avg_fill_rate: Mapped[float] = mapped_column(Float, default=1.0)
    supplier_reliability: Mapped[float] = mapped_column(Float, default=1.0)
    reasoning: Mapped[str] = mapped_column(String())


class ForecastOutput(TenantMixin, Base):
    __tablename__ = "forecast_output"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    location_code: Mapped[str] = mapped_column(String(32), index=True)
    period: Mapped[str] = mapped_column(String(10), index=True)
    forecast_qty: Mapped[float] = mapped_column(Float)
    selected_model: Mapped[str] = mapped_column(String(64))
    mape: Mapped[float] = mapped_column(Float)
    bias: Mapped[float] = mapped_column(Float)
    reasoning: Mapped[str] = mapped_column(String())


class DemandPlan(TenantMixin, Base):
    __tablename__ = "demand_plan"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    location_code: Mapped[str] = mapped_column(String(32), index=True)
    period: Mapped[str] = mapped_column(String(10), index=True)
    statistical_qty: Mapped[float] = mapped_column(Float)
    override_qty: Mapped[float | None] = mapped_column(Float, nullable=True)
    consensus_qty: Mapped[float] = mapped_column(Float)


class DemandSupplyHandshake(TenantMixin, Base):
    __tablename__ = "demand_supply_handshake"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    location_code: Mapped[str] = mapped_column(String(32), index=True)
    period: Mapped[str] = mapped_column(String(10), index=True)
    demand_qty: Mapped[float] = mapped_column(Float)
    available_supply_qty: Mapped[float] = mapped_column(Float)
    gap_qty: Mapped[float] = mapped_column(Float)
    fill_rate: Mapped[float] = mapped_column(Float)
    revenue_at_risk: Mapped[float] = mapped_column(Float)
    margin_at_risk: Mapped[float] = mapped_column(Float)
    recommendation: Mapped[str] = mapped_column(String())


class InventoryTarget(TenantMixin, Base):
    __tablename__ = "inventory_targets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    location_code: Mapped[str] = mapped_column(String(32), index=True)
    avg_monthly_demand: Mapped[float] = mapped_column(Float)
    safety_stock: Mapped[float] = mapped_column(Float)
    reorder_point: Mapped[float] = mapped_column(Float)
    target_inventory: Mapped[float] = mapped_column(Float)
    days_cover: Mapped[float] = mapped_column(Float)
    reasoning: Mapped[str] = mapped_column(String())


class NetRequirement(TenantMixin, Base):
    __tablename__ = "net_requirements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    location_code: Mapped[str] = mapped_column(String(32), index=True)
    period: Mapped[str] = mapped_column(String(10), index=True)
    gross_requirement: Mapped[float] = mapped_column(Float)
    safety_stock: Mapped[float] = mapped_column(Float)
    on_hand: Mapped[float] = mapped_column(Float)
    scheduled_receipts: Mapped[float] = mapped_column(Float)
    net_requirement: Mapped[float] = mapped_column(Float)
    planned_order: Mapped[float] = mapped_column(Float)
    reasoning: Mapped[str] = mapped_column(String())


class PlanningPriority(TenantMixin, Base):
    __tablename__ = "planning_priority"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    score: Mapped[float] = mapped_column(Float)
    rank: Mapped[int] = mapped_column(Integer)
    reasoning: Mapped[str] = mapped_column(String())


class SupplyRequirement(TenantMixin, Base):
    """MRP material explosion — dependent demand for RM/PM/SFG."""
    __tablename__ = "supply_requirements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    period: Mapped[str] = mapped_column(String(10), index=True)
    level: Mapped[int] = mapped_column(Integer)     # BOM level (0=FG)
    gross_requirement: Mapped[float] = mapped_column(Float)
    net_requirement: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(8))  # make/buy


class CapacityLoad(TenantMixin, Base):
    __tablename__ = "capacity_load"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resource_code: Mapped[str] = mapped_column(String(32), index=True)
    period: Mapped[str] = mapped_column(String(10), index=True)
    load_hours: Mapped[float] = mapped_column(Float)
    available_hours: Mapped[float] = mapped_column(Float)
    utilization: Mapped[float] = mapped_column(Float)
    constraint_status: Mapped[str] = mapped_column(String(16))


class ProductionPlan(TenantMixin, Base):
    __tablename__ = "production_plan"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    period: Mapped[str] = mapped_column(String(10), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    scenario: Mapped[str] = mapped_column(String(32), index=True)


class PurchasePlan(TenantMixin, Base):
    __tablename__ = "purchase_plan"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    supplier_code: Mapped[str] = mapped_column(String(32))
    period: Mapped[str] = mapped_column(String(10), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    scenario: Mapped[str] = mapped_column(String(32), index=True)


class SolverExplanation(TenantMixin, Base):
    __tablename__ = "solver_explanations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario: Mapped[str] = mapped_column(String(32), index=True)
    objective: Mapped[str] = mapped_column(String())
    objective_value: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32))
    reasoning: Mapped[str] = mapped_column(String())


class UomConversion(TenantMixin, Base):
    """Unit-of-measure conversion table. Seeded with standard conversions;
    clients can add their own in the upload template.
    factor: multiply qty in from_uom by factor to get qty in to_uom."""
    __tablename__ = "uom_conversions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_uom: Mapped[str] = mapped_column(String(16), index=True)
    to_uom: Mapped[str] = mapped_column(String(16), index=True)
    factor: Mapped[float] = mapped_column(Float)
    notes: Mapped[str] = mapped_column(String(), default="")


class SupplyLane(TenantMixin, Base):
    """Origin → destination lane for an item (or all items if item_code is null).
    Captures: who ships what, from where, to where, via which mode, how fast, min lot.
    This is the explicit item-location association that was previously missing.
    """
    __tablename__ = "supply_lanes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lane_code: Mapped[str] = mapped_column(String(64), index=True)
    from_location: Mapped[str] = mapped_column(String(32), index=True)   # supplier_code or location_code
    to_location: Mapped[str] = mapped_column(String(32), index=True)     # plant or DC location_code
    item_code: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)  # None = applies to all
    transport_mode: Mapped[str] = mapped_column(String(32), default="ROAD")
    lead_time_days: Mapped[float] = mapped_column(Float)
    min_lot_size: Mapped[float] = mapped_column(Float, default=0.0)
    min_lot_uom: Mapped[str] = mapped_column(String(16), default="")
    cost_per_unit: Mapped[float | None] = mapped_column(Float, nullable=True)


class DemandOverride(TenantMixin, Base):
    """Planner/data-driven demand adjustments. Source of the override (UI or upload),
    so NOTHING is hardcoded. consensus uses these when present.
    override_type: 'absolute' (set qty directly) or 'uplift_pct' (e.g. 25 = +25% on forecast)."""
    __tablename__ = "demand_overrides"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(32), index=True)
    location_code: Mapped[str] = mapped_column(String(32), index=True)
    period: Mapped[str] = mapped_column(String(10), index=True)
    override_qty: Mapped[float] = mapped_column(Float)
    override_type: Mapped[str] = mapped_column(String(12), default="absolute")
    reason: Mapped[str] = mapped_column(String(), default="")
    source: Mapped[str] = mapped_column(String(12), default="planner")  # planner | upload


class Parameter(TenantMixin, Base):
    """Every tunable value lives here as DATA, never hardcoded.
    source: 'client' (uploaded) | 'derived' (computed w/ assumption) | 'planner' (UI override).
    scope: 'global' or an item_code / resource_code the parameter applies to.
    assumption: human-readable note shown in the UI when source='derived'.
    """
    __tablename__ = "parameters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), index=True)     # e.g. forecast_holdout, holding_cost_pct
    scope: Mapped[str] = mapped_column(String(48), default="global", index=True)
    value: Mapped[str] = mapped_column(String())                  # stored as text, cast on read
    value_type: Mapped[str] = mapped_column(String(12), default="float")  # float/int/str/bool
    source: Mapped[str] = mapped_column(String(12), default="derived")
    assumption: Mapped[str] = mapped_column(String(), default="")
    editable: Mapped[bool] = mapped_column(default=True)


# ----------------------------------------------------------------------------
# AUTH / TENANCY / WORKFLOW
# ----------------------------------------------------------------------------
class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    email: Mapped[str] = mapped_column(String(160), index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)  # reserved for later
    password_hash: Mapped[str] = mapped_column(String(256))
    full_name: Mapped[str] = mapped_column(String(128))
    roles_csv: Mapped[str] = mapped_column(String(256), default="viewer")  # e.g. "planner,approver"
    is_active: Mapped[bool] = mapped_column(default=True)
    must_change_password: Mapped[bool] = mapped_column(default=False)  # forced on first login after admin-create/reset
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    @property
    def roles(self) -> list[str]:
        return [r.strip() for r in self.roles_csv.split(",") if r.strip()]


class ChangeRequest(TenantMixin, Base):
    __tablename__ = "change_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requested_by: Mapped[str] = mapped_column(String(160))      # user email
    change_type: Mapped[str] = mapped_column(String(32))        # demand_override | parameter
    target: Mapped[str] = mapped_column(String(256))            # human-readable target
    payload_json: Mapped[str] = mapped_column(String())         # the proposed change, as JSON
    old_value: Mapped[str] = mapped_column(String(), default="")
    new_value: Mapped[str] = mapped_column(String(), default="")
    status: Mapped[str] = mapped_column(String(16), default="submitted")  # submitted|approved|rejected
    reviewed_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    review_note: Mapped[str] = mapped_column(String(), default="")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuditLog(TenantMixin, Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_email: Mapped[str] = mapped_column(String(160))
    action: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str] = mapped_column(String(), default="")


# ----------------------------------------------------------------------------
# Engine / session factory
# ----------------------------------------------------------------------------
def make_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


def make_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def init_db(engine):
    Base.metadata.create_all(engine)
