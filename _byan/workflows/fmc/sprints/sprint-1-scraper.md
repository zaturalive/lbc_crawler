---
name: "sprint-1-scraper"
description: "Sprint 1 — Scraper: lbc_scraper.py, fiches_auto_scraper.py, regex_engine.py, Dockerfile ARM64"
agent: fmc-scraper
model_context: claude-sonnet-4.6
model_worker: claude-haiku-4.5
depends_on: sprint-0-infra
---

# Sprint 1 — Scraper

**Agent responsable :** `fmc-scraper`
**Dépendance :** Sprint 0 terminé (docker-compose.yml + init.sql disponibles)
**Livrables :** `scraper/` complet, service scraper fonctionnel

---

## Ordre d'exécution

```
E1-US3 (regex_engine.py)
  ↓
E1-US1 (lbc_scraper.py)
  ↓
E1-US2 (fiches_auto_scraper.py)
  ↓
E1-US4 (Dockerfile + API interne)
```

> regex_engine en premier — lbc_scraper l'importe.

---

## US E1-US3 — regex_engine.py

**Modèle worker :** `claude-haiku-4.5`

**Fichiers à générer :**
- `scraper/regex_engine.py`

**Acceptance criteria :**
- Classe `RegexEngine` avec méthode `match(description: str, patterns: list[dict]) -> list[str]`
- Patterns pré-configurés chargés depuis BDD (ou dict par défaut si BDD non dispo)
- Validation regex custom : `validate_pattern(pattern: str) -> bool` — lève ValueError si invalide
- Tous les patterns : `re.IGNORECASE`
- Retourne liste des noms de patterns déclenchés (ex: `["CT valide", "Carte grise"]`)
- Test unitaire inclus dans le fichier (`if __name__ == '__main__'`)

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E1-US3, agent_name=fmc-scraper, sprint_id=sprint-1
```

---

## US E1-US1 — lbc_scraper.py

**Modèle worker :** `claude-haiku-4.5`

**Fichiers à générer :**
- `scraper/lbc_scraper.py`

**Acceptance criteria :**
- Classe `LBCScraper` avec méthode `search(filters: SearchFilters) -> list[dict]`
- `SearchFilters` dataclass : brand, model, price_min, price_max, mileage_max, year_min, horsepower_min, horsepower_max, gearbox
- Utilise `lbc.Client()` pour le scraping
- Rate limiting : `time.sleep(random.uniform(1.0, 2.0))` entre chaque page
- Max pages configurable (défaut: 5)
- User-Agent configurable via env var `LBC_USER_AGENT`
- Chaque annonce retournée respecte le data contract défini dans find_my_car-architecture.md
- Champs extraits : lbc_id, title, price, year, mileage, horsepower, gearbox, location, description, url, brand, model
- Appelle `RegexEngine.match()` sur chaque description → ajoute `matched_keywords`
- Gestion d'exception : si une annonce échoue, log l'erreur et continue

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E1-US1, agent_name=fmc-scraper, sprint_id=sprint-1
```

---

## US E1-US2 — fiches_auto_scraper.py

**Modèle worker :** `claude-sonnet-4.6` (logique de parsing HTML + cache)

**Fichiers à générer :**
- `scraper/fiches_auto_scraper.py`

**Acceptance criteria :**
- Classe `FichesAutoScraper` avec méthode `get_vehicle_data(brand: str, model: str) -> dict | None`
- Recherche sur fiches-auto.fr par brand+model
- Extrait : `reliability_score` (int 0-10), `common_issues` (list[str])
- Fail gracefully : si modèle non trouvé → retourne `None`, ne bloque pas
- Rate limiting : 2s entre requêtes
- Headers réalistes (User-Agent, Accept-Language: fr-FR)
- Résultat mis en cache dans fichier JSON local `scraper/cache/fiches_auto_cache.json`
  - Clé : `"{brand}_{model}"`
  - TTL : 7 jours
- Ne pas re-scraper si cache valide

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E1-US2, agent_name=fmc-scraper, sprint_id=sprint-1
```

---

## US E1-US4 — Dockerfile ARM64 + API interne scraper

**Modèle worker :** `claude-haiku-4.5`

**Fichiers à générer :**
- `scraper/Dockerfile`
- `scraper/requirements.txt`
- `scraper/main.py` (FastAPI minimal, expose POST /scrape)

**Acceptance criteria :**
- Dockerfile : `FROM python:3.11-slim`, platform `linux/arm64`
- Multi-stage si possible pour réduire taille image
- `requirements.txt` : lbc, requests, beautifulsoup4, fastapi, uvicorn, sqlalchemy, pymysql
- `main.py` : FastAPI app, endpoint `POST /scrape` accepte `SearchFilters` + `patterns`, retourne `list[ListingDict]`
- Health check endpoint : `GET /health` → `{"status": "ok"}`
- Port : 8001 (interne Docker uniquement)
- Uvicorn lancé avec `--host 0.0.0.0 --port 8001`

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E1-US4, agent_name=fmc-scraper, sprint_id=sprint-1
```

---

## Gate Sprint 1

Après chaque US, exécuter :
```
Read: {project-root}/_byan/workflows/fmc/gate-workflow.md
```

Après E1-US4 :
```
SPRINT 1 TERMINÉ — Scraper généré.

Prochaine étape : Sprint 2 — Backend
Read: {project-root}/_byan/workflows/fmc/sprints/sprint-2-backend.md

[BYAN] Valider avant de lancer Sprint 2 ?
```
