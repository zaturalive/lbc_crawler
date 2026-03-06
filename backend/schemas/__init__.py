from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VehicleResponse(BaseModel):
    id: Optional[int] = None
    brand: str
    model: str
    reliability_score: Optional[int] = None
    common_issues: Optional[list[str]] = None

    model_config = {"from_attributes": True}


class ListingResponse(BaseModel):
    id: int
    lbc_id: str
    title: Optional[str]
    price: Optional[int]
    year: Optional[int]
    mileage: Optional[int]
    horsepower: Optional[int]
    gearbox: Optional[str]
    location: Optional[str]
    url: Optional[str]
    matched_keywords: Optional[list[str]]
    vehicle: Optional[VehicleResponse] = None
    scraped_at: Optional[datetime]

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    mileage_max: Optional[int] = None
    year_min: Optional[int] = None
    horsepower_min: Optional[int] = None
    horsepower_max: Optional[int] = None
    gearbox: Optional[str] = None
    pattern_ids: list[int] = []
    custom_regex: Optional[str] = None


class SearchResult(BaseModel):
    session_id: int
    count: int
    listings: list[ListingResponse]


class PatternResponse(BaseModel):
    id: int
    name: str
    pattern: str
    description: Optional[str]
    is_default: bool

    model_config = {"from_attributes": True}


class PatternCreate(BaseModel):
    name: str
    pattern: str
    description: Optional[str] = None
