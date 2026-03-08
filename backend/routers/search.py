from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import decode_token
from db.database import get_db
from schemas import SearchRequest, SearchResult
from services.search_service import run_search
from services.credits_service import check_search_available, consume_search_credit

router = APIRouter()
_bearer = HTTPBearer(auto_error=False)

ANONYMOUS_USER_ID = 1  # fallback pour utilisateurs non connectés


def _get_user_id(credentials: HTTPAuthorizationCredentials | None) -> int:
    if not credentials:
        return ANONYMOUS_USER_ID
    payload = decode_token(credentials.credentials)
    if payload is None:
        return ANONYMOUS_USER_ID
    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        return ANONYMOUS_USER_ID


@router.post("/search", response_model=SearchResult)
async def search(
    req: SearchRequest,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = _get_user_id(credentials)

    # Vérifier disponibilité de la recherche
    availability = await check_search_available(user_id, db)
    if not availability["ok"]:
        reason = availability.get("reason", "")
        if reason == "daily_results_limit":
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "daily_results_limit",
                    "message": "Limite journalière de 300 résultats atteinte. Revenez demain.",
                },
            )
        raise HTTPException(
            status_code=402,
            detail={
                "code": "no_search_credits",
                "message": "3 recherches gratuites épuisées. Achetez des crédits de recherche.",
                "free_remaining": 0,
                "paid_balance": availability.get("paid_balance", 0),
            },
        )

    result = await run_search(req, db)

    # Consommer le crédit après la recherche réussie
    await consume_search_credit(user_id, result.count, db)

    return result
