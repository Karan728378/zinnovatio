/**
 * KilnLink Frontend API Client (Person 3)
 * Supports live backend and defensive fallbacks for local / offline operation.
 */

const API_BASE = (typeof window !== "undefined" && window.__API_BASE__) || "http://127.0.0.1:8000";
export const USE_MOCK = false;

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) return { status: "degraded", code: res.status };
    return await res.json();
  } catch (err) {
    return { status: "offline", error: err.message };
  }
}

export async function fetchConfig() {
  try {
    const res = await fetch(`${API_BASE}/config`);
    if (!res.ok) return { mandate_share: { "2025-11": 0.2, "2026-11": 0.3, "2027-11": 0.4, "2028-11": 0.5 } };
    return await res.json();
  } catch (err) {
    return { mandate_share: { "2025-11": 0.2, "2026-11": 0.3, "2027-11": 0.4, "2028-11": 0.5 }, error: err.message };
  }
}

export async function fetchKilns() {
  try {
    const res = await fetch(`${API_BASE}/kilns`);
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    return [];
  }
}

export async function fetchKilnNeeds(kilnId, month = "2026-11") {
  try {
    const res = await fetch(`${API_BASE}/kilns/${encodeURIComponent(kilnId)}/needs?month=${encodeURIComponent(month)}`);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    return null;
  }
}

export async function fetchKilnSuppliers(kilnId) {
  try {
    const res = await fetch(`${API_BASE}/kilns/${encodeURIComponent(kilnId)}/suppliers`);
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    return [];
  }
}

