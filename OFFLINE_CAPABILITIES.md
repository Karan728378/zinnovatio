# Parali Mitra / KilnLink — Offline Capabilities & Graceful Degradation Guide

Parali Mitra is engineered with an **offline-first architectural principle**. Critical regulatory enforcement, economic matching, machine learning inference, and cryptographic verification functions run entirely on local computing infrastructure without requiring continuous cloud or internet connectivity.

---

## 1. What Works 100% Offline (Zero Internet Required)

| Subsystem | Offline Implementation | Technical Mechanism |
| :--- | :--- | :--- |
| **Relational Database** | Full ACID persistence | Persistent local SQLite (`data/kilnlink.db`) with foreign key enforcement and idempotent initialization. |
| **Regulatory Compliance Ledger** | Fully operational | Real-time calculation of kiln fuel quotas, delivered tonnes, compliance share, and statutory gap based on CAQM Direction No. 92. |
| **Haversine Sourcing & Ranking** | Fully operational | Pure-math Great Circle distance calculation and delivered cost optimization (base price + transport + chopping fee). |
| **Zero-Dependency ML Inference** | Fully operational | Pure Python tree-traversal engine (`backend/app/ml_engine.py`) executing trained Random Forests and Decision Trees without NumPy/SciPy runtime requirements. |
| **Auto-Dispatch Optimization** | Fully operational | Deterministic greedy allocation simulator matching supplier inventory to kiln deficits, computing coal savings and unmet demand. |
| **Cryptographic Tamper-Evident Audit** | Fully operational | SHA-256 hash chaining on all delivery receipts; `GET /receipts/verify` audits the full chain locally in milliseconds. |
| **Standalone Web Launcher** | Fully operational | `launcher.py` detects whether FastAPI/Uvicorn is installed; if not, it automatically boots Python's built-in `http.server` to serve the interactive application. |
| **Full Automated Test Suite** | Fully operational | All 37 unit tests across security, validation, persistence, mandate, ML, and dispatch run in under 1 second without external network calls. |

---

## 2. Graceful Degradation Under Network Disconnection

When operating in field environments with intermittent or absent cellular/broadband connectivity, external dependencies degrade cleanly without throwing unhandled exceptions or crashing the user interface:

### 2.1 Remote Map Tile Layer
- **Connected State**: MapLibre GL 3D renders CartoDB Dark Matter raster tiles.
- **Disconnected / Offline State**: If remote map tiles or the MapLibre CDN cannot be reached within 3 seconds, `initMap()` cleanly intercepts the timeout, prevents infinite retry loops, and renders a stylish "Offline Radar Mode Active" placeholder card.
- **Data Availability**: All 12 pilot brick kilns, 15 suppliers, and 120 supply cells remain **100% accessible and filterable** in the tabular compliance workbench below the map canvas.

### 2.2 Live NASA FIRMS Satellite Synchronizer
- **Connected State** (with valid API key in `.env`): Live FIRMS endpoint downloads recent active fire detections from the NASA MODAPS server.
- **Disconnected / Offline State** (or unconfigured key): The pipeline automatically falls back to `data/raw/firms_cache.csv` containing 537 real VIIRS 375m active fire detections collected during peak Punjab harvest.
- **UI Truthfulness**: The status badge in the top navigation updates to `🛰️ NASA FIRMS: Cached Seed (537 Fires)` or `🛰️ NASA FIRMS: Offline Fallback (537 Fires)`. It never falsely reports "Live Active" when running disconnected.

---

## 3. How to Verify Offline Capability

To independently verify that the system runs completely offline:

1. **Disconnect Network**: Turn off Wi-Fi or disconnect your Ethernet cable.
2. **Execute Launcher**:
   ```bash
   python launcher.py
   ```
   The application boots on `http://127.0.0.1:8000/`.
3. **Run the 2-Minute Demo**:
   Click **Run Demo** in the top navigation or perform manual supplier matching, delivery recording, and kiln compliance inspection.
4. **Run the Automated Test Suite**:
   ```bash
   python -m unittest discover tests
   ```
   All 37 test cases will pass with zero internet connectivity.

