"""
Parali Mitra Cross-Platform Machine Learning Inference Engine
Zero external dependencies (pure Python / standard library).
Runs on Windows, macOS, Linux, and web servers.
"""
import os
import json
from typing import Dict, Any, List

MODELS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "models", "trained_models.json")
METRICS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "models", "metrics.json")

_MODEL_CACHE = None

def load_models() -> Dict[str, Any]:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    if os.path.exists(MODELS_FILE):
        with open(MODELS_FILE, "r") as f:
            _MODEL_CACHE = json.load(f)
            return _MODEL_CACHE
    return {}

def load_metrics() -> Dict[str, Any]:
    if os.path.exists(METRICS_FILE):
        with open(METRICS_FILE, "r") as f:
            return json.load(f)
    return {}

def _eval_tree(x: List[float], node: Dict[str, Any]) -> Any:
    if node.get("is_leaf", False):
        return node["value"]
    feat = node["feature"]
    thresh = node["threshold"]
    if x[feat] <= thresh:
        return _eval_tree(x, node["left"])
    return _eval_tree(x, node["right"])

def predict_biomass_yield(acres: float, variety_idx: int, grain_yield: float, ndvi: float, cut_height: float) -> Dict[str, Any]:
    """
    Predicts paddy straw tonnage from farm parcel parameters using trained Random Forest.
    """
    models = load_models()
    forest = models.get("yield_forest", [])
    x = [float(acres), float(variety_idx), float(grain_yield), float(ndvi), float(cut_height)]
    
    if not forest:
        # Fallback baseline formula
        ratio = 1.25 if variety_idx == 1 else (0.95 if variety_idx == 2 else 1.10)
        est = acres * (grain_yield * 0.1) * ratio
        return {"predicted_straw_tonnes": round(est, 2), "model": "rule_fallback", "confidence": "baseline"}

    preds = [_eval_tree(x, tree) for tree in forest]
    mean_pred = sum(preds) / len(preds)
    variance = sum((p - mean_pred) ** 2 for p in preds) / len(preds)
    std_err = variance ** 0.5

    return {
        "predicted_straw_tonnes": round(mean_pred, 2),
        "uncertainty_tonnes": round(std_err, 2),
        "model": "RandomForestRegressor (10 trees)",
        "features": {
            "acres": acres,
            "crop_variety": "PR-126" if variety_idx == 0 else ("Pusa-44" if variety_idx == 1 else "Basmati"),
            "grain_yield_qtl_acre": grain_yield,
            "satellite_ndvi": ndvi,
            "cutting_height_cm": cut_height
        }
    }

def predict_delivered_price(distance_km: float, form_idx: int, moisture_pct: float, harvest_week: int, supply_density: float) -> Dict[str, Any]:
    """
    Predicts dynamic market-clearing delivered straw price (₹/tonne).
    form_idx: 0: bale, 1: chopped, 2: pellet
    """
    models = load_models()
    tree = models.get("price_tree")
    x = [float(distance_km), float(form_idx), float(moisture_pct), float(harvest_week), float(supply_density)]

    form_names = ["Bale", "Chopped", "Pellet"]
    form_str = form_names[form_idx] if 0 <= form_idx < 3 else "Chopped"

    if not tree:
        base = 2550.0 if form_idx == 2 else (1800.0 if form_idx == 1 else 1420.0)
        est = base + (distance_km * 6.0) + (150.0 if form_idx == 1 else 0.0)
        return {"predicted_delivered_price_per_tonne": round(est, 2), "model": "rule_fallback"}

    pred_price = _eval_tree(x, tree)
    coal_benchmark = 9000.0
    savings = max(0.0, coal_benchmark - pred_price)

    return {
        "predicted_delivered_price_per_tonne": round(pred_price, 2),
        "savings_vs_coal_per_tonne": round(savings, 2),
        "coal_benchmark_price": coal_benchmark,
        "model": "DecisionTreeRegressor",
        "features": {
            "distance_km": distance_km,
            "form": form_str,
            "moisture_pct": moisture_pct,
            "harvest_week": harvest_week,
            "supply_density_index": supply_density
        }
    }

def predict_fire_risk(days_left: float, dist_kiln: float, machinery_score: int, cell_fire: float) -> Dict[str, Any]:
    """
    Predicts stubble fire burning risk level and probability distribution.
    """
    models = load_models()
    tree = models.get("risk_tree")
    x = [float(days_left), float(dist_kiln), float(machinery_score), float(cell_fire)]

    if not tree:
        return {"risk_category": "Moderate Risk", "burn_probability": 0.45, "model": "rule_fallback"}

    class_probs = _eval_tree(x, tree)  # [p_low, p_mod, p_high]
    classes = ["Low Risk", "Moderate Risk", "High Risk"]
    best_idx = int(max(range(len(class_probs)), key=lambda i: class_probs[i]))

    return {
        "risk_category": classes[best_idx],
        "risk_level_code": best_idx,
        "probabilities": {
            "low": round(class_probs[0], 3),
            "moderate": round(class_probs[1], 3),
            "high": round(class_probs[2], 3)
        },
        "model": "DecisionTreeClassifier",
        "advisory": (
            "Field at critical risk of residue burning. Expedite priority straw aggregator dispatch."
            if best_idx == 2 else (
                "Moderate window. Encourage neighbor aggregation for combined transport."
                if best_idx == 1 else "Safe window for agronomic incorporation or baling."
            )
        )
    }
