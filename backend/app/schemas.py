"""
KilnLink / Parali Mitra Authoritative Pydantic Schemas
Strict validation, business rule bounds, and security-hardened inputs.
"""
from typing import List, Optional, Dict, Any, Literal
import datetime
from pydantic import BaseModel, Field, field_validator

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
    state: str = "Punjab"
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
    role: Optional[str] = None
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
    name: str = Field(..., min_length=2, max_length=100, description="Supplier name or organization")
    village: str = Field(..., min_length=2, max_length=100, description="Village or tehsil name")
    straw_form: Literal["bale", "chopped", "pellet"] = Field(..., description="Straw form must be bale, chopped, or pellet")
    tonnes: float = Field(..., gt=0.0, le=1000.0, description="Available quantity must be positive and <= 1,000 tonnes")
    price_per_tonne: float = Field(..., gt=0.0, le=50000.0, description="Price per tonne in INR (positive)")
    kind: Optional[Literal["farmer", "aggregator", "pellet_unit"]] = Field(default="farmer")
    lat: Optional[float] = Field(default=None, ge=28.0, le=34.0)
    lon: Optional[float] = Field(default=None, ge=73.0, le=78.0)
    supplier_id: Optional[str] = Field(default=None, max_length=20)

    @field_validator("name", "village")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        cleaned = v.strip()
        if "<" in cleaned or ">" in cleaned:
            # Strip dangerous characters to prevent injection
            cleaned = cleaned.replace("<", "").replace(">", "").strip()
        if not cleaned:
            raise ValueError("Field cannot be empty after stripping invalid characters.")
        return cleaned

class CreateDeliveryRequest(BaseModel):
    kiln_id: str = Field(..., min_length=2, max_length=20, pattern=r"^[A-Za-z0-9_-]+$")
    supplier_id: str = Field(..., min_length=2, max_length=20, pattern=r"^[A-Za-z0-9_-]+$")
    date: str = Field(..., description="ISO 8601 calendar date YYYY-MM-DD")
    tonnes: float = Field(..., gt=0.0, le=500.0, description="Delivery tonnage must be positive and <= 500t per dispatch")
    form: Literal["bale", "chopped", "pellet"] = Field(..., description="Straw form must be bale, chopped, or pellet")
    photo_ref: Optional[str] = Field(default="slip_default.jpg", max_length=120)

    @field_validator("date")
    @classmethod
    def validate_iso_date(cls, v: str) -> str:
        s = v.strip()
        try:
            # Enforce valid real calendar date (checks leap years, day ranges 1-31, etc.)
            d = datetime.date.fromisoformat(s)
            return d.isoformat()
        except ValueError:
            raise ValueError(f"Invalid calendar date '{v}'. Expected valid ISO YYYY-MM-DD date.")

class DeliveryResponse(BaseModel):
    delivery_id: str
    status: str = "recorded"
    receipt: str
    receipt_hash: Optional[str] = None
    prev_hash: Optional[str] = None
    timestamp: Optional[str] = None

class ReceiptVerificationItem(BaseModel):
    receipt_id: str
    delivery_id: str
    date: str
    tonnes: float
    current_hash: str
    prev_hash: str
    is_valid: bool

class ReceiptVerificationResponse(BaseModel):
    is_valid: bool
    total_receipts: int
    broken_links_count: int
    chain_head: Optional[str] = None
    receipts: List[ReceiptVerificationItem]
    message: str

class ReceiptHeadResponse(BaseModel):
    chain_head: str
    latest_receipt_id: Optional[str] = None
    timestamp: Optional[str] = None
    total_receipts: int
    tracker_head_hash: Optional[str] = None
    tracker_count: Optional[int] = None

class KilnComplianceItem(BaseModel):
    kiln_id: str
    name: str
    lat: float
    lon: float
    straw_tonnes: float
    fuel_tonnes: float
    share: float
    status: str  # meets_target | below_target
    share_pellet_only: Optional[float] = None
    share_all_forms: Optional[float] = None

class ComplianceTotals(BaseModel):
    kilns: int
    meeting_target: int
    straw_tonnes: float

class ComplianceSummaryResponse(BaseModel):
    month: str
    target_share: float
    kilns: List[KilnComplianceItem]
    totals: ComplianceTotals
    eligibility_mode: Optional[str] = "all_forms"

# --- HOURLY OBSERVATION ANALYSIS SCHEMAS ---

class ObservationHourItem(BaseModel):
    hour_utc: int
    hour_ist: int
    label_ist: str
    count: int
    percentage: float

class SatelliteObservationAnalysisResponse(BaseModel):
    date_range: str
    total_detections: int
    peak_window_ist: str
    satellite_sensor: str
    orbital_type: str
    overpass_schedule_notes: str
    hourly_distribution: List[ObservationHourItem]

