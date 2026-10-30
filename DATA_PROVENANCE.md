# Parali Mitra / KilnLink — Data Provenance & Scientific Integrity Report

This document establishes the origin, methodology, sensor characteristics, agronomic constants, statutory schedule, and data boundaries of all datasets, models, and simulations incorporated into Parali Mitra.

---

## 1. Satellite Remote Sensing Data (NASA FIRMS)

### 1.1 Sensor & Constellation
- **Data Source**: NASA Earthdata / Fire Information for Resource Management System (FIRMS).
- **Instruments**: Visible Infrared Imaging Radiometer Suite (VIIRS 375m active fire product `VNP14IMGTDL_NRT` / `VJ114IMGTDL_NRT`).
- **Platforms**: Joint Polar Satellite System (Suomi NPP and NOAA-20 / JPSS-1).
- **Spatial Resolution**: 375 meters at nadir (I-bands: I4 3.74 µm thermal brightness, I5 11.45 µm infrared).
- **Corridor Geographic Bounding Box**: `[74.30°E, 29.50°N, 77.40°E, 32.50°N]`, encompassing all 23 districts of Punjab and non-NCR northern Haryana.

### 1.2 Observation Window & Sampling Mechanics
- **Cached Dataset**: 537 real active fire observations collected during the peak paddy harvesting window (26 October – 29 October).
- **Spatial Binning Grid**: Standardized 0.05° (~5 km × 5 km) cell resolution, producing 120 spatial supply cells. Cell IDs are deterministically derived from coordinates (`CELL_{lat*100}_{lon*100}`).

### 1.3 Critical Orbital Sampling Analysis (UTC vs. IST)
A vital data science boundary that must be understood by reviewers and regulators:
- NASA FIRMS records acquisition timestamps in **Coordinated Universal Time (UTC)**.
- VIIRS operates in a **Sun-Synchronous Low Earth Orbit (LEO)** at ~824 km altitude with an inclination of 98.7° and an ascending node crossing the equator at ~13:30 local solar time.
- As a consequence of this orbital geometry, the satellite flies over Punjab exactly twice per 24-hour cycle:
  1. **Daytime Overpass**: ~07:15 – 07:45 UTC, corresponding to **12:45 PM – 1:15 PM IST** (UTC + 5:30).
  2. **Nighttime Overpass**: ~20:45 – 21:15 UTC, corresponding to **02:15 AM – 02:45 AM IST**.
- In the 537 observations within `data/raw/firms_cache.csv`:
  - **70.9% (381 fires)** were acquired between 07:24 and 07:30 UTC (**12:54 PM – 1:00 PM IST**).
  - **18.8% (101 fires)** were acquired between 08:00 and 09:00 UTC (**1:30 PM – 2:30 PM IST**).
  - **7.6% (41 fires)** were acquired between 06:45 and 07:15 UTC (**12:15 PM – 12:45 PM IST**).
  - **97.4% of all observations** cluster within the 12:00 PM – 2:00 PM IST window.

> [!IMPORTANT]
> **Orbital Constraint Notice**: The complete absence of satellite detections in late afternoon (after 3:00 PM IST) and evening is purely a **geometric orbital sampling artifact of polar-orbiting satellites**. It does **NOT** indicate that farmers stopped burning residue after 2 PM. Parali Mitra documents this orbital reality transparently rather than fabricating artificial evening observations.

---

## 2. Agronomic Stubble Ratios & Parameters

All biomass yield formulas and synthetic training parameters are grounded in empirical agricultural literature from the **Punjab Agricultural University (PAU), Ludhiana** and the **Indian Council of Agricultural Research (ICAR)**:

### 2.1 Crop Varieties & Residue Ratios
| Crop Variety | Category | Maturation Period | Straw-to-Grain Ratio | Loose Residue Recovery |
| :--- | :--- | :--- | :--- | :--- |
| **PR-126** | Short-duration Parmal | ~123 days | 1.10 : 1 | 85% recovered, 15% root stubble |
| **Pusa-44** | Long-duration Parmal | ~160 days | 1.25 : 1 | 88% recovered, 12% root stubble |
| **Basmati PB-1121** | Aromatic long grain | ~145 days | 0.95 : 1 | 80% recovered, 20% root stubble |

