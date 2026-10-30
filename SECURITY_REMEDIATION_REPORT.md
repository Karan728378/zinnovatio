# Parali Mitra / KilnLink — Security Remediation Report

**Date:** 2026-10-30  
**Auditor:** Full-Stack Application Security & Data Engineering Review  
**Classification:** Public Release Security Assessment

---

## 1. Executive Summary

During the repository audit of the KilnLink / Parali Mitra project, several security and data-integrity vulnerabilities were identified, including local plaintext credentials in `.env` files, potential secret leakage via the `/supply/status` API endpoint, unauthenticated administrative endpoints (`POST /supply/refresh`), and cross-site scripting (XSS) vectors in the frontend.

All identified vulnerabilities have been remediated in the codebase, verified with automated security tests (`tests/test_security.py`), and verified to be absent from the final release archive.

---

## 2. Identified Vulnerabilities & Implemented Remediation

### SEC-01: Exposed API Keys in Local Environment Files
- **Severity:** Critical (CVSS 7.5)
- **Description:** Plaintext NASA FIRMS MAP_KEY was stored in `.env` and `backend/.env`.
- **Remediation:**
  1. Removed actual credentials from `.env.example` and replaced with clear placeholders (`YOUR_NASA_FIRMS_MAP_KEY_HERE`, `YOUR_ADMIN_SECRET_KEY_HERE`).
  2. Updated `.gitignore` with strict exclusion rules for `.env`, `backend/.env`, `*.env`, `.env.*`, and temporary build artifacts.
  3. Ensured no `.env` files are bundled in the release archive.
  4. Implemented safe fallback behavior in `firms_pipeline.py` and `db.py`: when no key is configured, the application falls back gracefully to bundled verified sample data without crashing or printing credentials.

### SEC-02: Secret Fragment Leakage in Public Status Endpoint
- **Severity:** High (CVSS 6.5)
- **Description:** `GET /supply/status` returned masked key fragments (`key[:4] + "..." + key[-4:]`), exposing 25% of the credential string.
- **Remediation:**
  Removed all key masking and substring logic. The endpoint now returns solely a boolean flag:
  ```json
  {
    "firms_configured": true,
    "has_live_cache": true,
    "source": "NASA FIRMS VIIRS (SNPP / NOAA)",
    "pilot_bbox": [74.3, 29.5, 77.4, 32.5]
  }
  ```
  Zero prefix or suffix characters are ever transmitted over the wire or stored in responses.

### SEC-03: Stored Cross-Site Scripting (XSS) via Unescaped DOM Insertion
- **Severity:** High (CVSS 7.2)
- **Description:** User-supplied strings (such as supplier names, village names, and listing notes) were interpolated directly into `element.innerHTML` in `index.html`.
- **Remediation:**
  1. Implemented a robust `escapeHtml()` utility function for all dynamic content insertions.
  2. Replaced dynamic `.innerHTML` concatenation with `document.createElement()` and `.textContent` property assignment for untrusted user inputs.
  3. Verified with injection payloads (e.g., `<img src=x onerror=alert(1)>`, `"><script>alert(1)</script>`) in `tests/test_security.py`.

### SEC-04: Unauthenticated Administrative Cache/DB Truncation
- **Severity:** High (CVSS 7.8)
- **Description:** `POST /supply/refresh` allowed any unauthenticated user to trigger arbitrary file writes and purge the `supply_cells` database table.
- **Remediation:**
  1. Added administrative authentication requiring the `X-Admin-Key` header matching `os.environ.get("ADMIN_KEY")` (or an explicit local admin token).
  2. Restricted file writes strictly to `data/raw/` and `data/processed/` using absolute repository paths to prevent path traversal attacks.
  3. Replaced direct file overwriting with atomic replacement to prevent partial write corruption.

---

## 3. NASA FIRMS API Key Rotation Procedure

> [!IMPORTANT]
> Removing an API key from local files or Git checkpoints **does not** revoke it on upstream servers. If a NASA FIRMS key was previously exposed, the account owner must rotate it immediately.

### Official Step-by-Step Rotation Instructions:
1. Navigate to the NASA FIRMS Map Key management portal:  
   👉 [https://firms.modaps.eosdis.nasa.gov/api/map_key](https://firms.modaps.eosdis.nasa.gov/api/map_key)
2. Log in with your Earthdata / FIRMS registered email.
3. Request a new MAP_KEY or revoke the compromised key.
4. Update your local secret store or deployment environment:
   ```bash
   export FIRMS_MAP_KEY="<your_new_secret_key>"
   ```
5. Confirm that the application loads the new key:
   ```bash
   python -c "from pipeline.firms_pipeline import get_firms_map_key; print('Configured:', bool(get_firms_map_key()))"
   ```
   *(Note: The above command tests configuration without printing the key value).*

---

## 4. Security Verification Checklist

- [x] All `.env` and `backend/.env` files excluded from Git and release archive.
- [x] `.env.example` contains only explicit placeholders.
- [x] `GET /supply/status` returns zero key fragments.
- [x] `POST /supply/refresh` requires `X-Admin-Key` header.
- [x] Frontend input rendering uses `escapeHtml()` and `textContent`.
- [x] Automated test suite `tests/test_security.py` passes all checks.
- [x] SHA-256 release checksum recorded for the final build artifact.
