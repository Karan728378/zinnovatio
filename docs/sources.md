# Parali Mitra — Verified Sources, Data Credits & Open Items Resolution

## 1. Pilot District & Bounding Box (for Person 2)
* **Pilot District:** Sangrur & Malerkotla districts, Punjab (highest stubble-density belt in central Punjab).
* **Bounding Box (west, south, east, north):** 75.50, 30.05, 76.10, 30.65 (from bboxfinder.com).
* **Demo Map Centre (config.json):** center_lat: 30.35, center_lon: 75.85, zoom: 10.

---

## 2. Verified Facts & Statistics (Safe to Quote in Pitch & Demo)

| Claim / Fact | Status | Source & Date | Link / Reference |
| :--- | :--- | :--- | :--- |
| **Brick kilns in Punjab and non-NCR Haryana must co-fire paddy-straw pellets/briquettes: 20% from 1 Nov 2025, 30% from 1 Nov 2026, 40% from 1 Nov 2027, 50% from 1 Nov 2028.** | **VERIFIED** | CAQM Statutory Direction No. 92 (Issued 03 Jun 2025, PIB Release ID 2133553); Lok Sabha Unstarred Question Annex AU1362 (08 Dec 2025) & AU3733 (16 Mar 2026); CAQM Review (Oct 2026). | https://caqm.nic.in/ and https://sansad.in/getFile/loksabhaquestions/annex/186/AU1362_5ISCXh.pdf |
| **Traditional hand-fed brick kilns find pellets technically difficult and prefer chopped straw mixed with coal.** | **VERIFIED (News)** | The Tribune India (Yamunanagar Brick Kiln Owners Association statement). | Reported in The Tribune India (2025–2026 coverage). |
| **Punjab is adding 72 small pelletisation units to the ~40 operating earlier.** | **VERIFIED (News)** | BioEnergy Times (28 Sep 2026); The Tribune India. | BioEnergy Times, 28 Sep 2026. |
| **Farmers have only a 20–25 day window between paddy harvest and wheat sowing.** | **VERIFIED (News)** | Construction World (19 Oct 2026, reporting on the Centre's mission-mode directive to states). | Construction World, 19 Oct 2026. |
| **Over 90% of large farm fires in Punjab in 2024–25 occurred after 3:00 PM, outside satellite overpass windows (meaning satellite fire counts are an undercount).** | **VERIFIED (News)** | iFOREST Report, covered by The Tribune and national media (Dec 2025). | iFOREST / The Tribune (Dec 2025). |

---

## 3. Unverified Figures & Configurable Placeholders (Label Openly — Do Not Present as Verified Fact)

* **~2,050 operational brick kilns in Punjab and ~940 in non-NCR Haryana:** **UNVERIFIED (Secondary)** — Appears in a 2025 Punjab Biomass Pellet Plant DPR / consultancy summary (scribd.com/document/1064812978/DPR-Biomass-Pellet-Plant-Punjab). State as *"estimated at roughly 2,000+ in Punjab and ~940 in non-NCR Haryana in industry DPRs"*.
* **Straw collection and baling cost of ~INR 1,330/tonne for 15 km (CEEW):** **UNVERIFIED (Secondary quote)** — Quoted in secondary summary; label as an indicative estimate.
* **Cost Settings in config.json (coal_price_per_tonne: 9000, 	ransport_per_tonne_km: 6, chopping_cost_per_tonne: 150, straw_to_fuel_factor: 1.0):** **PLACEHOLDER / SAMPLE** — Label on slides and screens as *"Configurable assumption, to be sourced"*.
* **Kilns (kilns.csv), Suppliers (suppliers.csv), and Deliveries (deliveries.csv):** **SAMPLE DATA** — Every screen and slide displays "SAMPLE DATA".

---

## 4. Resolution of Section 9.3 Open Items

1. **Does the 30% co-firing share in CAQM Direction No. 92 mean by weight or by energy?**
   * **Finding:** The official PIB release (03 Jun 2025, Release ID 2133553) and MoEFCC parliamentary filings (Lok Sabha Annex AU1362 / AU3733) specify *"20% / 30% / 40% / 50% co-firing of paddy straw-based biomass pellets / briquettes"* with conventional fuel, tracked via monthly fuel consumption returns without mandating a separate calorific conversion formula in the summary text.
   * **How Parali Mitra handles it:** In config.json, share_basis is set to "weight" with a configurable "straw_to_fuel_factor": 1.0. If a state pollution board audits on an energy-equivalent basis (coal CV / straw CV ≈ 1.4–1.6), the officer or kiln changes straw_to_fuel_factor in config.json without changing a single line of code.
2. **Does any similar app already exist that matches straw suppliers directly to brick kilns?**
   * **Finding (Google & Play Store check):**
     * **HSPCB Brick Kiln Portal (dustapp.hspcb.org.in/BrickKiln/):** Handles regulatory registration and inspection for Haryana kilns, **not** straw supplier discovery or delivered-cost matching.
     * **Punjab *i-Khet Machine* / *FARMS* apps:** Connect farmers to Custom Hiring Centres (CHCs) for balers/happy seeders, **not** to brick kilns.
     * **BiofuelCircle / Agri-biomass marketplaces:** Focus on large industrial/thermal power plant tenders and aggregators, not hyper-local village-to-brick-kiln compliance tracking for traditional kilns using chopped straw, bales, and pellets.
   * **One-line pitch differentiation:** *"Existing portals either rent farm machinery (i-Khet) or register kilns for inspection (HSPCB); Parali Mitra is the missing local link that matches village straw (chopped, bale, or pellet) to nearby brick kilns at a delivered cost and updates the kiln's 30% CAQM compliance ledger live."*
3. **Are real brick kiln GPS locations public?**
   * **Finding:** Academic/satellite datasets exist for parts of the Indo-Gangetic Plain (e.g., Zenodo IGP Brick Kiln dataset), and state pollution boards (PPCB/HSPCB) hold consent-to-operate lists, but there is no clean, public real-time CSV of Punjab kiln monthly fuel tonnages. Therefore, keeping kilns.csv clearly labelled as SAMPLE DATA in Sangrur/Malerkotla is the honest, compliant choice.

---

## 5. Data & Map Credits
* **Satellite Fire Detections:** NASA FIRMS (Fire Information for Resource Management System) VIIRS/MODIS active fire data (cached from Oct–Nov 2025 season). Note: Satellite counts are an undercount due to afternoon overpass timing and are used strictly as a 0–1 *relative straw-supply index*, never a tonnage.
* **Base Maps:** © OpenStreetMap contributors (rendered via Leaflet).
