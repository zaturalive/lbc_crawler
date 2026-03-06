from dataclasses import asdict, field
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from fiches_auto_scraper import FichesAutoScraper
from lbc_scraper import LBCScraper, SearchFilters
from regex_engine import RegexEngine

app = FastAPI(title="fmc-scraper", version="1.0.0")

_lbc = LBCScraper()
_fiches = FichesAutoScraper()
_regex = RegexEngine()


class ScrapeRequest(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    mileage_max: Optional[int] = None
    year_min: Optional[int] = None
    horsepower_min: Optional[int] = None
    horsepower_max: Optional[int] = None
    gearbox: Optional[str] = None
    pattern_ids: list[int] = field(default_factory=list)
    custom_regex: Optional[str] = None


class VehicleInfoRequest(BaseModel):
    brand: str
    model: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scrape")
def scrape(req: ScrapeRequest):
    extra = []
    if req.custom_regex:
        try:
            RegexEngine.validate_pattern(req.custom_regex)
            extra.append({"name": "Custom", "pattern": req.custom_regex})
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

    filters = SearchFilters(
        brand=req.brand,
        model=req.model,
        price_min=req.price_min,
        price_max=req.price_max,
        mileage_max=req.mileage_max,
        year_min=req.year_min,
        horsepower_min=req.horsepower_min,
        horsepower_max=req.horsepower_max,
        gearbox=req.gearbox,
        extra_patterns=extra,
    )
    listings = _lbc.search(filters)

    if req.horsepower_min or req.horsepower_max:
        listings = [
            l for l in listings
            if (req.horsepower_min is None or (l["horsepower"] or 0) >= req.horsepower_min)
            and (req.horsepower_max is None or (l["horsepower"] or 999) <= req.horsepower_max)
        ]

    return listings


@app.post("/vehicle-info")
def vehicle_info(req: VehicleInfoRequest):
    data = _fiches.get_vehicle_data(req.brand, req.model)
    if data is None:
        return {"reliability_score": None, "common_issues": []}
    return data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
