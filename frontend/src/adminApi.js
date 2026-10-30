/**
 * KilnLink Regulator & Admin API Client (Person 4)
 */

const API_BASE = (typeof window !== "undefined" && window.__API_BASE__) || "http://localhost:8000";

export async function fetchSupplyMap() {
  const res = await fetch(`${API_BASE}/supply/map`);
  return res.json();
}

export async function fetchComplianceSummary(month = "2026-11") {
  const res = await fetch(`${API_BASE}/compliance/summary?month=${month}`);
  return res.json();
}
