"""
KilnLink Core Mathematical, Domain, and Statutory Mandate Logic
Authoritative implementation of Section 5 shared contract rules.
"""
import math
import re
from typing import Dict, Any, List, Optional

MONTH_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

def month_bounds(month: str) -> tuple[str, str]:
    """
    Computes [start_date, next_month_start_date) for strict date range filtering.
    For example: '2026-11' -> ('2026-11-01', '2026-12-01')
    '2026-12' -> ('2026-12-01', '2027-01-01')
    """
    validated = validate_month_format(month)
    year, mo = int(validated[:4]), int(validated[5:7])
    start_date = f"{year:04d}-{mo:02d}-01"
    if mo == 12:
        end_date = f"{year + 1:04d}-01-01"
    else:
        end_date = f"{year:04d}-{mo + 1:02d}-01"
    return start_date, end_date

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth in kilometres.
    Formula: Haversine distance with Earth radius R = 6371.0 km.
    """
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)

def validate_month_format(month: str) -> str:
    """
    Validates that a string is a valid ISO YYYY-MM month.
    Raises ValueError on invalid formats.
    """
    if not month or not isinstance(month, str) or not MONTH_REGEX.match(month.strip()):
        raise ValueError(f"Invalid month format '{month}'. Expected ISO 'YYYY-MM' (e.g. '2026-11').")
    return month.strip()

def get_effective_mandate_share(month: str, cfg: Dict[str, Any]) -> float:
    """
    Determines the authoritative statutory co-firing mandate share for a given month.
    Selects the latest effective mandate configuration where effective_month <= requested_month.
    If requested_month is prior to the earliest configured effective month (2025-11), returns 0.00
    indicating the statutory requirement was not yet in force.
    """
    valid_month = validate_month_format(month)
    mandate_schedule = cfg.get("mandate_share", {
        "2025-11": 0.20,
        "2026-11": 0.30,
        "2027-11": 0.40,
        "2028-11": 0.50
    })

    sorted_schedule = sorted(mandate_schedule.items(), key=lambda x: x[0])
    effective_share = 0.0
    for eff_month, share in sorted_schedule:
        if eff_month <= valid_month:
            effective_share = float(share)
        else:
            break

    return round(effective_share, 4)

def straw_needed(share: float, fuel_tonnes: float, factor: float = 1.0) -> float:
    """
    Calculate required paddy straw tonnes under the mandated share.
    straw_needed (tonnes) = mandated_share * monthly_fuel_tonnes * straw_to_fuel_factor
    """
    if fuel_tonnes < 0:
        raise ValueError(f"fuel_tonnes cannot be negative ({fuel_tonnes})")
    if share < 0 or share > 1.0:
        raise ValueError(f"mandate share must be between 0.0 and 1.0 ({share})")
    return round(share * fuel_tonnes * factor, 2)

def delivered_cost(price: float, km: float, form: str, cfg: Dict[str, Any]) -> float:
    """
    Calculate delivered cost per tonne to the kiln.
    Delivered cost per tonne = price_per_tonne + (transport_per_tonne_km * distance_km) + (chopping_cost if chopped)
    """
    transport_rate = float(cfg.get("transport_per_tonne_km", 6.0))
    chopping_cost = float(cfg.get("chopping_cost_per_tonne", 150.0)) if form.lower() == "chopped" else 0.0
    total = price + (transport_rate * km) + chopping_cost
    return round(total, 2)

def compliance_share(straw_tonnes: float, fuel_tonnes: float) -> float:
    """
    Calculate kiln compliance share.
    Compliance share = straw delivered in the month / monthly fuel tonnes.
    Returns 0.0 if fuel_tonnes is zero or negative.
    """
    if not fuel_tonnes or fuel_tonnes <= 0:
        return 0.0
    if straw_tonnes < 0:
        return 0.0
    return round(straw_tonnes / fuel_tonnes, 4)

def rank_suppliers(kiln: Dict[str, Any], suppliers: List[Dict[str, Any]], cfg: Dict[str, Any], max_distance_km: float = 100.0) -> List[Dict[str, Any]]:
    """
    Compute distance and delivered cost for all suppliers relative to a kiln,
    and rank by delivered cost per tonne ascending, then distance ascending.
    """
    results = []
    kiln_lat = float(kiln["lat"])
    kiln_lon = float(kiln["lon"])

    for s in suppliers:
        dist = haversine(kiln_lat, kiln_lon, float(s["lat"]), float(s["lon"]))
        if max_distance_km and dist > max_distance_km:
            continue
        form = s.get("straw_form") or s.get("form", "bale")
        price = float(s["price_per_tonne"])
        cost = delivered_cost(price, dist, form, cfg)

        item = {
            "supplier_id": s["supplier_id"],
            "name": s["name"],
            "kind": s["kind"],
            "form": form,
            "distance_km": dist,
            "price_per_tonne": price,
            "delivered_cost_per_tonne": cost,
            "available_tonnes": float(s["available_tonnes"])
        }
        results.append(item)

    # Rank by delivered cost, then distance, then available tonnes descending
    results.sort(key=lambda x: (x["delivered_cost_per_tonne"], x["distance_km"], -x["available_tonnes"]))
    return results

def rank_kilns_for_supplier(supplier: Dict[str, Any], kilns: List[Dict[str, Any]], cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Compute distance and delivered cost for all kilns relative to a supplier.
    """
    results = []
    sup_lat = float(supplier["lat"])
    sup_lon = float(supplier["lon"])
    form = supplier.get("straw_form") or supplier.get("form", "bale")
    price = float(supplier.get("price_per_tonne", 1500.0))

    for k in kilns:
        dist = haversine(sup_lat, sup_lon, float(k["lat"]), float(k["lon"]))
        cost = delivered_cost(price, dist, form, cfg)
        results.append({
            "kiln_id": k["kiln_id"],
            "name": k["name"],
            "village": k["village"],
            "distance_km": dist,
            "delivered_cost_per_tonne": cost,
            "monthly_fuel_tonnes": float(k["monthly_fuel_tonnes"])
        })

    results.sort(key=lambda x: (x["distance_km"], x["delivered_cost_per_tonne"]))
    return results
