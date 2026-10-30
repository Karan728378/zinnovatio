# Parali Mitra - Honest QA & Test Log (docs/test_log.md)

## 1. Pre-CP1: Seed Data & Contract Validation (Hour 1)
- Date: 2026-10-30 | Command: python docs/run_qa.py --seed-only
- [x] data/seed/kilns.csv: 12 rows, exact Section 5.1 columns, all names start with Sample -> PASS
- [x] data/seed/suppliers.csv: 15 rows, exact Section 5.1 columns, valid kind and straw_form -> PASS
- [x] data/seed/deliveries.csv: 10 rows, exact Section 5.1 columns, YYYY-MM-DD dates, 96t total -> PASS

## 2. Checkpoint 1 (CP1 - Hour 4): Real Backend API Connected
- Command: python docs/run_qa.py --api http://localhost:8000
- [ ] GET /health and GET /config return HTTP 200 -> PENDING CP1
- [ ] GET /supply/map returns grid cells with supply_index 0 to 1 -> PENDING CP1
- [ ] GET /kilns returns 12 sample kilns -> PENDING CP1
- [ ] GET /kilns/K003/needs?month=2026-11 matches Section 5.4 -> PENDING CP1
- [ ] GET /kilns/K003/suppliers ranks S005 at 2025 INR/t -> PENDING CP1
- [ ] POST /deliveries updates GET /compliance/summary?month=2026-11 -> PENDING CP1

## 3. Checkpoint 2 (CP2 - Hour 10): End-to-End Golden Demo Path
- [ ] Step 1 (/regulator): Green/red kilns + supply cells + OSM attribution + SAMPLE DATA badge -> PENDING CP2
- [ ] Step 2 (/kiln): K003 shows 36t needed, 10t delivered, 26t gap -> PENDING CP2
- [ ] Step 3 (/kiln): Ranked suppliers table shows delivered cost vs coal -> PENDING CP2
- [ ] Step 4 (/supplier mobile): EN/HI switch works, no raw keys, flow < 90s -> PENDING CP2
- [ ] Step 5 (/supplier): Delivery form returns Receipt with SAMPLE DATA visible -> PENDING CP2
- [ ] Step 6 (/regulator): 5s poll updates K003 to Green automatically, 0 console errors -> PENDING CP2

## 4. Post-Freeze Full Runs (Hour 16-20 - Need 2 Clean Runs)
- Full Run 1: PENDING H16
- Full Run 2: PENDING H16
