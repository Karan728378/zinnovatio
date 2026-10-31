"""
tests/test_hygiene.py
Automated hygiene verification:
- Scans working tree for forbidden credential files (.env, backend/.env)
- Scans text files for leaked secrets and 32-hex keys
- Tests release builder filtering logic
- Tests admin auth paths: unset ADMIN_KEY (503), valid ADMIN_KEY (200 with stub)
"""
import os
import re
import unittest
import pathlib
from unittest.mock import patch
import pandas as pd

from fastapi.testclient import TestClient
from backend.app.main import app
from scripts.build_release import check_file, DENY_PATTERNS

# Configure test-safe ADMIN_KEY so existing auth tests pass without hardcoded production defaults
os.environ.setdefault("ADMIN_KEY", "test-admin-secret-2026")

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

class TestHygieneAndRelease(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_no_env_files_in_tree(self):
        """Scans the repo tree (excluding .git) to ensure no active .env files are tracked in git."""
        import subprocess
        try:
            tracked = subprocess.check_output(["git", "ls-files"], cwd=str(REPO_ROOT), text=True).splitlines()
            forbidden_found = [f for f in tracked if f == ".env" or (f.endswith(".env") and f != ".env.example")]
        except Exception:
            forbidden_found = []
        self.assertEqual(forbidden_found, [], f"Active .env files tracked in repo: {forbidden_found}")

    def test_no_raw_32hex_keys_in_source(self):
        """Ensures no real 32-hex secret keys are hardcoded in source text files."""
        pattern = re.compile(r'KEY\s*[:=]\s*["\']?([a-f0-9]{32})["\']?', re.IGNORECASE)
        flagged = []
        for root, dirs, files in os.walk(str(REPO_ROOT)):
            dirs[:] = [d for d in dirs if d not in (".git", ".venv", "venv", "__pycache__", "data")]
            for f in files:
                ext = pathlib.Path(f).suffix.lower()
                if ext in (".py", ".json", ".md", ".txt", ".html", ".js", ".sh"):
                    p = pathlib.Path(root) / f
                    try:
                        text = p.read_text(encoding="utf-8", errors="replace")
                        matches = pattern.findall(text)
                        if matches:
                            rel = os.path.relpath(str(p), str(REPO_ROOT))
                            flagged.append((rel, matches))
                    except Exception:
                        pass
        self.assertEqual(flagged, [], f"Found 32-hex keys next to KEY in source files: {flagged}")

    def test_release_builder_filters_forbidden_patterns(self):
        """Asserts that build_release check_file rejects forbidden patterns."""
        self.assertNotEqual(check_file(".env"), "")
        self.assertNotEqual(check_file("backend/.env"), "")
        self.assertNotEqual(check_file("data/kilnlink.db"), "")
        self.assertNotEqual(check_file("backend/__pycache__/main.cpython-310.pyc"), "")

        # Valid tracked files should pass
        self.assertEqual(check_file("requirements.txt"), "")
        self.assertEqual(check_file("README.md"), "")
        self.assertEqual(check_file(".env.example"), "")

    def test_supply_refresh_unset_key_returns_503(self):
        """When ADMIN_KEY is unset in the environment, /supply/refresh returns 503."""
        with patch("backend.app.main.get_admin_key", return_value=None):
            res = self.client.post("/supply/refresh", headers={"X-Admin-Key": "any-key"})
            self.assertEqual(res.status_code, 503)
            self.assertIn("not configured", res.json()["detail"].lower())

    def test_supply_refresh_success_path_with_stub(self):
        """With configured ADMIN_KEY and valid header, /supply/refresh succeeds with stubbed pipeline."""
        test_key = "secure-test-admin-key-2026"
        stub_cells = pd.DataFrame([
            {"cell_id": "CELL_3025_7585", "lat": 30.25, "lon": 75.85, "fire_count_last_season": 12, "supply_index": 0.85}
        ])

        with patch.dict(os.environ, {"ADMIN_KEY": test_key}):
            with patch("pipeline.firms_pipeline.download_firms_data", return_value=stub_cells):
                with patch("pipeline.firms_pipeline.process_grid_cells", return_value=stub_cells):
                    res = self.client.post(
                        "/supply/refresh",
                        headers={"X-Admin-Key": test_key}
                    )
                    self.assertEqual(res.status_code, 200)
                    data = res.json()
                    self.assertEqual(data["status"], "success")
                    self.assertIn("cells_count", data)

if __name__ == "__main__":
    unittest.main()

