from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models import Listing, RequeteIA, ReponseIA
from schemas import RequeteIAOut
from services.ai_service import build_prompt, call_github_models, GITHUB_MODEL

router = APIRouter(prefix="/listings", tags=["analysis"])


@router.post("/{listing_id}/analyze", response_model=RequeteIAOut)
async def analyze(listing_id: int, db: AsyncSession = Depends(get_db)):
    # Check if analysis already cached (requete with status=done)
    result = await db.execute(
        select(RequeteIA)
        .where(RequeteIA.listing_id == listing_id)
        .where(RequeteIA.status == "done")
    )
    cached = result.scalar_one_or_none()
    if cached:
        out = RequeteIAOut.model_validate(cached)
        out.is_premium = False
        if cached.reponse:
            out.reponse.is_premium = False
        return out

    # Fetch listing
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if not listing.description:
        raise HTTPException(status_code=422, detail="Cette annonce n'a pas de description à analyser.")

    prompt_text = build_prompt(
        title=listing.title,
        description=listing.description,
        mileage=listing.mileage,
        year=listing.year,
        price=listing.price,
    )

    # Create requete record (pending)
    requete = RequeteIA(
        listing_id=listing_id,
        prompt_text=prompt_text,
        model=GITHUB_MODEL,
        status="pending",
    )
    db.add(requete)
    await db.commit()
    await db.refresh(requete)

    # Call GitHub Models API
    try:
        analysis_data = await call_github_models(prompt_text)
    except ValueError as e:
        requete.status = "error"
        await db.commit()
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        requete.status = "error"
        await db.commit()
        raise HTTPException(status_code=503, detail=f"Analyse IA indisponible: {e}")

    # Save response
    reponse = ReponseIA(
        requete_id=requete.id,
        repairs_found=analysis_data.get("repairs_found", []),
        upcoming_maintenance=analysis_data.get("upcoming_maintenance", []),
        condition_summary=analysis_data.get("condition_summary"),
        risk_level=analysis_data.get("risk_level", "medium"),
        raw_response=analysis_data.get("raw_response"),
    )
    db.add(reponse)
    requete.status = "done"
    await db.commit()
    await db.refresh(requete)

    out = RequeteIAOut.model_validate(requete)
    out.is_premium = False
    if out.reponse:
        out.reponse.is_premium = False
    return out
