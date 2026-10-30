"""
KilnLink Core Mathematical and Domain Logic (Section 5.5 Contract)
"""
import math
from typing import Dict, Any, List

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth in kilometres.
    """
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)

def straw_needed(share: float, fuel_tonnes: float, factor: float = 1.0) -> float:
    """
    Calculate required paddy straw tonnes under the mandated share.
    straw_needed (tonnes) = mandated_share * monthly_fuel_tonnes * straw_to_fuel_factor
    """
    return round(share * fuel_tonnes * factor, 2)

def delivered_cost(price: float, km: float, form: str, cfg: Dict[str, Any]) -> float:
    """
    Calculate delivered cost per tonne to the kiln.
    Delivered cost per tonne = price_per_tonne + transport_per_tonne_km * distance_km + (chopping_cost if form is chopped)
    """
    transport_rate = cfg.get("transport_per_tonne_km", 6.0)
    chopping_cost = cfg.get("chopping_cost_per_tonne", 150.0) if form.lower() == "chopped" else 0.0
    total = price + (transport_rate * km) + chopping_cost
    return round(total, 2)

def compliance_share(straw_tonnes: float, fuel_tonnes: float) -> float:
    """
    Calculate kiln compliance share.
    Compliance share = straw delivered in the month / monthly fuel tonnes.
    """
    if not fuel_tonnes or fuel_tonnes <= 0:
        return 0.0
    return round(straw_tonnes / fuel_tonnes, 4)

def rank_suppliers(kiln: Dict[str, Any], suppliers: List[Dict[str, Any]], cfg: Dict[str, Any], max_distance_km: float = 100.0) -> List[Dict[str, Any]]:
    """
    Compute distance and delivered cost for all suppliers relative to a kiln,
    and rank by delivered cost per tonne ascending, then distance ascending.
    """
    results = []
    kiln_lat = kiln["lat"]
    kiln_lon = kiln["lon"]

    for s in suppliers:
        dist = haversine(kiln_lat, kiln_lon, s["lat"], s["lon"])
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

    # Rank by cost, then distance, then available tonnes descending
    results.sort(key=lambda x: (x["delivered_cost_per_tonne"], x["distance_km"], -x["available_tonnes"]))
    return results

def rank_kilns_for_supplier(supplier: Dict[str, Any], kilns: List[Dict[str, Any]], cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Compute distance and delivered cost for all kilns relative to a supplier.
    """
    results = []
    sup_lat = supplier["lat"]
    sup_lon = supplier["lon"]
    form = supplier.get("straw_form") or supplier.get("form", "bale")
    price = float(supplier.get("price_per_tonne", 1500.0))

    for k in kilns:
        dist = haversine(sup_lat, sup_lon, k["lat"], k["lon"])
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
