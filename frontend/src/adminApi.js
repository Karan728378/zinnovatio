/**
 * KilnLink Regulator & Admin API Client (Person 4)
 * Supports live backend and defensive fallbacks for local / offline operation.
 */

const API_BASE = (typeof window !== "undefined" && window.__API_BASE__) || "http://127.0.0.1:8000";

export async function fetchSupplyMap() {
  try {
    const res = await fetch(`${API_BASE}/supply/map`);
    if (!res.ok) return { total_cells: 0, cells: [] };
    const data = await res.json();
    return data || { total_cells: 0, cells: [] };
  } catch (err) {
    return { total_cells: 0, cells: [], error: err.message };
  }
}

export async function fetchComplianceSummary(month = "2026-11") {
  try {
    const res = await fetch(`${API_BASE}/compliance/summary?month=${encodeURIComponent(month)}`);
    if (!res.ok) return { month, totals: { kilns: 0, meeting_target: 0, straw_tonnes: 0 }, kilns: [] };
    const data = await res.json();
    return data || { month, totals: { kilns: 0, meeting_target: 0, straw_tonnes: 0 }, kilns: [] };
  } catch (err) {
    return { month, totals: { kilns: 0, meeting_target: 0, straw_tonnes: 0 }, kilns: [], error: err.message };
  }
}

export async function fetchSupplyStatus() {
  try {
    const res = await fetch(`${API_BASE}/supply/status`);
    if (!res.ok) return { firms_configured: false, detections: 0, source: "offline_fallback" };
    return await res.json();
  } catch (err) {
    return { firms_configured: false, detections: 0, source: "offline_fallback", error: err.message };
  }
}

export async function fetchSupplyBlindspot() {
  try {
    const res = await fetch(`${API_BASE}/supply/blindspot`);
    if (!res.ok) return { blindspot_count: 0, cells: [] };
    return await res.json();
  } catch (err) {
    return { blindspot_count: 0, cells: [], error: err.message };
  }
}

export async function fetchSatelliteHours() {
  try {
    const res = await fetch(`${API_BASE}/supply/hours`);
    if (!res.ok) return { satellite_sensor: "VIIRS 375m", hourly_distribution: [] };
    return await res.json();
  } catch (err) {
    return { satellite_sensor: "VIIRS 375m", hourly_distribution: [], error: err.message };
  }
}
