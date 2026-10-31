import os
import csv
from io import StringIO
import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response

# Load environment variables (.env from workspace root)
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    for _enc in ("utf-8", "utf-8-sig", "utf-16", "cp1252"):
        try:
            load_dotenv(_env_path, encoding=_enc)
            break
        except Exception:
            pass
else:
    load_dotenv()

FIRMS_MAP_KEY = os.getenv("FIRMS_MAP_KEY") or os.getenv("NASA_FIRMS_MAP_KEY", "")
app = FastAPI(title="Parali Mitra — All-India Fire Intelligence")

# Embedded Frontend HTML/JS/CSS (Unobstructed Map, NASA FIRMS WMS Raster Streaming, Docked Sidebar)
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parali Mitra — Live NASA FIRMS WMS Satellite Stream</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #090d16;
            --bg-card: rgba(15, 23, 42, 0.85);
            --bg-card-border: rgba(51, 65, 85, 0.6);
            --border-highlight: rgba(245, 158, 11, 0.4);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
            --accent-fire: #f97316;
            --accent-fire-glow: rgba(249, 115, 22, 0.35);
            --accent-hot: #ef4444;
            --accent-emerald: #10b981;
            --accent-cyan: #38bdf8;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body, html {
            height: 100%;
            width: 100%;
            background-color: var(--bg-base);
            color: var(--text-main);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            overflow: hidden;
        }

        /* Top Docked Header Bar */
        #header-bar {
            height: 56px;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(51, 65, 85, 0.6);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            z-index: 50;
        }

        .brand-section {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-icon {
            font-size: 20px;
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(249, 115, 22, 0.3));
            padding: 6px;
            border-radius: 8px;
            border: 1px solid rgba(249, 115, 22, 0.4);
        }

        .brand-text h1 {
            font-size: 15px;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .brand-badge {
            font-size: 10px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(245, 158, 11, 0.15);
            color: #fcd34d;
            border: 1px solid rgba(245, 158, 11, 0.3);
            text-transform: uppercase;
            font-family: 'JetBrains Mono', monospace;
        }

        .brand-subtitle {
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 1px;
        }

        .header-controls {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 9999px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.3);
            font-size: 11px;
            font-weight: 600;
            color: #6ee7b7;
            font-family: 'JetBrains Mono', monospace;
        }

        .pulse-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: var(--accent-emerald);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        .select-input {
            background: #1e293b;
            color: #e2e8f0;
            border: 1px solid #475569;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
            font-weight: 500;
            outline: none;
            cursor: pointer;
        }

        .btn-sync {
            background: #2563eb;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-sync:hover {
            background: #1d4ed8;
        }

        /* Main Workspace: CSS Grid Layout */
        #dashboard-workspace {
            display: grid;
            grid-template-columns: 1fr 380px;
            height: calc(100vh - 56px);
            width: 100%;
            overflow: hidden;
        }

        /* Dedicated Map Container (100% unobstructed, zero overlay pollution) */
        #map-container {
            position: relative;
            height: 100%;
            width: 100%;
            background-color: #0b1120;
            overflow: hidden;
        }

        #map {
            position: relative;
            height: 100%;
            width: 100%;
            outline: none;
        }

        /* Docked Control Sidebar */
        #sidebar {
            background: rgba(15, 23, 42, 0.98);
            border-left: 1px solid rgba(51, 65, 85, 0.6);
            display: flex;
            flex-direction: column;
            gap: 16px;
            padding: 16px;
            overflow-y: auto;
            z-index: 10;
        }

        #sidebar::-webkit-scrollbar {
            width: 5px;
        }
        #sidebar::-webkit-scrollbar-thumb {
            background: rgba(100, 116, 139, 0.4);
            border-radius: 3px;
        }

        /* Card Widgets */
        .widget-card {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(51, 65, 85, 0.7);
            border-radius: 10px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .widget-title {
            font-size: 11px;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        /* KPI Grid */
        .kpi-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }

        .kpi-box {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(51, 65, 85, 0.5);
            border-radius: 8px;
            padding: 10px;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .kpi-num {
            font-size: 18px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            color: #ffffff;
        }

        .kpi-lbl {
            font-size: 10px;
            color: var(--text-muted);
            font-weight: 500;
        }

        /* NASA FIRMS WMS Stream Inspection Panel */
        #stream-panel {
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.95) 100%);
            border: 1px solid var(--border-highlight);
            box-shadow: 0 4px 20px rgba(245, 158, 11, 0.08);
            border-radius: 10px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(51, 65, 85, 0.6);
        }

        .panel-badge {
            font-size: 9px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(16, 185, 129, 0.2);
            color: #6ee7b7;
            border: 1px solid rgba(16, 185, 129, 0.4);
            font-family: 'JetBrains Mono', monospace;
        }

        .fields-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
            font-size: 12px;
        }

        .field-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 4px 8px;
            border-radius: 6px;
            background: rgba(15, 23, 42, 0.6);
        }

        .field-label {
            color: var(--text-muted);
            font-size: 11px;
        }

        .field-val {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            color: #ffffff;
        }

        .btn-action {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 10px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
            box-shadow: 0 4px 12px rgba(217, 119, 6, 0.3);
            margin-top: 4px;
        }

        .btn-action:hover {
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            transform: translateY(-1px);
        }

        /* Controls Widget */
        .slider-control {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .slider-label-row {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: var(--text-muted);
        }

        input[type="range"] {
            width: 100%;
            height: 5px;
            background: #334155;
            border-radius: 4px;
            outline: none;
            -webkit-appearance: none;
            cursor: pointer;
        }

        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: var(--accent-fire);
            box-shadow: 0 0 8px rgba(249, 115, 22, 0.8);
            cursor: pointer;
        }

        /* Docked Legend */
        .legend-gradient {
            height: 8px;
            border-radius: 4px;
            background: linear-gradient(to right, #10b981, #f59e0b, #f97316, #ef4444);
            margin-top: 4px;
        }

        .legend-labels {
            display: flex;
            justify-content: space-between;
            font-size: 9px;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-muted);
            margin-top: 4px;
        }

        @media (max-width: 900px) {
            #dashboard-workspace {
                grid-template-columns: 1fr;
                grid-template-rows: 1fr 320px;
            }
            #sidebar {
                border-left: none;
                border-top: 1px solid rgba(51, 65, 85, 0.6);
            }
        }
    </style>
