from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.deps import get_current_user
from db.database import get_db
from models import Like, Listing, SearchSession, User, Vehicle
from schemas import ListingResponse, SearchSessionResponse, VehicleResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/searches", response_model=list[SearchSessionResponse])
async def my_searches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SearchSession)
        .where(SearchSession.user_id == current_user.id)
        .order_by(SearchSession.created_at.desc())
        .limit(20)
    )
    return list(result.scalars().all())


@router.get("/me/likes", response_model=list[ListingResponse])
async def my_likes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Listing)
        .join(Like, Like.listing_id == Listing.id)
        .where(Like.user_id == current_user.id)
        .options(selectinload(Listing.vehicle))
        .order_by(Like.created_at.desc())
    )
    listings = list(result.scalars().all())
    out = []
    for listing in listings:
        resp = ListingResponse.model_validate(listing)
        if listing.vehicle:
            resp.vehicle = VehicleResponse.model_validate(listing.vehicle)
        resp.is_liked = True
        out.append(resp)
    return out
