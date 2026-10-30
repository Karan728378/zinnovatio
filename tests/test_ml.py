"""
Parali Mitra Machine Learning Integration Tests
Tests model loading, yield prediction, dynamic pricing, and fire risk classification.
"""
import sys
import os
import unittest

import importlib.util
class DirectPathFinder:
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        parts = fullname.split('.')
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        rel_path = os.path.join(*parts)
        pkg_init = os.path.join(base_dir, rel_path, '__init__.py')
        mod_py = os.path.join(base_dir, rel_path + '.py')
        if os.path.exists(pkg_init):
            return importlib.util.spec_from_file_location(fullname, pkg_init, submodule_search_locations=[os.path.join(base_dir, rel_path)])
        elif os.path.exists(mod_py):
            return importlib.util.spec_from_file_location(fullname, mod_py)
        return None

if DirectPathFinder not in sys.meta_path:
    sys.meta_path.insert(0, DirectPathFinder)

from fastapi.testclient import TestClient
from backend.app.main import app

class TestMLIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_model_metrics(self):
        res = self.client.get("/models/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("yield_predictor", data)
        self.assertIn("price_predictor", data)
        self.assertIn("fire_risk_classifier", data)
        self.assertGreater(data["yield_predictor"]["test_r2"], 0.85)
        self.assertGreater(data["price_predictor"]["test_r2"], 0.85)

    def test_02_predict_yield(self):
        payload = {
            "acres": 12.0,
            "variety_idx": 1,  # Pusa-44
            "grain_yield_qtl_acre": 30.0,
            "ndvi": 0.80,
            "cutting_height_cm": 15.0
        }
        res = self.client.post("/predict/yield", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("predicted_straw_tonnes", data)
        # 12 acres * 3 tonnes grain * 1.25 ratio ~ 40-45 tonnes
        self.assertGreater(data["predicted_straw_tonnes"], 25.0)
        self.assertLess(data["predicted_straw_tonnes"], 60.0)

    def test_03_predict_price(self):
        payload = {
            "distance_km": 15.0,
            "form_idx": 1,  # Chopped
            "moisture_pct": 14.0,
            "harvest_week": 2,
            "supply_density_index": 0.70
        }
        res = self.client.post("/predict/price", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("predicted_delivered_price_per_tonne", data)
        self.assertIn("savings_vs_coal_per_tonne", data)
        # Delivered price should be between 1600 and 2600
        self.assertGreater(data["predicted_delivered_price_per_tonne"], 1500.0)
        self.assertLess(data["predicted_delivered_price_per_tonne"], 3000.0)
        # Savings vs coal should be > 6000
        self.assertGreater(data["savings_vs_coal_per_tonne"], 6000.0)

    def test_04_predict_fire_risk(self):
        # Critical situation: 6 days to wheat sowing, 40km to kiln, poor machinery
        payload = {
            "days_to_wheat_sowing": 6.0,
            "dist_to_kiln_km": 40.0,
            "machinery_access_score": 1,
            "cell_fire_density": 0.90
        }
        res = self.client.post("/predict/fire-risk", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("risk_category", data)
        self.assertIn("probabilities", data)
        self.assertEqual(data["risk_category"], "High Risk")

if __name__ == "__main__":
    unittest.main()
