"""
KilnLink / Parali Mitra Pydantic Schemas matching Section 5 Shared Contract + ML Endpoints
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str
    app: str = "Parali Mitra"
    version: str = "1.0.0"

class KilnItem(BaseModel):
    kiln_id: str
    name: str
    lat: float
    lon: float
    village: str
    monthly_fuel_tonnes: float

class SupplierItem(BaseModel):
    supplier_id: str
    name: str
    kind: str
    lat: float
    lon: float
    village: str
    straw_form: str
    price_per_tonne: float
    available_tonnes: float

class SupplyCellItem(BaseModel):
    cell_id: str
    lat: float
    lon: float
    fire_count_last_season: int
    supply_index: float

class KilnNeedsResponse(BaseModel):
    kiln_id: str
    month: str
    mandate_share: float
    monthly_fuel_tonnes: float
    straw_needed_tonnes: float
    delivered_tonnes: float
    gap_tonnes: float
    basis: str = "weight"
    note: str = "SAMPLE DATA"

class RankedSupplier(BaseModel):
    supplier_id: str
    name: str
    kind: str
    form: str
    distance_km: float
    price_per_tonne: float
    delivered_cost_per_tonne: float
    available_tonnes: float

class KilnSuppliersResponse(BaseModel):
    kiln_id: str
    coal_cost_per_tonne: float
    suppliers: List[RankedSupplier]

class CreateListingRequest(BaseModel):
    name: str
    village: str
    straw_form: str
    tonnes: float
    price_per_tonne: float
    kind: Optional[str] = "farmer"
    lat: Optional[float] = None
    lon: Optional[float] = None
    supplier_id: Optional[str] = None

class CreateDeliveryRequest(BaseModel):
    kiln_id: str
    supplier_id: str
    date: str
    tonnes: float
    form: str
    photo_ref: Optional[str] = "slip_default.jpg"

class DeliveryResponse(BaseModel):
    delivery_id: str
    status: str = "recorded"
    receipt: str

class KilnComplianceItem(BaseModel):
    kiln_id: str
    name: str
    lat: float
    lon: float
    straw_tonnes: float
    fuel_tonnes: float
    share: float
    status: str  # meets_target | below_target

class ComplianceTotals(BaseModel):
    kilns: int
    meeting_target: int
    straw_tonnes: float

class ComplianceSummaryResponse(BaseModel):
    month: str
    target_share: float
    kilns: List[KilnComplianceItem]
    totals: ComplianceTotals

# --- ML PREDICTION SCHEMAS ---

class YieldPredictRequest(BaseModel):
    acres: float = 10.0
    variety_idx: int = 1  # 0: PR-126, 1: Pusa-44, 2: Basmati
    grain_yield_qtl_acre: float = 28.0
    ndvi: float = 0.78
    cutting_height_cm: float = 18.0

class PricePredictRequest(BaseModel):
    distance_km: float = 12.0
    form_idx: int = 1  # 0: bale, 1: chopped, 2: pellet
    moisture_pct: float = 14.0
    harvest_week: int = 2
    supply_density_index: float = 0.75

class FireRiskPredictRequest(BaseModel):
    days_to_wheat_sowing: float = 10.0
    dist_to_kiln_km: float = 15.0
    machinery_access_score: int = 2  # 1 to 5
    cell_fire_density: float = 0.65
