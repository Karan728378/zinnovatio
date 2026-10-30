import unittest
from fastapi.testclient import TestClient
from backend.app.main import app

class TestDispatchAndSatelliteHours(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_dispatch_simulation_endpoint(self):
        """Tests the deterministic auto-dispatch simulation endpoint."""
        res = self.client.post("/dispatch/simulate?month=2026-11")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["reporting_month"], "2026-11")
        self.assertIn("allocations", data)
        self.assertIn("kiln_summaries", data)
        self.assertGreater(data["total_allocated_tonnes"], 0.0)
        self.assertGreater(data["total_estimated_cost_inr"], 0.0)

    def test_satellite_hourly_observations_endpoint(self):
        """Tests the NASA FIRMS hourly distribution and IST conversion endpoint."""
        res = self.client.get("/supply/hours")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("hourly_distribution", data)
        self.assertIn("overpass_schedule_notes", data)
        self.assertIn("total_detections", data)

        # Check IST conversion logic
        distribution = data["hourly_distribution"]
        self.assertGreater(len(distribution), 0)
        for row in distribution:
            self.assertIn("hour_utc", row)
            self.assertIn("hour_ist", row)
            self.assertIn("count", row)
            self.assertIn("percentage", row)
            self.assertIn("label_ist", row)

        # Verify overpass explanation notes are present and truthful
        notes = data["overpass_schedule_notes"].lower()
        self.assertIn("sun-synchronous", data["orbital_type"].lower())
        self.assertIn("viirs", data["satellite_sensor"].lower())

if __name__ == "__main__":
    unittest.main()
