# Parali Mitra (ਪਰਾਲੀ ਮਿੱਤਰ / पराली मित्र) / KilnLink
> **Track**: AgriTech & Rural Transformation · **Event**: Zinnovatio 4.0, Chandigarh University, Mohali  
> **Team CrackHeads**: Kunwar Rishab Singh, Rachit Rajput, Manan Dhingra, Samarth Singh, Karan  
> **Statutory Mandate**: CAQM Statutory Direction No. 92 (Paddy straw co-firing enforcement in brick kilns)

Turning paddy crop residue into a certified, tamper-evident industrial fuel for brick kilns across Punjab and non-NCR northern Haryana.

---

## ⚡ Quickstart

### 1. Zero-Install Instant Browser Execution
Parali Mitra operates completely offline without installing any software, server, or compiler runtime:
- Open `paralimitra_app.html` or `index.html` directly in any modern browser (Chrome, Edge, Firefox, Safari).
- All interactive radar layers, calculators, sorting algorithms, multi-language dictionaries (English / हिन्दी / ਪੰਜਾਬੀ), and ML decision models run client-side in the browser.

### 2. Universal Application Launcher
- **Windows**:
  ```powershell
  python launcher.py
  # or run.bat
  ```
- **macOS & Linux**:
  ```bash
  chmod +x run.sh launcher.py
  python3 launcher.py
  # or ./run.sh
  ```
The launcher automatically checks for FastAPI and Uvicorn. If installed, it boots the full REST API backend and opens `http://127.0.0.1:8000/`. If third-party packages are absent, it seamlessly falls back to Python's standard-library HTTP server to serve the single-page application.

### 3. Automated Test Verification
Run the complete 74-test regression test suite:
```bash
python -m unittest discover tests -v
```
All 74 tests pass in ~3.5 seconds with zero external network calls, running against an isolated temporary database.

---

## 🏗️ Architecture & Core Subsystems

```
parali-mitra/
├── backend/app/
│   ├── main.py              # FastAPI endpoints, security auth, static router, error sanitizers
│   ├── config.py            # Centralized single dotenv configuration loader (root and backend)
│   ├── db.py                # Persistent SQLite (data/kilnlink.db), WAL mode, FK enforcement, triggers
│   ├── schemas.py           # Pydantic v2 strict models, date checks, string sanitizers, float clamps
│   ├── logic.py             # Haversine distance, delivered cost, statutory mandate schedule
│   ├── ml_engine.py         # Zero-dependency ML inference engine with range warnings
│   ├── receipts.py          # Cryptographic SHA-256 tamper-evident hash chaining & verification
│   └── dispatch.py          # Deterministic greedy auto-dispatch optimization
├── data/
│   ├── kilnlink.db          # Persistent SQLite database with foreign keys & WAL mode
│   ├── raw/firms_cache.csv  # 537 real VIIRS 375m active fire detections (Punjab-Haryana)
│   ├── seed/                # Authoritative seed CSVs (12 kilns, 15 suppliers, 10 deliveries)
│   └── processed/config.json# Statutory co-firing schedule (2025-11: 20%, 2026-11: 30%, etc.)
├── frontend/
│   ├── index.html           # Canonical single-source frontend with glassmorphism UI
│   └── src/i18n/pa.json     # Complete Gurmukhi Punjabi language dictionary
├── models/
│   ├── trained_models.json  # Serialized decision trees & random forest weights
│   └── metrics.json         # Evaluation metrics with explicit synthetic provenance disclosures
├── pipeline/
│   ├── firms_pipeline.py    # NASA FIRMS data ingestion, atomic write, UTC->IST analysis
│   └── train_models.py      # Cross-platform training pipeline (pure NumPy/Python)
├── scripts/
│   ├── sync_frontend.py     # Deterministic SHA-256 synchronizer for index.html targets
│   └── build_release.py     # Clean release packager excluding .env, *.db, cache, and secrets
├── tests/                   # Complete 74-test automated test suite (100% passing)
│   ├── conftest.py          # Isolated temporary database fixtures (never touches dev DB)
│   ├── test_api.py          # API contracts & CRUD endpoints
│   ├── test_dispatch.py     # Auto-dispatch simulation & satellite time endpoints
│   ├── test_frontend_sync.py# Frontend SHA-256 parity, hygiene & Punjabi support
│   ├── test_hygiene.py      # Secret hygiene, release builder filters & admin auth paths
│   ├── test_logic.py        # Haversine distance & delivered cost arithmetic
│   ├── test_mandate.py      # Statutory mandate escalation schedule
│   ├── test_ml.py           # Machine learning inference & metrics verification
│   ├── test_persistence.py  # SQLite foreign key enforcement & idempotency
│   ├── test_phase4.py       # Concurrency (20 threads), tamper scenarios, rollover, IST, XSS
│   ├── test_security.py     # Credential protection, zero key exposure & SHA-256 receipt chain
│   └── test_validation.py   # Schema bounds, calendar date validation & stock overspend
├── launcher.py              # Universal adaptive launcher (FastAPI or built-in HTTP)
├── index.html               # Synchronized root distribution frontend
├── paralimitra_app.html     # Synchronized standalone frontend
├── SECURITY_REMEDIATION_REPORT.md # Security audit & NASA FIRMS key rotation checklist
├── DATA_PROVENANCE.md       # Satellite sensors, PAU agronomic constants & data boundaries
├── OFFLINE_CAPABILITIES.md  # Detailed offline operations & graceful degradation guide
├── TEST_REPORT.md           # Master test execution records & exit codes (74/74 PASSED)
└── ISSUE_LEDGER.md          # Comprehensive 27-defect engineering resolution ledger
```

