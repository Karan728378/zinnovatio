"""
KilnLink NASA FIRMS Fire Detection Data Pipeline (Person 2)
Downloads satellite fire detection data for Punjab / Haryana stubble corridor,
aggregates into 0.05-degree (~5km) spatial grid cells, computes supply index,
and caches results to data/processed/supply_cells.csv.
"""
import os
import sys
import math
import json
import io
import pandas as pd
import requests

# Load environment variables from backend/.env or root .env
try:
    from dotenv import load_dotenv
    _base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    load_dotenv(os.path.join(_base_dir, "backend", ".env"))
    load_dotenv(os.path.join(_base_dir, ".env"))
except ImportError:
    pass

# Bounding box for Punjab & Northern Haryana stubble belt (West, South, East, North)
# From bboxfinder.com: approx 74.3 to 77.4 E, 29.5 to 32.5 N
PILOT_BBOX = [74.3, 29.5, 77.4, 32.5]
GRID_SIZE = 0.05  # ~5 km resolution

def get_firms_map_key(map_key: str = None) -> str:
    """
    Retrieves the NASA FIRMS map key from arguments or environment variables.
    Checks FIRMS_MAP_KEY first, then NASA_FIRMS_MAP_KEY as fallback.
    """
    if map_key and str(map_key).strip():
        return str(map_key).strip()
    return (os.environ.get("FIRMS_MAP_KEY") or os.environ.get("NASA_FIRMS_MAP_KEY") or "").strip()

def download_firms_data(map_key: str = None, day_range: int = 5, force_refresh: bool = False) -> pd.DataFrame:
    """
    Downloads active fire data from NASA FIRMS VIIRS (SNPP / NOAA-20/21) or MODIS.
    Requires free MAP_KEY from firms.modaps.eosdis.nasa.gov.
    Accepts day_range between 1 and 5 (NASA FIRMS Area API constraint).
    Gracefully falls back to cached or simulated data if offline or rate-limited.
    """
    key = get_firms_map_key(map_key)
    cache_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "raw", "firms_cache.csv"))

    if not force_refresh and os.path.exists(cache_path):
        try:
            print(f"Loading cached fire detections from {cache_path}")
            df_cache = pd.read_csv(cache_path)
            if len(df_cache) > 0 and "latitude" in df_cache.columns:
                return df_cache
        except Exception as e:
            print(f"Notice reading cached file: {e}")

    if not key:
        print("No NASA FIRMS MAP_KEY provided in environment (FIRMS_MAP_KEY).")
        print("Using bundled realistic satellite detections.")
        return generate_simulated_satellite_data()

    # NASA FIRMS Area API endpoint expects day_range [1..5]
    day_range_clamped = min(max(int(day_range), 1), 5)
    bbox_str = f"{PILOT_BBOX[0]},{PILOT_BBOX[1]},{PILOT_BBOX[2]},{PILOT_BBOX[3]}"
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/VIIRS_SNPP_NRT/{bbox_str}/{day_range_clamped}"
    
    masked_key = key[:4] + "..." + key[-4:] if len(key) > 8 else "***"
    print(f"Requesting live FIRMS data from NASA (key: {masked_key}, range: {day_range_clamped} days, bbox: {bbox_str})...")
    
    try:
        resp = requests.get(url, timeout=25)
        if resp.status_code == 200 and "latitude" in resp.text:
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(resp.text)
            df = pd.read_csv(io.StringIO(resp.text))
            print(f"Successfully retrieved {len(df)} live satellite fire detections from NASA FIRMS!")
            if len(df) > 0:
                return df
            else:
                print("NASA FIRMS returned 0 active fires for this window. Checking fallback...")
        else:
            print(f"FIRMS API notice ({resp.status_code}): {resp.text[:200]}")
    except requests.exceptions.Timeout:
        print("NASA FIRMS API request timed out (>25s). Falling back gracefully.")
    except Exception as e:
        print(f"Network error accessing FIRMS API ({e}). Falling back gracefully.")

    # Graceful fallback: 1) cache if exists, 2) simulated data
    if os.path.exists(cache_path):
        try:
            return pd.read_csv(cache_path)
        except Exception:
            pass

    print("Falling back to bundled realistic satellite detections.")
    return generate_simulated_satellite_data()

def generate_simulated_satellite_data() -> pd.DataFrame:
    """
    Generates realistic spatial fire detections reflecting the stubble burning belt
    in Sangrur, Patiala, Ludhiana, Barnala, Bathinda, and Moga.
    """
    import numpy as np
    np.random.seed(42)
    # Cluster around high burning districts
    centers = [
        (30.25, 75.85, 300),  # Sangrur
        (30.38, 75.55, 200),  # Barnala
        (30.34, 76.38, 250),  # Patiala / Nabha
        (30.75, 75.80, 280),  # Ludhiana / Khanna
        (30.21, 74.95, 180),  # Bathinda
        (30.82, 75.17, 160)   # Moga
    ]
    records = []
    for c_lat, c_lon, count in centers:
        lats = np.random.normal(c_lat, 0.12, count)
        lons = np.random.normal(c_lon, 0.14, count)
        for lat, lon in zip(lats, lons):
            records.append({
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "acq_date": "2025-10-28",
                "acq_time": 1330,
                "confidence": "nominal"
            })
    return pd.DataFrame(records)

def process_grid_cells(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build 0.05-degree grid cells: cell id = floor(lat/0.05) and floor(lon/0.05).
    Count fires per cell, divide by the maximum, and save supply_cells.csv.
    """
    if df is None or len(df) == 0:
        print("No fire detections to aggregate. Using simulated fallback.")
        df = generate_simulated_satellite_data()

    df = df.copy()
    # Ensure latitude and longitude columns exist and are numeric
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])

    df["cell_lat_idx"] = (df["latitude"] / GRID_SIZE).apply(math.floor)
    df["cell_lon_idx"] = (df["longitude"] / GRID_SIZE).apply(math.floor)

    grouped = df.groupby(["cell_lat_idx", "cell_lon_idx"]).size().reset_index(name="fire_count_last_season")
    grouped["lat"] = ((grouped["cell_lat_idx"] + 0.5) * GRID_SIZE).round(3)
    grouped["lon"] = ((grouped["cell_lon_idx"] + 0.5) * GRID_SIZE).round(3)

    # Filter out single fire noise if many cells exist, or keep all if fewer
    if len(grouped) > 20:
        filtered = grouped[grouped["fire_count_last_season"] >= 2].copy()
        if len(filtered) >= 10:
            grouped = filtered

    max_fires = grouped["fire_count_last_season"].max() if len(grouped) > 0 else 1
    grouped["supply_index"] = (grouped["fire_count_last_season"] / max_fires).round(3)
    grouped["cell_id"] = [f"CELL_{i+1:03d}" for i in range(len(grouped))]

    output_df = grouped[["cell_id", "lat", "lon", "fire_count_last_season", "supply_index"]]

    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed", "supply_cells.csv"))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    output_df.to_csv(out_path, index=False)
    print(f"Processed {len(output_df)} supply cells. Saved to {out_path}.")
    return output_df

if __name__ == "__main__":
    key = get_firms_map_key()
    force = "--force" in sys.argv or "--refresh" in sys.argv
    df_raw = download_firms_data(key, force_refresh=force)
    process_grid_cells(df_raw)
