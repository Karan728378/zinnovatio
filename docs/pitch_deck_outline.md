# Parali Mitra — Pitch Deck (Zinnovatio 4.0)
Track: AgriTech & Rural Transformation | Team CrackHeads

## Slide 1: Title — Parali Mitra
* **Subtitle:** Turning paddy straw into a tracked, paid fuel for brick kilns before 1 November 2026
* **Team CrackHeads:** Kunwar Rishab Singh, Rachit Rajput, Manan Dhingra, Samarth Singh, Karan
* **Tag:** [SAMPLE DATA IN DEMO | REAL CAQM MANDATE & NASA FIRMS DATA]

## Slide 2: The Problem & Why Tomorrow Matters (1 Nov 2026)
* **Farmer Window:** Only 20–25 days between paddy harvest and wheat sowing (Construction World, 19 Oct 2026) with no easy local paid outlet.
* **The Legal Deadline:** CAQM Statutory Direction No. 92 mandates brick kilns in Punjab & non-NCR Haryana to co-fire paddy-straw fuel:
  * **20%** from 1 Nov 2025 -> **30% from 1 Nov 2026 (Tomorrow)** -> **40%** (2027) -> **50%** (2028).
* **The Ground Reality:** Hand-fed traditional kilns find pellets difficult and prefer chopped straw mixed with coal (Tribune India), while Punjab is adding 72 pellet units to ~40 existing ones (BioEnergy Times, 28 Sep 2026).

## Slide 3: The Idea — Four Connected Modules
1. **Kiln Calculator:** Enter monthly fuel tonnes -> shows 30% mandated straw needed and current shortfall.
2. **Straw Supply Map:** Last season's real NASA FIRMS fire density as a 0–1 relative supply index (not tonnage) + sample supplier listings.
3. **Match & Delivered Cost:** Ranks nearest farmers, aggregators, and pellet units by delivered cost per tonne (bale, chopped, or pellet) vs coal.
4. **Live Compliance Ledger:** Every delivery logs weight, form, date, and weighbridge slip photo reference -> updates kiln compliance share live and issues a supplier receipt.

## Slide 4: Live Demo Path (One Delivery, Three Users)
1. **Regulator Dashboard:** View Sangrur/Malerkotla kilns coloured Green/Red vs the 30% mandate.
2. **Kiln Owner Page (K003):** Needs 36 t straw (30% of 120 t fuel); 10 t delivered so far -> 26 t gap.
3. **Supplier Match:** Compare delivered cost (S005 chopped straw at INR 2,025/t delivered vs INR 9,000/t coal placeholder).
4. **Supplier App (Mobile):** List straw -> record 26 t delivery with slip_001.jpg -> get Receipt R021 (evidence straw left the field).
5. **Live Update:** Regulator map and compliance bar update automatically in 5 seconds.

## Slide 5: Architecture & Free Stack
* **Data Layer:** Cached NASA FIRMS satellite fire detections (supply_cells.csv) + seed CSVs (kilns.csv, suppliers.csv, deliveries.csv) + config.json.
* **Backend:** Python + FastAPI + SQLite + pure rule-based calculation engine (logic.py using Haversine distance & configurable conversion factors).
* **Frontend:** React + Vite + Leaflet (OpenStreetMap) + Recharts + EN/HI bilingual support.
* **100% Free & Transparent:** Rule-based platform (no black-box ML claims, no paid APIs).

## Slide 6: Honesty, Limits & Open Assumptions
* **What is Real:** CAQM Direction No. 92 mandate schedule (20/30/40/50%) and cached NASA FIRMS satellite fire detections.
* **Satellite Undercount:** Over 90% of large Punjab farm fires in 2024–25 occurred after 3 PM outside satellite overpass windows (iFOREST, Dec 2025) — hence our map is labelled a *Relative Supply Index*, never tonnage.
* **What is Sample / Placeholder:** Kilns, suppliers, deliveries, and prices are labelled SAMPLE DATA. Transport/chopping/coal costs and weight-vs-energy factor (1.0) are configurable assumptions in config.json.
* **Audit Support, Not Proof:** A delivery receipt + photo reference is stronger evidence than a selfie that straw left the field, supporting (not replacing) physical audits.

## Slide 7: Differentiation & Roadmap
* **How We Differ:** *i-Khet* rents farm machinery; *HSPCB Portal* registers kilns for inspection. **Parali Mitra** connects village straw (bale, chopped, pellet) directly to brick kilns with delivered-cost math and live compliance tracking.
* **Next Steps (Post-Hackathon):**
  1. Pilot with 5 brick kilns and 1 FPO in Sangrur/Malerkotla during Nov 2026.
  2. Integrate electronic weighbridge (Dharamkanta) slip OCR/QR verification.
  3. Validate revenue hypothesis (small transaction/SaaS fee paid by kilns or pellet units; free for farmers and pollution boards).