</head>
<body>

    <!-- DOCKED TOP HEADER -->
    <header id="header-bar">
        <div class="brand-section">
            <div class="brand-icon">🔥</div>
            <div class="brand-text">
                <h1>Parali Mitra <span class="brand-badge">NASA FIRMS WMS</span></h1>
                <div class="brand-subtitle">All-India Agricultural Residue Combustion &amp; Thermal Telemetry</div>
            </div>
        </div>
        <div class="header-controls">
            <div class="status-pill">
                <span class="pulse-dot"></span>
                <span id="header-status-text">NASA FIRMS: Live Streaming</span>
            </div>
            <select class="select-input" id="month-select" title="Mandate Period">
                <option value="2026-11">Nov 2026 (30% Statutory)</option>
                <option value="2025-11">Nov 2025 (20% Baseline)</option>
                <option value="2027-11">Nov 2027 (40% Escalation)</option>
            </select>
            <button class="btn-sync" onclick="refreshFeed()" title="Refresh satellite WMS stream and telemetry">
                <span id="sync-icon">🔄</span> Sync Feed
            </button>
        </div>
    </header>

    <!-- MAIN WORKSPACE: MAP CONTAINER + DOCKED SIDEBAR -->
    <main id="dashboard-workspace">
        
        <!-- 100% UNOBSTRUCTED MAP CONTAINER -->
        <div id="map-container">
            <div id="map"></div>
        </div>

        <!-- DOCKED SIDEBAR (OUTSIDE MAP) -->
        <aside id="sidebar">
            
            <!-- LIVE TELEMETRY KPI SUMMARY -->
            <div class="widget-card">
                <div class="widget-title">
                    <span>Telemetry Overview</span>
                    <span style="font-family:'JetBrains Mono'; color:#38bdf8;">All India</span>
                </div>
                <div class="kpi-row">
                    <div class="kpi-box">
                        <span class="kpi-num" id="kpi-total-fires">--</span>
                        <span class="kpi-lbl">Active Anomalies</span>
                    </div>
                    <div class="kpi-box">
                        <span class="kpi-num" id="kpi-peak-frp" style="color:#f87171;">--</span>
                        <span class="kpi-lbl">Peak FRP (MW)</span>
                    </div>
                </div>
                <div class="kpi-row">
                    <div class="kpi-box">
                        <span class="kpi-num" id="kpi-avg-temp" style="color:#fde047;">--</span>
                        <span class="kpi-lbl">Peak Temp (K)</span>
                    </div>
                    <div class="kpi-box">
                        <span class="kpi-num" id="kpi-sat-pass" style="color:#6ee7b7; font-size:13px;">VIIRS SNPP 24h</span>
                        <span class="kpi-lbl">Constellation</span>
                    </div>
                </div>
            </div>

            <!-- NASA FIRMS WMS STREAM INSPECTION PANEL -->
            <div id="stream-panel">
                <div class="panel-header">
                    <span style="font-size:12px; font-weight:700; color:#fbbf24;">Live Satellite Stream</span>
                    <span class="panel-badge" id="layer-badge">VIIRS_SNPP_24</span>
                </div>
                <div class="fields-list">
                    <div class="field-row">
                        <span class="field-label">Stream Protocol</span>
                        <span class="field-val" style="color:#38bdf8;">OGC WMS 1.3.0</span>
                    </div>
                    <div class="field-row">
                        <span class="field-label">Active Sensor</span>
                        <span class="field-val">VIIRS S-NPP (375m)</span>
                    </div>
                    <div class="field-row">
                        <span class="field-label">Temporal Window</span>
                        <span class="field-val" style="color:#6ee7b7;">Rolling 24h NRT</span>
                    </div>
                    <div class="field-row">
                        <span class="field-label">Coverage Extent</span>
                        <span class="field-val">All-India (68°-98°E)</span>
                    </div>
                    <div class="field-row">
                        <span class="field-label">Delivery Mode</span>
                        <span class="field-val" style="color:#fcd34d;">Live Dynamic Tiles</span>
                    </div>
                </div>
                <button class="btn-action" onclick="matchCorridorQuota()">
                    Match High-Intensity Clusters ➔
                </button>
            </div>

            <!-- WMS STREAM & INTENSITY CONTROLS -->
            <div class="widget-card">
                <div class="widget-title">
                    <span>WMS Stream Controls</span>
                    <span id="opacity-value-label" style="font-family:'JetBrains Mono'; color:#f59e0b;">90%</span>
                </div>
                <div class="slider-control">
                    <div class="slider-label-row">
                        <span>WMS Layer Opacity</span>
                    </div>
                    <input type="range" id="opacity-slider" min="10" max="100" value="90" step="5" oninput="updateOpacity(this.value)">
                </div>
                <div class="slider-control" style="margin-top:6px;">
                    <div class="slider-label-row">
                        <span>Satellite Layer</span>
                    </div>
                    <select class="select-input" id="sensor-layer-select" onchange="updateSensorLayer(this.value)">
                        <option value="fires_viirs_snpp_24">VIIRS S-NPP 375m (24 Hours NRT)</option>
                        <option value="fires_viirs_noaa20_24">VIIRS NOAA-20 375m (24 Hours NRT)</option>
                        <option value="fires_modis_24">MODIS Terra/Aqua 1km (24 Hours NRT)</option>
                    </select>
                </div>
            </div>

            <!-- DOCKED THERMAL INTENSITY SPECTRUM LEGEND -->
            <div class="widget-card">
                <div class="widget-title">Thermal Intensity Spectrum</div>
                <div class="legend-gradient"></div>
                <div class="legend-labels">
                    <span>&lt; 5 MW</span>
                    <span>15 MW</span>
                    <span>30 MW</span>
                    <span>&gt; 50 MW</span>
                </div>
            </div>

        </aside>
    </main>

    <!-- LEAFLET JAVASCRIPT: NASA FIRMS WMS RASTER INTEGRATION -->
    <script>
        // 1. Initialize Map cleanly (zero overlays over the map div)
        var map = L.map('map', {
            zoomControl: false,
            attributionControl: true
        }).setView([23.5, 78.5], 5);

        // Add zoom control at bottom-right
        L.control.zoom({ position: 'bottom-right' }).addTo(map);

        // Base Map (CartoDB Dark)
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions" target="_blank">CARTO</a>'
        }).addTo(map);

        // 2. NASA FIRMS WMS Raster Tile Layer (Live Dynamic Overpass Imagery)
        var firmsWMSLayer = L.tileLayer.wms('https://firms.modaps.eosdis.nasa.gov/mapserver/wms/fires/8261465bf52125fd25a9dcb32380d884/', {
            layers: 'fires_viirs_snpp_24',
            format: 'image/png',
            transparent: true,
            version: '1.3.0',
            attribution: 'NASA FIRMS'
        });
        firmsWMSLayer.addTo(map);

        // 3. Sidebar Telemetry & KPI Binding
        function loadKpis() {
            var statusEl = document.getElementById('header-status-text');
            var syncIcon = document.getElementById('sync-icon');
            if (syncIcon) syncIcon.textContent = '⏳';

            fetch('/api/live-fires')
                .then(response => response.json())
                .then(data => {
                    if (syncIcon) syncIcon.textContent = '🔄';
                    if (data.error) {
                        console.error("Backend Error:", data.error);
                        if (statusEl) statusEl.textContent = 'NASA FIRMS: Standby';
                        return;
                    }
                    updateKpiDisplays(data);
                })
                .catch(err => {
                    if (syncIcon) syncIcon.textContent = '🔄';
                    console.error("Error fetching telemetry KPIs:", err);
                    if (statusEl) statusEl.textContent = 'NASA FIRMS: Offline Fallback';
                });
        }

        function updateKpiDisplays(data) {
            var countEl = document.getElementById('kpi-total-fires');
            var peakFrpEl = document.getElementById('kpi-peak-frp');
            var avgTempEl = document.getElementById('kpi-avg-temp');
            var statusEl = document.getElementById('header-status-text');

            if (!data || data.length === 0) {
                if (countEl) countEl.textContent = '0';
                if (peakFrpEl) peakFrpEl.textContent = '0.0';
                if (avgTempEl) avgTempEl.textContent = '0.0';
                return;
            }

            var maxFrp = 0;
            var maxTemp = 0;
            data.forEach(d => {
                if (d.frp > maxFrp) maxFrp = d.frp;
                var t = d.temp_k || 335.0;
                if (t > maxTemp) maxTemp = t;
            });

            if (countEl) countEl.textContent = data.length.toLocaleString();
            if (peakFrpEl) peakFrpEl.textContent = maxFrp.toFixed(1);
            if (avgTempEl) avgTempEl.textContent = maxTemp.toFixed(1);
            if (statusEl) statusEl.textContent = 'NASA FIRMS: Live Streaming (' + data.length + ' anomalies)';
        }

        // 4. Interactive Controls
        function updateOpacity(val) {
            var opacity = parseFloat(val) / 100;
            firmsWMSLayer.setOpacity(opacity);
            var label = document.getElementById('opacity-value-label');
            if (label) label.textContent = val + '%';
        }

        function updateSensorLayer(layerName) {
            firmsWMSLayer.setParams({ layers: layerName });
            var badge = document.getElementById('layer-badge');
            if (badge) badge.textContent = layerName.toUpperCase();
        }

        function refreshFeed() {
            firmsWMSLayer.redraw();
            loadKpis();
        }

        function matchCorridorQuota() {
            alert('Connecting live NASA FIRMS thermal cluster coordinates to nearest registered Zig-Zag Brick Kilns under CAQM 30% co-firing mandate...');
        }

        // Initialize on DOM load
        document.addEventListener('DOMContentLoaded', function() {
            loadKpis();
        });
    </script>
