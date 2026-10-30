import os
import unittest
from backend.app.db import get_connection, init_db

class TestDatabasePersistence(unittest.TestCase):
    def test_idempotent_init_preserves_records(self):
        """Ensures that repeated init_db calls do not drop tables or delete deliveries."""
        # Check current count of deliveries
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM deliveries;")
        initial_delivery_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM kilns;")
        initial_kiln_count = cur.fetchone()[0]
        conn.close()

        self.assertGreater(initial_delivery_count, 0)
        self.assertEqual(initial_kiln_count, 12)

        # Call init_db(force_reload_seeds=False) simulating a server restart
        init_db(force_reload_seeds=False)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM deliveries;")
        post_delivery_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM kilns;")
        post_kiln_count = cur.fetchone()[0]
        conn.close()

        # Counts must match exactly
        self.assertEqual(initial_delivery_count, post_delivery_count)
        self.assertEqual(initial_kiln_count, post_kiln_count)

    def test_foreign_keys_are_enforced(self):
        """Ensures SQLite foreign key constraints are active on connections."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys;")
        fk_status = cur.fetchone()[0]
        conn.close()
        self.assertEqual(fk_status, 1, "Foreign key enforcement must be active")

if __name__ == "__main__":
    unittest.main()