---

## 🔒 Security & Data Integrity

1. **Zero Credential Exposure**:
   - `GET /supply/status` returns boolean configuration status (`firms_configured: bool`) with zero key substrings, prefixes, or suffixes exposed over the wire.
   - `.env` and `backend/.env` are strictly excluded in `.gitignore` and purged from git history. `.env.example` contains only sanitized non-sensitive dummy placeholders (`YOUR_FIRMS_API_KEY_HERE`).
   - `POST /supply/refresh` requires timing-safe `X-Admin-Key` header authentication using `hmac.compare_digest`. When `ADMIN_KEY` is unset in the server environment, it fails safely with HTTP 503.
   - Request exception logging in `firms_pipeline.py` catches `requests.RequestException` and suppresses URL exception strings that could contain the API key parameter.
2. **Persistent ACID Database & Concurrency Safety**:
   - Relocated from OS temporary directory to `data/kilnlink.db`.
   - Seeding is idempotent and never drops tables or deletes deliveries on server restarts.
   - Enabled SQLite Write-Ahead Logging (`PRAGMA journal_mode=WAL;`), busy timeout (`PRAGMA busy_timeout=5000;`), and foreign key constraints (`PRAGMA foreign_keys = ON;`) on every request connection.
   - Delivery recording runs inside `BEGIN IMMEDIATE` transaction locking with atomic stock decrement (`UPDATE suppliers SET available_tonnes = available_tonnes - ? WHERE supplier_id=? AND available_tonnes >= ?`). If rowcount == 0, raises HTTP 409 Conflict.
   - Verified via automated concurrency test: 20 parallel threads attempting 5t deliveries against a 40t supplier stock yield exactly 8 successes, 12 conflicts, stock never goes negative, and the receipt chain remains intact.
3. **Cryptographic Tamper-Evident Receipts**:
   - Every delivery receipt is cryptographically linked to the previous receipt using **SHA-256 hash chaining**.
   - SQLite triggers (`prevent_delivery_receipt_update`, `prevent_delivery_receipt_delete`) abort any direct SQL mutations on historical receipt records.
   - `GET /receipts/verify` audits the full chain and mathematically detects any retroactive alterations to delivery records.

---

## ⚖️ CAQM Statutory Direction No. 92 Enforcement

