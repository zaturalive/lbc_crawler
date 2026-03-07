"""AI analysis service — uses GitHub Models API (GITHUB_TOKEN, no extra key needed)."""
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_MODEL = os.getenv("GITHUB_MODEL", "gpt-4o-mini")
GITHUB_MODELS_URL = "https://models.inference.ai.azure.com/chat/completions"

SYSTEM_PROMPT = """Tu es un expert automobile. Analyse la description d'une annonce de voiture d'occasion.

Extrais et retourne un JSON structuré avec ces 4 champs EXACTEMENT:
- repairs_found: liste des réparations/interventions déjà effectuées mentionnées dans l'annonce (liste de strings, vide si aucune)
- upcoming_maintenance: liste des révisions/réparations probablement à prévoir selon le kilométrage, l'âge et l'état décrit (liste de strings)
- condition_summary: résumé de l'état général du véhicule en 2-3 phrases claires en français
- risk_level: niveau de risque global: "low" (bon état, entretenu) | "medium" (état correct, quelques points d'attention) | "high" (risques importants, réparations majeures à prévoir)

Réponds UNIQUEMENT avec le JSON valide, sans markdown, sans explication, sans texte autour."""

USER_PROMPT_TEMPLATE = """Annonce de voiture d'occasion à analyser:

Titre: {title}
Kilométrage: {mileage} km
Année: {year}
Prix: {price} €

Description du vendeur:
{description}

Analyse cette annonce et retourne le JSON structuré demandé."""


def build_prompt(title: str, description: str, mileage=None, year=None, price=None) -> str:
    return USER_PROMPT_TEMPLATE.format(
        title=title or "Non renseigné",
        mileage=mileage or "?",
        year=year or "?",
        price=price or "?",
        description=description or "Pas de description disponible.",
    )


async def call_github_models(prompt_text: str) -> dict:
    """Call GitHub Models API (gpt-4o-mini via GITHUB_TOKEN)."""
    import httpx

    if not GITHUB_TOKEN:
        raise ValueError(
            "GITHUB_TOKEN non configuré. "
            "Ajoute GITHUB_TOKEN dans ton .env (le même token GitHub que pour CI/CD)."
        )

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            GITHUB_MODELS_URL,
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "model": GITHUB_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_text},
                ],
                "temperature": 0.3,
                "max_tokens": 1000,
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

    return _parse_llm_response(content)


def _parse_llm_response(content: str) -> dict:
    clean = content.strip()
    # Strip markdown code fences if present
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1] if len(parts) > 1 else clean
        if clean.startswith("json"):
            clean = clean[4:]
    clean = clean.strip()

    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("LLM returned invalid JSON: %s", content[:300])
        data = {
            "repairs_found": [],
            "upcoming_maintenance": [],
            "condition_summary": content[:500] if content else "Analyse indisponible.",
            "risk_level": "medium",
        }

    # Ensure expected keys exist
    data.setdefault("repairs_found", [])
    data.setdefault("upcoming_maintenance", [])
    data.setdefault("condition_summary", "")
    data.setdefault("risk_level", "medium")
    data["raw_response"] = content
    return data
