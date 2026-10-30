"""
Parali Mitra Machine Learning Training Pipeline
Trains cross-platform models for:
1. Biomass Stubble Yield Prediction (Random Forest Regressor)
2. Dynamic Delivered Straw Price & Freight Prediction (Ridge / Tree Regressor)
3. Satellite Stubble Burning Risk Classifier (Decision Tree Classifier)

All algorithms implemented in pure NumPy / Python for zero-dependency execution across any OS.
"""
import os
import sys
import json
import math
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

np.random.seed(42)

# --- TREE IMPLEMENTATIONS FOR CROSS-PLATFORM EXPORT ---

class Node:
    def __init__(self, feature=None, threshold=None, left=None, right=None, *, value=None, is_leaf=False):
        self.feature = feature
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value
        self.is_leaf = is_leaf

    def to_dict(self):
        if self.is_leaf:
            return {"is_leaf": True, "value": float(self.value) if not isinstance(self.value, list) else [float(x) for x in self.value]}
        return {
            "is_leaf": False,
            "feature": int(self.feature),
            "threshold": float(self.threshold),
            "left": self.left.to_dict(),
            "right": self.right.to_dict()
        }

class PureDecisionTreeRegressor:
    def __init__(self, max_depth=5, min_samples_split=4):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.root = None

    def fit(self, X, y):
        self.root = self._grow_tree(X, y, depth=0)

    def _grow_tree(self, X, y, depth):
        n_samples, n_features = X.shape
        if depth >= self.max_depth or n_samples < self.min_samples_split or np.var(y) < 1e-7:
            return Node(value=np.mean(y), is_leaf=True)

        best_feat, best_thresh = None, None
        best_mse = float("inf")

        # Subsample features if needed
        feat_idxs = np.random.choice(n_features, max(1, int(n_features * 0.8)), replace=False)

        for feat in feat_idxs:
            vals = np.unique(X[:, feat])
            if len(vals) > 20:
                vals = np.percentile(vals, np.linspace(5, 95, 15))
            for thresh in vals:
                left_mask = X[:, feat] <= thresh
                right_mask = ~left_mask
                if np.sum(left_mask) < 2 or np.sum(right_mask) < 2:
                    continue
                y_l, y_r = y[left_mask], y[right_mask]
                mse = np.sum((y_l - np.mean(y_l)) ** 2) + np.sum((y_r - np.mean(y_r)) ** 2)
                if mse < best_mse:
                    best_mse = mse
                    best_feat = feat
                    best_thresh = thresh

        if best_feat is None:
            return Node(value=np.mean(y), is_leaf=True)

        left_mask = X[:, best_feat] <= best_thresh
        left_child = self._grow_tree(X[left_mask], y[left_mask], depth + 1)
        right_child = self._grow_tree(X[~left_mask], y[~left_mask], depth + 1)
        return Node(feature=best_feat, threshold=best_thresh, left=left_child, right=right_child)

    def predict(self, X):
        return np.array([self._predict_one(x, self.root) for x in X])

    def _predict_one(self, x, node):
        if node.is_leaf:
            return node.value
        if x[node.feature] <= node.threshold:
            return self._predict_one(x, node.left)
        return self._predict_one(x, node.right)


class PureRandomForestRegressor:
    def __init__(self, n_estimators=10, max_depth=6, min_samples_split=4):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.trees = []

    def fit(self, X, y):
        self.trees = []
        n_samples = X.shape[0]
        for _ in range(self.n_estimators):
            boot_idxs = np.random.choice(n_samples, n_samples, replace=True)
            tree = PureDecisionTreeRegressor(max_depth=self.max_depth, min_samples_split=self.min_samples_split)
            tree.fit(X[boot_idxs], y[boot_idxs])
            self.trees.append(tree)

    def predict(self, X):
        tree_preds = np.array([tree.predict(X) for tree in self.trees])
        return np.mean(tree_preds, axis=0)

    def to_dict(self):
        return [tree.root.to_dict() for tree in self.trees]