export async function createListing(listingData) {
  try {
    const res = await fetch(`${API_BASE}/listings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(listingData),
    });
    return await res.json();
  } catch (err) {
    return { error: err.message };
  }
}

export async function getSupplierKilns(supplierId) {
  try {
    const res = await fetch(`${API_BASE}/suppliers/${encodeURIComponent(supplierId)}/kilns`);
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    return [];
  }
}

export async function recordDelivery(deliveryData) {
  try {
    const res = await fetch(`${API_BASE}/deliveries`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(deliveryData),
    });
    return await res.json();
  } catch (err) {
    return { error: err.message };
  }
}

export async function simulateDispatch(month = "2026-11") {
  try {
    const res = await fetch(`${API_BASE}/dispatch/simulate?month=${encodeURIComponent(month)}`, { method: "POST" });
    if (!res.ok) return { total_kiln_demand_tonnes: 0, total_allocated_tonnes: 0, allocations: [] };
    return await res.json();
  } catch (err) {
    return { total_kiln_demand_tonnes: 0, total_allocated_tonnes: 0, allocations: [], error: err.message };
  }
}

export async function verifyReceiptChain() {
  try {
    const res = await fetch(`${API_BASE}/receipts/verify`);
    if (!res.ok) return { is_valid: false, total_receipts: 0, broken_links_count: 0, receipts: [] };
    return await res.json();
  } catch (err) {
    return { is_valid: false, total_receipts: 0, broken_links_count: 0, receipts: [], error: err.message };
  }
}

export const MOCK_SUPPLIERS = [
  {
    "supplier_id": "S001",
    "name": "Sangrur Baler Union",
    "role": "CHC Center",
    "kind": "aggregator",
    "lat": 30.26,
    "lon": 75.85,
    "village": "Sangrur",
    "straw_form": "bale",
    "price_per_tonne": 1400.0,
    "available_tonnes": 45.0
  },
  {
    "supplier_id": "S002",
    "name": "Dhuri Biomass Aggregator",
    "role": "Aggregator Hub",
    "kind": "aggregator",
    "lat": 30.32,
    "lon": 75.92,
    "village": "Dhuri",
    "straw_form": "bale",
    "price_per_tonne": 1550.0,
    "available_tonnes": 50.0
  },
  {
    "supplier_id": "S003",
    "name": "Sunam Farmers Cooperative",
    "role": "Lead Farmer",
    "kind": "farmer",
    "lat": 30.2,
    "lon": 75.8,
    "village": "Sunam",
    "straw_form": "bale",
    "price_per_tonne": 1450.0,
    "available_tonnes": 80.0
  },
  {
    "supplier_id": "S004",
    "name": "Sangrur Bio-Pellets Unit",
    "role": "Pellet Manufacturer",
    "kind": "fpo_depot",
    "lat": 30.28,
    "lon": 75.88,
    "village": "Sangrur",
    "straw_form": "pellet",
    "price_per_tonne": 2400.0,
    "available_tonnes": 120.0
  },
  {
    "supplier_id": "S005",
    "name": "Malerkotla Farmers FPO",
    "role": "Cooperative FPO",
    "kind": "fpo_depot",
    "lat": 30.6115,
    "lon": 75.9,
    "village": "Malerkotla",
    "straw_form": "bale",
    "price_per_tonne": 1600.0,
    "available_tonnes": 40.0
  },
  {
    "supplier_id": "S006",
    "name": "Ahmedgarh Kisan Union",
    "role": "Farmer Group",
    "kind": "farmer",
    "lat": 30.43,
    "lon": 75.76,
    "village": "Ahmedgarh",
    "straw_form": "bale",
    "price_per_tonne": 1350.0,
    "available_tonnes": 25.0
  },
  {
    "supplier_id": "S007",
    "name": "Lehragaga Aggregators Network",
    "role": "Aggregator Hub",
    "kind": "aggregator",
    "lat": 30.14,
    "lon": 75.96,
    "village": "Lehragaga",
    "straw_form": "bale",
    "price_per_tonne": 1520.0,
    "available_tonnes": 35.0
  },
  {
    "supplier_id": "S008",
    "name": "Bhawanigarh Biomass Aggregation",
    "role": "Aggregator Hub",
    "kind": "aggregator",
    "lat": 30.36,
    "lon": 76.0,
    "village": "Bhawanigarh",
    "straw_form": "bale",
    "price_per_tonne": 1550.0,
    "available_tonnes": 60.0
  },
  {
    "supplier_id": "S009",
    "name": "Amargarh Green Fuel Depot",
    "role": "Pellet Depot",
    "kind": "fpo_depot",
    "lat": 30.45,
    "lon": 75.94,
    "village": "Amargarh",
    "straw_form": "pellet",
    "price_per_tonne": 2500.0,
    "available_tonnes": 150.0
  },
  {
    "supplier_id": "S010",
    "name": "Longowal Progressive Farmers",
    "role": "Farmer Group",
    "kind": "farmer",
    "lat": 30.3,
    "lon": 75.7,
    "village": "Longowal",
    "straw_form": "bale",
    "price_per_tonne": 1420.0,
    "available_tonnes": 20.0
  },
  {
    "supplier_id": "S011",
    "name": "Dirba Rural Baler Cooperative",
    "role": "CHC Center",
    "kind": "aggregator",
    "lat": 30.1,
    "lon": 75.87,
    "village": "Dirba",
    "straw_form": "bale",
    "price_per_tonne": 1500.0,
    "available_tonnes": 70.0
  },
  {
    "supplier_id": "S012",
    "name": "Moonak Farmers Producer Group",
    "role": "Cooperative Farmer",
    "kind": "farmer",
    "lat": 30.22,
    "lon": 76.02,
    "village": "Moonak",
    "straw_form": "bale",
    "price_per_tonne": 1400.0,
    "available_tonnes": 28.0
  },
  {
    "supplier_id": "S013",
    "name": "Sunam Biofuel Depot",
    "role": "Pellet Depot",
    "kind": "fpo_depot",
    "lat": 30.19,
    "lon": 75.82,
    "village": "Sunam",
    "straw_form": "pellet",
    "price_per_tonne": 2350.0,
    "available_tonnes": 100.0
  },
  {
    "supplier_id": "S014",
    "name": "Sherpur Biomass Depot",
    "role": "Storage Depot",
    "kind": "fpo_depot",
    "lat": 30.35,
    "lon": 75.79,
    "village": "Sherpur",
    "straw_form": "bale",
    "price_per_tonne": 1480.0,
    "available_tonnes": 32.0
  },
  {
    "supplier_id": "S015",
    "name": "Dhuri Farmer Collective",
    "role": "Farmer Group",
    "kind": "farmer",
    "lat": 30.33,
    "lon": 75.9,
    "village": "Dhuri",
    "straw_form": "bale",
    "price_per_tonne": 1500.0,
    "available_tonnes": 55.0
  }
];
