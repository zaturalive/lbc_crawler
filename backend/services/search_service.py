import logging
import os
from datetime import datetime
from typing import Optional

import httpx
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models import Listing, RegexPattern, SearchHistory, SearchSession, Vehicle
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
        "mileage_min": req.mileage_min,
        "year_min": req.year_min,
        "horsepower_min": req.horsepower_min,
        "horsepower_max": req.horsepower_max,
        "gearbox": req.gearbox,
        "fuel": req.fuel,
        "city": req.city,
        "radius": req.radius,
        "condition": req.condition,
        "pattern_ids": req.pattern_ids,
        "custom_regex": req.custom_regex,
        "limit": req.limit,  # propagate for early-stop in scraper
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

    # Si des patterns sont sélectionnés, exclure les annonces sans aucun mot-clé trouvé
    if req.pattern_ids:
        upserted = [l for l in upserted if l.matched_keywords]

    # Tri des résultats
    if req.sort_by == 'price_asc':
        upserted.sort(key=lambda l: l.price or 0)
    elif req.sort_by == 'price_desc':
        upserted.sort(key=lambda l: l.price or 0, reverse=True)
    elif req.sort_by == 'recent':
        upserted.sort(key=lambda l: l.scraped_at or datetime.min, reverse=True)
    elif req.sort_by == 'oldest':
        upserted.sort(key=lambda l: l.scraped_at or datetime.max)
    # 'pertinence' = order du scraper, pas de tri

    # Appliquer la limite demandée par le client
    upserted = upserted[:req.limit]

    session = SearchSession(
        filters={k: v for k, v in req.model_dump().items() if k != "pattern_ids"},
        patterns=[p.name for p in patterns],
        result_count=len(upserted),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Save search history (best-effort, don't fail the request)
    try:
        history_entry = SearchHistory(
            user_id=1,
            params={
                **{k: v for k, v in req.__dict__.items() if v is not None and k != "limit"},
                "listing_ids": [l.id for l in upserted],
            },
            result_count=len(upserted),
        )
        db.add(history_entry)
        await db.commit()
    except Exception:
        pass  # Ne pas faire échouer la recherche pour ca

    return SearchResult(session_id=session.id, count=len(upserted), limit=req.limit, listings=upserted)


async def _call_scraper(payload: dict) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=SCRAPER_TIMEOUT) as client:
            resp = await client.post(f"{SCRAPER_URL}/scrape", json=payload)
            if resp.status_code == 422:
                detail = resp.json().get("detail", "Erreur de validation scraper")
                raise HTTPException(status_code=422, detail=detail)
            resp.raise_for_status()
            data = resp.json()
            # Scraper returns {"listings": [...], "count": N}
            return data.get("listings", data) if isinstance(data, dict) else data
    except HTTPException:
        raise
    except httpx.TimeoutException:
        logger.error("Scraper timed out after %ss", SCRAPER_TIMEOUT)
        raise HTTPException(status_code=503, detail="Le scraper ne répond pas (timeout). Réessaie dans quelques secondes.")
    except httpx.HTTPStatusError as exc:
        logger.error("Scraper returned error: %s", exc)
        raise HTTPException(status_code=503, detail=f"Erreur scraper: {exc.response.status_code}")
    except Exception as exc:
        logger.error("Scraper call failed: %s", exc)
        raise HTTPException(status_code=503, detail="Scraper inaccessible.")


async def _resolve_vehicle(brand: str, model: str, db: AsyncSession) -> Optional[Vehicle]:
    """DB-only lookup avec fallback fuzzy (case-insensitive LIKE).
    LBC retourne model='clio', DB stocke 'Renault Clio 1/2/3/4/5' → match partiel.
    """
    if not brand or not model:
        return None
    # 1. Match exact avec score (priorité absolue)
    result = await db.execute(
        select(Vehicle)
        .where(Vehicle.brand == brand, Vehicle.model == model, Vehicle.reliability_score.isnot(None))
        .limit(1)
    )
    vehicle = result.scalar_one_or_none()
    if vehicle:
        return vehicle
    # 2. Fuzzy: brand exact (case-insensitive) + model LIKE '%model%' avec score
    escaped_model = model.lower().replace('%', r'\%').replace('_', r'\_')
    result = await db.execute(
        select(Vehicle)
        .where(
            func.lower(Vehicle.brand) == brand.lower(),
            func.lower(Vehicle.model).like(f"%{escaped_model}%"),
            Vehicle.reliability_score.isnot(None),
        )
        .order_by(func.length(Vehicle.model))  # préférer le modèle le plus court
        .limit(1)
    )
    vehicle = result.scalar_one_or_none()
    if vehicle:
        return vehicle
    # 3. Fallback sans filtre score (pour conserver le lien vehicle même sans score)
    result = await db.execute(
        select(Vehicle).where(Vehicle.brand == brand, Vehicle.model == model).limit(1)
    )
    return result.scalar_one_or_none()


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
            fuel_type=raw.get("fuel_type"),
            doors=raw.get("doors"),
            seats=raw.get("seats"),
            color=raw.get("color"),
            location=raw.get("location"),
            description=raw.get("description"),
            url=raw.get("url"),
            matched_keywords=raw.get("matched_keywords", []),
            images=raw.get("images", []),
            vehicle_id=vehicle_id,
        )
        .on_duplicate_key_update(
            title=raw.get("title"),
            price=raw.get("price"),
            mileage=raw.get("mileage"),
            fuel_type=raw.get("fuel_type"),
            doors=raw.get("doors"),
            seats=raw.get("seats"),
            color=raw.get("color"),
            location=raw.get("location"),
            matched_keywords=raw.get("matched_keywords", []),
            images=raw.get("images", []),
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
