import logging
import os

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, text
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.security import decode_token
from db.database import get_db
from models import Vehicle, RequeteIA

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

SCRAPER_URL = os.getenv("SCRAPER_URL", "http://scraper:8001")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "1"))
_raw_admin_ids = os.getenv("ADMIN_USER_IDS", str(ADMIN_USER_ID))
ADMIN_USER_IDS: set[int] = {int(x.strip()) for x in _raw_admin_ids.split(",") if x.strip().isdigit()}

_bearer_scheme = HTTPBearer(auto_error=False)


def _require_admin(credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme)) -> int:
    """Vérifie que le token est valide et appartient à un admin."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requis pour accéder à l'administration.")
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré.")
    user_id = payload.get("user_id") or payload.get("sub")
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=403, detail="Accès refusé.")
    if user_id not in ADMIN_USER_IDS:
        raise HTTPException(status_code=403, detail="Accès réservé à l'administrateur.")
    return user_id


@router.get("/ai-analyses")
async def admin_ai_analyses(
    _admin: int = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: list all AI analyses with associated listing info."""
    result = await db.execute(
        select(RequeteIA)
        .options(selectinload(RequeteIA.reponse))
        .order_by(RequeteIA.created_at.desc())
        .limit(200)
    )
    rows = result.scalars().all()

    analyses = []
    for r in rows:
        analyses.append({
            "id": r.id,
            "listing_id": r.listing_id,
            "user_id": r.user_id,
            "model": r.model,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "risk_level": r.reponse.risk_level if r.reponse else None,
            "condition_summary": r.reponse.condition_summary if r.reponse else None,
        })

    done = sum(1 for a in analyses if a["status"] == "done")
    errors = sum(1 for a in analyses if a["status"] == "error")
    pending = sum(1 for a in analyses if a["status"] == "pending")

    return {
        "total": len(analyses),
        "done": done,
        "errors": errors,
        "pending": pending,
        "analyses": analyses,
    }


@router.post("/sync-vehicles")
async def sync_vehicles(
    background_tasks: BackgroundTasks,
    _admin: int = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger a full fiches-auto.fr scrape and store all vehicles in DB.
    Runs in background — poll /admin/sync-status for progress.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{SCRAPER_URL}/scrape/vehicles-catalog")
            resp.raise_for_status()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Could not reach scraper: {exc}")

    background_tasks.add_task(_poll_and_store, db)
    return {"status": "started", "message": "Scraping in progress. Poll /admin/sync-status."}


@router.get("/sync-status")
async def sync_status(_admin: int = Depends(_require_admin)):
    """Check fiches-auto sync status from scraper."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{SCRAPER_URL}/scrape/vehicles-status")
            return resp.json()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/sync-vehicles/store")
async def store_vehicles(
    _admin: int = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch completed vehicle catalog from scraper and store in DB.
    Call this after /sync-status returns status=done.
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{SCRAPER_URL}/scrape/vehicles-status")
            data = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if data.get("status") != "done":
        raise HTTPException(status_code=409, detail=f"Scraper not ready: {data.get('status')}")

    vehicles = data.get("vehicles", [])
    inserted = 0

    for v in vehicles:
        stmt = (
            insert(Vehicle)
            .values(
                brand=v["brand"],
                model=v["model"],
                year_start=v.get("year_start"),
                year_end=v.get("year_end"),
                reliability_score=v.get("reliability_score"),
                total_testimonials=v.get("total_testimonials", 0),
                common_issues=v.get("common_issues", []),
                known_issues_text=v.get("known_issues_text", []),
                source_url=v.get("source_url"),
                reliability_rank=v.get("reliability_rank"),
            )
            .on_duplicate_key_update(
                reliability_score=v.get("reliability_score"),
                total_testimonials=v.get("total_testimonials", 0),
                common_issues=v.get("common_issues", []),
                known_issues_text=v.get("known_issues_text", []),
                source_url=v.get("source_url"),
                year_start=v.get("year_start"),
                year_end=v.get("year_end"),
                reliability_rank=v.get("reliability_rank"),
            )
        )
        await db.execute(stmt)
        inserted += 1

    await db.commit()
    logger.info("Stored %d vehicles in DB", inserted)
    return {"status": "ok", "stored": inserted}


async def _poll_and_store(db: AsyncSession):
    """Background task: wait for scraper to finish, then store results."""
    import asyncio
    for _ in range(600):  # max 10 min
        await asyncio.sleep(3)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{SCRAPER_URL}/scrape/vehicles-status")
                data = resp.json()
            if data.get("status") == "done":
                vehicles = data.get("vehicles", [])
                for v in vehicles:
                    stmt = (
                        insert(Vehicle)
                        .values(
                            brand=v["brand"],
                            model=v["model"],
                            year_start=v.get("year_start"),
                            year_end=v.get("year_end"),
                            reliability_score=v.get("reliability_score"),
                            total_testimonials=v.get("total_testimonials", 0),
                            common_issues=v.get("common_issues", []),
                            known_issues_text=v.get("known_issues_text", []),
                            source_url=v.get("source_url"),
                            reliability_rank=v.get("reliability_rank"),
                        )
                        .on_duplicate_key_update(
                            reliability_score=v.get("reliability_score"),
                            total_testimonials=v.get("total_testimonials", 0),
                            common_issues=v.get("common_issues", []),
                            known_issues_text=v.get("known_issues_text", []),
                            source_url=v.get("source_url"),
                            reliability_rank=v.get("reliability_rank"),
                        )
                    )
                    await db.execute(stmt)
                await db.commit()
                logger.info("Auto-stored %d vehicles", len(vehicles))
                return
            if data.get("status") == "error":
                logger.error("Scraper sync error: %s", data.get("error"))
                return
        except Exception as exc:
            logger.warning("Poll failed: %s", exc)
