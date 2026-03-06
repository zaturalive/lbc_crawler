import logging
import os
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models import Listing, RegexPattern, SearchSession, Vehicle
from schemas import ListingResponse, SearchRequest, SearchResult, VehicleResponse

logger = logging.getLogger(__name__)

SCRAPER_URL = os.getenv("SCRAPER_URL", "http://scraper:8001")
SCRAPER_TIMEOUT = float(os.getenv("SCRAPER_TIMEOUT", "120"))


async def run_search(req: SearchRequest, db: AsyncSession) -> SearchResult:
    patterns = await _load_patterns(req.pattern_ids, db)

    scraper_payload = {
        "brand": req.brand,
        "model": req.model,
        "price_min": req.price_min,
        "price_max": req.price_max,
        "mileage_max": req.mileage_max,
        "year_min": req.year_min,
        "horsepower_min": req.horsepower_min,
        "horsepower_max": req.horsepower_max,
        "gearbox": req.gearbox,
        "pattern_ids": req.pattern_ids,
        "custom_regex": req.custom_regex,
    }

    raw_listings = await _call_scraper(scraper_payload)

    upserted = []
    for raw in raw_listings:
        vehicle = await _resolve_vehicle(raw.get("brand", ""), raw.get("model", ""), db)
        listing = await _upsert_listing(raw, vehicle.id if vehicle else None, db)
        listing_resp = ListingResponse.model_validate(listing)
        if vehicle:
            listing_resp.vehicle = VehicleResponse.model_validate(vehicle)
        upserted.append(listing_resp)

    session = SearchSession(
        filters={k: v for k, v in req.model_dump().items() if k != "pattern_ids"},
        patterns=[p.name for p in patterns],
        result_count=len(upserted),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SearchResult(session_id=session.id, count=len(upserted), listings=upserted)


async def _call_scraper(payload: dict) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=SCRAPER_TIMEOUT) as client:
            resp = await client.post(f"{SCRAPER_URL}/scrape", json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.TimeoutException:
        logger.error("Scraper timed out after %ss", SCRAPER_TIMEOUT)
        return []
    except httpx.HTTPStatusError as exc:
        logger.error("Scraper returned error: %s", exc)
        return []
    except Exception as exc:
        logger.error("Scraper call failed: %s", exc)
        return []


async def _resolve_vehicle(brand: str, model: str, db: AsyncSession) -> Optional[Vehicle]:
    if not brand or not model:
        return None
    result = await db.execute(
        select(Vehicle).where(Vehicle.brand == brand, Vehicle.model == model).limit(1)
    )
    vehicle = result.scalar_one_or_none()
    if vehicle:
        return vehicle

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{SCRAPER_URL}/vehicle-info",
                json={"brand": brand, "model": model},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("Could not fetch vehicle info for %s %s: %s", brand, model, exc)
        return None

    vehicle = Vehicle(
        brand=brand,
        model=model,
        reliability_score=data.get("reliability_score"),
        common_issues=data.get("common_issues", []),
    )
    db.add(vehicle)
    await db.flush()
    return vehicle


async def _upsert_listing(raw: dict, vehicle_id: Optional[int], db: AsyncSession) -> Listing:
    stmt = (
        insert(Listing)
        .values(
            lbc_id=raw["lbc_id"],
            title=raw.get("title"),
            price=raw.get("price"),
            year=raw.get("year"),
            mileage=raw.get("mileage"),
            horsepower=raw.get("horsepower"),
            gearbox=raw.get("gearbox"),
            location=raw.get("location"),
            description=raw.get("description"),
            url=raw.get("url"),
            matched_keywords=raw.get("matched_keywords", []),
            vehicle_id=vehicle_id,
        )
        .on_duplicate_key_update(
            title=raw.get("title"),
            price=raw.get("price"),
            mileage=raw.get("mileage"),
            matched_keywords=raw.get("matched_keywords", []),
            vehicle_id=vehicle_id,
        )
    )
    await db.execute(stmt)
    await db.flush()
    result = await db.execute(select(Listing).where(Listing.lbc_id == raw["lbc_id"]))
    return result.scalar_one()


async def _load_patterns(pattern_ids: list[int], db: AsyncSession) -> list[RegexPattern]:
    if not pattern_ids:
        return []
    result = await db.execute(
        select(RegexPattern).where(RegexPattern.id.in_(pattern_ids))
    )
    return list(result.scalars().all())
