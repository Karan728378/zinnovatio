import unittest
from fastapi.testclient import TestClient
from backend.app.main import app

class TestInputValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_delivery_negative_or_zero_tonnes_rejected(self):
        """Rejects non-positive delivery quantities."""
        payload = {
            "kiln_id": "K001",
            "supplier_id": "S001",
            "date": "2026-11-05",
            "tonnes": 0.0,
            "form": "bale",
            "photo_ref": "test.jpg"
        }
        res = self.client.post("/deliveries", json=payload)
        self.assertEqual(res.status_code, 422)

        payload["tonnes"] = -10.0
        res = self.client.post("/deliveries", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_delivery_excessive_tonnes_rejected(self):
        """Rejects absurdly large single delivery (> 500t)."""
        payload = {
            "kiln_id": "K001",
            "supplier_id": "S001",
            "date": "2026-11-05",
            "tonnes": 501.0,
            "form": "bale",
            "photo_ref": "test.jpg"
        }
        res = self.client.post("/deliveries", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_delivery_invalid_form_rejected(self):
        """Rejects straw forms outside {'bale', 'chopped', 'pellet'}."""
        payload = {
            "kiln_id": "K001",
            "supplier_id": "S001",
            "date": "2026-11-05",
            "tonnes": 10.0,
            "form": "liquid",
            "photo_ref": "test.jpg"
        }
        res = self.client.post("/deliveries", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_delivery_invalid_calendar_date_rejected(self):
        """Rejects non-existent calendar dates like 2026-02-31."""
        payload = {
            "kiln_id": "K001",
            "supplier_id": "S001",
            "date": "2026-02-31",
            "tonnes": 5.0,
            "form": "bale",
            "photo_ref": "test.jpg"
        }
        res = self.client.post("/deliveries", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_delivery_inventory_overspend_returns_409(self):
        """Returns 409 Conflict when delivery exceeds available supplier inventory."""
        sup_res = self.client.get("/kilns/K001/suppliers")
        self.assertEqual(sup_res.status_code, 200)
        suppliers = sup_res.json()["suppliers"]
        target_sup = suppliers[0]
        avail = target_sup["available_tonnes"]

        over_order = {
            "kiln_id": "K001",
            "supplier_id": target_sup["supplier_id"],
            "date": "2026-11-05",
            "tonnes": float(avail) + 100.0,
            "form": target_sup["form"],
            "photo_ref": "slip_overspend.jpg"
        }
        res = self.client.post("/deliveries", json=over_order)
        self.assertEqual(res.status_code, 409)
        self.assertIn("exceeds supplier available inventory", res.json()["detail"])

    def test_listing_unknown_supplier_returns_404(self):
        """Returns 404 Not Found when creating listing for non-existent supplier."""
        payload = {
            "name": "Nonexistent Supplier Test",
            "village": "Sangrur",
            "straw_form": "bale",
            "price_per_tonne": 1500.0,
            "tonnes": 20.0,
            "supplier_id": "S999_NONEXISTENT"
        }
        res = self.client.post("/listings", json=payload)
        self.assertEqual(res.status_code, 404)

if __name__ == "__main__":
    unittest.main()
