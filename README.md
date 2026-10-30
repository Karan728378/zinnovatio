# Parali Mitra (पराली मित्र) — Multi-OS AI-Enabled Paddy Straw Fuel Platform
> **Track**: AgriTech & Rural Transformation · **Event**: Zinnovatio 4.0, Chandigarh University, Mohali  
> **Team CrackHeads**: Kunwar Rishab Singh, Rachit Rajput, Manan Dhingra, Samarth Singh, Karan

Turning paddy straw into a tracked, paid fuel for brick kilns — before **1 November 2026** under **CAQM Direction No. 92** (mandating $\ge 30\%$ crop residue co-firing).

---

## 💻 Run on Any Operating System

Parali Mitra is engineered with a **zero-dependency architecture** that runs natively across **Windows**, **macOS**, **Linux**, **Android**, and **iOS**.

### 1. Browser-Only (Instant Execution on Any OS / Zero Install)
You can run the entire platform **completely offline** with full interactive maps, calculators, and trained ML predictions without installing any software or package:
* Open `paralimitra_app.html` (or `index.html`) directly in any web browser (Chrome, Edge, Safari, Firefox).
* All trained machine learning trees and mathematical formulas run client-side in the browser's JavaScript engine.

### 2. Universal Desktop & Server Launchers

* **Windows**:
  Double-click `run.bat` or run:
  ```cmd
  run.bat
  ```
  *(Or execute `python launcher.py` in Command Prompt / PowerShell)*

* **macOS & Linux**:
  Open terminal and run:
  ```bash
  chmod +x run.sh launcher.py
  ./run.sh
  ```
  *(Or execute `python3 launcher.py`)*

* **Auto-Adaptive Runtime**:
  `launcher.py` automatically inspects your environment:
  - If `fastapi` and `uvicorn` are present, it launches the high-performance asynchronous REST backend.
  - If third-party packages are absent, it seamlessly falls back to Python's standard-library HTTP engine with zero errors.
  - Automatically launches your default web browser to `http://127.0.0.1:8000/`.

---

## 🤖 Machine Learning Intelligence & Training

Parali Mitra incorporates three pre-trained, cross-platform machine learning models calibrated on Punjab agricultural records and satellite observations:

| Model | Architecture | Training Target | Validation Performance |
|---|---|---|---|
| **Biomass Stubble Yield** | Random Forest Regressor (10 bagged trees) | Recoverable straw tonnage per farm parcel | **$R^2 = 0.982$**, $\text{MAE} = 3.26\text{ tonnes}$ |
| **Delivered Price & Savings** | Decision Tree Regressor | Market-clearing delivered straw price (₹/t) | **$R^2 = 0.967$**, $\text{MAE} = ₹53.0\text{/t}$ |
| **Fire Burning Risk** | Decision Tree Classifier | Stubble in-situ fire risk category (Low / Mod / High) | **$70.0\%$ Accuracy** |

### How to Re-Train the Models
You can retrain the models at any time using:
```bash
python3 pipeline/train_models.py
```
This runs the training pipeline, performs an 80/20 train-test evaluation, logs metrics to `models/metrics.json`, and exports portable decision tree weights into `models/trained_models.json`.

---

## 🧪 Test Suite Execution
Run the automated test suites verifying formulas, API contracts, and ML inference:
```bash
python3 tests/test_logic.py   # Mathematical formulas (haversine, cost, share)
python3 tests/test_api.py     # Section 5 FastAPI REST contract endpoints
python3 tests/test_ml.py      # Machine learning prediction endpoints
```
*(All 16 test cases pass 100%)*
