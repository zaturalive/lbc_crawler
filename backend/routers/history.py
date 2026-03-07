from fastapi import APIRouter, Depends
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models import SearchHistory, ViewedListing
from schemas import SearchHistoryOut, ViewedListingOut

router = APIRouter(prefix="/history", tags=["history"])

USER_ID = 1


@router.get("/searches", response_model=list[SearchHistoryOut])
async def get_search_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SearchHistory)
        .where(SearchHistory.user_id == USER_ID)
        .order_by(SearchHistory.created_at.desc())
        .limit(20)
    )
    return result.scalars().all()


@router.post("/searches", response_model=SearchHistoryOut)
async def add_search_history(payload: dict, db: AsyncSession = Depends(get_db)):
    entry = SearchHistory(
        user_id=USER_ID,
        params=payload.get("params", {}),
        result_count=payload.get("result_count", 0),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.get("/listings", response_model=list[ViewedListingOut])
async def get_viewed_listings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ViewedListing)
        .where(ViewedListing.user_id == USER_ID)
        .order_by(ViewedListing.viewed_at.desc())
        .limit(20)
    )
    return result.scalars().all()


@router.post("/listings/{listing_id}", response_model=ViewedListingOut)
async def mark_listing_viewed(listing_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ViewedListing)
        .where(ViewedListing.user_id == USER_ID)
        .where(ViewedListing.listing_id == listing_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.viewed_at = func.now()
        await db.commit()
        await db.refresh(existing)
        return existing

    entry = ViewedListing(user_id=USER_ID, listing_id=listing_id)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/searches")
async def clear_search_history(db: AsyncSession = Depends(get_db)):
    await db.execute(delete(SearchHistory).where(SearchHistory.user_id == USER_ID))
    await db.commit()
    return {"ok": True}


@router.delete("/listings")
async def clear_viewed_listings(db: AsyncSession = Depends(get_db)):
    await db.execute(delete(ViewedListing).where(ViewedListing.user_id == USER_ID))
    await db.commit()
    return {"ok": True}
