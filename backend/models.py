from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CalibrationRequest(BaseModel):
    box_x: float
    box_y: float
    box_w: float
    box_h: float
    real_w: float
    real_h: float

class ProjectBase(BaseModel):
    filename: str
    filepath: str
    width: int
    height: int
    scale_factor: Optional[float] = None
    reference_box: Optional[Dict[str, Any]] = None  # e.g. {x: 10, y: 10, w: 100, h: 50, real_w: 50.0, real_h: 25.0}
    build_volume: int = 1000

class Project(ProjectBase):
    id: str
    created_at: str

class DetectionBase(BaseModel):
    designator: Optional[str] = None
    component_class: str
    bbox: Dict[str, float]  # {xmin, ymin, xmax, ymax} in global pixel coords
    marking_text: Optional[str] = None
    visual_notes: Optional[str] = None
    confidence: str  # high, medium, low
    package: Optional[str] = None
    measured_width: Optional[float] = None
    measured_height: Optional[float] = None
    package_status: str = "unresolved"  # resolved, unresolved, custom
    manually_added: bool = False
    is_deleted: bool = False

class Detection(DetectionBase):
    id: int
    project_id: str

class SourcingCacheItem(BaseModel):
    key: str  # e.g., "R:0603:10k" or "U:SOIC-8:NE555"
    manufacturer: Optional[str] = None
    part_number: Optional[str] = None
    description: Optional[str] = None
    distributor: Optional[str] = None
    distributor_part_number: Optional[str] = None
    price_breaks: List[Dict[str, Any]] = []  # [{qty: 1, price: 0.1}, {qty: 10, price: 0.08}, ...]
    datasheet_url: Optional[str] = None
    product_page_url: Optional[str] = None
    match_basis: str  # identified, equivalent, generic
    timestamp: str

class CostedBOMRow(BaseModel):
    line_number: int
    component_class: str
    designators: str  # comma separated
    quantity: int
    marking_text: Optional[str] = None
    package: Optional[str] = None
    measured_length: Optional[float] = None
    measured_width: Optional[float] = None
    package_resolution_status: str
    
    # Sourcing
    manufacturer: Optional[str] = None
    part_number: Optional[str] = None
    description: Optional[str] = None
    distributor: Optional[str] = None
    distributor_part_number: Optional[str] = None
    datasheet_url: Optional[str] = None
    product_page_url: Optional[str] = None
    match_basis: str
    
    # Pricing
    unit_price: Optional[float] = None
    currency: str = "USD"
    price_break_qty: Optional[int] = None
    moq: Optional[int] = None
    stock_status: Optional[str] = None
    extended_cost: Optional[float] = None
    price_date: Optional[str] = None
    
    # Provenance
    confidence: str
    manufacturer_read: bool = False
    part_number_read: bool = False
    price_read: bool = False
    note: Optional[str] = None
