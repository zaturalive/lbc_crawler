"""AI analysis service — uses GitHub Models API (GITHUB_TOKEN, no extra key needed)."""
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_MODEL = os.getenv("GITHUB_MODEL", "gpt-4o-mini")
GITHUB_MODELS_URL = "https://models.inference.ai.azure.com/chat/completions"

_BASE_SYSTEM_PROMPT = """Tu es un expert automobile spécialisé dans l'évaluation des voitures d'occasion en France. \
Tu analyses des annonces LeBonCoin pour aider les acheteurs à prendre une décision éclairée.

Extrais et retourne un JSON structuré avec ces 4 champs EXACTEMENT:
- repairs_found: liste des réparations/interventions DÉJÀ effectuées mentionnées dans l'annonce (liste de strings). \
  Si le vendeur mentionne un carnet d'entretien → ajoute "Carnet d'entretien mentionné — à vérifier physiquement"
- upcoming_maintenance: liste des points de vigilance et révisions probables à prévoir. \
  Sois PRÉCIS et CONCRET : nomme les pièces, les kilométrages types, les coûts approximatifs si connus. \
  Minimum 3 points, même si la voiture semble en bon état.
- condition_summary: résumé détaillé de l'état général en 4-5 phrases. \
  Inclure: état général, cohérence prix/km/année, points forts, points faibles, verdict final.
- risk_level: "low" | "medium" | "high"

Réponds UNIQUEMENT avec le JSON valide, sans markdown, sans explication."""

_RELIABILITY_CONTEXT_TEMPLATE = """

FICHE FIABILITÉ DU MODÈLE (source: fiches-auto.fr — données réelles de propriétaires):
Véhicule: {vehicle_label}
Score fiabilité: {reliability_score}/100 ({reliability_interpretation}) basé sur {total_testimonials} témoignages
Catégorie: {category}

TOP DÉFAUTS SIGNALÉS (classés par fréquence):
{top_defauts}

DÉTAILS DES PRINCIPAUX PROBLÈMES:
{known_issues_detail}

RÈGLES OBLIGATOIRES — tu DOIS respecter ces règles dans ta réponse:
1. Pour chacun des TOP DÉFAUTS ci-dessus:
   - Si l'annonce mentionne explicitement que ce problème a été réglé → ajoute dans repairs_found: "✓ [NOM DU DÉFAUT] : mentionné comme traité par le vendeur"
   - Si ce défaut N'EST PAS mentionné dans l'annonce → ajoute dans upcoming_maintenance: "⚠️ [NOM DU DÉFAUT] (N signalements) : défaut fréquent sur ce modèle, non mentionné par le vendeur — à vérifier"
2. Si le score fiabilité est inférieur à 50 → risk_level doit être au minimum "medium"
3. Si 3 défauts coûteux (FAP, injection, boîte de vitesse, moteur, turbo, courroie de distribution) ne sont pas mentionnés → risk_level = "high"
4. Dans condition_summary, cite EXPLICITEMENT le score fiabilité et les 2-3 défauts les plus fréquents pour ce modèle."""


def _parse_common_issues(common_issues) -> list[tuple[str, int]]:
    """Parse common_issues JSON into sorted list of (name, count) tuples, top 10."""
    import re
    if not common_issues:
        return []
    if isinstance(common_issues, str):
        import json as _json
        try:
            common_issues = _json.loads(common_issues)
        except Exception:
            return []
    if not isinstance(common_issues, list):
        return []

    result = []
    seen = set()
    for item in common_issues:
        if not isinstance(item, str):
            continue
        # "Embray.: 68 témoignages" → ("Embray.", 68)
        m = re.match(r'^(.+?):\s*(\d+)\s*t[ée]moignage', item)
        if m:
            name = m.group(1).strip()
            count = int(m.group(2))
            # Déduplique (Boîte de Vit. / Boîte de vit.)
            key = name.lower().replace('.', '').replace(' ', '')
            if key not in seen:
                seen.add(key)
                result.append((name, count))

    result.sort(key=lambda x: x[1], reverse=True)
    return result[:10]


def _parse_known_issues_text(known_issues_text) -> list[str]:
    """Extract issue names + first meaningful sentence from known_issues_text JSON."""
    if not known_issues_text:
        return []
    if isinstance(known_issues_text, str):
        import json as _json
        try:
            items = _json.loads(known_issues_text)
        except Exception:
            return []
    else:
        items = known_issues_text

    if not isinstance(items, list):
        return []

    result = []
    for item in items[:5]:  # max 5 problèmes détaillés
        if not isinstance(item, str):
            continue
        # Extrait "NomDuProblème : première phrase."
        first_line = item.split('\r\n')[0].split('\n')[0].strip()
        if len(first_line) > 200:
            first_line = first_line[:200] + "..."
        if first_line:
            result.append(first_line)
    return result


