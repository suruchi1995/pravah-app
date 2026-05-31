"""
Copilot Context Builder
=======================
Gathers GROUNDED facts from the stored planning outputs so the AI answers from
real engine results, never invention. Also powers a deterministic fallback that
works with no API key.

For a given question we pull the relevant slices:
  - top revenue-at-risk gaps (handshake)
  - forecast accuracy + model per series
  - capacity bottlenecks
  - optimizer scenario outcomes + reasoning
  - segmentation
and assemble a compact, factual context block + structured facts.
"""
import os, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import DEFAULT_TENANT


def gather_facts(session, tenant=DEFAULT_TENANT):
    facts = {}

    # handshake — gaps and risk
    hs = session.query(m.DemandSupplyHandshake).filter_by(tenant_id=tenant).all()
    hs_sorted = sorted(hs, key=lambda r: -r.revenue_at_risk)
    facts["total_revenue_at_risk"] = round(sum(r.revenue_at_risk for r in hs), 2)
    facts["total_margin_at_risk"] = round(sum(r.margin_at_risk for r in hs), 2)
    facts["top_gaps"] = [{
        "sku": r.item_code, "dc": r.location_code, "demand": round(r.demand_qty),
        "supply": round(r.available_supply_qty), "gap": round(r.gap_qty),
        "fill_rate": round(r.fill_rate, 3), "revenue_at_risk": round(r.revenue_at_risk),
        "recommendation": r.recommendation,
    } for r in hs_sorted[:8]]

    # forecast — accuracy summary
    fc = session.query(m.ForecastOutput).filter_by(tenant_id=tenant).all()
    if fc:
        facts["avg_mape"] = round(sum(r.mape for r in fc) / len(fc), 2)
        models = defaultdict(int)
        for r in fc:
            models[r.selected_model] += 1
        facts["forecast_models"] = dict(models)

    # capacity — bottlenecks
    caps = session.query(m.CapacityLoad).filter_by(tenant_id=tenant).all()
    bott = [c for c in caps if c.constraint_status in ("TIGHT", "OVERLOADED")]
    facts["bottlenecks"] = [{
        "resource": c.resource_code, "period": c.period,
        "utilization": round(c.utilization, 3), "status": c.constraint_status,
    } for c in sorted(bott, key=lambda x: -x.utilization)[:6]]

    # optimizer — scenarios
    expl = session.query(m.SolverExplanation).filter_by(tenant_id=tenant).all()
    facts["scenarios"] = [{
        "scenario": e.scenario, "objective": e.objective,
        "status": e.status, "reasoning": e.reasoning,
    } for e in expl]

    # segmentation
    seg = session.query(m.ProductSegmentation).filter_by(tenant_id=tenant).all()
    facts["segmentation"] = [{"sku": s.item_code, "class": s.abc_xyz,
                              "annual_value": round(s.annual_value)} for s in seg]

    return facts


def facts_for_sku(session, sku, tenant=DEFAULT_TENANT):
    """Drill into one SKU across engines (for 'why is FG001 short?')."""
    out = {"sku": sku}
    hs = session.query(m.DemandSupplyHandshake).filter_by(tenant_id=tenant, item_code=sku).all()
    out["handshake"] = [{
        "dc": r.location_code, "demand": round(r.demand_qty), "supply": round(r.available_supply_qty),
        "gap": round(r.gap_qty), "fill_rate": round(r.fill_rate, 3),
        "revenue_at_risk": round(r.revenue_at_risk), "recommendation": r.recommendation,
    } for r in hs]
    fc = session.query(m.ForecastOutput).filter_by(tenant_id=tenant, item_code=sku).all()
    if fc:
        out["forecast_model"] = fc[0].selected_model
        out["forecast_mape"] = fc[0].mape
    net = session.query(m.NetRequirement).filter_by(tenant_id=tenant, item_code=sku).all()
    out["netting"] = [{"period": n.period, "gross": round(n.gross_requirement),
                       "on_hand": round(n.on_hand), "net": round(n.net_requirement),
                       "planned_order": round(n.planned_order)} for n in net]
    seg = session.query(m.ProductSegmentation).filter_by(tenant_id=tenant, item_code=sku).first()
    if seg:
        out["segment"] = seg.abc_xyz
        out["segment_reasoning"] = seg.reasoning
    return out


def build_context_text(facts):
    """Compact factual brief for the LLM system prompt."""
    lines = ["PLANNING FACTS (use ONLY these; do not invent numbers):"]
    lines.append(f"- Total revenue at risk: Rs {facts.get('total_revenue_at_risk', 0):,.0f}; "
                 f"margin at risk: Rs {facts.get('total_margin_at_risk', 0):,.0f}.")
    if facts.get("avg_mape") is not None:
        lines.append(f"- Forecast avg MAPE: {facts['avg_mape']}%; models used: {facts.get('forecast_models', {})}.")
    if facts.get("top_gaps"):
        lines.append("- Top demand-supply gaps:")
        for g in facts["top_gaps"]:
            lines.append(f"    {g['sku']} @ {g['dc']}: demand {g['demand']}, supply {g['supply']}, "
                         f"gap {g['gap']}, fill {g['fill_rate']*100:.0f}%, "
                         f"revenue@risk Rs {g['revenue_at_risk']:,.0f}. Rec: {g['recommendation']}")
    if facts.get("bottlenecks"):
        lines.append("- Capacity bottlenecks:")
        for b in facts["bottlenecks"]:
            lines.append(f"    {b['resource']} {b['period'][:7]}: {b['utilization']*100:.0f}% [{b['status']}]")
    if facts.get("scenarios"):
        lines.append("- Optimizer scenarios:")
        for s in facts["scenarios"]:
            lines.append(f"    {s['scenario']} ({s['status']}): {s['reasoning']}")
    return "\n".join(lines)
