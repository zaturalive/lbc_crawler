import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

class VehicleResponse(BaseModel):
    id: Optional[int] = None
    brand: str
    model: str
    reliability_score: Optional[int] = None
    total_testimonials: Optional[int] = None
    common_issues: Optional[list[str]] = None
    known_issues_text: Optional[list] = None
    source_url: Optional[str] = None
    reliability_rank: Optional[str] = None

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
    fuel_type: Optional[str]
    doors: Optional[int]
    seats: Optional[int]
    color: Optional[str]
    location: Optional[str]
    url: Optional[str]
    matched_keywords: Optional[list[str]]
    vehicle: Optional[VehicleResponse] = None
    scraped_at: Optional[datetime]
    is_liked: Optional[bool] = False

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    mileage_min: Optional[int] = None
    mileage_max: Optional[int] = None
    year_min: Optional[int] = None
    horsepower_min: Optional[int] = None
    horsepower_max: Optional[int] = None
    gearbox: Optional[str] = None
    fuel: Optional[str] = None
    city: Optional[str] = None
    radius: Optional[int] = None  # km
    sort_by: Optional[str] = None   # price_asc | price_desc | recent | oldest | None (pertinence)
    condition: Optional[str] = None  # excellent | good | fair | minor_repairs | major_repairs | damaged | not_running
    pattern_ids: list[int] = []
    custom_regex: Optional[str] = None
    limit: int = Field(default=100, ge=50, le=600)


class SearchResult(BaseModel):
    session_id: int
    count: int
    limit: int
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


class LikeResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    listing_id: int
    created_at: Optional[datetime]
    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Format email invalide')
        return v.lower().strip()


class UserResponse(BaseModel):
    id: int
    email: str
    is_verified: bool
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class SearchSessionResponse(BaseModel):
    id: int
    filters: Optional[dict] = None
    patterns: Optional[list] = None
    result_count: Optional[int] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class ListingAnalysisResponse(BaseModel):
    id: int
    listing_id: int
    model_used: Optional[str] = None
    repairs_found: Optional[list[str]] = None
    upcoming_maintenance: Optional[list[str]] = None
    condition_summary: Optional[str] = None
    risk_level: Optional[str] = None
    created_at: Optional[datetime] = None
    is_premium: bool = False   # toujours False pour l'instant

    model_config = {"from_attributes": True}
