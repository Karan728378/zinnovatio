"""
KilnLink API Integration Tests (FastAPI TestClient)
Verifies all endpoints from Section 5.3 and 5.4 contract.
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
from backend.app.db import init_db

class TestKilnLinkAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db(force_reload_seeds=True)
        cls.client = TestClient(app)

    def test_01_health_and_config(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

        res_cfg = self.client.get("/config")
        self.assertEqual(res_cfg.status_code, 200)
        data = res_cfg.json()
        self.assertEqual(data["demo_month"], "2026-11")
        self.assertIn("2026-11", data["mandate_share"])
        self.assertEqual(data["mandate_share"]["2026-11"], 0.30)

    def test_02_supply_map(self):
        res = self.client.get("/supply/map")
        self.assertEqual(res.status_code, 200)
        cells = res.json()
        self.assertGreater(len(cells), 10)
        self.assertIn("cell_id", cells[0])
        self.assertIn("supply_index", cells[0])

    def test_03_kilns_list(self):
        res = self.client.get("/kilns")
        self.assertEqual(res.status_code, 200)
        kilns = res.json()
        self.assertEqual(len(kilns), 12)
        self.assertEqual(kilns[0]["kiln_id"], "K001")

    def test_04_kiln_needs(self):
        res = self.client.get("/kilns/K003/needs?month=2026-11")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["kiln_id"], "K003")
        self.assertEqual(data["month"], "2026-11")
        self.assertEqual(data["mandate_share"], 0.30)
        self.assertEqual(data["monthly_fuel_tonnes"], 120.0)
        self.assertEqual(data["straw_needed_tonnes"], 36.0)
        self.assertEqual(data["delivered_tonnes"], 10.0)
        self.assertEqual(data["gap_tonnes"], 26.0)
        self.assertEqual(data["note"], "SAMPLE DATA")

    def test_05_kiln_suppliers(self):
        res = self.client.get("/kilns/K003/suppliers")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["kiln_id"], "K003")
        self.assertEqual(data["coal_cost_per_tonne"], 9000.0)
        self.assertGreater(len(data["suppliers"]), 0)
        first_sup = data["suppliers"][0]
        self.assertIn("delivered_cost_per_tonne", first_sup)
        self.assertLess(first_sup["delivered_cost_per_tonne"], 9000.0)

    def test_06_create_listing(self):
        payload = {
            "name": "Sample Farmer Test Singh",
            "village": "Sunam Rural",
            "straw_form": "bale",
            "tonnes": 25.0,
            "price_per_tonne": 1400.0,
            "kind": "farmer",
            "lat": 30.15,
            "lon": 75.80
        }
        res = self.client.post("/listings", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("listing_id", data)
        self.assertEqual(data["status"], "active")
        self.assertIn("nearest_kilns", data)

    def test_07_record_delivery_and_verify_compliance_change(self):
        res1 = self.client.get("/kilns/K003/needs?month=2026-11")
        init_delivered = res1.json()["delivered_tonnes"]

        d1 = {
            "kiln_id": "K003",
            "supplier_id": "S005",
            "date": "2026-11-03",
            "tonnes": 15.0,
            "form": "chopped",
            "photo_ref": "slip_k003_02.jpg"
        }
        resp1 = self.client.post("/deliveries", json=d1)
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp1.json()["status"], "recorded")
        self.assertIn("receipt", resp1.json())

        d2 = {
            "kiln_id": "K003",
            "supplier_id": "S005",
            "date": "2026-11-04",
            "tonnes": 12.0,
            "form": "chopped",
            "photo_ref": "slip_k003_03.jpg"
        }
        resp2 = self.client.post("/deliveries", json=d2)
        self.assertEqual(resp2.status_code, 200)

        res2 = self.client.get("/kilns/K003/needs?month=2026-11")
        updated_delivered = res2.json()["delivered_tonnes"]
        self.assertEqual(updated_delivered, init_delivered + 27.0)

        res_summary = self.client.get("/compliance/summary?month=2026-11")
        self.assertEqual(res_summary.status_code, 200)
        summary = res_summary.json()
        k003_item = next(k for k in summary["kilns"] if k["kiln_id"] == "K003")
        self.assertEqual(k003_item["straw_tonnes"], 37.0)
        self.assertEqual(k003_item["status"], "meets_target")

if __name__ == "__main__":
    unittest.main()
