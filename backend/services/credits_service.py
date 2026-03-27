"""
Service de gestion des crédits utilisateur.

Règles :
- 3 recherches GRATUITES par jour (reset minuit UTC)
- 300 résultats/jour maximum (anti-abus)
- Au-delà : search_credits obligatoires
- Analyses IA : DAILY_AI_REQUESTS_MAX requêtes/jour (configurable via env), puis analysis_credits payants
"""
import os
from datetime import date, timezone, datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import UserCredits

DAILY_FREE_SEARCHES = 3
DAILY_RESULTS_LIMIT = 300
DAILY_AI_REQUESTS_MAX = int(os.getenv("DAILY_AI_REQUESTS_MAX", "5"))

# Top-up journalier
DAILY_AI_CREDITS_CAP    = int(os.getenv("DAILY_AI_CREDITS_CAP", "10"))   # seuil/plafond IA
DAILY_SEARCH_TOPUP      = int(os.getenv("DAILY_SEARCH_TOPUP", "3"))       # crédits recherche ajoutés/jour
DAILY_SEARCH_CREDITS_CAP = int(os.getenv("DAILY_SEARCH_CREDITS_CAP", "5")) # plafond crédits recherche

_raw_admin_ids = os.getenv("ADMIN_USER_IDS", "1")
ADMIN_USER_IDS: set[int] = {int(x.strip()) for x in _raw_admin_ids.split(",") if x.strip().isdigit()}


async def get_or_create_user_credits(user_id: int, db: AsyncSession) -> UserCredits:
    """Récupère ou crée le solde de crédits pour un utilisateur."""
    result = await db.execute(
        select(UserCredits).where(UserCredits.user_id == user_id)
    )
    credits = result.scalar_one_or_none()
    if credits is None:
        credits = UserCredits(user_id=user_id)
        db.add(credits)
        await db.commit()
        await db.refresh(credits)
    return credits


async def _reset_daily_if_needed(credits: UserCredits, db: AsyncSession) -> UserCredits:
    """Remet à zéro les compteurs quotidiens si le jour a changé (UTC).
    Applique aussi le top-up journalier :
    - Crédits IA  : complétés à DAILY_AI_CREDITS_CAP si en dessous (jamais réduits)
    - Crédits recherche : +DAILY_SEARCH_TOPUP par jour, plafonné à DAILY_SEARCH_CREDITS_CAP
    """
    today = datetime.now(timezone.utc).date()
    if credits.daily_reset_date is None or credits.daily_reset_date < today:
        credits.daily_searches_used = 0
        credits.daily_results_used = 0
        credits.daily_ai_requests_used = 0
        credits.daily_reset_date = today
        # Top-up IA : on amène à 10 ceux qui sont en dessous, on ne touche pas ceux au-dessus
        credits.analysis_credits = max(credits.analysis_credits, DAILY_AI_CREDITS_CAP)
        # Top-up recherche : +3/jour plafonné à 5
        credits.search_credits = min(credits.search_credits + DAILY_SEARCH_TOPUP, DAILY_SEARCH_CREDITS_CAP)
        await db.commit()
        await db.refresh(credits)
    return credits


async def check_search_available(user_id: int, db: AsyncSession) -> dict:
    """
    Vérifie si une recherche est disponible pour l'utilisateur.
    Retourne : {ok, is_free, free_remaining, paid_balance, results_remaining}
    """
    # Les admins ont un accès illimité
    if user_id in ADMIN_USER_IDS:
        return {
            "ok": True,
            "is_free": True,
            "free_remaining": 999,
            "paid_balance": 9999,
            "results_remaining": 9999,
        }

    credits = await get_or_create_user_credits(user_id, db)
    credits = await _reset_daily_if_needed(credits, db)

    free_remaining = max(0, DAILY_FREE_SEARCHES - credits.daily_searches_used)
    results_remaining = max(0, DAILY_RESULTS_LIMIT - credits.daily_results_used)

    if results_remaining == 0:
        return {
            "ok": False,
            "reason": "daily_results_limit",
            "free_remaining": free_remaining,
            "paid_balance": credits.search_credits,
            "results_remaining": 0,
        }

    if free_remaining > 0:
        return {
            "ok": True,
            "is_free": True,
            "free_remaining": free_remaining,
            "paid_balance": credits.search_credits,
            "results_remaining": results_remaining,
        }

    if credits.search_credits > 0:
        return {
            "ok": True,
            "is_free": False,
            "free_remaining": 0,
            "paid_balance": credits.search_credits,
            "results_remaining": results_remaining,
        }

    return {
        "ok": False,
        "reason": "no_search_credits",
        "free_remaining": 0,
        "paid_balance": 0,
        "results_remaining": results_remaining,
    }


