"""
KilnLink SQLite Database and Seed Loader (Person 1 & Shared Contract)
"""
import sqlite3
import os
import json
import pandas as pd
from typing import Dict, Any, List, Optional

import tempfile

# Default to temporary directory to support Windows, Linux, macOS and filesystems without POSIX locking
DEFAULT_DB_PATH = os.path.join(tempfile.gettempdir(), "kilnlink.db")
DB_PATH = os.environ.get("KILNLINK_DB_PATH", DEFAULT_DB_PATH)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_PATH = os.path.join(BASE_DIR, "data", "processed", "config.json")
KILNS_CSV = os.path.join(BASE_DIR, "data", "seed", "kilns.csv")
SUPPLIERS_CSV = os.path.join(BASE_DIR, "data", "seed", "suppliers.csv")
DELIVERIES_CSV = os.path.join(BASE_DIR, "data", "seed", "deliveries.csv")
SUPPLY_CELLS_CSV = os.path.join(BASE_DIR, "data", "processed", "supply_cells.csv")

def get_connection():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {
        "demo_month": "2026-11",
        "center_lat": 30.37,
        "center_lon": 75.85,
        "zoom": 9,
        "mandate_share": {"2026-11": 0.30, "2027-11": 0.40, "2028-11": 0.50},
        "share_basis": "weight",
        "straw_to_fuel_factor": 1.0,
        "transport_per_tonne_km": 6.0,
        "chopping_cost_per_tonne": 150.0,
        "coal_price_per_tonne": 9000.0
    }

def init_db(force_reload_seeds: bool = True):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS kilns (
        kiln_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        village TEXT NOT NULL,
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
        available_tonnes REAL NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS deliveries (
        delivery_id TEXT PRIMARY KEY,
        kiln_id TEXT NOT NULL,
        supplier_id TEXT NOT NULL,
        date TEXT NOT NULL,
        tonnes REAL NOT NULL,
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

    conn.commit()

    if force_reload_seeds:
        # Load kilns
        if os.path.exists(KILNS_CSV):
            df_kilns = pd.read_csv(KILNS_CSV)
            cur.execute("DELETE FROM kilns;")
            for _, r in df_kilns.iterrows():
                cur.execute(
                    "INSERT INTO kilns (kiln_id, name, lat, lon, village, monthly_fuel_tonnes) VALUES (?, ?, ?, ?, ?, ?)",
                    (r["kiln_id"], r["name"], float(r["lat"]), float(r["lon"]), r["village"], float(r["monthly_fuel_tonnes"]))
                )

        # Load suppliers
        if os.path.exists(SUPPLIERS_CSV):
            df_sup = pd.read_csv(SUPPLIERS_CSV)
            cur.execute("DELETE FROM suppliers;")
            for _, r in df_sup.iterrows():
                cur.execute(
                    "INSERT INTO suppliers (supplier_id, name, kind, lat, lon, village, straw_form, price_per_tonne, available_tonnes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (r["supplier_id"], r["name"], r["kind"], float(r["lat"]), float(r["lon"]), r["village"], r["straw_form"], float(r["price_per_tonne"]), float(r["available_tonnes"]))
                )

        # Load deliveries if table is empty or reload requested
        cur.execute("DELETE FROM deliveries;")
        if os.path.exists(DELIVERIES_CSV):
            df_deliv = pd.read_csv(DELIVERIES_CSV)
            for _, r in df_deliv.iterrows():
                rec_id = "R" + r["delivery_id"].replace("D", "")
                cur.execute(
                    "INSERT INTO deliveries (delivery_id, kiln_id, supplier_id, date, tonnes, form, photo_ref, receipt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (r["delivery_id"], r["kiln_id"], r["supplier_id"], r["date"], float(r["tonnes"]), r["form"], r["photo_ref"], rec_id)
                )

        # Load supply cells
        if os.path.exists(SUPPLY_CELLS_CSV):
            df_cells = pd.read_csv(SUPPLY_CELLS_CSV)
            cur.execute("DELETE FROM supply_cells;")
            for _, r in df_cells.iterrows():
                cur.execute(
                    "INSERT INTO supply_cells (cell_id, lat, lon, fire_count_last_season, supply_index) VALUES (?, ?, ?, ?, ?)",
                    (r["cell_id"], float(r["lat"]), float(r["lon"]), int(r["fire_count_last_season"]), float(r["supply_index"]))
                )

        conn.commit()

    conn.close()

def get_next_id(prefix: str, table: str, col: str) -> str:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT {col} FROM {table} WHERE {col} LIKE '{prefix}%' ORDER BY {col} DESC LIMIT 1;")
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        try:
            num = int(row[0].replace(prefix, "")) + 1
            return f"{prefix}{num:03d}"
        except Exception:
            pass
    return f"{prefix}001"
