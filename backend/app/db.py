"""
KilnLink SQLite Database and Seed Loader
Authoritative, persistent, and idempotent database management.
"""
import sqlite3
import os
import json
import pandas as pd
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Persistent application data location by default; configurable via KILNLINK_DB_PATH
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "kilnlink.db")
DB_PATH = os.environ.get("KILNLINK_DB_PATH", DEFAULT_DB_PATH)

CONFIG_PATH = os.path.join(BASE_DIR, "data", "processed", "config.json")
KILNS_CSV = os.path.join(BASE_DIR, "data", "seed", "kilns.csv")
SUPPLIERS_CSV = os.path.join(BASE_DIR, "data", "seed", "suppliers.csv")
DELIVERIES_CSV = os.path.join(BASE_DIR, "data", "seed", "deliveries.csv")
SUPPLY_CELLS_CSV = os.path.join(BASE_DIR, "data", "processed", "supply_cells.csv")

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    target_path = db_path or os.environ.get("KILNLINK_DB_PATH", DB_PATH)
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sqlite3.connect(target_path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except Exception:
        pass
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn

def get_db(db_path: Optional[str] = None):
    """
    FastAPI generator dependency yielding a thread-safe managed SQLite connection.
    Guarantees connection closure on request termination.
    """
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()

def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "demo_month": "2026-11",
        "center_lat": 30.37,
        "center_lon": 75.85,
        "zoom": 9,
        "mandate_share": {
            "2025-11": 0.20,
            "2026-11": 0.30,
            "2027-11": 0.40,
            "2028-11": 0.50
        },
        "share_basis": "weight",
        "straw_to_fuel_factor": 1.0,
        "transport_per_tonne_km": 6.0,
        "chopping_cost_per_tonne": 150.0,
        "coal_price_per_tonne": 9000.0
    }

