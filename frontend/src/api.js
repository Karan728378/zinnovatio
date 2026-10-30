/**
 * KilnLink Frontend API Client (Person 3)
 * Supports live backend and seamless in-memory fallback for local demonstration.
 */

const API_BASE = (typeof window !== "undefined" && window.__API_BASE__) || "http://localhost:8000";
export const USE_MOCK = false;

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchConfig() {
  const res = await fetch(`${API_BASE}/config`);
  return res.json();
}

export async function fetchKilns() {
  const res = await fetch(`${API_BASE}/kilns`);
  return res.json();
}

export async function fetchKilnNeeds(kilnId, month = "2026-11") {
  const res = await fetch(`${API_BASE}/kilns/${kilnId}/needs?month=${month}`);
  return res.json();
}

export async function fetchKilnSuppliers(kilnId) {
  const res = await fetch(`${API_BASE}/kilns/${kilnId}/suppliers`);
  return res.json();
}

export async function createListing(listingData) {
  const res = await fetch(`${API_BASE}/listings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(listingData),
  });
  return res.json();
}

export async function getSupplierKilns(supplierId) {
  const res = await fetch(`${API_BASE}/suppliers/${supplierId}/kilns`);
  return res.json();
}

export async function recordDelivery(deliveryData) {
  const res = await fetch(`${API_BASE}/deliveries`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(deliveryData),
  });
  return res.json();
}
