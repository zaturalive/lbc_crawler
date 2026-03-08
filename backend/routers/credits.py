"""Route GET /credits/me — retourne le solde crédits de l'utilisateur connecté."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import decode_token
from db.database import get_db
from services.credits_service import get_credits_summary

router = APIRouter(prefix="/credits", tags=["credits"])
_bearer = HTTPBearer(auto_error=False)


def _require_user_id(credentials: HTTPAuthorizationCredentials | None) -> int:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentification requise")
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token invalide")


@router.get("/me")
async def get_my_credits(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    """Retourne le solde crédits complet de l'utilisateur connecté."""
    user_id = _require_user_id(credentials)
    return await get_credits_summary(user_id, db)
