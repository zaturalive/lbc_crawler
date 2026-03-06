import logging
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from fiches_auto_scraper import bulk_scrape_vehicles
from lbc_scraper import LBCScraper, SearchFilters
from regex_engine import RegexEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="fmc-scraper", version="2.0.0")

_lbc = LBCScraper()
_regex = RegexEngine()

# Track sync status
_sync_status = {"running": False, "last_count": 0, "last_error": None}


class ScrapeRequest(BaseModel):
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
    radius: Optional[int] = None  # km, default 30
    patterns: list[dict] = []
    custom_regex: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok", "sync_status": _sync_status}


@app.post("/scrape")
def scrape(req: ScrapeRequest):
    extra = list(req.patterns or [])
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
        mileage_min=req.mileage_min,
        year_min=req.year_min,
        horsepower_min=req.horsepower_min,
        horsepower_max=req.horsepower_max,
        gearbox=req.gearbox,
        fuel=req.fuel,
        city=req.city,
        radius=req.radius,
        extra_patterns=extra,
    )
    try:
        listings = _lbc.search(filters)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"listings": listings, "count": len(listings)}


@app.post("/scrape/vehicles-catalog")
def scrape_vehicles_catalog(background_tasks: BackgroundTasks):
    """Trigger a full fiches-auto.fr scrape (async). Returns vehicle data when complete."""
    if _sync_status["running"]:
        raise HTTPException(status_code=409, detail="Sync already in progress")

    _sync_status["running"] = True
    _sync_status["last_error"] = None

    def _run():
        try:
            vehicles = bulk_scrape_vehicles()
            _sync_status["last_count"] = len(vehicles)
            logger.info("Bulk scrape complete: %d vehicles", len(vehicles))
            _sync_status["vehicles_buffer"] = vehicles
        except Exception as exc:
            _sync_status["last_error"] = str(exc)
            logger.error("Bulk scrape failed: %s", exc)
        finally:
            _sync_status["running"] = False

    background_tasks.add_task(_run)
    return {"status": "started", "message": "Scraping fiches-auto.fr in background. Poll /scrape/vehicles-status"}


@app.get("/scrape/vehicles-status")
def vehicles_status():
    """Check sync status and retrieve results when done."""
    if _sync_status["running"]:
        return {"status": "running"}
    if _sync_status.get("last_error"):
        return {"status": "error", "error": _sync_status["last_error"]}
    vehicles = _sync_status.pop("vehicles_buffer", None)
    if vehicles is not None:
        return {"status": "done", "count": len(vehicles), "vehicles": vehicles}
    return {"status": "idle", "last_count": _sync_status["last_count"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