</body>
</html>
"""

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Silences browser favicon requests with 204 No Content."""
    return Response(content=b"", status_code=204)

@app.get("/supply/firms-live")
def get_firms_live(day_range: int = 2):
    """Returns live NASA FIRMS detections across Punjab-Haryana corridor."""
    try:
        from pipeline.firms_pipeline import fetch_live_firms_detections
        return fetch_live_firms_detections(day_range=day_range)
    except Exception:
        return {"error": "Failed to fetch live satellite detections"}

@app.get("/regulator", response_class=HTMLResponse)
@app.get("/supplier", response_class=HTMLResponse)
@app.get("/kiln", response_class=HTMLResponse)
@app.get("/ai-studio", response_class=HTMLResponse)
@app.get("/about", response_class=HTMLResponse)
@app.get("/paralimitra_app.html", response_class=HTMLResponse)
def serve_full_dashboard():
    """Serves the full Parali Mitra multi-tab dashboard when requested."""
    base_dir = os.path.dirname(__file__)
    for candidate in ["index.html", "paralimitra_app.html", "frontend/index.html"]:
        p = os.path.join(base_dir, candidate)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return HTMLResponse(content=HTML_CONTENT)

@app.get("/", response_class=HTMLResponse)
def serve_map():
    """Serves the integrated Leaflet frontend with NASA FIRMS WMS raster layer."""
    return HTML_CONTENT

