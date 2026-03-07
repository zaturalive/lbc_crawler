# ✨ Feature : Analyse IA des annonces

> Branche : `feature/ai-listing-analysis`  
> Statut : Gratuit (futur : payant)

---

## Vue d'ensemble

La feature **Analyse IA** permet d'analyser automatiquement la description texte d'une annonce LeBonCoin avec un LLM (Large Language Model). L'IA extrait des informations structurées qui ne sont pas disponibles dans les métadonnées de l'annonce.

### Informations extraites

| Champ | Description |
|-------|-------------|
| `repairs_found` | Liste des réparations/interventions déjà effectuées mentionnées dans l'annonce |
| `upcoming_maintenance` | Révisions et réparations probablement à prévoir (basé sur kilométrage, âge, état) |
| `condition_summary` | Résumé de l'état général en 2-3 phrases claires |
| `risk_level` | Niveau de risque global : `low` / `medium` / `high` |

---

## Architecture

```
Frontend (ReliabilityModal)
    └── POST /listings/{id}/analyze
            └── Backend (routers/analysis.py)
                    └── services/ai_service.py
                            ├── OpenAI API  (AI_PROVIDER=openai)
                            └── Ollama API  (AI_PROVIDER=ollama)
                    └── DB: listing_analyses (cache)
```

### Cache
Les analyses sont **mises en cache** dans la table `listing_analyses`. Un second clic sur "Lancer l'analyse" retourne immédiatement le résultat sauvegardé sans re-appeler le LLM.

---

## Variables d'environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `AI_PROVIDER` | `openai` | Fournisseur LLM : `openai` ou `ollama` |
| `OPENAI_API_KEY` | _(vide)_ | Clé API OpenAI — obligatoire si `AI_PROVIDER=openai` |
| `OPENAI_MODEL` | `gpt-4o-mini` | Modèle OpenAI à utiliser |
| `OLLAMA_URL` | `http://localhost:11434` | URL du serveur Ollama — obligatoire si `AI_PROVIDER=ollama` |
| `OLLAMA_MODEL` | `mistral` | Modèle Ollama à utiliser |

### Configuration recommandée

**Production (OpenAI) :**
```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

**Dev local (Ollama, gratuit) :**
```bash
# Installer Ollama : https://ollama.ai
ollama pull mistral
```
```env
AI_PROVIDER=ollama
OLLAMA_URL=http://host.docker.internal:11434
OLLAMA_MODEL=mistral
```

---

## API Reference

### `POST /listings/{listing_id}/analyze`

Déclenche ou retourne (depuis le cache) l'analyse IA d'une annonce.

**Paramètres** : `listing_id` (int, path)

**Réponse 200 :**
```json
{
  "id": 42,
  "listing_id": 1337,
  "model_used": "gpt-4o-mini",
  "repairs_found": [
    "Courroie de distribution changée à 120 000 km",
    "Embrayage remplacé"
  ],
  "upcoming_maintenance": [
    "Vidange (tous les 15 000 km — bientôt à prévoir)",
    "Contrôle technique dans 1 an"
  ],
  "condition_summary": "Véhicule bien entretenu avec carnet de suivi. Quelques traces d'usure cosmétiques sans impact mécanique. Historique transparent.",
  "risk_level": "low",
  "created_at": "2025-01-15T10:30:00",
  "is_premium": false
}
```

**Erreurs :**
- `404` — Annonce introuvable
- `422` — Annonce sans description
- `503` — LLM indisponible (clé API manquante, timeout…)

---

## Prompt LLM

### System prompt
```
Tu es un expert automobile. Analyse la description d'une annonce de voiture d'occasion.

Extrais et retourne un JSON structuré avec:
- repairs_found: liste des réparations/interventions déjà effectuées mentionnées (liste de strings)
- upcoming_maintenance: liste des révisions/réparations probablement à prévoir selon le kilométrage, l'âge et l'état décrit (liste de strings)  
- condition_summary: résumé de l'état général du véhicule en 2-3 phrases claires
- risk_level: niveau de risque global ("low" | "medium" | "high") basé sur l'état et les réparations

Réponds UNIQUEMENT avec le JSON valide, sans markdown, sans explication.
```

### User prompt (template)
```
Annonce: {title}
Kilométrage: {mileage} km
Année: {year}
Prix: {price} €

Description:
{description}
```

---

## Schéma DB : `listing_analyses`

```sql
CREATE TABLE listing_analyses (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    listing_id   INT NOT NULL UNIQUE,
    model_used   VARCHAR(100),
    repairs_found        JSON,
    upcoming_maintenance JSON,
    condition_summary    TEXT,
    risk_level   VARCHAR(20),
    raw_response TEXT,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id)
);
```

---

## Roadmap monétisation

### Phase actuelle : Gratuit
- ✅ Toutes les annonces analysables sans limite
- ✅ `is_premium: false` dans la réponse
- ✅ Badge "✓ Gratuit" affiché dans l'UI

### Phase future : Freemium
- 🔒 X analyses gratuites par compte/mois
- 💎 Abonnement Premium pour analyses illimitées
- 🔒 Analyses stockées en cache uniquement pour Premium (les Free re-paient le token à chaque visite)

**Implémentation future suggérée :**
1. Ajouter `user_id` à `listing_analyses` + table `usage_credits`
2. Middleware `check_ai_quota` sur l'endpoint
3. Stripe Checkout pour upgrade
4. `is_premium: true` dans la réponse quand l'user est abonné

---

## Fichiers modifiés

| Fichier | Changement |
|---------|------------|
| `backend/models/__init__.py` | + classe `ListingAnalysis` |
| `backend/schemas/__init__.py` | + `ListingAnalysisResponse` |
| `backend/services/ai_service.py` | **nouveau** — logique LLM |
| `backend/routers/analysis.py` | **nouveau** — endpoint REST |
| `backend/main.py` | + `include_router(analysis_router)` |
| `infra/docker-compose.dev.yml` | + env vars AI |
| `frontend/src/api/client.js` | + `analyzeListingAI()` |
| `frontend/src/components/ReliabilityModal.jsx` | + onglet "Analyse IA" |
