import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from pipeline.firms_pipeline import (
    get_district,
    generate_15min_temporal_timeline,
    fetch_live_firms_detections,
    PILOT_BBOX,
)

class TestFirmsLiveTelemetry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_pilot_bbox_covers_full_corridor(self):
        """Validates that PILOT_BBOX covers full Punjab-Haryana corridor."""
        self.assertEqual(PILOT_BBOX, [73.80, 28.40, 77.60, 32.60])

    def test_district_reverse_mapping(self):
        """Tests geographic district reverse-mapping for Punjab and Haryana coordinates."""
        # Sangrur center
        self.assertEqual(get_district(30.25, 75.85), "Sangrur")
        # Ludhiana
        self.assertEqual(get_district(30.90, 75.85), "Ludhiana")
        # Karnal (Haryana)
        self.assertEqual(get_district(29.68, 76.98), "Karnal")
        # Default fallback outside custom boxes
        self.assertEqual(get_district(20.0, 80.0), "Punjab")

    def test_15min_temporal_timeline_generation(self):
        """Tests that 24 slots are generated ending at T-30m IST."""
        timeline = generate_15min_temporal_timeline()
        self.assertEqual(len(timeline), 24)
        for slot in timeline:
            self.assertIn("slot_index", slot)
            self.assertIn("ist_label", slot)
            self.assertIn("ist_time", slot)
            self.assertIn("is_live", slot)
            self.assertIn("plumes", slot)
            self.assertIn("peak_k", slot)
            self.assertIn("max_frp", slot)
        # Oldest slot is slot 0, newest is slot 23
        self.assertEqual(timeline[0]["slot_index"], 0)
        self.assertEqual(timeline[-1]["slot_index"], 23)
        self.assertTrue(timeline[-1]["is_live"])

    def test_firms_live_endpoint(self):
        """Tests the GET /supply/firms-live API endpoint."""
        res = self.client.get("/supply/firms-live")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("is_live", data)
        self.assertIn("source", data)
        self.assertIn("fetched_at_ist", data)
        self.assertIn("bbox", data)
        self.assertIn("total_detections", data)
        self.assertIn("detections", data)
        self.assertIn("timeline", data)
        self.assertIn("updated_badge", data)

        self.assertEqual(data["bbox"], [73.80, 28.40, 77.60, 32.60])
        self.assertEqual(len(data["timeline"]), 24)
        if data["detections"]:
            first_det = data["detections"][0]
            self.assertIn("cell_id", first_det)
            self.assertIn("latitude", first_det)
            self.assertIn("longitude", first_det)
            self.assertIn("district", first_det)
            self.assertIn("acq_time_ist", first_det)
            self.assertIn("bright_ti4", first_det)
            self.assertIn("frp", first_det)

    def test_live_fires_all_india_endpoint(self):
        """Tests the GET /api/live-fires endpoint for All-India coverage and required fields."""
        res = self.client.get("/api/live-fires")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        first = data[0]
        self.assertIn("lat", first)
        self.assertIn("lon", first)
        self.assertIn("frp", first)
        self.assertIn("temp_k", first)
        self.assertIn("date", first)
        self.assertIn("time", first)


if __name__ == "__main__":
    unittest.main()

