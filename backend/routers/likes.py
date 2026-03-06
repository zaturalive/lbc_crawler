from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.dialects.mysql import insert

from db.database import get_db
from models import Like, Listing
from schemas import LikeResponse

router = APIRouter()

USER_ID = 1  # Pour l'instant un seul utilisateur


@router.post("/listings/{listing_id}/like", response_model=LikeResponse, status_code=201)
async def like_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Listing not found")

    stmt = (
        insert(Like)
        .values(user_id=USER_ID, listing_id=listing_id)
        .prefix_with("IGNORE")
    )
    await db.execute(stmt)
    await db.commit()

    result = await db.execute(
        select(Like).where(Like.user_id == USER_ID, Like.listing_id == listing_id)
    )
    like = result.scalar_one()
    return like


@router.delete("/listings/{listing_id}/like", status_code=204)
async def unlike_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(
        delete(Like).where(Like.user_id == USER_ID, Like.listing_id == listing_id)
    )
    await db.commit()


@router.get("/likes", response_model=list[int])
async def get_liked_listing_ids(db: AsyncSession = Depends(get_db)):
    """Retourne la liste des listing_id likes par l'utilisateur courant."""
    result = await db.execute(
        select(Like.listing_id).where(Like.user_id == USER_ID)
    )
    return list(result.scalars().all())
