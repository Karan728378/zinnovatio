"""
KilnLink Logic and Math Unit Tests (Section 5.5)
"""
import sys
import os
import unittest

# Ensure direct file resolution works across test environments
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

from backend.app.logic import haversine, straw_needed, delivered_cost, compliance_share, rank_suppliers

class TestKilnLinkLogic(unittest.TestCase):

    def setUp(self):
        self.cfg = {
            "transport_per_tonne_km": 6.0,
            "chopping_cost_per_tonne": 150.0,
            "coal_price_per_tonne": 9000.0
        }

    def test_haversine(self):
        dist = haversine(28.6139, 77.2090, 30.7333, 76.7794)
        self.assertAlmostEqual(dist, 238.0, delta=15.0)
        self.assertEqual(haversine(30.0, 75.0, 30.0, 75.0), 0.0)

    def test_straw_needed(self):
        # 30% mandate on 120 tonnes fuel with factor 1.0 = 36 tonnes
        self.assertEqual(straw_needed(0.30, 120.0, 1.0), 36.0)
        # 40% mandate on 100 tonnes = 40 tonnes
        self.assertEqual(straw_needed(0.40, 100.0, 1.0), 40.0)

    def test_delivered_cost(self):
        # Bale form (no chopping): price 1500 + 6 * 10 km = 1560
        cost_bale = delivered_cost(1500.0, 10.0, "bale", self.cfg)
        self.assertEqual(cost_bale, 1560.0)

        # Chopped form (with 150 chopping fee): price 1800 + 6 * 12.4 + 150 = 2024.4
        cost_chopped = delivered_cost(1800.0, 12.4, "chopped", self.cfg)
        self.assertEqual(cost_chopped, 2024.4)

    def test_compliance_share(self):
        self.assertAlmostEqual(compliance_share(10.0, 120.0), 0.0833, places=3)
        self.assertEqual(compliance_share(36.0, 120.0), 0.30)
        self.assertEqual(compliance_share(10.0, 0.0), 0.0)

    def test_rank_suppliers(self):
        kiln = {"lat": 30.20, "lon": 75.80}
        suppliers = [
            {"supplier_id": "S1", "name": "Far Sup", "kind": "farmer", "lat": 30.60, "lon": 75.80, "straw_form": "bale", "price_per_tonne": 1400.0, "available_tonnes": 50},
            {"supplier_id": "S2", "name": "Near Sup", "kind": "aggregator", "lat": 30.22, "lon": 75.81, "straw_form": "chopped", "price_per_tonne": 1500.0, "available_tonnes": 80}
        ]
        ranked = rank_suppliers(kiln, suppliers, self.cfg)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]["supplier_id"], "S2")

if __name__ == "__main__":
    unittest.main()
