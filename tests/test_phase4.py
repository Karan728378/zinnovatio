"""
tests/test_phase4.py
Phase 4 test suite covering:
- ID rollover (D999->D1000, S999->S1000)
- Tamper detection x4 scenarios
- XSS round-trip sanitization
- Admin-key paths (correct, missing, wrong, unset)
- Month parameter injection attempts
- NaN/inf/huge float rejection
- Dispatch allocation invariants
- Pipeline IST conversion accuracy
"""
import os
import re
import json
import sqlite3
import tempfile
import unittest
import datetime
from unittest.mock import patch
from fastapi.testclient import TestClient

# Ensure test ADMIN_KEY is set before importing app
os.environ.setdefault("ADMIN_KEY", "test-admin-secret-2026")
os.environ.setdefault("DEMO_MODE", "1")

from backend.app.main import app
from backend.app.db import init_db, get_connection
from backend.app.receipts import (
    canonical_receipt_payload, compute_hash, GENESIS_HASH, verify_receipt_chain
)
from pipeline.firms_pipeline import acq_time_to_ist


class TestIDRollover(unittest.TestCase):
    """Tests that delivery and supplier IDs support numeric rollover beyond 3 digits."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.environ["KILNLINK_DB_PATH"] = self.db_path
        os.environ.setdefault("ADMIN_KEY", "test-admin-secret-2026")
        os.environ.setdefault("DEMO_MODE", "1")
        init_db(force_reload_seeds=True, db_path=self.db_path)
        self.client = TestClient(app)

    def tearDown(self):
        os.close(self.db_fd)
        del os.environ["KILNLINK_DB_PATH"]

    def test_delivery_id_rollover_d999_to_d1000(self):
        """D999 -> D1000 when delivery_id sequence crosses 999."""
        conn = get_connection(self.db_path)
        cur = conn.cursor()
        # Manually insert a delivery with id D999
        cur.execute(
            "INSERT INTO deliveries (delivery_id, kiln_id, supplier_id, date, tonnes, form, photo_ref, receipt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("D999", "K001", "S001", "2026-11-01", 5.0, "bale", "slip.jpg", None)
        )
        conn.commit()
        conn.close()

        # Now POST a delivery - should get D1000
        payload = {
            "kiln_id": "K001",
            "supplier_id": "S001",
            "date": "2026-11-02",
            "tonnes": 5.0,
            "form": "bale",
            "photo_ref": "test.jpg"
        }
        res = self.client.post("/deliveries", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["delivery_id"], "D1000")

    def test_supplier_id_rollover_s999_to_s1000(self):
        """S999 -> S1000 when supplier_id sequence crosses 999."""
        conn = get_connection(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO suppliers (supplier_id, name, kind, lat, lon, village, straw_form, price_per_tonne, available_tonnes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("S999", "Test Supplier 999", "farmer", 30.25, 75.85, "Sangrur", "pellet", 2400.0, 50.0)
        )
        conn.commit()
        conn.close()

        payload = {
            "name": "New Rollover Supplier",
            "village": "Dhuri Rural",
            "straw_form": "bale",
            "tonnes": 30.0,
            "price_per_tonne": 1400.0,
            "kind": "farmer",
            "lat": 30.20,
            "lon": 75.90
        }
        res = self.client.post("/listings", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["supplier_id"], "S1000")


class TestTamperDetection(unittest.TestCase):
    """Verifies receipt chain detects x4 tamper scenarios."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.environ["KILNLINK_DB_PATH"] = self.db_path
        os.environ.setdefault("ADMIN_KEY", "test-admin-secret-2026")
        os.environ.setdefault("DEMO_MODE", "1")
        init_db(force_reload_seeds=True, db_path=self.db_path)
        self.client = TestClient(app)

        # Ensure at least one delivery/receipt in chain
        payload = {
            "kiln_id": "K001",
            "supplier_id": "S001",
            "date": "2026-11-05",
            "tonnes": 5.0,
            "form": "bale",
            "photo_ref": "slip_tamper_test.jpg"
        }
        res = self.client.post("/deliveries", json=payload)
        self.assertEqual(res.status_code, 200)
        self.test_delivery_id = res.json()["delivery_id"]
        self.test_receipt_id = res.json()["receipt"]

    def tearDown(self):
        os.close(self.db_fd)
        del os.environ["KILNLINK_DB_PATH"]

    def _verify(self):
        res = self.client.get("/receipts/verify")
        self.assertEqual(res.status_code, 200)
        return res.json()

    def test_tamper1_modified_delivery_tonnes(self):
        """Editing deliveries.tonnes triggers is_valid: False on verify."""
        conn = get_connection(self.db_path)
        cur = conn.cursor()
        # Bypass trigger by dropping trigger temporarily, editing, re-enabling
        cur.execute("DROP TRIGGER IF EXISTS prevent_receipt_update;")
        cur.execute("UPDATE deliveries SET tonnes = 99.99 WHERE delivery_id = ?;", (self.test_delivery_id,))
        conn.commit()
        conn.close()

        result = self._verify()
        self.assertFalse(result["is_valid"], "Modified delivery tonnes must invalidate chain")
        self.assertGreater(result["broken_links_count"], 0)

    def test_tamper2_modified_receipt_hash(self):
        """Editing delivery_receipts.current_hash triggers is_valid: False."""
        conn = get_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("DROP TRIGGER IF EXISTS prevent_receipt_update;")
        cur.execute(
            "UPDATE delivery_receipts SET current_hash = 'deadbeefdeadbeefdeadbeefdeadbeef0000000000000000000000000000dead' WHERE receipt_id = ?;",
            (self.test_receipt_id,)
        )
        conn.commit()
        conn.close()

        result = self._verify()
        self.assertFalse(result["is_valid"], "Modified receipt hash must invalidate chain")
        self.assertGreater(result["broken_links_count"], 0)

    def test_tamper3_deleted_tail_receipt(self):
        """Deleting tail receipts triggers chain truncation detection."""
        conn = get_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("DROP TRIGGER IF EXISTS prevent_receipt_delete;")
        cur.execute("DELETE FROM delivery_receipts WHERE receipt_id = ?;", (self.test_receipt_id,))
        conn.commit()
        conn.close()

        result = self._verify()
        self.assertFalse(result["is_valid"], "Deleted tail receipt must invalidate chain via truncation check")

    def test_tamper4_orphan_delivery_without_receipt(self):
        """Inserting a delivery without a corresponding receipt triggers is_valid: False."""
        conn = get_connection(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO deliveries (delivery_id, kiln_id, supplier_id, date, tonnes, form, photo_ref, receipt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("D_ORPHAN", "K001", "S001", "2026-11-06", 3.0, "bale", "orphan.jpg", None)
        )
        conn.commit()
        conn.close()

        result = self._verify()
        self.assertFalse(result["is_valid"], "Orphan delivery without receipt must invalidate chain")


class TestXSSRoundTrip(unittest.TestCase):
    """Ensures XSS payload names are sanitized and not echoed back dangerously."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.environ["KILNLINK_DB_PATH"] = self.db_path
        os.environ.setdefault("ADMIN_KEY", "test-admin-secret-2026")
        init_db(force_reload_seeds=True, db_path=self.db_path)
        self.client = TestClient(app)

    def tearDown(self):
        os.close(self.db_fd)
        del os.environ["KILNLINK_DB_PATH"]

    def test_xss_name_is_sanitized(self):
        """Supplier names with XSS payloads must be sanitized by schema validator."""
        # Pydantic schema strips < and > characters
        payload = {
            "name": '"><img src=x onerror=1>Test Farmer',
            "village": "Sangrur",
            "straw_form": "bale",
            "tonnes": 20.0,
            "price_per_tonne": 1400.0,
            "kind": "farmer",
            "lat": 30.25,
            "lon": 75.85
        }
        res = self.client.post("/listings", json=payload)
        self.assertEqual(res.status_code, 200)
        # Get the supplier ID and verify name was sanitized
        sup_id = res.json()["supplier_id"]
        conn = get_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM suppliers WHERE supplier_id = ?;", (sup_id,))
        stored_name = cur.fetchone()[0]
        conn.close()
        self.assertNotIn("<", stored_name, "< character must be stripped from stored supplier name")
        self.assertNotIn(">", stored_name, "> character must be stripped from stored supplier name")


class TestAdminKeyPaths(unittest.TestCase):
    """Tests all 4 admin-key scenarios for /supply/refresh."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.environ["KILNLINK_DB_PATH"] = self.db_path
        init_db(force_reload_seeds=True, db_path=self.db_path)
        self.client = TestClient(app)

    def tearDown(self):
        os.close(self.db_fd)
        del os.environ["KILNLINK_DB_PATH"]
        os.environ.setdefault("ADMIN_KEY", "test-admin-secret-2026")

    def test_admin_correct_key_succeeds(self):
        """Correct ADMIN_KEY with stubbed pipeline succeeds (200)."""
        import pandas as pd
        stub_cells = pd.DataFrame([
            {"cell_id": "CELL_3025_7585", "lat": 30.25, "lon": 75.85, "fire_count_last_season": 5, "supply_index": 0.7}
        ])
        test_key = "test-admin-secret-2026"
        os.environ["ADMIN_KEY"] = test_key
        with patch("pipeline.firms_pipeline.download_firms_data", return_value=stub_cells):
            with patch("pipeline.firms_pipeline.process_grid_cells", return_value=stub_cells):
                res = self.client.post("/supply/refresh", headers={"X-Admin-Key": test_key})
        self.assertEqual(res.status_code, 200)

    def test_admin_missing_key_returns_401(self):
        """Missing X-Admin-Key header returns 401 when key is configured."""
        os.environ["ADMIN_KEY"] = "test-admin-secret-2026"
        res = self.client.post("/supply/refresh")
        self.assertEqual(res.status_code, 401)

    def test_admin_wrong_key_returns_401(self):
        """Wrong X-Admin-Key header returns 401 when key is configured."""
        os.environ["ADMIN_KEY"] = "test-admin-secret-2026"
        res = self.client.post("/supply/refresh", headers={"X-Admin-Key": "definitely-wrong-key"})
        self.assertEqual(res.status_code, 401)

    def test_admin_unset_key_returns_503(self):
        """503 when ADMIN_KEY is unset in server environment."""
        with patch("backend.app.main.get_admin_key", return_value=None):
            res = self.client.post("/supply/refresh", headers={"X-Admin-Key": "any-key"})
        self.assertEqual(res.status_code, 503)


class TestMonthParamInjection(unittest.TestCase):
    """Ensures month parameter injection attempts are rejected cleanly."""

    def setUp(self):
        self.client = TestClient(app)

    def test_month_sql_wildcard_rejected(self):
        """Month with SQL wildcard % is rejected as invalid format."""
        res = self.client.get("/kilns/K003/needs?month=2026-11%25")
        # Should get 400 Bad Request (invalid month format)
        self.assertEqual(res.status_code, 400)

    def test_month_underscore_wildcard_rejected(self):
        """Month with underscore wildcard is rejected as invalid format."""
        res = self.client.get("/kilns/K003/needs?month=2026-1_")
        self.assertEqual(res.status_code, 400)

    def test_month_injection_string_rejected(self):
        """Month injection string is rejected as invalid format."""
        res = self.client.get("/kilns/K003/needs?month=2026-11 OR 1=1")
        self.assertEqual(res.status_code, 400)

    def test_month_format_too_short_rejected(self):
        """Single digit month is rejected as invalid format."""
        res = self.client.get("/kilns/K003/needs?month=2026-1")
        self.assertEqual(res.status_code, 400)


class TestNaNInfFloatRejection(unittest.TestCase):
    """Tests rejection of NaN, infinity, and extremely large floats."""

    def setUp(self):
        self.client = TestClient(app)

    def test_delivery_nan_tonnes_rejected(self):
        """NaN tonnes in delivery request is rejected (422)."""
        import json
        # JSON cannot encode NaN natively; use string workaround
        raw_payload = '{"kiln_id": "K001", "supplier_id": "S001", "date": "2026-11-05", "tonnes": NaN, "form": "bale"}'
        res = self.client.post(
            "/deliveries",
            content=raw_payload,
            headers={"Content-Type": "application/json"}
        )
        self.assertIn(res.status_code, [400, 422])

    def test_predict_yield_huge_acres_clamped(self):
        """Very large acres value is clamped internally and returns a valid prediction."""
        payload = {
            "acres": 1e15,
            "variety_idx": 0,
            "grain_yield_qtl_acre": 20.0,
            "ndvi": 0.75,
            "cutting_height_cm": 20.0
        }
        res = self.client.post("/predict/yield", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("predicted_straw_tonnes", data)
        # Should not return inf or NaN
        import math
        val = data["predicted_straw_tonnes"]
        self.assertFalse(math.isinf(val), "predicted_straw_tonnes must not be inf")
        self.assertFalse(math.isnan(val), "predicted_straw_tonnes must not be NaN")


class TestDispatchInvariants(unittest.TestCase):
    """Verifies auto-dispatch simulation allocation invariants."""

    def setUp(self):
        self.client = TestClient(app)

    def test_dispatch_allocation_does_not_exceed_stock(self):
        """Each simulated allocation must not exceed available supplier stock."""
        res = self.client.post("/dispatch/simulate?month=2026-11")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Get current supplier stocks
        sup_res = self.client.get("/kilns/K001/suppliers")
        sup_data = sup_res.json()
        stock_map = {s["supplier_id"]: s["available_tonnes"] for s in sup_data["suppliers"]}

        # Sum allocations per supplier
        alloc_map = {}
        for alloc in data.get("allocations", []):
            sid = alloc["supplier_id"]
            alloc_map[sid] = alloc_map.get(sid, 0.0) + alloc["allocated_tonnes"]

        for sid, allocated in alloc_map.items():
            if sid in stock_map:
                self.assertLessEqual(
                    allocated,
                    stock_map[sid] + 0.01,  # Allow tiny float tolerance
                    f"Supplier {sid} allocated {allocated} but stock is only {stock_map[sid]}"
                )

    def test_dispatch_allocated_does_not_exceed_gap(self):
        """Allocated tonnes per kiln must not exceed the calculated gap."""
        res = self.client.post("/dispatch/simulate?month=2026-11")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        for kiln_summary in data.get("kiln_summaries", []):
            gap = kiln_summary.get("gap_tonnes", 0.0)
            allocated = kiln_summary.get("allocated_tonnes", 0.0)
            self.assertLessEqual(
                allocated,
                gap + 0.01,
                f"Kiln {kiln_summary.get('kiln_id')} allocated {allocated} exceeds gap {gap}"
            )

    def test_dispatch_total_costs_computed(self):
        """Total estimated cost field must be non-negative."""
        res = self.client.post("/dispatch/simulate?month=2026-11")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data.get("total_estimated_cost", 0.0), 0.0)


class TestPipelineISTConversion(unittest.TestCase):
    """Tests pipeline acq_time_to_ist() UTC->IST conversion accuracy."""

    def test_0807_converts_to_1337_ist(self):
        """acq_time 0807 (08:07 UTC) -> 13:37 IST."""
        h, m, fmt = acq_time_to_ist(807)
        self.assertEqual(h, 13)
        self.assertEqual(m, 37)
        self.assertEqual(fmt, "13:37")

    def test_2053_converts_to_0223_ist(self):
        """acq_time 2053 (20:53 UTC) -> 02:23 IST next day."""
        h, m, fmt = acq_time_to_ist(2053)
        self.assertEqual(h, 2)
        self.assertEqual(m, 23)
        self.assertEqual(fmt, "02:23")

    def test_2359_wraps_to_0529_ist(self):
        """acq_time 2359 (23:59 UTC) -> 05:29 IST next day (midnight wrap)."""
        h, m, fmt = acq_time_to_ist(2359)
        self.assertEqual(h, 5)
        self.assertEqual(m, 29)
        self.assertEqual(fmt, "05:29")

    def test_0000_converts_to_0530_ist(self):
        """acq_time 0000 (00:00 UTC midnight) -> 05:30 IST."""
        h, m, fmt = acq_time_to_ist(0)
        self.assertEqual(h, 5)
        self.assertEqual(m, 30)
        self.assertEqual(fmt, "05:30")

    def test_1330_converts_to_1900_ist(self):
        """acq_time 1330 (13:30 UTC, typical VIIRS ascending node) -> 19:00 IST."""
        h, m, fmt = acq_time_to_ist(1330)
        self.assertEqual(h, 19)
        self.assertEqual(m, 0)
        self.assertEqual(fmt, "19:00")


class TestMLRangeFlags(unittest.TestCase):
    """Tests that ML endpoints handle out-of-training-range values gracefully."""

    def setUp(self):
        self.client = TestClient(app)

    def test_predict_yield_extreme_inputs_return_result(self):
        """Extreme inputs are clamped and return a valid result (not error)."""
        payload = {
            "acres": -999.0,  # negative -> clamped to 0
            "variety_idx": 99,  # out of range -> clamped to 2
            "grain_yield_qtl_acre": -50.0,  # negative -> clamped to 0
            "ndvi": 5.0,  # > 1.0 -> clamped to 1.0
            "cutting_height_cm": -10.0  # negative -> clamped to 5.0
        }
        res = self.client.post("/predict/yield", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("predicted_straw_tonnes", data)

    def test_predict_price_extreme_inputs_return_result(self):
        """Extreme price prediction inputs are clamped and return valid result."""
        payload = {
            "distance_km": -100.0,
            "form_idx": 99,
            "moisture_pct": 200.0,
            "harvest_week": -5,
            "density_idx": 5.0
        }
        res = self.client.post("/predict/price", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("predicted_delivered_price_per_tonne", data)


class TestConcurrentDeliveries(unittest.TestCase):
    """20 parallel threads attempting 5t deliveries against 40t supplier stock."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.environ["KILNLINK_DB_PATH"] = self.db_path
        os.environ.setdefault("ADMIN_KEY", "test-admin-secret-2026")
        os.environ.setdefault("DEMO_MODE", "1")
        init_db(force_reload_seeds=True, db_path=self.db_path)
        self.client = TestClient(app)

    def tearDown(self):
        os.close(self.db_fd)
        if "KILNLINK_DB_PATH" in os.environ:
            del os.environ["KILNLINK_DB_PATH"]

    def test_concurrent_deliveries_inventory_and_hash_chain(self):
        """20 parallel threads attempt 5t deliveries against 40t stock: exactly 8 succeed, stock==0, chain valid."""
        import concurrent.futures

        # Create a dedicated supplier S099 with exactly 40.0t stock
        conn = get_connection(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO suppliers (supplier_id, name, kind, lat, lon, village, straw_form, price_per_tonne, available_tonnes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("S099", "Concurrent Test Supplier", "farmer", 30.5, 75.9, "Malerkotla", "chopped", 1600.0, 40.0)
        )
        conn.commit()
        conn.close()

        def make_delivery(idx):
            payload = {
                "kiln_id": "K003",
                "supplier_id": "S099",
                "date": "2026-11-02",
                "tonnes": 5.0,
                "form": "chopped",
                "photo_ref": f"concur_{idx}.jpg"
            }
            return self.client.post("/deliveries", json=payload)

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_delivery, i) for i in range(20)]
            results = [f.result() for f in futures]

        status_codes = [r.status_code for r in results]
        success_count = status_codes.count(200)
        conflict_count = status_codes.count(409)

        self.assertEqual(success_count, 8, f"Expected exactly 8 successes (40t / 5t), got {success_count}. Statuses: {status_codes}")
        self.assertEqual(conflict_count, 12, f"Expected exactly 12 409 conflicts, got {conflict_count}")

        # Assert stock is exactly 0.0 and never negative
        conn = get_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT available_tonnes FROM suppliers WHERE supplier_id = 'S099'")
        remaining = cur.fetchone()[0]
        self.assertEqual(remaining, 0.0, "Supplier stock must be exactly 0.0")

        # Verify receipt hash chain integrity
        res_verify = self.client.get("/receipts/verify")
        self.assertEqual(res_verify.status_code, 200)
        verify_data = res_verify.json()
        self.assertTrue(verify_data["is_valid"], "Receipt chain must be valid after concurrent writes")
        self.assertEqual(verify_data["broken_links_count"], 0, "No broken links in receipt chain")
        conn.close()


if __name__ == "__main__":
    unittest.main()