class PureDecisionTreeClassifier:
    def __init__(self, max_depth=4, min_samples_split=5):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.root = None

    def fit(self, X, y):
        self.n_classes = len(np.unique(y))
        self.root = self._grow_tree(X, y, depth=0)

    def _gini(self, y):
        _, counts = np.unique(y, return_counts=True)
        probs = counts / len(y)
        return 1.0 - np.sum(probs ** 2)

    def _grow_tree(self, X, y, depth):
        n_samples, n_features = X.shape
        vals, counts = np.unique(y, return_counts=True)
        majority_class = vals[np.argmax(counts)]

        # Class probabilities
        class_probs = [float(np.mean(y == c)) for c in range(self.n_classes)]

        if depth >= self.max_depth or n_samples < self.min_samples_split or len(vals) == 1:
            return Node(value=class_probs, is_leaf=True)

        best_feat, best_thresh = None, None
        best_gain = -1.0
        current_gini = self._gini(y)

        for feat in range(n_features):
            unique_vals = np.unique(X[:, feat])
            if len(unique_vals) > 20:
                unique_vals = np.percentile(unique_vals, np.linspace(5, 95, 15))
            for thresh in unique_vals:
                left_mask = X[:, feat] <= thresh
                right_mask = ~left_mask
                if np.sum(left_mask) < 2 or np.sum(right_mask) < 2:
                    continue
                g_left = self._gini(y[left_mask])
                g_right = self._gini(y[right_mask])
                w_left = np.sum(left_mask) / n_samples
                gain = current_gini - (w_left * g_left + (1.0 - w_left) * g_right)
                if gain > best_gain:
                    best_gain = gain
                    best_feat = feat
                    best_thresh = thresh

        if best_feat is None or best_gain <= 1e-5:
            return Node(value=class_probs, is_leaf=True)

        left_mask = X[:, best_feat] <= best_thresh
        left_child = self._grow_tree(X[left_mask], y[left_mask], depth + 1)
        right_child = self._grow_tree(X[~left_mask], y[~left_mask], depth + 1)
        return Node(feature=best_feat, threshold=best_thresh, left=left_child, right=right_child)

    def predict(self, X):
        probs = np.array([self._predict_one(x, self.root) for x in X])
        return np.argmax(probs, axis=1)

    def predict_proba(self, X):
        return np.array([self._predict_one(x, self.root) for x in X])

    def _predict_one(self, x, node):
        if node.is_leaf:
            return node.value
        if x[node.feature] <= node.threshold:
            return self._predict_one(x, node.left)
        return self._predict_one(x, node.right)

    def to_dict(self):
        return self.root.to_dict()


# --- DATASET GENERATION BASED ON PUNJAB AGRICULTURAL DATA ---

def generate_yield_dataset(n=600):
    # Features: [acres, crop_variety_idx, grain_yield_qtl_acre, ndvi, cutting_height_cm]
    # Crop variety: 0: PR-126 (short duration), 1: Pusa-44 (long, heavy straw), 2: Basmati (PB-1121)
    acres = np.random.uniform(2.0, 35.0, n)
    variety = np.random.choice([0, 1, 2], n, p=[0.45, 0.35, 0.20])
    
    # Grain yield in quintals / acre (PAU averages 24 to 32 qtl/acre for Parmal, 18-24 for Basmati)
    base_yield = np.where(variety == 2, np.random.normal(21.0, 2.5, n),
                 np.where(variety == 1, np.random.normal(30.0, 2.8, n),
                                       np.random.normal(27.0, 2.2, n)))
    grain_yield = np.clip(base_yield, 15.0, 36.0)

    # Satellite NDVI at maturity (0.62 to 0.86)
    ndvi = np.clip(0.55 + 0.009 * grain_yield + np.random.normal(0, 0.03, n), 0.58, 0.88)

    # Cutting height in cm (10 to 30 cm)
    cut_height = np.random.uniform(10.0, 30.0, n)

    # Straw-to-grain ratio: Pusa-44 ~ 1.25, PR-126 ~ 1.10, Basmati ~ 0.95
    ratio = np.where(variety == 1, 1.25, np.where(variety == 2, 0.95, 1.10))
    # Height adjustment: higher cut leaves more stubble, but loose straw recovered decreases
    recovery_factor = 1.0 - (cut_height - 15.0) * 0.008

    # 1 quintal = 0.1 tonne
    total_grain_tonnes = acres * (grain_yield * 0.1)
    straw_tonnes = total_grain_tonnes * ratio * recovery_factor + np.random.normal(0, 0.5, n)
    straw_tonnes = np.clip(straw_tonnes, 1.0, 150.0)

    X = np.column_stack([acres, variety, grain_yield, ndvi, cut_height])
    feature_names = ["acres", "crop_variety_idx", "grain_yield_qtl_acre", "ndvi", "cutting_height_cm"]
    return X, straw_tonnes, feature_names