# --- AUTO-DISPATCH SIMULATION SCHEMAS ---

class DispatchAllocationItem(BaseModel):
    kiln_id: str
    kiln_name: str
    supplier_id: str
    supplier_name: str
    straw_form: str
    distance_km: float
    delivered_cost_per_tonne: float
    allocated_tonnes: float
    total_cost_inr: float

class DispatchKilnSummary(BaseModel):
    kiln_id: str
    kiln_name: str
    monthly_fuel_tonnes: float
    straw_needed_tonnes: float
    pre_existing_delivered_tonnes: float
    simulated_allocated_tonnes: float
    net_gap_remaining: float
    target_met: bool

class AutoDispatchSimulationResponse(BaseModel):
    status: str = "simulation"
    provenance: str = "Deterministic greedy matching on current database state. Simulation only; no production records altered."
    reporting_month: str
    target_mandate_share: float
    total_kiln_demand_tonnes: float
    total_allocated_tonnes: float
    total_unmet_tonnes: float
    total_estimated_cost_inr: float
    allocations: List[DispatchAllocationItem]
    kiln_summaries: List[DispatchKilnSummary]

# --- ML PREDICTION SCHEMAS ---

class YieldPredictRequest(BaseModel):
    """ML yield prediction — extreme values are clamped to training bounds, not rejected."""
    acres: float = Field(default=10.0)
    variety_idx: int = Field(default=1)
    grain_yield_qtl_acre: float = Field(default=28.0)
    ndvi: float = Field(default=0.78)
    cutting_height_cm: float = Field(default=18.0)

    @field_validator("acres", "grain_yield_qtl_acre", "ndvi", "cutting_height_cm", mode="before")
    @classmethod
    def reject_nan_inf(cls, v: object) -> float:
        import math
        f = float(v)  # type: ignore[arg-type]
        if math.isnan(f) or math.isinf(f):
            raise ValueError("NaN and Inf are not allowed")
        return f

    @field_validator("acres")
    @classmethod
    def clamp_acres(cls, v: float) -> float:
        return min(max(v, 0.01), 5000.0)

    @field_validator("variety_idx", mode="before")
    @classmethod
    def clamp_variety(cls, v: object) -> int:
        return min(max(int(v), 0), 2)  # type: ignore[arg-type]

    @field_validator("grain_yield_qtl_acre")
    @classmethod
    def clamp_grain(cls, v: float) -> float:
        return min(max(v, 0.01), 100.0)

    @field_validator("ndvi")
    @classmethod
    def clamp_ndvi(cls, v: float) -> float:
        return min(max(v, 0.0), 1.0)

    @field_validator("cutting_height_cm")
    @classmethod
    def clamp_cutting(cls, v: float) -> float:
        return min(max(v, 5.0), 60.0)


class PricePredictRequest(BaseModel):
    """ML price prediction — extreme values are clamped to training bounds, not rejected."""
    distance_km: float = Field(default=12.0)
    form_idx: int = Field(default=1)
    moisture_pct: float = Field(default=14.0)
    harvest_week: int = Field(default=2)
    supply_density_index: float = Field(default=0.75)

    @field_validator("distance_km", "moisture_pct", "supply_density_index", mode="before")
    @classmethod
    def reject_nan_inf_price(cls, v: object) -> float:
        import math
        f = float(v)  # type: ignore[arg-type]
        if math.isnan(f) or math.isinf(f):
            raise ValueError("NaN and Inf are not allowed")
        return f

    @field_validator("distance_km")
    @classmethod
    def clamp_distance(cls, v: float) -> float:
        return min(max(v, 0.0), 200.0)

    @field_validator("form_idx", mode="before")
    @classmethod
    def clamp_form(cls, v: object) -> int:
        return min(max(int(v), 0), 2)  # type: ignore[arg-type]

    @field_validator("moisture_pct")
    @classmethod
    def clamp_moisture(cls, v: float) -> float:
        return min(max(v, 5.0), 40.0)

    @field_validator("harvest_week", mode="before")
    @classmethod
    def clamp_harvest_week(cls, v: object) -> int:
        return min(max(int(v), 1), 8)  # type: ignore[arg-type]

    @field_validator("supply_density_index")
    @classmethod
    def clamp_density(cls, v: float) -> float:
        return min(max(v, 0.0), 1.0)


class FireRiskPredictRequest(BaseModel):
    days_to_wheat_sowing: float = Field(default=10.0, ge=0.0, le=60.0)
    dist_to_kiln_km: float = Field(default=15.0, ge=0.0, le=200.0)
    machinery_access_score: int = Field(default=2, ge=1, le=5)
    cell_fire_density: float = Field(default=0.65, ge=0.0, le=1.0)