1. **Statutory Authority**:
   - Direction No. 92 issued under Section 12 of the Commission for Air Quality Management in National Capital Region and Adjoining Areas Act, 2021.
   - Co-firing mandate escalation:
     - Prior to Nov 2025: 0.0% (Voluntary guidelines)
     - Effective 01 Nov 2025: **20.0%** (Phase 1 statutory enforcement)
     - Effective 01 Nov 2026: **30.0%** (Phase 2 statutory escalation)
     - Effective 01 Nov 2027: **40.0%** (Phase 3 statutory escalation)
     - Effective 01 Nov 2028: **50.0%** (Phase 4 statutory threshold)
2. **Mandate Form Eligibility Toggle**:
   - Regulators and kiln owners face an open policy question: does CAQM Direction No. 92 require exclusively dense biomass pellets/briquettes, or does loose/chopped agricultural residue count?
   - Parali Mitra provides an interactive **Mandate Form Selector** in the regulator dashboard and via the `eligibility_mode` API parameter (`all_forms` vs `pellet_only`).
   - When set to `pellet_only`, the engine excludes loose bales and chopped straw from statutory co-firing compliance calculations, allowing regulators to audit both compliance scenarios in real time.

---

## 🛰️ NASA FIRMS Remote Sensing & Time Analysis

- **Sensor**: VIIRS 375m active fire detections (Suomi NPP / NOAA-20) over the Punjab-Haryana corridor (`[74.30°E, 29.50°N, 77.40°E, 32.50°N]`).
- **Orbital Window**: VIIRS operates in a Sun-synchronous low Earth orbit crossing Punjab at ~13:00 IST (daytime) and ~02:30 IST (nighttime).
- **Time Analysis (`GET /supply/hours`)**: Converts raw UTC timestamps to Indian Standard Time (IST). Explains that 97.4% of fires cluster between 12:00 PM and 2:00 PM IST due to orbital mechanics.
- **Diurnal Blindspot Estimation (`GET /supply/blindspot`)**: The absence of evening detections is a satellite revisit constraint, not proof that burning stopped. The `/supply/blindspot` endpoint models the 24-hour diurnal fire cycle, incorporating published field studies indicating 65–75% of stubble burning ignites after 3:00 PM when combine harvesters complete their shift.

---

## 🌐 Multi-Language Accessibility (English / हिन्दी / ਪੰਜਾਬੀ)

- Tailored for field adoption among farmers, aggregators, and kiln operators in Punjab and Haryana.
- Segmented 3-way sliding toggle in the top navigation bar supporting English (`en`), Hindi (`hi`), and Gurmukhi Punjabi (`pa`).
- All interactive cards, form labels, receipts, and alert toasts update instantly without page reloads.

---

## 🤖 Machine Learning Intelligence

Three pure-Python, zero-dependency estimators calibrated on agronomic equations from the Punjab Agricultural University (PAU):
1. **Biomass Stubble Yield Predictor**: Random Forest Regressor (10 trees), estimating recoverable straw tonnage from acres, crop variety (PR-126, Pusa-44, Basmati), grain yield, NDVI, and cut height. (Synthetic Test $R^2 = 0.982$).
2. **Delivered Straw Price Estimator**: Decision Tree Regressor (depth 6), computing delivered price based on distance, straw form (bale/chopped/pellet), moisture content, harvest week, and local supply density. (Synthetic Test $R^2 = 0.967$).
3. **Fire Burning Risk Classifier**: Decision Tree Classifier (depth 4), predicting field-level burning probability based on days remaining until rabi wheat sowing, distance to nearest kiln, machinery access score, and satellite cluster density. (Synthetic Test Accuracy = 70.0%).

*Note: Models are pre-trained and serialized into pure JSON weights (`models/trained_models.json`). They execute client-side in the browser and in Python without requiring scikit-learn, TensorFlow, or PyTorch.*

---

## 📦 Submission & Release Building

To package a clean, production-ready release ZIP with SHA-256 verification:
```bash
python scripts/build_release.py
```
The script validates that only tracked Git files are included, excludes all `.env` files, SQLite databases, and bytecode caches, verifies zero secret key patterns, and outputs the SHA-256 checksum of the release artifact.