def build_system_prompt(known_issues=None, common_issues=None, vehicle_meta=None) -> str:
    """Build the system prompt, enriched with vehicle reliability context when available."""
    prompt = _BASE_SYSTEM_PROMPT
    has_known = known_issues and (
        (isinstance(known_issues, list) and len(known_issues) > 0)
        or (isinstance(known_issues, str) and known_issues.strip())
    )
    has_common = common_issues and (
        (isinstance(common_issues, list) and len(common_issues) > 0)
        or (isinstance(common_issues, str) and common_issues.strip())
    )
    if not (has_known or has_common):
        return prompt

    meta = vehicle_meta or {}
    brand = meta.get("brand") or ""
    model = meta.get("model") or ""
    year_start = meta.get("year_start") or ""
    year_end = meta.get("year_end") or ""
    score = meta.get("reliability_score")
    testimonials = meta.get("total_testimonials") or 0
    category = meta.get("category") or "Non renseigné"

    year_range = f"{year_start}–{year_end}" if year_start and year_end else (str(year_start) or "")
    vehicle_label = f"{brand} {model} ({year_range})".strip() if brand else "Modèle non identifié"

    if score is not None:
        if score >= 80:
            reliability_interpretation = "excellente fiabilité"
        elif score >= 60:
            reliability_interpretation = "bonne fiabilité"
        elif score >= 40:
            reliability_interpretation = "fiabilité moyenne"
        else:
            reliability_interpretation = "fiabilité médiocre — prudence"
    else:
        reliability_interpretation = "Non disponible"
    score_str = str(score) if score is not None else "?"

    # Top défauts formatés
    parsed_common = _parse_common_issues(common_issues)
    if parsed_common:
        top_defauts_lines = []
        for name, count in parsed_common:
            top_defauts_lines.append(f"  - {name}: {count} signalements")
        top_defauts = "\n".join(top_defauts_lines)
    else:
        top_defauts = "  Aucune donnée disponible"

    # Détail des problèmes principaux
    known_details = _parse_known_issues_text(known_issues)
    if known_details:
        known_issues_detail = "\n".join(f"  • {d}" for d in known_details)
    else:
        known_issues_detail = "  Aucun détail disponible"

    prompt += _RELIABILITY_CONTEXT_TEMPLATE.format(
        vehicle_label=vehicle_label,
        reliability_score=score_str,
        reliability_interpretation=reliability_interpretation,
        total_testimonials=testimonials,
        category=category,
        top_defauts=top_defauts,
        known_issues_detail=known_issues_detail,
    )
    return prompt


USER_PROMPT_TEMPLATE = """Annonce de voiture d'occasion à analyser:

Titre: {title}
Kilométrage: {mileage} km
Année: {year}
Prix: {price} €

Description du vendeur:
{description}

DÉTECTION RÉVISION: Si la description mentionne une révision avec date ou kilométrage, indique dans upcoming_maintenance si elle est récente ou à refaire sous peu (intervalles typiques: révision toutes les 30 000 km ou 2 ans pour la plupart des modèles).

Analyse cette annonce et retourne le JSON structuré demandé."""


def build_prompt(
    title: str,
    description: str,
    mileage=None,
    year=None,
    price=None,
    known_issues=None,
    common_issues=None,
    vehicle_meta=None,
) -> tuple[str, str]:
    """Return (user_prompt, system_prompt) for the listing analysis.

    The system prompt is enriched with vehicle reliability context when
    known_issues, common_issues or vehicle_meta are provided.
    """
    user_prompt = USER_PROMPT_TEMPLATE.format(
        title=title or "Non renseigné",
        mileage=mileage or "?",
        year=year or "?",
        price=price or "?",
        description=description or "Pas de description disponible.",
    )
    system_prompt = build_system_prompt(
        known_issues=known_issues,
        common_issues=common_issues,
        vehicle_meta=vehicle_meta,
    )
    return user_prompt, system_prompt


async def call_github_models(prompt_text: str, system_prompt: Optional[str] = None) -> dict:
    """Call GitHub Models API (gpt-4o-mini via GITHUB_TOKEN)."""
    import httpx

    if not GITHUB_TOKEN:
        raise ValueError(
            "GITHUB_TOKEN non configuré. "
            "Ajoute GITHUB_TOKEN dans ton .env (le même token GitHub que pour CI/CD)."
        )

    effective_system = system_prompt if system_prompt is not None else _BASE_SYSTEM_PROMPT

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
                    {"role": "system", "content": effective_system},
                    {"role": "user", "content": prompt_text},
                ],
                "temperature": 0.3,
                "max_tokens": 1500,
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