### 2.2 Farm Parcel Variables
- **Grain Yield**: Averaging 24–32 quintals/acre for Parmal varieties, 18–24 quintals/acre for Basmati. (1 quintal = 0.1 metric tonne).
- **Cutting Height**: Standard combine harvesters operate at 15–25 cm cut height. Higher cut heights increase rooted stubble mass and decrease baled loose straw yield according to empirical coefficient: \(\text{Yield Adjustment} = 1.0 - (\text{Height} - 15) \times 0.008\).
- **Satellite NDVI Range**: 0.58 – 0.88 at harvest maturity, correlating positively with vegetative biomass density.

---

## 3. Statutory Regulatory Framework & Co-Firing Schedule

### 3.1 CAQM Statutory Authority
- **Statutory Direction**: Direction No. 92, issued by the **Commission for Air Quality Management in National Capital Region and Adjoining Areas (CAQM)** pursuant to Section 12 of the CAQM Act, 2021.
- **Parliamentary Reference**: Lok Sabha Unstarred Question AU1362 (Ministry of Environment, Forest and Climate Change) and Rajya Sabha AU3733.
- **Statutory Co-Firing Mandate Escalation**:
  - **Prior to November 2025**: Voluntary co-firing guidelines; statutory compliance threshold = **0.0%**.
  - **Effective 01 November 2025**: Phase 1 statutory enforcement across Punjab and non-NCR Haryana; statutory minimum = **20.0%**.
  - **Effective 01 November 2026**: Phase 2 statutory escalation; statutory minimum = **30.0%**.
  - **Effective 01 November 2027**: Phase 3 statutory escalation; statutory minimum = **40.0%**.
  - **Effective 01 November 2028**: Phase 4 statutory escalation; statutory minimum = **50.0%**.

### 3.2 Economic Reference Benchmarks
- **Industrial Coal Benchmark**: ₹9,000 / metric tonne delivered at kiln gate.
- **Logistics Freight Rate**: ₹6.00 / tonne·km for rural tractor-trolley and medium-duty freight transport.
- **Custom Chopping / Processing Fee**: ₹150 / tonne for field chopping into 20–50 mm furnace feed lengths.
- **Moisture Penalty**: Above 16% moisture, drying cost penalty of ₹40 per percentage point is applied; below 16%, a dryness premium of ₹15 per point is credited.

---

## 4. Machine Learning Model Boundaries & Provenance

### 4.1 Training Data Nature
- **Demonstration / Simulation Models**: The datasets used to train the three zero-dependency machine learning estimators (`models/trained_models.json`) are **synthetically generated** from the PAU agronomic constants and CAQM market parameters described above.
- **Holdout Validation Metrics**:
  - **Biomass Yield Predictor** (Random Forest, 10 trees): Synthetic Test \(R^2 = 0.982\), \(\text{MAE} = 3.26\text{ tonnes}\).
  - **Delivered Price Estimator** (Decision Tree Regressor, depth 6): Synthetic Test \(R^2 = 0.967\), \(\text{MAE} = ₹53.0\text{ / tonne}\).
  - **Fire Burning Risk Classifier** (Decision Tree Classifier, depth 4): Synthetic Test Accuracy = \(70.0\%\).

> [!NOTE]
> **Honest Metric Boundary**: These evaluation metrics reflect performance against held-out synthetic test splits generated from published agronomic and economic formulas. They demonstrate algorithmic soundness and cross-platform inference capability. They must be calibrated against empirical weighbridge tickets and farm parcel audits before commercial deployment.

---

## 5. Cryptographic Audit Chain Provenance

- **Hash Standard**: SHA-256 (NIST FIPS 180-4).
- **Genesis Block Hash**: `0000000000000000000000000000000000000000000000000000000000000000`.
- **Chaining Invariant**: Each receipt hash is computed deterministically as:
  \[
  \text{Hash}_i = \text{SHA256}(\text{ReceiptID} \,\|\, \text{DeliveryID} \,\|\, \text{KilnID} \,\|\, \text{SupplierID} \,\|\, \text{Date} \,\|\, \text{Tonnes} \,\|\, \text{Form} \,\|\, \text{Hash}_{i-1})
  \]
- **Verification Guarantee**: Any retroactive modification of delivery tonnage, date, kiln ID, or supplier ID immediately invalidates all subsequent block hashes, providing regulators with foolproof mathematical proof of tampering.

