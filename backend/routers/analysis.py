from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models import Listing, RequeteIA, ReponseIA, AnalyseRecherche, ReponseRechercheIA, SearchHistory
from schemas import RequeteIAOut, AnalyseRechercheOut
from services.ai_service import (
    build_prompt, call_github_models, GITHUB_MODEL,
    build_search_prompt, call_github_models_search,
    scan_immat_vision,
)

router = APIRouter(tags=["analysis"])


# --- Analyse d'une recherche complete -------------------------------------------

@router.post("/search/{search_id}/analyze", response_model=AnalyseRechercheOut)
async def analyze_search(search_id: int, db: AsyncSession = Depends(get_db)):
    # Cache check
    result = await db.execute(
        select(AnalyseRecherche)
        .where(AnalyseRecherche.search_id == search_id)
        .where(AnalyseRecherche.status == "done")
    )
    cached = result.scalar_one_or_none()
    if cached:
        return AnalyseRechercheOut.model_validate(cached)

    # Fetch search history
    result = await db.execute(select(SearchHistory).where(SearchHistory.id == search_id))
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=404, detail="Search history not found")

    # Fetch listings from this search (stored as listing_ids in params)
    listing_ids = (search.params or {}).get("listing_ids", [])
    if not listing_ids:
        raise HTTPException(status_code=422, detail="Aucune annonce associee a cette recherche.")

    result = await db.execute(
        select(Listing).where(Listing.id.in_(listing_ids))
    )
    listings = list(result.scalars().all())
    if not listings:
        raise HTTPException(status_code=422, detail="Les annonces de cette recherche ne sont plus disponibles.")

    brand = (search.params or {}).get("brand", "")
    model_name = (search.params or {}).get("model", "")

    listings_data = [
        {
            "title": l.title,
            "year": l.year,
            "mileage": l.mileage,
            "price": l.price,
            "description": l.description,
        }
        for l in listings
    ]
    prompt_text = build_search_prompt(listings_data, brand=brand, model_name=model_name)

    # Create analyse record (pending)
    analyse = AnalyseRecherche(
        search_id=search_id,
        listing_ids=listing_ids,
        prompt_text=prompt_text,
        model=GITHUB_MODEL,
        status="pending",
    )
    db.add(analyse)
    await db.commit()
    await db.refresh(analyse)

    # Call LLM
    try:
        data = await call_github_models_search(prompt_text)
    except ValueError as e:
        analyse.status = "error"
        await db.commit()
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        analyse.status = "error"
        await db.commit()
        raise HTTPException(status_code=503, detail=f"Analyse IA indisponible: {e}")

    # Save response
    reponse = ReponseRechercheIA(
        analyse_id=analyse.id,
        synthese_globale=data.get("synthese_globale"),
        themes_mentionnes=data.get("themes_mentionnes", []),
        themes_absents=data.get("themes_absents", []),
        prochaines_reparations=data.get("prochaines_reparations", []),
        risk_level=data.get("risk_level", "medium"),
        raw_response=data.get("raw_response"),
    )
    db.add(reponse)
    analyse.status = "done"
    await db.commit()
    await db.refresh(analyse)

    return AnalyseRechercheOut.model_validate(analyse)


@router.get("/search/{search_id}/analyze", response_model=AnalyseRechercheOut)
async def get_search_analysis(search_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AnalyseRecherche)
        .where(AnalyseRecherche.search_id == search_id)
    )
    analyse = result.scalar_one_or_none()
    if not analyse:
        raise HTTPException(status_code=404, detail="Aucune analyse pour cette recherche.")
    return AnalyseRechercheOut.model_validate(analyse)


# --- Scan immatriculation par annonce -------------------------------------------

@router.post("/listings/{listing_id}/scan-immat")
async def scan_immat(listing_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    images = listing.images or []
    if not images:
        raise HTTPException(status_code=422, detail="Aucune image disponible pour cette annonce.")

    for img_url in images[:3]:
        plate = await scan_immat_vision(img_url)
        if plate:
            return {"immat": plate, "image_url": img_url}

    return {"immat": None, "image_url": None}


# --- Analyse d'une annonce individuelle (ancien endpoint, conserve) -------------

@router.post("/listings/{listing_id}/analyze", response_model=RequeteIAOut)
async def analyze_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RequeteIA)
        .where(RequeteIA.listing_id == listing_id)
        .where(RequeteIA.status == "done")
    )
    cached = result.scalar_one_or_none()
    if cached:
        out = RequeteIAOut.model_validate(cached)
        out.is_premium = False
        return out

    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if not listing.description:
        raise HTTPException(status_code=422, detail="Cette annonce n'a pas de description a analyser.")

    prompt_text = build_prompt(
        title=listing.title,
        description=listing.description,
        mileage=listing.mileage,
        year=listing.year,
        price=listing.price,
    )

    requete = RequeteIA(
        listing_id=listing_id,
        prompt_text=prompt_text,
        model=GITHUB_MODEL,
        status="pending",
    )
    db.add(requete)
    await db.commit()
    await db.refresh(requete)

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
    return out
