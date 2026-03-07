from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from core.security import decode_token
from db.database import get_db
from models import Listing, ListingAnalysisUser, RequeteIA, ReponseIA, AnalyseRecherche, ReponseRechercheIA, SearchHistory, Vehicle
from schemas import RequeteIAOut, AnalyseRechercheOut
from services.ai_service import (
    build_prompt, call_github_models, GITHUB_MODEL,
    build_search_prompt, call_github_models_search,
    scan_immat_vision,
)

router = APIRouter(tags=["analysis"])

_bearer_scheme = HTTPBearer(auto_error=False)

QUOTA_LISTING_MAX = 10
QUOTA_SEARCH_MAX = 3


def _extract_user_id(credentials) -> int:
    """Extract user_id from optional Bearer token. Falls back to 1 if absent or invalid."""
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


# --- Bulk cache fetch — retourne uniquement les analyses déjà payées par cet user -----

@router.get("/ai/analyses")
async def get_cached_analyses(
    listing_ids: str = Query(..., description="Comma-separated listing IDs, e.g. 1,2,3"),
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Return analyses already paid for by this user (in listing_analysis_users)."""
    try:
        ids = [int(i.strip()) for i in listing_ids.split(",") if i.strip().isdigit()]
    except ValueError:
        raise HTTPException(status_code=422, detail="listing_ids must be comma-separated integers")

    if not ids:
        return {}

    current_user_id = _extract_user_id(credentials)

    # Trouver quels listing_ids cet user a déjà "payés"
    owned_result = await db.execute(
        select(ListingAnalysisUser.listing_id)
        .where(ListingAnalysisUser.user_id == current_user_id)
        .where(ListingAnalysisUser.listing_id.in_(ids))
    )
    owned_ids = {row[0] for row in owned_result.fetchall()}

    if not owned_ids:
        return {}

    # Récupérer les analyses correspondantes
    result = await db.execute(
        select(RequeteIA)
        .options(selectinload(RequeteIA.reponse))
        .where(RequeteIA.listing_id.in_(owned_ids))
        .where(RequeteIA.status == "done")
    )
    rows = result.scalars().all()

    out = {}
    for row in rows:
        if row.listing_id not in out:
            o = RequeteIAOut.model_validate(row)
            o.cached = True
            out[row.listing_id] = o.model_dump()
    return out


# --- Endpoint quota utilisateur -----------------------------------------------

@router.get("/ai/quota")
async def get_quota(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user_id = _extract_user_id(credentials)

    # Quota listing = nombre d'entrées dans listing_analysis_users pour cet user
    listing_count_result = await db.execute(
        select(func.count()).select_from(ListingAnalysisUser)
        .where(ListingAnalysisUser.user_id == current_user_id)
    )
    listing_used = listing_count_result.scalar() or 0

    search_count_result = await db.execute(
        select(func.count()).select_from(AnalyseRecherche)
        .where(AnalyseRecherche.user_id == current_user_id)
    )
    search_used = search_count_result.scalar() or 0

    return {
        "listing_analyses_used": listing_used,
        "listing_analyses_max": QUOTA_LISTING_MAX,
        "search_analyses_used": search_used,
        "search_analyses_max": QUOTA_SEARCH_MAX,
    }

@router.post("/search/{search_id}/analyze", response_model=AnalyseRechercheOut)
async def analyze_search(
    search_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user_id = _extract_user_id(credentials)

    # Quota check
    quota_result = await db.execute(
        select(func.count()).select_from(AnalyseRecherche)
        .where(AnalyseRecherche.user_id == current_user_id)
    )
    quota_used = quota_result.scalar() or 0
    if quota_used >= QUOTA_SEARCH_MAX:
        raise HTTPException(
            status_code=429,
            detail="Quota atteint : 3 analyses globales maximum.",
        )

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

    # Fetch listings from this search (stored as listing_ids in params), limited to 50
    listing_ids = search.listing_ids or []
    if not listing_ids:
        raise HTTPException(status_code=422, detail="Aucune annonce associee a cette recherche.")
    listing_ids = listing_ids[:50]

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
        user_id=current_user_id,
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


# --- Analyse d'une annonce individuelle -----------------------------------------

@router.post("/listings/{listing_id}/analyze", response_model=RequeteIAOut)
async def analyze_listing(
    listing_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    current_user_id = _extract_user_id(credentials)

    # ÉTAPE 1 — Cet user a-t-il déjà payé pour cette annonce ?
    owned_result = await db.execute(
        select(ListingAnalysisUser)
        .where(ListingAnalysisUser.user_id == current_user_id)
        .where(ListingAnalysisUser.listing_id == listing_id)
    )
    already_owned = owned_result.scalar_one_or_none()
    if already_owned:
        # Gratuit — retourne le cache sans consommer de crédit
        cached_result = await db.execute(
            select(RequeteIA)
            .options(selectinload(RequeteIA.reponse))
            .where(RequeteIA.listing_id == listing_id)
            .where(RequeteIA.status == "done")
        )
        cached = cached_result.scalar_one_or_none()
        if cached and cached.reponse:
            out = RequeteIAOut.model_validate(cached)
            out.is_premium = False
            out.cached = True
            return out

    # ÉTAPE 2 — Vérifier le quota de cet user
    quota_result = await db.execute(
        select(func.count()).select_from(ListingAnalysisUser)
        .where(ListingAnalysisUser.user_id == current_user_id)
    )
    quota_used = quota_result.scalar() or 0
    if quota_used >= QUOTA_LISTING_MAX:
        raise HTTPException(
            status_code=429,
            detail=f"Quota atteint : {QUOTA_LISTING_MAX} analyses maximum. Votre quota sera réinitialisé prochainement.",
        )

    # ÉTAPE 3 — Une analyse globale existe déjà pour ce listing (autre user) ?
    global_cached_result = await db.execute(
        select(RequeteIA)
        .options(selectinload(RequeteIA.reponse))
        .where(RequeteIA.listing_id == listing_id)
        .where(RequeteIA.status == "done")
    )
    global_cached = global_cached_result.scalar_one_or_none()

    if global_cached and global_cached.reponse:
        # Cache global disponible — consomme 1 crédit, ZÉRO appel API
        db.add(ListingAnalysisUser(
            listing_id=listing_id,
            user_id=current_user_id,
            used_cache=True,
        ))
        await db.commit()
        out = RequeteIAOut.model_validate(global_cached)
        out.is_premium = False
        out.cached = True
        return out

    # ÉTAPE 4 — Pas de cache : appel IA réel
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if not listing.description:
        raise HTTPException(status_code=422, detail="Cette annonce n'a pas de description a analyser.")

    # Contexte fiabilité du véhicule
    vehicle = None
    if listing.vehicle_id:
        v_result = await db.execute(select(Vehicle).where(Vehicle.id == listing.vehicle_id))
        vehicle = v_result.scalar_one_or_none()

    known_issues = vehicle.known_issues_text if vehicle else None
    common_issues = vehicle.common_issues if vehicle else None
    vehicle_meta = {
        "brand": vehicle.brand if vehicle else None,
        "model": vehicle.model if vehicle else None,
        "year_start": vehicle.year_start if vehicle else None,
        "year_end": vehicle.year_end if vehicle else None,
        "reliability_score": vehicle.reliability_score if vehicle else None,
        "total_testimonials": vehicle.total_testimonials if vehicle else None,
        "category": vehicle.category if vehicle else None,
    } if vehicle else None

    user_prompt, system_prompt = build_prompt(
        title=listing.title,
        description=listing.description,
        mileage=listing.mileage,
        year=listing.year,
        price=listing.price,
        known_issues=known_issues,
        common_issues=common_issues,
        vehicle_meta=vehicle_meta,
    )

    requete = RequeteIA(
        listing_id=listing_id,
        user_id=current_user_id,
        prompt_text=user_prompt,
        model=GITHUB_MODEL,
        status="pending",
    )
    db.add(requete)
    await db.commit()
    await db.refresh(requete)

    try:
        analysis_data = await call_github_models(user_prompt, system_prompt=system_prompt)
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

    # Enregistrer que cet user a consommé un crédit pour ce listing
    db.add(ListingAnalysisUser(
        listing_id=listing_id,
        user_id=current_user_id,
        used_cache=False,
    ))
    await db.commit()
    await db.refresh(requete)

    out = RequeteIAOut.model_validate(requete)
    out.is_premium = False
    out.cached = False
    return out
