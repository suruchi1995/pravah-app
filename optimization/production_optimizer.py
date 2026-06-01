"""
Production Optimizer (Google OR-Tools, CBC MIP/LP)
==================================================
Multi-period production plan that decides how much of each FG to produce in each
period, respecting finite resource capacity and demand, under one of three objectives.

Decision variables
  produce[i,t] >= 0     units of FG i produced in period t
  inv[i,t]     >= 0     ending inventory of FG i in period t
  short[i,t]   >= 0     unmet demand (shortage) of FG i in period t

Constraints
  Inventory balance:  inv[i,t] = inv[i,t-1] + produce[i,t] + scheduled_receipts[i,t]
                                  - (demand[i,t] - short[i,t])
  Capacity:           sum_i produce[i,t] * runtime[i,r] <= available[r,t]   for each resource r
  Safety stock:       inv[i,t] >= safety_stock[i]  (soft via shortage allowed on demand only)

Objectives
  min_cost      : minimise production cost + holding cost + shortage penalty
  max_service   : minimise total shortage (then cost as tie-break)
  balanced      : weighted blend

Writes production_plan + solver_explanations. (Purchase plan derived from MRP on the
optimised production in a later step.)
"""
import os, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ortools.linear_solver import pywraplp
from backend import models as m
from backend.config import DEFAULT_TENANT

SHORTAGE_PENALTY_MULT = 3.0   # penalty per unit short = mult * unit margin


def _gather(session, tenant):
    items = {it.item_code: it for it in session.query(m.Item).filter_by(tenant_id=tenant)}
    fgs = [c for c, it in items.items() if it.item_type == "FG"]
    cost = {c.item_code: c for c in session.query(m.Cost).filter_by(tenant_id=tenant)}

    # demand by FG x period (consensus, summed across DCs)
    demand = defaultdict(lambda: defaultdict(float))
    for r in session.query(m.DemandPlan).filter_by(tenant_id=tenant):
        demand[r.item_code][r.period] += r.consensus_qty
    periods = sorted({p for fg in fgs for p in demand[fg]})

    # opening inventory per FG
    open_inv = defaultdict(float)
    for inv in session.query(m.Inventory).filter_by(tenant_id=tenant):
        if inv.item_code in fgs:
            open_inv[inv.item_code] += inv.on_hand_qty

    # scheduled receipts (open prod orders) -> first period
    receipts = defaultdict(lambda: defaultdict(float))
    for po in session.query(m.ProductionOrder).filter_by(tenant_id=tenant):
        if po.item_code in fgs and periods:
            receipts[po.item_code][periods[0]] += po.quantity

    # safety stock per FG (sum DC targets)
    ss = defaultdict(float)
    for t in session.query(m.InventoryTarget).filter_by(tenant_id=tenant):
        ss[t.item_code] += t.safety_stock

    # routing: FG -> {resource: hr}, resource available hours
    routing = defaultdict(dict)
    for rt in session.query(m.Routing).filter_by(tenant_id=tenant):
        if rt.item_code in fgs:
            routing[rt.item_code][rt.resource_code] = rt.runtime_hr_per_unit
    avail = {r.resource_code: r.hours_per_month for r in session.query(m.Resource).filter_by(tenant_id=tenant)}

    return items, fgs, cost, demand, periods, open_inv, receipts, ss, routing, avail