def generate_price_dataset(n=600):
    # Features: [distance_km, form_idx, moisture_pct, harvest_week, supply_density_index]
    # form_idx: 0: bale, 1: chopped, 2: pellet
    dist = np.random.uniform(1.0, 45.0, n)
    form = np.random.choice([0, 1, 2], n, p=[0.4, 0.45, 0.15])
    moisture = np.random.uniform(10.0, 24.0, n)
    harvest_week = np.random.choice([1, 2, 3, 4], n, p=[0.2, 0.4, 0.3, 0.1])
    supply_idx = np.random.uniform(0.1, 1.0, n)

    # Economics: Base price (bale: ~1400, chopped: ~1800, pellet: ~2550)
    base_price = np.where(form == 2, 2550.0, np.where(form == 1, 1800.0, 1420.0))
    # Peak harvest glut in week 2 & 3 slightly lowers ex-gate price (-₹80/t)
    glut_effect = np.where((harvest_week == 2) | (harvest_week == 3), -75.0 * supply_idx, 0.0)
    # Moisture penalty (>16% moisture incurs ₹35 per % point deduction/drying cost)
    moisture_adj = np.where(moisture > 16.0, (moisture - 16.0) * 40.0, -(16.0 - moisture) * 15.0)
    # Haulage freight (₹6.00 / t-km)
    freight = dist * 6.0
    # Chopping fee
    chop_fee = np.where(form == 1, 150.0, 0.0)

    delivered_price = base_price + freight + chop_fee + glut_effect + moisture_adj + np.random.normal(0, 25.0, n)
    delivered_price = np.clip(delivered_price, 1200.0, 3600.0)

    X = np.column_stack([dist, form, moisture, harvest_week, supply_idx])
    feature_names = ["distance_km", "form_idx", "moisture_pct", "harvest_week", "supply_density_index"]
    return X, delivered_price, feature_names


def generate_fire_risk_dataset(n=600):
    # Features: [days_to_wheat_sowing, dist_to_kiln_km, machinery_access_score, cell_fire_density]
    days_left = np.random.uniform(4.0, 28.0, n)
    dist_kiln = np.random.uniform(2.0, 50.0, n)
    machinery = np.random.choice([1, 2, 3, 4, 5], n, p=[0.25, 0.30, 0.25, 0.15, 0.05])  # 1: poor, 5: high
    cell_fire = np.random.uniform(0.05, 1.0, n)

    # Risk score: tighter timeline + far kiln + low machinery + high historical fire = High Risk
    risk_score = (
        (30.0 - days_left) * 0.45 +
        (dist_kiln / 50.0) * 15.0 +
        (6 - machinery) * 3.5 +
        cell_fire * 20.0 +
        np.random.normal(0, 3.0, n)
    )

    # Category: 0: Low Risk (<24), 1: Moderate Risk (24-34), 2: High/Severe Risk (>=34)
    risk_class = np.where(risk_score >= 34.0, 2, np.where(risk_score >= 24.0, 1, 0))

    X = np.column_stack([days_left, dist_kiln, machinery, cell_fire])
    feature_names = ["days_to_wheat_sowing", "dist_to_kiln_km", "machinery_access_score", "cell_fire_density"]
    return X, risk_class, feature_names


# --- TRAINING EXECUTION & SERIALIZATION ---

