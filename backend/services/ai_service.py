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


SEARCH_SYSTEM_PROMPT = """Tu es un expert automobile analyste. On te donne la liste complète des annonces trouvées pour un modèle de voiture.

Analyse l'ENSEMBLE des annonces et retourne un JSON structuré avec ces 5 champs EXACTEMENT:
- synthese_globale: résumé général de ce que tu observes sur toutes les annonces (état général du marché de ces véhicules, tendances de prix, kilométrages, etc.) en 3-4 phrases en français
- themes_mentionnes: liste des sujets/éléments qui reviennent souvent dans les descriptions (ex: "révision récente", "pneus neufs", "CT valide", "carnet entretien", etc.) — liste de strings
- themes_absents: liste des éléments importants qu'on ne mentionne JAMAIS ou presque jamais dans ces annonces (ex: "état de la courroie de distribution", "historique d'accidents", "nombre de propriétaires", etc.) — liste de strings
- prochaines_reparations: liste des réparations/révisions probablement à prévoir sur ces véhicules en général, basée sur les kilométrages et années typiques observés — liste de strings
- risk_level: risque général du lot: "low" | "medium" | "high"

Réponds UNIQUEMENT avec le JSON valide, sans markdown, sans explication."""

SEARCH_USER_TEMPLATE = """Annonces trouvées ({count} résultats) pour {brand} {model_name}:

{listings_text}

Analyse ces annonces collectivement et retourne le JSON structuré demandé."""


def build_search_prompt(listings: list, brand: str = "", model_name: str = "") -> str:
    lines = []
    for i, l in enumerate(listings[:25], 1):  # max 25 annonces
        parts = [f"[{i}] {l.get('title', 'Sans titre')}"]
        if l.get("year"):
            parts.append(f"Annee: {l['year']}")
        if l.get("mileage"):
            parts.append(f"Km: {l['mileage']}")
        if l.get("price"):
            parts.append(f"Prix: {l['price']}EUR")
        desc = (l.get("description") or "").strip()[:400]
        if desc:
            parts.append(f"Description: {desc}")
        lines.append(" | ".join(parts))

    listings_text = "\n\n".join(lines) if lines else "Aucune description disponible."
    return SEARCH_USER_TEMPLATE.format(
        count=len(listings),
        brand=brand,
        model_name=model_name,
        listings_text=listings_text,
    )


async def call_github_models_search(prompt_text: str) -> dict:
    """Call GitHub Models API for search-level analysis."""
    import httpx

    if not GITHUB_TOKEN:
        raise ValueError(
            "GITHUB_TOKEN non configure. "
            "Ajoute GITHUB_TOKEN dans ton .env."
        )

    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            GITHUB_MODELS_URL,
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "model": GITHUB_MODEL,
                "messages": [
                    {"role": "system", "content": SEARCH_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_text},
                ],
                "temperature": 0.3,
                "max_tokens": 1500,
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

    return _parse_search_response(content)


def _parse_search_response(content: str) -> dict:
    clean = content.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1] if len(parts) > 1 else clean
        if clean.startswith("json"):
            clean = clean[4:]
    clean = clean.strip()

    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("LLM search returned invalid JSON: %s", content[:300])
        data = {
            "synthese_globale": content[:800] if content else "Analyse indisponible.",
            "themes_mentionnes": [],
            "themes_absents": [],
            "prochaines_reparations": [],
            "risk_level": "medium",
        }

    data.setdefault("synthese_globale", "")
    data.setdefault("themes_mentionnes", [])
    data.setdefault("themes_absents", [])
    data.setdefault("prochaines_reparations", [])
    data.setdefault("risk_level", "medium")
    data["raw_response"] = content
    return data


async def scan_immat_vision(image_url: str) -> Optional[str]:
    """Use GitHub Models vision API to extract license plate from image."""
    import httpx

    if not GITHUB_TOKEN:
        return None

    vision_model = "gpt-4o"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                GITHUB_MODELS_URL,
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": vision_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Regarde cette image de voiture. Si tu vois une plaque d'immatriculation francaise, retourne UNIQUEMENT la plaque (format: AB-123-CD ou AB 123 CD). Si aucune plaque visible ou lisible, reponds exactement: AUCUNE",
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": image_url},
                                },
                            ],
                        }
                    ],
                    "max_tokens": 20,
                },
            )
            resp.raise_for_status()
            result = resp.json()["choices"][0]["message"]["content"].strip()
            if result and result != "AUCUNE" and len(result) <= 15:
                return result
            return None
    except Exception as e:
        logger.warning("scan_immat_vision failed: %s", e)
        return None
