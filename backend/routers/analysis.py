from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models import Listing, ListingAnalysis
from schemas import ListingAnalysisResponse
from services.ai_service import analyze_listing

router = APIRouter(prefix="/listings", tags=["analysis"])


@router.post("/{listing_id}/analyze", response_model=ListingAnalysisResponse)
async def analyze(listing_id: int, db: AsyncSession = Depends(get_db)):
    # Check if analysis already cached
    result = await db.execute(
        select(ListingAnalysis).where(ListingAnalysis.listing_id == listing_id)
    )
    cached = result.scalar_one_or_none()
    if cached:
        cached_resp = ListingAnalysisResponse.model_validate(cached)
        cached_resp.is_premium = False
        return cached_resp

    # Fetch listing
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if not listing.description:
        raise HTTPException(status_code=422, detail="Cette annonce n'a pas de description à analyser.")

    try:
        analysis_data = await analyze_listing(
            title=listing.title,
            description=listing.description,
            mileage=listing.mileage,
            year=listing.year,
            price=listing.price,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Analyse IA indisponible: {e}")

    # Persist
    analysis = ListingAnalysis(
        listing_id=listing_id,
        model_used=analysis_data.get("model_used"),
        repairs_found=analysis_data.get("repairs_found", []),
        upcoming_maintenance=analysis_data.get("upcoming_maintenance", []),
        condition_summary=analysis_data.get("condition_summary"),
        risk_level=analysis_data.get("risk_level", "medium"),
        raw_response=analysis_data.get("raw_response"),
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    resp = ListingAnalysisResponse.model_validate(analysis)
    resp.is_premium = False
    return resp
