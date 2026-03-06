import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models import Listing, SearchSession
from schemas import ListingResponse

router = APIRouter()


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
    return [ListingResponse.model_validate(l) for l in result.scalars().all()]
