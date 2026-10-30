"""
tests/test_frontend_sync.py
Verifies synchronization across frontend/index.html, index.html, and paralimitra_app.html,
and validates frontend interactive controls, map sizing, and offline fallbacks.
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

    def test_map_container_has_explicit_css_dimensions(self):
        """Map container must have explicit CSS height and width to prevent zero-height collapse."""
        with open(SOURCE, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('id="regulator-map"', content)
        self.assertTrue(
            'min-height: 580px' in content and 'height: 100%' in content,
            "Map container #regulator-map must have explicit height & min-height"
        )

    def test_offline_cdn_fallbacks_present(self):
        """MapLibre and Leaflet tags must include onerror fallbacks for offline reliability."""
        with open(SOURCE, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("onerror=\"this.onerror=null;this.href='/static/maplibre-gl.css';", content)
        self.assertIn("onerror=\"this.onerror=null;var s=document.createElement('script');s.src='/static/maplibre-gl.js';", content)

    def test_interactive_action_buttons_present(self):
        """Auto-dispatch, FIRMS hours, and receipt audit buttons must exist with handlers."""
        with open(SOURCE, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("openAutoDispatchModal", content)
        self.assertIn("openSatelliteHoursModal", content)
        self.assertIn("openReceiptAuditModal", content)
        self.assertIn("btn-auto-dispatch-action", content)
        self.assertIn("btn-satellite-hours-action", content)
        self.assertIn("btn-receipt-audit-action", content)

    def test_caqm_direction_92_and_month_schedule_controls(self):
        """CAQM Direction 92 pellet filter and month escalation schedule must be interactive."""
        with open(SOURCE, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("updateEligibilityMode", content)
        self.assertIn("pellet_only", content)
        self.assertIn("updateMonthFilter", content)
        self.assertIn("month-filter", content)

    def test_async_syntax_validity_on_submit_delivery(self):
        """submitQuickDelivery must be an async function to avoid syntax errors with await."""
        with open(SOURCE, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("window.submitQuickDelivery = async function", content)

    def test_pilot_region_hubs_present(self):
        """Key Punjab pilot hubs must be defined for floating map labels."""
        with open(SOURCE, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Sangrur District", content)
        self.assertIn("Malerkotla Hub", content)
        self.assertIn("Dhuri Cluster", content)
        self.assertIn("Sunam Sector", content)

if __name__ == "__main__":
    unittest.main()
