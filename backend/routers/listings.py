import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models import Like, Listing, SearchSession
from schemas import ListingResponse

router = APIRouter()

USER_ID = 1  # Hardcoded until auth is implemented


@router.get("/listings", response_model=list[ListingResponse])
async def get_listings(
    session_id: int,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    result = await db.execute(
        select(Listing)
        .join(SearchSession, SearchSession.id == session_id, isouter=True)
        .order_by(Listing.scraped_at.desc())
        .offset(offset)
        .limit(limit)
    )
    listings = result.scalars().all()

    # Fetch liked listing ids for current user
    liked_result = await db.execute(
        select(Like.listing_id).where(Like.user_id == USER_ID)
    )
    liked_ids = set(liked_result.scalars().all())

    listing_responses = []
    for listing in listings:
        resp = ListingResponse.model_validate(listing)
        resp.is_liked = listing.id in liked_ids
        listing_responses.append(resp)

    return listing_responses