async def consume_search_credit(user_id: int, result_count: int, db: AsyncSession) -> None:
    """
    Consomme 1 crédit de recherche ou incrémente le compteur quotidien.
    Doit être appelé après une recherche réussie.
    """
    # Les admins ne consomment pas de crédits
    if user_id in ADMIN_USER_IDS:
        return

    credits = await get_or_create_user_credits(user_id, db)
    credits = await _reset_daily_if_needed(credits, db)

    free_remaining = max(0, DAILY_FREE_SEARCHES - credits.daily_searches_used)

    if free_remaining > 0:
        credits.daily_searches_used += 1
    else:
        credits.search_credits = max(0, credits.search_credits - 1)

    credits.daily_results_used = min(
        DAILY_RESULTS_LIMIT,
        credits.daily_results_used + result_count,
    )
    await db.commit()


async def check_analysis_available(user_id: int, db: AsyncSession) -> dict:
    """
    Vérifie si l'utilisateur peut lancer une analyse IA.
    Retourne : {ok, balance}
    """
    if user_id in ADMIN_USER_IDS:
        return {"ok": True, "balance": 9999}
    credits = await get_or_create_user_credits(user_id, db)
    if credits.analysis_credits > 0:
        return {"ok": True, "balance": credits.analysis_credits}
    return {"ok": False, "balance": 0}


async def check_daily_ai_quota(user_id: int, db: AsyncSession) -> dict:
    """
    Vérifie si l'utilisateur n'a pas atteint son quota journalier de requêtes IA.
    Retourne : {ok, used, max, remaining}
    """
    if user_id in ADMIN_USER_IDS:
        return {"ok": True, "used": 0, "max": 9999, "remaining": 9999}
    credits = await get_or_create_user_credits(user_id, db)
    credits = await _reset_daily_if_needed(credits, db)
    remaining = max(0, DAILY_AI_REQUESTS_MAX - credits.daily_ai_requests_used)
    return {
        "ok": remaining > 0,
        "used": credits.daily_ai_requests_used,
        "max": DAILY_AI_REQUESTS_MAX,
        "remaining": remaining,
    }


async def consume_daily_ai_request(user_id: int, db: AsyncSession) -> None:
    """Incrémente le compteur journalier de requêtes IA. À appeler après une analyse consommée."""
    if user_id in ADMIN_USER_IDS:
        return
    credits = await get_or_create_user_credits(user_id, db)
    credits.daily_ai_requests_used = credits.daily_ai_requests_used + 1
    await db.commit()


async def consume_analysis_credit(user_id: int, db: AsyncSession) -> None:
    """Déduit 1 crédit d'analyse. À appeler après une analyse réussie."""
    if user_id in ADMIN_USER_IDS:
        return
    credits = await get_or_create_user_credits(user_id, db)
    credits.analysis_credits = max(0, credits.analysis_credits - 1)
    await db.commit()


async def add_credits(
    user_id: int,
    pack_type: str,
    amount: int,
    db: AsyncSession,
) -> UserCredits:
    """Ajoute des crédits au solde d'un utilisateur (appelé par le webhook Stripe)."""
    credits = await get_or_create_user_credits(user_id, db)
    if pack_type == "search":
        credits.search_credits += amount
    elif pack_type == "analysis":
        credits.analysis_credits += amount
    await db.commit()
    await db.refresh(credits)
    return credits


async def get_credits_summary(user_id: int, db: AsyncSession) -> dict:
    """Retourne un résumé du solde crédits pour l'API."""
    from datetime import timezone
    credits = await get_or_create_user_credits(user_id, db)
    credits = await _reset_daily_if_needed(credits, db)
    today = datetime.now(timezone.utc).date()

    return {
        "search_credits": credits.search_credits,
        "analysis_credits": credits.analysis_credits,
        "daily_searches_used": credits.daily_searches_used,
        "daily_searches_free": DAILY_FREE_SEARCHES,
        "daily_searches_free_remaining": max(0, DAILY_FREE_SEARCHES - credits.daily_searches_used),
        "daily_results_used": credits.daily_results_used,
        "daily_results_limit": DAILY_RESULTS_LIMIT,
        "daily_results_remaining": max(0, DAILY_RESULTS_LIMIT - credits.daily_results_used),
        "daily_ai_requests_used": credits.daily_ai_requests_used,
        "daily_ai_requests_max": DAILY_AI_REQUESTS_MAX,
        "daily_ai_requests_remaining": max(0, DAILY_AI_REQUESTS_MAX - credits.daily_ai_requests_used),
        "daily_ai_credits_cap": DAILY_AI_CREDITS_CAP,
        "daily_search_topup": DAILY_SEARCH_TOPUP,
        "daily_search_credits_cap": DAILY_SEARCH_CREDITS_CAP,
        "resets_at": str(today),
    }
