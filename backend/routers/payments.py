"""
Router paiements Stripe.

Endpoints :
- GET  /payments/packs          — liste les packs disponibles
- POST /payments/create-checkout — crée une session Stripe Checkout
- POST /payments/webhook         — reçoit les events Stripe (checkout.session.completed)
"""
import os
import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.security import decode_token
from db.database import get_db
from models import CreditTransaction
from services.credits_service import add_credits

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])
_bearer = HTTPBearer(auto_error=False)

STRIPE_SECRET_KEY     = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL          = os.getenv("FRONTEND_URL", "http://localhost:3000")

stripe.api_key = STRIPE_SECRET_KEY

# ─── Packs définis en code (pas besoin de Stripe Products pré-créés) ──────────

PACKS = [
    # Analyses IA
    {"id": "analysis_5",  "name": "Starter Analyse",  "pack_type": "analysis", "credits": 5,   "price_cents": 199,  "description": "5 analyses IA"},
    {"id": "analysis_10", "name": "Standard Analyse", "pack_type": "analysis", "credits": 10,  "price_cents": 349,  "description": "10 analyses IA"},
    {"id": "analysis_50", "name": "Pro Analyse",      "pack_type": "analysis", "credits": 50,  "price_cents": 1499, "description": "50 analyses IA"},
    # Recherches
    {"id": "search_5",    "name": "Mini Recherche",   "pack_type": "search",   "credits": 5,   "price_cents": 99,   "description": "5 recherches supplémentaires"},
    {"id": "search_20",   "name": "Standard Recherche","pack_type": "search",  "credits": 20,  "price_cents": 249,  "description": "20 recherches supplémentaires"},
    {"id": "search_100",  "name": "Illimité Recherche","pack_type": "search",  "credits": 100, "price_cents": 899,  "description": "100 recherches supplémentaires"},
]

PACKS_BY_ID = {p["id"]: p for p in PACKS}


def _get_user_id(credentials: HTTPAuthorizationCredentials | None) -> int | None:
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if payload is None:
        return None
    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        return None


# ─── Liste des packs ──────────────────────────────────────────────────────────

@router.get("/packs")
async def list_packs():
    """Retourne tous les packs disponibles à l'achat."""
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "pack_type": p["pack_type"],
            "credits": p["credits"],
            "price_cents": p["price_cents"],
            "price_eur": p["price_cents"] / 100,
            "description": p["description"],
        }
        for p in PACKS
    ]


# ─── Création de session Checkout ─────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    pack_id: str


@router.post("/create-checkout")
async def create_checkout(
    body: CheckoutRequest,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = _get_user_id(credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentification requise")

    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Paiement non configuré (STRIPE_SECRET_KEY manquant)")

    pack = PACKS_BY_ID.get(body.pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack introuvable")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": pack["name"],
                        "description": pack["description"],
                    },
                    "unit_amount": pack["price_cents"],
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/payment/cancel",
            metadata={
                "user_id": str(user_id),
                "pack_id": pack["id"],
                "pack_type": pack["pack_type"],
                "credits": str(pack["credits"]),
            },
        )
    except stripe.StripeError as e:
        logger.error("Stripe error: %s", e)
        raise HTTPException(status_code=502, detail=f"Erreur Stripe : {e.user_message or str(e)}")

    # Créer la transaction en attente
    tx = CreditTransaction(
        user_id=user_id,
        credits_added=pack["credits"],
        pack_type=pack["pack_type"],
        stripe_session_id=session.id,
        status="pending",
    )
    db.add(tx)
    await db.commit()

    return {"checkout_url": session.url, "session_id": session.id}


# ─── Webhook Stripe ───────────────────────────────────────────────────────────

@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Écoute les événements Stripe.
    checkout.session.completed → crédite le compte de l'utilisateur.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except stripe.errors.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Signature webhook invalide")
    else:
        import json
        event = json.loads(payload)

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        stripe_session_id = session_obj["id"]
        metadata = session_obj.get("metadata", {})

        user_id   = int(metadata.get("user_id", 0))
        pack_type = metadata.get("pack_type", "")
        credits   = int(metadata.get("credits", 0))

        if not user_id or not pack_type or not credits:
            logger.warning("Webhook: metadata incomplète, session %s", stripe_session_id)
            return {"status": "ignored"}

        # Vérifier si déjà traité (idempotence)
        result = await db.execute(
            select(CreditTransaction).where(
                CreditTransaction.stripe_session_id == stripe_session_id,
                CreditTransaction.status == "completed",
            )
        )
        if result.scalar_one_or_none():
            return {"status": "already_processed"}

        # Créditer l'utilisateur
        await add_credits(user_id, pack_type, credits, db)

        # Mettre à jour la transaction
        tx_result = await db.execute(
            select(CreditTransaction).where(
                CreditTransaction.stripe_session_id == stripe_session_id
            )
        )
        tx = tx_result.scalar_one_or_none()
        if tx:
            tx.status = "completed"
            tx.stripe_payment_id = session_obj.get("payment_intent")
            await db.commit()
        else:
            # Transaction non trouvée (paiement direct sans passage par create-checkout)
            tx = CreditTransaction(
                user_id=user_id,
                credits_added=credits,
                pack_type=pack_type,
                stripe_session_id=stripe_session_id,
                stripe_payment_id=session_obj.get("payment_intent"),
                status="completed",
            )
            db.add(tx)
            await db.commit()

        logger.info("Credits added: user=%s type=%s amount=%s", user_id, pack_type, credits)

    return {"status": "ok"}
