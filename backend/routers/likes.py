from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import selectinload

from core.security import decode_token
from db.database import get_db
from models import Like, Listing, Vehicle
from schemas import LikeResponse, ListingResponse, VehicleResponse

router = APIRouter()

_bearer_scheme = HTTPBearer(auto_error=False)


def _extract_user_id(credentials) -> int:
    """Extract user_id from Bearer token. Falls back to 1 if absent or invalid."""
    if not credentials:
        return 1
    payload = decode_token(credentials.credentials)
    if payload is None:
        return 1
    sub = payload.get("sub")
    try:
        return int(sub)
    except (TypeError, ValueError):
        return 1


@router.post("/listings/{listing_id}/like", response_model=LikeResponse, status_code=201)
async def like_listing(
    listing_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    user_id = _extract_user_id(credentials)
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Listing not found")

    stmt = (
        insert(Like)
        .values(user_id=user_id, listing_id=listing_id)
        .prefix_with("IGNORE")
    )
    await db.execute(stmt)
    await db.commit()

    result = await db.execute(
        select(Like).where(Like.user_id == user_id, Like.listing_id == listing_id)
    )
    like = result.scalar_one()
    return like


@router.delete("/listings/{listing_id}/like", status_code=204)
async def unlike_listing(
    listing_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    user_id = _extract_user_id(credentials)
    await db.execute(
        delete(Like).where(Like.user_id == user_id, Like.listing_id == listing_id)
    )
    await db.commit()


@router.get("/likes", response_model=list[int])
async def get_liked_listing_ids(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Retourne la liste des listing_id likés par l'utilisateur courant."""
    user_id = _extract_user_id(credentials)
    result = await db.execute(
        select(Like.listing_id).where(Like.user_id == user_id)
    )
    return list(result.scalars().all())


@router.get("/likes/listings", response_model=list[ListingResponse])
async def get_liked_listings_full(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Retourne les annonces likées complètes avec leur vehicle."""
    user_id = _extract_user_id(credentials)
    result = await db.execute(
        select(Listing)
        .join(Like, Like.listing_id == Listing.id)
        .where(Like.user_id == user_id)
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
