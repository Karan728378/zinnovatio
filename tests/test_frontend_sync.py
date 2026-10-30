"""
tests/test_frontend_sync.py
Verifies synchronization across frontend/index.html, index.html, and paralimitra_app.html,
and validates frontend hygiene rules.
"""
import os
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE = os.path.join(REPO_ROOT, "frontend", "index.html")
TARGET_ROOT = os.path.join(REPO_ROOT, "index.html")
TARGET_APP = os.path.join(REPO_ROOT, "paralimitra_app.html")

def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

class TestFrontendSyncAndHygiene(unittest.TestCase):
    """Ensures single source of truth for frontend HTML and proper synchronization."""

    def test_all_three_html_files_exist(self):
        self.assertTrue(os.path.exists(SOURCE), "frontend/index.html must exist")
        self.assertTrue(os.path.exists(TARGET_ROOT), "root index.html must exist")
        self.assertTrue(os.path.exists(TARGET_APP), "paralimitra_app.html must exist")

    def test_all_three_html_files_are_identical(self):
        source_hash = compute_sha256(SOURCE)
        root_hash = compute_sha256(TARGET_ROOT)
        app_hash = compute_sha256(TARGET_APP)

        self.assertEqual(
            source_hash, root_hash,
            "frontend/index.html and index.html must have identical SHA-256 hashes"
        )
        self.assertEqual(
            source_hash, app_hash,
            "frontend/index.html and paralimitra_app.html must have identical SHA-256 hashes"
        )

    def test_no_client_math_random_hash_generation(self):
        """Receipt hash must come from server or cryptographic hash, not Math.random()."""
        with open(SOURCE, "r", encoding="utf-8") as f:
            content = f.read()

        # Check that receipt hash does not use Math.random
        self.assertNotIn(
            "receipt-hash').textContent = Math.random()",
            content,
            "Receipt hash must not be generated via Math.random()"
        )

    def test_punjabi_language_supported(self):
        """Frontend must include Punjabi (pa / Gurmukhi) language dictionary or option."""
        with open(SOURCE, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertTrue(
            "I18N_PA" in content or "ਪੰਜਾਬੀ" in content or "ਪਰਾਲੀ" in content,
            "Frontend must support Punjabi language option"
        )

if __name__ == "__main__":
    unittest.main()

