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
| `GITHUB_TOKEN` | _(vide)_ | Token GitHub — **obligatoire** (même token que CI/CD) |
| `GITHUB_MODEL` | `gpt-4o-mini` | Modèle GitHub Models à utiliser |

### Configuration

**Aucune clé API supplémentaire requise.** Utilise ton Personal Access Token GitHub habituel :

```env
GITHUB_TOKEN=ghp_...        # ton token GitHub (même que pour CI/CD)
GITHUB_MODEL=gpt-4o-mini    # gratuit en preview
```

> **GitHub Models** est accessible sur `https://models.inference.ai.azure.com` avec le même `GITHUB_TOKEN` que tu utilises pour GitHub Actions. `gpt-4o-mini` est gratuit en preview.

---

## API Reference

### `POST /listings/{listing_id}/analyze`

Déclenche ou retourne (depuis le cache) l'analyse IA d'une annonce.

**Paramètres** : `listing_id` (int, path)

**Réponse 200 :**
```json
{
  "id": 1,
  "listing_id": 42,
  "model": "gpt-4o-mini",
  "status": "done",
  "created_at": "2025-01-15T10:30:00",
  "is_premium": false,
  "reponse": {
    "id": 1,
    "requete_id": 1,
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

## Schéma DB

Deux tables séparées : la **requête** (prompt envoyé) et la **réponse** (analyse structurée).

```sql
-- Requête envoyée au LLM
CREATE TABLE requete_ia (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    listing_id   INT NOT NULL,
    prompt_text  TEXT NOT NULL,
    model        VARCHAR(100) NOT NULL,
    status       VARCHAR(20) DEFAULT 'pending',   -- pending | done | error
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id)
);

-- Réponse structurée du LLM (1-to-1 avec requete_ia)
CREATE TABLE reponse_ia (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    requete_id           INT NOT NULL UNIQUE,
    repairs_found        JSON,
    upcoming_maintenance JSON,
    condition_summary    TEXT,
    risk_level           VARCHAR(20),    -- "low" | "medium" | "high"
    raw_response         TEXT,
    created_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (requete_id) REFERENCES requete_ia(id)
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
| `backend/models/__init__.py` | + classes `RequeteIA` + `ReponseIA` (remplace `ListingAnalysis`) |
| `backend/schemas/__init__.py` | + `RequeteIAOut` + `ReponseIAOut` |
| `backend/services/ai_service.py` | **nouveau** — GitHub Models API (GITHUB_TOKEN) |
| `backend/routers/analysis.py` | **nouveau** — endpoint REST avec séparation requête/réponse |
| `backend/main.py` | + `include_router(analysis_router)` |
| `infra/docker-compose.dev.yml` | + `GITHUB_TOKEN` + `GITHUB_MODEL` |
| `frontend/src/api/client.js` | + `analyzeListingAI()` |
| `frontend/src/components/ReliabilityModal.jsx` | + onglet "Analyse IA", accès via `aiAnalysis.reponse.*` |
