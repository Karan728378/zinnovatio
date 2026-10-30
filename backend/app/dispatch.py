"""
KilnLink One-Click Auto-Dispatch Optimization Simulation
Deterministic, explainable allocation of available supplier stock to kiln demand.
Simulation only: does NOT mutate persistent production records without confirmation.
"""
import sqlite3
from typing import Dict, Any, List
from .logic import get_effective_mandate_share, straw_needed, rank_suppliers

def simulate_auto_dispatch(conn: sqlite3.Connection, cfg: Dict[str, Any], month: str) -> Dict[str, Any]:
    """
    Simulates optimal assignment of supplier inventory to kiln statutory co-firing gaps.
    Algorithm:
    1. For each kiln, computes remaining straw required under the effective statutory mandate.
    2. Sorts kilns by remaining gap descending (prioritizes highest deficits).
    3. Greedily allocates from lowest delivered-cost eligible suppliers within inventory bounds.
    4. Tracks allocated amounts and unmet demand deterministically.
    """
    cur = conn.cursor()

    # 1. Authoritative mandate share for requested month
    mandate_share = get_effective_mandate_share(month, cfg)
    factor = float(cfg.get("straw_to_fuel_factor", 1.0))

    # 2. Load kilns
    cur.execute("SELECT * FROM kilns ORDER BY kiln_id ASC;")
    kilns = [dict(r) for r in cur.fetchall()]

    # 3. Load pre-existing deliveries for this month
    cur.execute(
        "SELECT kiln_id, SUM(tonnes) as delivered FROM deliveries WHERE date LIKE ? GROUP BY kiln_id;",
        (f"{month}%",)
    )
    delivered_map = {r["kiln_id"]: float(r["delivered"]) for r in cur.fetchall()}

    # 4. Load suppliers with positive stock
    cur.execute("SELECT * FROM suppliers WHERE available_tonnes > 0 ORDER BY supplier_id ASC;")
    suppliers = [dict(r) for r in cur.fetchall()]

    # In-memory supplier stock tracking (simulated)
    sim_stock = {s["supplier_id"]: float(s["available_tonnes"]) for s in suppliers}

    allocations: List[Dict[str, Any]] = []
    kiln_summaries: List[Dict[str, Any]] = []

    total_demand = 0.0
    total_allocated = 0.0
    total_estimated_cost = 0.0

    # Calculate initial gaps
    kiln_demands = []
    for k in kilns:
        kid = k["kiln_id"]
        monthly_fuel = float(k["monthly_fuel_tonnes"])
        needed = straw_needed(mandate_share, monthly_fuel, factor)
        pre_delivered = delivered_map.get(kid, 0.0)
        gap = max(0.0, round(needed - pre_delivered, 2))
        total_demand += gap
        kiln_demands.append({
            "kiln": k,
            "monthly_fuel": monthly_fuel,
            "needed": needed,
            "pre_delivered": pre_delivered,
            "gap": gap
        })

    # Sort kilns by gap descending for priority dispatch
    kiln_demands.sort(key=lambda x: -x["gap"])

    for kd in kiln_demands:
        k = kd["kiln"]
        kid = k["kiln_id"]
        remaining_gap = kd["gap"]
        allocated_to_kiln = 0.0

        if remaining_gap > 0:
            # Rank suppliers relative to this kiln
            active_suppliers = [
                {**s, "available_tonnes": sim_stock[s["supplier_id"]]}
                for s in suppliers
                if sim_stock[s["supplier_id"]] > 0.001
            ]
            ranked = rank_suppliers(k, active_suppliers, cfg, max_distance_km=100.0)

            for s in ranked:
                if remaining_gap <= 0.001:
                    break
                sid = s["supplier_id"]
                current_avail = sim_stock[sid]
                if current_avail <= 0.001:
                    continue

                allocate_qty = round(min(current_avail, remaining_gap), 2)
                if allocate_qty <= 0.0:
                    continue

                item_cost = round(allocate_qty * s["delivered_cost_per_tonne"], 2)
                sim_stock[sid] = round(sim_stock[sid] - allocate_qty, 2)
                remaining_gap = round(remaining_gap - allocate_qty, 2)
                allocated_to_kiln = round(allocated_to_kiln + allocate_qty, 2)
                total_allocated = round(total_allocated + allocate_qty, 2)
                total_estimated_cost = round(total_estimated_cost + item_cost, 2)

                allocations.append({
                    "kiln_id": kid,
                    "kiln_name": k["name"],
                    "supplier_id": sid,
                    "supplier_name": s["name"],
                    "straw_form": s["form"],
                    "distance_km": s["distance_km"],
                    "delivered_cost_per_tonne": s["delivered_cost_per_tonne"],
                    "allocated_tonnes": allocate_qty,
                    "total_cost_inr": item_cost
                })

        final_gap = max(0.0, round(kd["needed"] - (kd["pre_delivered"] + allocated_to_kiln), 2))
        kiln_summaries.append({
            "kiln_id": kid,
            "kiln_name": k["name"],
            "monthly_fuel_tonnes": kd["monthly_fuel"],
            "straw_needed_tonnes": kd["needed"],
            "pre_existing_delivered_tonnes": kd["pre_delivered"],
            "simulated_allocated_tonnes": allocated_to_kiln,
            "net_gap_remaining": final_gap,
            "target_met": final_gap <= 0.001
        })

    # Sort kiln summaries by ID
    kiln_summaries.sort(key=lambda x: x["kiln_id"])
    total_unmet = max(0.0, round(total_demand - total_allocated, 2))

    return {
        "status": "simulation",
        "provenance": "Deterministic greedy allocation based on delivered cost and stock limits. Simulation only; database state unaffected.",
        "reporting_month": month,
        "target_mandate_share": mandate_share,
        "total_kiln_demand_tonnes": round(total_demand, 2),
        "total_allocated_tonnes": round(total_allocated, 2),
        "total_unmet_tonnes": round(total_unmet, 2),
        "total_estimated_cost_inr": round(total_estimated_cost, 2),
        "allocations": allocations,
        "kiln_summaries": kiln_summaries
    }

