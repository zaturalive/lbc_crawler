"""AI analysis service — supports OpenAI and Ollama (local)."""
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")   # "openai" | "ollama"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

SYSTEM_PROMPT = """Tu es un expert automobile. Analyse la description d'une annonce de voiture d'occasion.

Extrais et retourne un JSON structuré avec:
- repairs_found: liste des réparations/interventions déjà effectuées mentionnées (liste de strings)
- upcoming_maintenance: liste des révisions/réparations probablement à prévoir selon le kilométrage, l'âge et l'état décrit (liste de strings)  
- condition_summary: résumé de l'état général du véhicule en 2-3 phrases claires
- risk_level: niveau de risque global ("low" | "medium" | "high") basé sur l'état et les réparations

Réponds UNIQUEMENT avec le JSON valide, sans markdown, sans explication."""

USER_PROMPT_TEMPLATE = """Annonce: {title}
Kilométrage: {mileage} km
Année: {year}
Prix: {price} €

Description:
{description}"""


async def analyze_listing(
    title: str,
    description: str,
    mileage: Optional[int] = None,
    year: Optional[int] = None,
    price: Optional[int] = None,
) -> dict:
    """Call LLM and return structured analysis dict."""
    user_msg = USER_PROMPT_TEMPLATE.format(
        title=title or "Non renseigné",
        mileage=mileage or "?",
        year=year or "?",
        price=price or "?",
        description=description or "Pas de description disponible.",
    )

    if AI_PROVIDER == "ollama":
        return await _call_ollama(user_msg)
    return await _call_openai(user_msg)


async def _call_openai(user_msg: str) -> dict:
    import httpx
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY non configurée")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                "temperature": 0.3,
                "max_tokens": 1000,
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
    return _parse_llm_response(content, OPENAI_MODEL)


async def _call_ollama(user_msg: str) -> dict:
    import httpx
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                "stream": False,
            },
        )
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
    return _parse_llm_response(content, OLLAMA_MODEL)


def _parse_llm_response(content: str, model: str) -> dict:
    # Strip markdown code fences if present
    clean = content.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("LLM returned invalid JSON: %s", content[:200])
        data = {
            "repairs_found": [],
            "upcoming_maintenance": [],
            "condition_summary": content[:500],
            "risk_level": "medium",
        }
    data["model_used"] = model
    data["raw_response"] = content
    return data
