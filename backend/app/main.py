"""
Parali Mitra FastAPI Application (Cross-Platform & Full Functionality)
Adheres strictly to Section 5 shared contract + ML Intelligence Engine.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import os
import sys

# Load environment variables (.env)
try:
    from dotenv import load_dotenv
    _base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    load_dotenv(os.path.join(_base_dir, "backend", ".env"))
    load_dotenv(os.path.join(_base_dir, ".env"))
except ImportError:
    pass

from .db import init_db, get_connection, load_config, get_next_id
from .schemas import (
    HealthResponse, KilnItem, SupplierItem, SupplyCellItem,
    KilnNeedsResponse, KilnSuppliersResponse, RankedSupplier,
    CreateListingRequest, CreateDeliveryRequest, DeliveryResponse,
    ComplianceSummaryResponse, KilnComplianceItem, ComplianceTotals,
    YieldPredictRequest, PricePredictRequest, FireRiskPredictRequest
)
from .logic import (
    straw_needed, delivered_cost, compliance_share,
    rank_suppliers, rank_kilns_for_supplier, haversine
)
from .ml_engine import (
    predict_biomass_yield, predict_delivered_price, predict_fire_risk, load_metrics
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables and seeds exist and load seed data
    init_db(force_reload_seeds=True)
    yield

app = FastAPI(
    title="Parali Mitra API",
    description="Turning paddy straw into a tracked, paid fuel for brick kilns (CAQM Direction No. 92 compliance)",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for any frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
def get_health():
    return HealthResponse(status="ok", app="Parali Mitra", version="1.0.0")

@app.get("/config")
def get_config():
    cfg = load_config()
    firms_key = os.environ.get("FIRMS_MAP_KEY") or os.environ.get("NASA_FIRMS_MAP_KEY")
    if isinstance(cfg, dict):
        cfg["firms_live_configured"] = bool(firms_key)
    return cfg

@app.get("/supply/map", response_model=List[SupplyCellItem])
def get_supply_map():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT cell_id, lat, lon, fire_count_last_season, supply_index FROM supply_cells;")
    rows = cur.fetchall()
    conn.close()
    return [
        SupplyCellItem(
            cell_id=r["cell_id"],
            lat=r["lat"],
            lon=r["lon"],
            fire_count_last_season=r["fire_count_last_season"],
            supply_index=r["supply_index"]
        ) for r in rows
    ]

@app.get("/supply/status")
def get_supply_status():
    key = os.environ.get("FIRMS_MAP_KEY") or os.environ.get("NASA_FIRMS_MAP_KEY") or ""
    has_key = bool(key)
    masked = key[:4] + "..." + key[-4:] if len(key) > 8 else ("***" if key else None)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cache_path = os.path.join(base_dir, "data", "raw", "firms_cache.csv")
    has_cache = os.path.exists(cache_path)
    return {
        "firms_configured": has_key,
        "api_key_masked": masked,
        "has_live_cache": has_cache,
        "source": "NASA FIRMS VIIRS (SNPP / NOAA)" if has_key else "Bundled Satellite Detections",
        "pilot_bbox": [74.3, 29.5, 77.4, 32.5]
    }

@app.post("/supply/refresh")
def refresh_supply_data(force: bool = False):
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
        from pipeline.firms_pipeline import download_firms_data, process_grid_cells
        df = download_firms_data(force_refresh=force)
        cells_df = process_grid_cells(df)
        
        # Reload database table
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM supply_cells;")
        for _, r in cells_df.iterrows():
            cur.execute(
                "INSERT INTO supply_cells (cell_id, lat, lon, fire_count_last_season, supply_index) VALUES (?, ?, ?, ?, ?)",
                (r["cell_id"], float(r["lat"]), float(r["lon"]), int(r["fire_count_last_season"]), float(r["supply_index"]))
            )
        conn.commit()
        conn.close()
        return {
            "status": "success",
            "message": f"Successfully refreshed {len(cells_df)} supply cells from NASA FIRMS.",
            "cells_count": len(cells_df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/kilns", response_model=List[KilnItem])
def get_kilns():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT kiln_id, name, lat, lon, village, monthly_fuel_tonnes FROM kilns ORDER BY kiln_id;")
    rows = cur.fetchall()
    conn.close()
    return [
        KilnItem(
            kiln_id=r["kiln_id"],
            name=r["name"],
            lat=r["lat"],
            lon=r["lon"],
            village=r["village"],
            monthly_fuel_tonnes=r["monthly_fuel_tonnes"]
        ) for r in rows
    ]

@app.get("/kilns/{kiln_id}/needs", response_model=KilnNeedsResponse)
def get_kiln_needs(kiln_id: str, month: Optional[str] = Query(None)):
    cfg = load_config()
    target_month = month or cfg.get("demo_month", "2026-11")
    mandate_share = cfg.get("mandate_share", {}).get(target_month, 0.30)
    factor = cfg.get("straw_to_fuel_factor", 1.0)
    basis = cfg.get("share_basis", "weight")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT kiln_id, name, monthly_fuel_tonnes FROM kilns WHERE kiln_id = ?;", (kiln_id,))
    kiln = cur.fetchone()
    if not kiln:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Kiln {kiln_id} not found")

    monthly_fuel = kiln["monthly_fuel_tonnes"]
    needed = straw_needed(mandate_share, monthly_fuel, factor)

    # Deliveries in this month
    cur.execute(
        "SELECT SUM(tonnes) FROM deliveries WHERE kiln_id = ? AND date LIKE ?;",
        (kiln_id, f"{target_month}%")
    )
    res = cur.fetchone()[0]
    delivered = round(float(res), 2) if res else 0.0
    gap = round(max(0.0, needed - delivered), 2)
    conn.close()

    return KilnNeedsResponse(
        kiln_id=kiln_id,
        month=target_month,
        mandate_share=mandate_share,
        monthly_fuel_tonnes=monthly_fuel,
        straw_needed_tonnes=needed,
        delivered_tonnes=delivered,
        gap_tonnes=gap,
        basis=basis,
        note="SAMPLE DATA"
    )

@app.get("/kilns/{kiln_id}/suppliers", response_model=KilnSuppliersResponse)
def get_kiln_suppliers(kiln_id: str):
    cfg = load_config()
    coal_price = cfg.get("coal_price_per_tonne", 9000.0)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT kiln_id, name, lat, lon FROM kilns WHERE kiln_id = ?;", (kiln_id,))
    kiln = cur.fetchone()
    if not kiln:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Kiln {kiln_id} not found")

    cur.execute("SELECT supplier_id, name, kind, lat, lon, village, straw_form, price_per_tonne, available_tonnes FROM suppliers WHERE available_tonnes > 0;")
    suppliers = [dict(r) for r in cur.fetchall()]
    conn.close()

    ranked = rank_suppliers(dict(kiln), suppliers, cfg)
    return KilnSuppliersResponse(
        kiln_id=kiln_id,
        coal_cost_per_tonne=coal_price,
        suppliers=[RankedSupplier(**s) for s in ranked]
    )

@app.post("/listings")
def create_listing(req: CreateListingRequest):
    conn = get_connection()
    cur = conn.cursor()
    sup_id = req.supplier_id

    # If new supplier
    if not sup_id:
        sup_id = get_next_id("S", "suppliers", "supplier_id")
        cur.execute(
            "INSERT INTO suppliers (supplier_id, name, kind, lat, lon, village, straw_form, price_per_tonne, available_tonnes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
            (sup_id, req.name, req.kind or "farmer", req.lat or 30.25, req.lon or 75.85, req.village, req.straw_form, req.price_per_tonne, req.tonnes)
        )
    else:
        cur.execute("UPDATE suppliers SET available_tonnes = available_tonnes + ? WHERE supplier_id = ?;", (req.tonnes, sup_id))

    listing_id = get_next_id("L", "listings", "listing_id")
    cur.execute(
        "INSERT INTO listings (listing_id, supplier_id, tonnes, status) VALUES (?, ?, ?, ?);",
        (listing_id, sup_id, req.tonnes, "active")
    )
    conn.commit()

    # Find nearest kilns
    cfg = load_config()
    cur.execute("SELECT * FROM suppliers WHERE supplier_id = ?;", (sup_id,))
    sup = dict(cur.fetchone())
    cur.execute("SELECT * FROM kilns;")
    kilns = [dict(r) for r in cur.fetchall()]
    conn.close()

    nearest_kilns = rank_kilns_for_supplier(sup, kilns, cfg)
    return {
        "listing_id": listing_id,
        "supplier_id": sup_id,
        "status": "active",
        "nearest_kilns": nearest_kilns[:5]
    }

@app.get("/suppliers/{supplier_id}/kilns")
def get_supplier_kilns(supplier_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM suppliers WHERE supplier_id = ?;", (supplier_id,))
    sup = cur.fetchone()
    if not sup:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Supplier {supplier_id} not found")

    cur.execute("SELECT * FROM kilns;")
    kilns = [dict(r) for r in cur.fetchall()]
    conn.close()

    cfg = load_config()
    ranked = rank_kilns_for_supplier(dict(sup), kilns, cfg)
    return {
        "supplier_id": supplier_id,
        "kilns": ranked
    }

@app.post("/deliveries", response_model=DeliveryResponse)
def record_delivery(req: CreateDeliveryRequest):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT kiln_id FROM kilns WHERE kiln_id = ?;", (req.kiln_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Kiln {req.kiln_id} not found")

    cur.execute("SELECT supplier_id, available_tonnes FROM suppliers WHERE supplier_id = ?;", (req.supplier_id,))
    sup = cur.fetchone()
    if not sup:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Supplier {req.supplier_id} not found")

    deliv_id = get_next_id("D", "deliveries", "delivery_id")
    rec_id = "R" + deliv_id.replace("D", "")

    cur.execute(
        "INSERT INTO deliveries (delivery_id, kiln_id, supplier_id, date, tonnes, form, photo_ref, receipt) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
        (deliv_id, req.kiln_id, req.supplier_id, req.date, req.tonnes, req.form, req.photo_ref, rec_id)
    )

    new_avail = max(0.0, sup["available_tonnes"] - req.tonnes)
    cur.execute("UPDATE suppliers SET available_tonnes = ? WHERE supplier_id = ?;", (new_avail, req.supplier_id))

    conn.commit()
    conn.close()

    return DeliveryResponse(
        delivery_id=deliv_id,
        status="recorded",
        receipt=rec_id
    )

@app.get("/compliance/summary", response_model=ComplianceSummaryResponse)
def get_compliance_summary(month: Optional[str] = Query(None)):
    cfg = load_config()
    target_month = month or cfg.get("demo_month", "2026-11")
    target_share = cfg.get("mandate_share", {}).get(target_month, 0.30)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT kiln_id, name, lat, lon, monthly_fuel_tonnes FROM kilns ORDER BY kiln_id;")
    kilns_raw = cur.fetchall()

    kiln_items = []
    total_straw = 0.0
    meeting_count = 0

    for k in kilns_raw:
        kid = k["kiln_id"]
        fuel = k["monthly_fuel_tonnes"]
        cur.execute("SELECT SUM(tonnes) FROM deliveries WHERE kiln_id = ? AND date LIKE ?;", (kid, f"{target_month}%"))
        res = cur.fetchone()[0]
        straw = round(float(res), 2) if res else 0.0
        share = compliance_share(straw, fuel)
        status = "meets_target" if share >= target_share else "below_target"

        if status == "meets_target":
            meeting_count += 1
        total_straw += straw

        kiln_items.append(KilnComplianceItem(
            kiln_id=kid,
            name=k["name"],
            lat=k["lat"],
            lon=k["lon"],
            straw_tonnes=straw,
            fuel_tonnes=fuel,
            share=share,
            status=status
        ))

    conn.close()

    return ComplianceSummaryResponse(
        month=target_month,
        target_share=target_share,
        kilns=kiln_items,
        totals=ComplianceTotals(
            kilns=len(kiln_items),
            meeting_target=meeting_count,
            straw_tonnes=round(total_straw, 2)
        )
    )

# --- TRAINED MACHINE LEARNING ENDPOINTS ---

@app.get("/models/metrics")
def get_model_metrics():
    """Returns validation metrics for the trained cross-platform ML models."""
    return load_metrics()

@app.post("/predict/yield")
def predict_yield_endpoint(req: YieldPredictRequest):
    """Predicts paddy straw tonnage generated from field acres and satellite parameters."""
    return predict_biomass_yield(
        acres=req.acres,
        variety_idx=req.variety_idx,
        grain_yield=req.grain_yield_qtl_acre,
        ndvi=req.ndvi,
        cut_height=req.cutting_height_cm
    )

@app.post("/predict/price")
def predict_price_endpoint(req: PricePredictRequest):
    """Predicts delivered straw market price (₹/tonne) and savings vs industrial coal."""
    return predict_delivered_price(
        distance_km=req.distance_km,
        form_idx=req.form_idx,
        moisture_pct=req.moisture_pct,
        harvest_week=req.harvest_week,
        supply_density=req.supply_density_index
    )

@app.post("/predict/fire-risk")
def predict_fire_risk_endpoint(req: FireRiskPredictRequest):
    """Predicts in-situ stubble burning risk category and probability distribution."""
    return predict_fire_risk(
        days_left=req.days_to_wheat_sowing,
        dist_kiln=req.dist_to_kiln_km,
        machinery_score=req.machinery_access_score,
        cell_fire=req.cell_fire_density
    )

INDEX_HTML_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "index.html"))

@app.get("/", response_class=HTMLResponse)
@app.get("/supplier", response_class=HTMLResponse)
@app.get("/kiln", response_class=HTMLResponse)
@app.get("/regulator", response_class=HTMLResponse)
@app.get("/ai-studio", response_class=HTMLResponse)
@app.get("/about", response_class=HTMLResponse)
@app.get("/paralimitra_app.html", response_class=HTMLResponse)
def serve_app():
    if os.path.exists(INDEX_HTML_PATH):
        return FileResponse(INDEX_HTML_PATH)
    return HTMLResponse("<h1>Parali Mitra Platform</h1>")
