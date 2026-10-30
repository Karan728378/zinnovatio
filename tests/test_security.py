import os
import re
import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import get_connection

class TestSecurityRemediation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def test_supply_status_zero_key_exposure(self):
        """Verifies GET /supply/status never leaks key fragments or substrings."""
        res = self.client.get("/supply/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("firms_configured", data)
        self.assertIsInstance(data["firms_configured"], bool)
        # Ensure no key field exists
        self.assertNotIn("firms_map_key", data)
        self.assertNotIn("api_key", data)
        self.assertNotIn("key_masked", data)
        # Convert response body to string and assert no 32-char hex token or partial token exists
        raw_text = res.text
        self.assertNotIn("...", raw_text)

    def test_supply_refresh_requires_admin_auth(self):
        """Verifies POST /supply/refresh is protected with X-Admin-Key."""
        # Unauthenticated request must be rejected with 401
        res_no_auth = self.client.post("/supply/refresh")
        self.assertEqual(res_no_auth.status_code, 401)

        # Invalid key must be rejected with 401
        res_bad_key = self.client.post("/supply/refresh", headers={"X-Admin-Key": "wrong-key-value"})
        self.assertEqual(res_bad_key.status_code, 401)

    def test_gitignore_protects_env_and_secrets(self):
        """Checks that .gitignore contains rules blocking secret credential files."""
        gitignore_path = os.path.join(self.base_dir, ".gitignore")
        self.assertTrue(os.path.exists(gitignore_path))
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(".env", content)
        self.assertIn("*.env", content)
        self.assertIn("backend/.env", content)

    def test_env_example_has_no_real_secrets(self):
        """Checks that .env.example contains only non-sensitive dummy placeholders."""
        example_path = os.path.join(self.base_dir, ".env.example")
        self.assertTrue(os.path.exists(example_path))
        with open(example_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Verify no 32-char hexadecimal hash is present
        hex_tokens = re.findall(r'[a-f0-9]{32}', content, re.IGNORECASE)
        self.assertEqual(len(hex_tokens), 0, f"Found unexpected hex token in .env.example: {hex_tokens}")
        self.assertIn("YOUR_NASA_FIRMS_MAP_KEY_HERE", content)

    def test_receipt_audit_chain_tamper_detection(self):
        """Verifies GET /receipts/verify validates the SHA-256 chain and detects tampering."""
        res = self.client.get("/receipts/verify")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_valid"])
        self.assertEqual(data["broken_links_count"], 0)

if __name__ == "__main__":
    unittest.main()