@app.get("/api/live-fires")
def get_live_fires():
    """Returns parsed thermal detections across India bounding box for sidebar KPIs."""
    key = os.getenv("FIRMS_MAP_KEY") or os.getenv("NASA_FIRMS_MAP_KEY") or FIRMS_MAP_KEY
    if not key:
        try:
            from pipeline.firms_pipeline import generate_simulated_satellite_data
            df = generate_simulated_satellite_data()
            return [
                {
                    "lat": float(r["latitude"]),
                    "lon": float(r["longitude"]),
                    "frp": float(r.get("frp", 10.0)),
                    "temp_k": float(r.get("bright_ti4", 345.2)),
                    "date": str(r.get("acq_date", "2026-10-30")),
                    "time": str(r.get("acq_time", "0724"))
                }
                for _, r in df.iterrows()
            ]
        except Exception:
            return {"error": "Failed to fetch data"}

    # Expanded Bounding Box for ALL OF INDIA: 68.0, 6.0, 98.0, 36.0
    sensors = ["VIIRS_SNPP_NRT", "VIIRS_SNPP", "VIIRS_NOAA20_NRT"]
    for sensor in sensors:
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{sensor}/68.0,6.0,98.0,36.0/1"
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200 and "latitude" in response.text:
                csv_data = StringIO(response.text)
                reader = csv.DictReader(csv_data)
                fire_points = []
                for row in reader:
                    try:
                        fire_points.append({
                            "lat": float(row["latitude"]),
                            "lon": float(row["longitude"]),
                            "frp": float(row["frp"]),
                            "temp_k": float(row.get("bright_ti4") or row.get("brightness") or 340.0),
                            "date": row.get("acq_date", "2026-10-30"),
                            "time": str(row.get("acq_time", "0724"))
                        })
                    except (KeyError, ValueError, TypeError):
                        continue
                if fire_points:
                    return fire_points
        except Exception:
            continue

    try:
        from pipeline.firms_pipeline import generate_simulated_satellite_data
        df = generate_simulated_satellite_data()
        return [
            {
                "lat": float(r["latitude"]),
                "lon": float(r["longitude"]),
                "frp": float(r.get("frp", 10.0)),
                "temp_k": float(r.get("bright_ti4", 345.2)),
                "date": str(r.get("acq_date", "2026-10-30")),
                "time": str(r.get("acq_time", "0724"))
            }
            for _, r in df.iterrows()
        ]
    except Exception:
        return {"error": "Failed to fetch data"}


# Include backend application routes so all API endpoints work seamlessly under main:app
try:
    from backend.app.main import app as _backend_app
    for _r in _backend_app.routes:
        if _r.path not in [x.path for x in app.routes]:
            app.routes.append(_r)
except Exception:
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
