"""
Test suite initialization.
Configures test-safe defaults for environment variables.
Guarantees tests use an isolated temporary SQLite database, never data/kilnlink.db.
"""
import os
import atexit
import tempfile

os.environ.setdefault("ADMIN_KEY", "test-admin-secret-2026")
os.environ.setdefault("DEMO_MODE", "1")

if "KILNLINK_DB_PATH" not in os.environ:
    temp_fd, temp_db = tempfile.mkstemp(suffix="_suite_default.db")
    os.close(temp_fd)
    os.environ["KILNLINK_DB_PATH"] = temp_db

    def _cleanup_suite_db():
        try:
            if os.path.exists(temp_db):
                os.remove(temp_db)
        except OSError:
            pass

    atexit.register(_cleanup_suite_db)