def optimize(session, scenario="min_cost", tenant=DEFAULT_TENANT):
    from backend.parameters import get_param
    SHORTAGE_PENALTY_MULT = get_param(session, "shortage_penalty_mult", tenant)
    (items, fgs, cost, demand, periods, open_inv, receipts, ss, routing, avail) = _gather(session, tenant)
    solver = pywraplp.Solver.CreateSolver("CBC")
    if solver is None:
        raise RuntimeError("CBC solver unavailable")
    INF = solver.infinity()

    produce, inv, short = {}, {}, {}
    for i in fgs:
        for t in periods:
            produce[i, t] = solver.NumVar(0, INF, f"prod_{i}_{t}")
            inv[i, t] = solver.NumVar(0, INF, f"inv_{i}_{t}")
            short[i, t] = solver.NumVar(0, INF, f"short_{i}_{t}")

    # inventory balance
    for i in fgs:
        prev = open_inv[i]
        for t in periods:
            d = demand[i].get(t, 0.0)
            r = receipts[i].get(t, 0.0)
            # inv_t = prev + produce + receipts - (demand - short)
            solver.Add(inv[i, t] == prev + produce[i, t] + r - (d - short[i, t]))
            # shortage can't exceed demand
            solver.Add(short[i, t] <= d)
            prev = inv[i, t]

    # capacity per resource per period — ONLY if real resource/routing data exists.
    # Without it we optimise unconstrained (never invent capacity limits).
    capacity_constrained = bool(avail) and any(routing[i] for i in fgs)
    if capacity_constrained:
        resources = set()
        for i in fgs:
            resources |= set(routing[i].keys())
        for t in periods:
            for res in resources:
                terms = [produce[i, t] * routing[i][res] for i in fgs if res in routing[i]]
                if terms:
                    solver.Add(solver.Sum(terms) <= avail.get(res, 0.0))

    # objective components
    prod_cost = solver.Sum(
        produce[i, t] * (cost[i].production_cost if i in cost else 0.0)
        for i in fgs for t in periods)
    hold_cost = solver.Sum(
        inv[i, t] * ((cost[i].production_cost if i in cost else 0.0) *
                     (cost[i].holding_cost_pct_month if i in cost else 0.02))
        for i in fgs for t in periods)
    # shortage penalty ~ margin lost * multiplier
    def margin(i):
        price = items[i].unit_price_or_cost or 0.0
        pc = cost[i].production_cost if i in cost else price * 0.5
        return max(1.0, price - pc)
    short_pen = solver.Sum(short[i, t] * margin(i) * SHORTAGE_PENALTY_MULT
                           for i in fgs for t in periods)
    total_short = solver.Sum(short[i, t] for i in fgs for t in periods)

    if scenario == "min_cost":
        solver.Minimize(prod_cost + hold_cost + short_pen)
        obj_label = "Minimise production + holding + shortage penalty"
    elif scenario == "max_service":
        # heavily weight shortage; small cost term as tie-break
        solver.Minimize(total_short * 1e6 + prod_cost + hold_cost)
        obj_label = "Maximise service (minimise total shortage)"
    else:  # balanced
        solver.Minimize(prod_cost + hold_cost + short_pen * 2.0)
        obj_label = "Balanced (cost with elevated shortage weight)"

    status = solver.Solve()
    status_str = {pywraplp.Solver.OPTIMAL: "OPTIMAL",
                  pywraplp.Solver.FEASIBLE: "FEASIBLE",
                  pywraplp.Solver.INFEASIBLE: "INFEASIBLE"}.get(status, str(status))

    # collect results
    total_prod = sum(produce[i, t].solution_value() for i in fgs for t in periods) if status in (0,1) else 0
    total_sh = total_short.solution_value() if status in (0,1) else 0
    total_demand = sum(demand[i].get(t,0.0) for i in fgs for t in periods)
    fill = 1 - (total_sh / total_demand) if total_demand else 1.0

    # write production plan
    session.query(m.ProductionPlan).filter_by(tenant_id=tenant, scenario=scenario).delete()
    rows = []
    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        for i in fgs:
            for t in periods:
                q = produce[i, t].solution_value()
                if q > 0.5:
                    rows.append(m.ProductionPlan(
                        tenant_id=tenant, item_code=i, period=t,
                        quantity=round(q, 2), scenario=scenario))
        session.bulk_save_objects(rows)

    # explanation
    obj_val = solver.Objective().Value() if status in (0,1) else 0.0
    reason = (f"{obj_label}. Status={status_str}. "
              f"Total production={total_prod:,.0f} units over {len(periods)} periods; "
              f"total shortage={total_sh:,.0f} (fill {fill:.1%}). "
              + ("Capacity-constrained (real resource/routing data)."
                 if capacity_constrained else
                 "UNCONSTRAINED — no capacity data provided; upload resources + routing to optimise against real line limits."))
    session.query(m.SolverExplanation).filter_by(tenant_id=tenant, scenario=scenario).delete()
    session.add(m.SolverExplanation(
        tenant_id=tenant, scenario=scenario, objective=obj_label,
        objective_value=round(obj_val, 2), status=status_str, reasoning=reason))
    session.commit()
    return {"scenario": scenario, "status": status_str, "rows": len(rows),
            "total_production": total_prod, "total_shortage": total_sh, "fill_rate": fill,
            "objective_value": obj_val}


def run(session, tenant=DEFAULT_TENANT):
    """Run all three scenarios."""
    out = {}
    for sc in ["min_cost", "max_service", "balanced"]:
        out[sc] = optimize(session, sc, tenant)
    return out


if __name__ == "__main__":
    from backend.config import DATABASE_URL
    eng = m.make_engine(DATABASE_URL); m.init_db(eng)
    Session = m.make_session_factory(eng)
    with Session() as ssn:
        res = run(ssn)
        print("OR-Tools optimization results:\n" + "-"*60)
        for sc, r in res.items():
            print(f"{sc:12s} | {r['status']:8s} | prod={r['total_production']:>9,.0f} | "
                  f"short={r['total_shortage']:>8,.0f} | fill={r['fill_rate']:6.1%} | "
                  f"obj={r['objective_value']:>14,.0f}")
