"""
Service de gestion des crédits utilisateur.

Règles :
- 3 recherches GRATUITES par jour (reset minuit UTC)
- 300 résultats/jour maximum (anti-abus)
- Au-delà : search_credits obligatoires
- Analyses IA : toujours payantes (analysis_credits)
"""
from datetime import date, timezone, datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import UserCredits

DAILY_FREE_SEARCHES = 3
DAILY_RESULTS_LIMIT = 300


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
    """Remet à zéro les compteurs quotidiens si le jour a changé (UTC)."""
    today = datetime.now(timezone.utc).date()
    if credits.daily_reset_date is None or credits.daily_reset_date < today:
        credits.daily_searches_used = 0
        credits.daily_results_used = 0
        credits.daily_reset_date = today
        await db.commit()
        await db.refresh(credits)
    return credits


async def check_search_available(user_id: int, db: AsyncSession) -> dict:
    """
    Vérifie si une recherche est disponible pour l'utilisateur.
    Retourne : {ok, is_free, free_remaining, paid_balance, results_remaining}
    """
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
    credits = await get_or_create_user_credits(user_id, db)
    if credits.analysis_credits > 0:
        return {"ok": True, "balance": credits.analysis_credits}
    return {"ok": False, "balance": 0}


async def consume_analysis_credit(user_id: int, db: AsyncSession) -> None:
    """Déduit 1 crédit d'analyse. À appeler après une analyse réussie."""
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
        "resets_at": str(today),
    }