def train_and_export_all():
    from pathlib import Path
    base_dir = Path(__file__).resolve().parent.parent
    models_dir = base_dir / "models"
    os.makedirs(models_dir, exist_ok=True)

    # 1. Train Model 1: Biomass Yield Predictor
    print("Training Model 1: Biomass Yield Predictor (Random Forest)...")
    X1, y1, feat1 = generate_yield_dataset(600)
    split1 = int(len(X1) * 0.8)
    X1_tr, X1_te, y1_tr, y1_te = X1[:split1], X1[split1:], y1[:split1], y1[split1:]

    rf_yield = PureRandomForestRegressor(n_estimators=10, max_depth=6)
    rf_yield.fit(X1_tr, y1_tr)
    y1_pred = rf_yield.predict(X1_te)
    r2_yield = 1.0 - (np.sum((y1_te - y1_pred) ** 2) / np.sum((y1_te - np.mean(y1_te)) ** 2))
    mae_yield = np.mean(np.abs(y1_te - y1_pred))
    print(f"  Yield Predictor Synthetic Test R^2: {r2_yield:.3f}, MAE: {mae_yield:.2f} tonnes")

    # 2. Train Model 2: Delivered Price Predictor
    print("Training Model 2: Dynamic Delivered Price Predictor...")
    X2, y2, feat2 = generate_price_dataset(600)
    split2 = int(len(X2) * 0.8)
    X2_tr, X2_te, y2_tr, y2_te = X2[:split2], X2[split2:], y2[:split2], y2[split2:]

    tree_price = PureDecisionTreeRegressor(max_depth=6)
    tree_price.fit(X2_tr, y2_tr)
    y2_pred = tree_price.predict(X2_te)
    r2_price = 1.0 - (np.sum((y2_te - y2_pred) ** 2) / np.sum((y2_te - np.mean(y2_te)) ** 2))
    mae_price = np.mean(np.abs(y2_te - y2_pred))
    print(f"  Price Predictor Synthetic Test R^2: {r2_price:.3f}, MAE: Rs. {mae_price:.1f}/tonne")

    # 3. Train Model 3: Fire Risk Classifier
    print("Training Model 3: Stubble Fire Risk Classifier...")
    X3, y3, feat3 = generate_fire_risk_dataset(600)
    split3 = int(len(X3) * 0.8)
    X3_tr, X3_te, y3_tr, y3_te = X3[:split3], X3[split3:], y3[:split3], y3[split3:]

    clf_risk = PureDecisionTreeClassifier(max_depth=4)
    clf_risk.fit(X3_tr, y3_tr)
    y3_pred = clf_risk.predict(X3_te)
    acc_risk = np.mean(y3_pred == y3_te)
    print(f"  Fire Risk Classifier Synthetic Test Accuracy: {acc_risk * 100:.1f}%")

    # Metrics Summary with Honest Provenance & Boundary Clarifications
    metrics = {
        "provenance": {
            "type": "synthetic_demonstration_models",
            "agronomic_references": [
                "Punjab Agricultural University (PAU) Rice-Wheat cropping system stubble ratios",
                "Commission for Air Quality Management (CAQM) biomass co-firing economics",
                "VIIRS 375m active fire cluster proximity distributions"
            ],
            "intended_use": "Demonstration, planning, and price guidance for brick kiln co-firing. Must be calibrated with regional weighbridge and farm audit records before commercial contracting."
        },
        "yield_predictor": {
            "model_type": "RandomForestRegressor",
            "evaluation_nature": "synthetic_holdout_validation",
            "features": feat1,
            "train_samples": int(split1),
            "test_samples": int(len(X1) - split1),
            "test_r2": round(float(r2_yield), 3),
            "test_mae_tonnes": round(float(mae_yield), 2),
            "synthetic_test_r2": round(float(r2_yield), 3),
            "synthetic_test_mae_tonnes": round(float(mae_yield), 2)
        },
        "price_predictor": {
            "model_type": "DecisionTreeRegressor",
            "evaluation_nature": "synthetic_holdout_validation",
            "features": feat2,
            "train_samples": int(split2),
            "test_samples": int(len(X2) - split2),
            "test_r2": round(float(r2_price), 3),
            "test_mae_rupees": round(float(mae_price), 2),
            "synthetic_test_r2": round(float(r2_price), 3),
            "synthetic_test_mae_rupees": round(float(mae_price), 2)
        },
        "fire_risk_classifier": {
            "model_type": "DecisionTreeClassifier",
            "evaluation_nature": "synthetic_holdout_validation",
            "features": feat3,
            "classes": ["Low Risk", "Moderate Risk", "High Risk"],
            "train_samples": int(split3),
            "test_samples": int(len(X3) - split3),
            "test_accuracy": round(float(acc_risk), 3),
            "synthetic_test_accuracy": round(float(acc_risk), 3)
        }
    }

    metrics_file = models_dir / "metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Export Trained Weights / Structures to portable JSON
    trained_export = {
        "version": "1.0.0",
        "timestamp": "2026-10-30",
        "provenance": "synthetic_demonstration_models",
        "yield_forest": rf_yield.to_dict(),
        "price_tree": tree_price.root.to_dict(),
        "risk_tree": clf_risk.to_dict(),
        "feature_schemas": {
            "yield": feat1,
            "price": feat2,
            "risk": feat3
        }
    }

    models_json_file = models_dir / "trained_models.json"
    with open(models_json_file, "w", encoding="utf-8") as f:
        json.dump(trained_export, f)

    print(f"Models successfully trained and exported to {models_json_file} and {metrics_file}")
    return metrics

if __name__ == "__main__":
    train_and_export_all()