def init_db(force_reload_seeds: bool = False, db_path: Optional[str] = None):
    """
    Initializes tables idempotently. Existing records are preserved across restarts
    unless explicit force_reload_seeds is True or RESET_DB=1 environment flag is set.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS kilns (
        kiln_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        village TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'Punjab',
        monthly_fuel_tonnes REAL NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        kind TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        village TEXT NOT NULL,
        straw_form TEXT NOT NULL,
        price_per_tonne REAL NOT NULL,
        available_tonnes REAL NOT NULL CHECK (available_tonnes >= 0),
        role TEXT DEFAULT 'Supplier'
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS deliveries (
        delivery_id TEXT PRIMARY KEY,
        kiln_id TEXT NOT NULL,
        supplier_id TEXT NOT NULL,
        date TEXT NOT NULL,
        tonnes REAL NOT NULL CHECK (tonnes > 0),
        form TEXT NOT NULL,
        photo_ref TEXT,
        receipt TEXT,
        FOREIGN KEY (kiln_id) REFERENCES kilns(kiln_id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS supply_cells (
        cell_id TEXT PRIMARY KEY,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        fire_count_last_season INTEGER NOT NULL,
        supply_index REAL NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS listings (
        listing_id TEXT PRIMARY KEY,
        supplier_id TEXT NOT NULL,
        tonnes REAL NOT NULL,
        status TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS delivery_receipts (
        receipt_id TEXT PRIMARY KEY,
        delivery_id TEXT NOT NULL,
        kiln_id TEXT NOT NULL,
        supplier_id TEXT NOT NULL,
        date TEXT NOT NULL,
        tonnes REAL NOT NULL,
        form TEXT NOT NULL,
        prev_hash TEXT NOT NULL,
        current_hash TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (delivery_id) REFERENCES deliveries(delivery_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chain_head_tracker (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        head_hash TEXT NOT NULL,
        receipt_count INTEGER NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Immutable append-only audit triggers on delivery_receipts
    cur.execute("""
    CREATE TRIGGER IF NOT EXISTS prevent_receipt_update
    BEFORE UPDATE ON delivery_receipts
    BEGIN
        SELECT RAISE(ABORT, 'delivery_receipts records are immutable and cannot be modified');
    END;
    """)

    cur.execute("""
    CREATE TRIGGER IF NOT EXISTS prevent_receipt_delete
    BEFORE DELETE ON delivery_receipts
    BEGIN
        SELECT RAISE(ABORT, 'delivery_receipts records are append-only and cannot be deleted');
    END;
    """)

        # Ensure role column exists on suppliers table
    cur.execute("PRAGMA table_info(suppliers);")
    sup_cols = [r[1] for r in cur.fetchall()]
    if "role" not in sup_cols:
        cur.execute("ALTER TABLE suppliers ADD COLUMN role TEXT DEFAULT 'Supplier';")

    # Record migration version 1
    cur.execute("INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (1, datetime('now'));")

    conn.commit()

    # Determine if an explicit destructive reset is requested
    env_reset = os.environ.get("RESET_DB", "0").lower() in ("1", "true", "yes")
    should_reset = force_reload_seeds or env_reset

    if should_reset:
        cur.execute("DROP TRIGGER IF EXISTS prevent_receipt_delete;")
        cur.execute("DROP TRIGGER IF EXISTS prevent_receipt_update;")
        cur.execute("DELETE FROM chain_head_tracker;")
        cur.execute("DELETE FROM delivery_receipts;")
        cur.execute("DELETE FROM listings;")
        cur.execute("DELETE FROM deliveries;")
        cur.execute("DELETE FROM suppliers;")
        cur.execute("DELETE FROM kilns;")
        cur.execute("DELETE FROM supply_cells;")
        conn.commit()

    # Migration: add state column to kilns if missing (for existing DBs)
    try:
        cur.execute("ALTER TABLE kilns ADD COLUMN state TEXT NOT NULL DEFAULT 'Punjab';")
        conn.commit()
    except Exception:
        pass  # Column already exists

    # Idempotent Seed: Kilns
    cur.execute("SELECT COUNT(*) FROM kilns;")
    if cur.fetchone()[0] == 0 and os.path.exists(KILNS_CSV):
        df_kilns = pd.read_csv(KILNS_CSV)
        for _, r in df_kilns.iterrows():
            state_val = r["state"] if "state" in df_kilns.columns else "Punjab"
            cur.execute(
                "INSERT OR IGNORE INTO kilns (kiln_id, name, lat, lon, village, state, monthly_fuel_tonnes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (r["kiln_id"], r["name"], float(r["lat"]), float(r["lon"]), r["village"], state_val, float(r["monthly_fuel_tonnes"]))
            )

    # Idempotent Seed: Suppliers
    cur.execute("SELECT COUNT(*) FROM suppliers;")
    if cur.fetchone()[0] == 0 and os.path.exists(SUPPLIERS_CSV):
        df_sup = pd.read_csv(SUPPLIERS_CSV)
        for _, r in df_sup.iterrows():
            role_val = r["role"] if "role" in df_sup.columns else r["kind"]
            cur.execute(
                "INSERT OR IGNORE INTO suppliers (supplier_id, name, kind, lat, lon, village, straw_form, price_per_tonne, available_tonnes, role) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (r["supplier_id"], r["name"], r["kind"], float(r["lat"]), float(r["lon"]), r["village"], r["straw_form"], float(r["price_per_tonne"]), float(r["available_tonnes"]), role_val)
            )

    # Idempotent Seed: Deliveries (and initialize genesis receipt chain)
    cur.execute("SELECT COUNT(*) FROM deliveries;")
    if cur.fetchone()[0] == 0 and os.path.exists(DELIVERIES_CSV):
        import hashlib
        df_deliv = pd.read_csv(DELIVERIES_CSV)
        prev_hash = "GENESIS_BLOCK_000000000000000000000000000000000000000000000000000000"
        for _, r in df_deliv.iterrows():
            rec_id = "R" + str(r["delivery_id"]).replace("D", "")
            cur.execute(
                "INSERT OR IGNORE INTO deliveries (delivery_id, kiln_id, supplier_id, date, tonnes, form, photo_ref, receipt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (r["delivery_id"], r["kiln_id"], r["supplier_id"], r["date"], float(r["tonnes"]), r["form"], r["photo_ref"], rec_id)
            )
            # Create receipt hash
            payload = f"{rec_id}:{r['delivery_id']}:{r['kiln_id']}:{r['supplier_id']}:{r['date']}:{float(r['tonnes']):.2f}:{r['form']}:{prev_hash}"
            curr_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            cur.execute(
                "INSERT OR IGNORE INTO delivery_receipts (receipt_id, delivery_id, kiln_id, supplier_id, date, tonnes, form, prev_hash, current_hash, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (rec_id, r["delivery_id"], r["kiln_id"], r["supplier_id"], r["date"], float(r["tonnes"]), r["form"], prev_hash, curr_hash, f"{r['date']}T12:00:00Z")
            )
            prev_hash = curr_hash

    # Ensure chain_head_tracker is synchronized with current receipts
    cur.execute("SELECT COUNT(*) FROM chain_head_tracker;")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT current_hash FROM delivery_receipts ORDER BY rowid DESC LIMIT 1;")
        last_row = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM delivery_receipts;")
        total_recs = cur.fetchone()[0]
        if last_row and total_recs > 0:
            cur.execute(
                "INSERT OR REPLACE INTO chain_head_tracker (id, head_hash, receipt_count, updated_at) VALUES (1, ?, ?, datetime('now'));",
                (last_row[0], total_recs)
            )

    # Idempotent Seed: Supply Cells
    cur.execute("SELECT COUNT(*) FROM supply_cells;")
    if cur.fetchone()[0] == 0 and os.path.exists(SUPPLY_CELLS_CSV):
        df_cells = pd.read_csv(SUPPLY_CELLS_CSV)
        for _, r in df_cells.iterrows():
            cur.execute(
                "INSERT OR IGNORE INTO supply_cells (cell_id, lat, lon, fire_count_last_season, supply_index) VALUES (?, ?, ?, ?, ?)",
                (r["cell_id"], float(r["lat"]), float(r["lon"]), int(r["fire_count_last_season"]), float(r["supply_index"]))
            )

    # Ensure immutable triggers are active on delivery_receipts
    cur.execute("""
    CREATE TRIGGER IF NOT EXISTS prevent_receipt_update
    BEFORE UPDATE ON delivery_receipts
    BEGIN
        SELECT RAISE(ABORT, 'delivery_receipts records are immutable and cannot be modified');
    END;
    """)

    cur.execute("""
    CREATE TRIGGER IF NOT EXISTS prevent_receipt_delete
    BEFORE DELETE ON delivery_receipts
    BEGIN
        SELECT RAISE(ABORT, 'delivery_receipts records are append-only and cannot be deleted');
    END;
    """)

    conn.commit()
    conn.close()

def get_next_id(prefix: str, table: str, col: str, db_path: Optional[str] = None) -> str:
    """
    Computes next numeric identifier safely inside transactions, supporting seamless rollover (D999 -> D1000).
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    p_len = len(prefix) + 1
    cur.execute(f"SELECT COALESCE(MAX(CAST(SUBSTR({col}, {p_len}) AS INTEGER)), 0) + 1 FROM {table} WHERE {col} LIKE '{prefix}%';")
    num = cur.fetchone()[0]
    conn.close()
    return f"{prefix}{num:03d}"
