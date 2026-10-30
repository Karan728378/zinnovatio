"""
tests/conftest.py
Test isolation and fixtures for KilnLink test suites.
Ensures tests run in a dedicated temporary SQLite database, never touching data/kilnlink.db.
"""
import os
import tempfile
import unittest
from fastapi.testclient import TestClient

os.environ.setdefault("ADMIN_KEY", "test-admin-secret-2026")
os.environ.setdefault("DEMO_MODE", "1")

from backend.app.main import app
from backend.app.db import init_db


class TempDBTestCase(unittest.TestCase):
    """
    Base test case providing an isolated temporary database for each test run.
    Ensures zero interaction with production or development databases.
    """

    def setUp(self):
        super().setUp()
        self.db_fd, self.db_path = tempfile.mkstemp(suffix="_test.db")
        os.close(self.db_fd)
        os.environ["KILNLINK_DB_PATH"] = self.db_path
        os.environ.setdefault("ADMIN_KEY", "test-admin-secret-2026")
        os.environ.setdefault("DEMO_MODE", "1")
        init_db(force_reload_seeds=True, db_path=self.db_path)
        self.client = TestClient(app)

    def tearDown(self):
        if "KILNLINK_DB_PATH" in os.environ:
            del os.environ["KILNLINK_DB_PATH"]
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except OSError:
            pass
        super().tearDown()


# Pytest fixtures if pytest is used
try:
    import pytest

    @pytest.fixture
    def isolated_db():
        fd, path = tempfile.mkstemp(suffix="_pytest.db")
        os.close(fd)
        os.environ["KILNLINK_DB_PATH"] = path
        init_db(force_reload_seeds=True, db_path=path)
        yield path
        if "KILNLINK_DB_PATH" in os.environ:
            del os.environ["KILNLINK_DB_PATH"]
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

    @pytest.fixture
    def test_client(isolated_db):
        return TestClient(app)
except ImportError:
    pass

