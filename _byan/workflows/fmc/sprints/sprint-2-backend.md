---
name: "sprint-2-backend"
description: "Sprint 2 — Backend: FastAPI + SQLAlchemy async + MariaDB. Endpoints /search /listings /vehicles /patterns"
agent: fmc-backend
model_context: claude-sonnet-4.6
model_worker: claude-haiku-4.5
depends_on: sprint-1-scraper
---

# Sprint 2 — Backend

**Agent responsable :** `fmc-backend`
**Dépendance :** Sprint 1 terminé (scraper/main.py + data contract disponibles)
**Livrables :** `backend/` complet, API FastAPI fonctionnelle

---

## Ordre d'exécution

```
E2-US1 (modèles SQLAlchemy + Pydantic)
  ↓
E2-US2 (couche DB async)
  ↓
E2-US3 (POST /search)
  ↓
E2-US4 (GET /listings + /vehicles + CRUD /patterns)
```

---

## US E2-US1 — Modèles SQLAlchemy + Pydantic schemas

**Modèle worker :** `claude-haiku-4.5`

**Fichiers à générer :**
- `backend/models/vehicle.py`
- `backend/models/listing.py`
- `backend/models/pattern.py`
- `backend/models/search_session.py`
- `backend/schemas/search.py`
- `backend/schemas/listing.py`
- `backend/schemas/vehicle.py`
- `backend/schemas/pattern.py`

**Acceptance criteria :**
- SQLAlchemy 2.x ORM (DeclarativeBase), pas de legacy Base
- Chaque modèle mappe exactement le DDL de init.sql
- Pas de champ supplémentaire non défini dans l'architecture
- Pydantic v2 (BaseModel)
- Schemas séparés : `XCreate`, `XResponse`, `XUpdate` quand pertinent
- `SearchRequest` : brand, model, price_min, price_max, mileage_max, year_min, horsepower_min, horsepower_max, gearbox, patterns (list[int] = pattern IDs), custom_regex (str | None)
- `ListingResponse` inclut `vehicle: VehicleResponse | None` (peut être null si fiches-auto non trouvé)
- `SearchResult` : session_id, count, listings: list[ListingResponse]

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E2-US1, agent_name=fmc-backend, sprint_id=sprint-2
```

---

## US E2-US2 — Couche DB async (database.py)

**Modèle worker :** `claude-haiku-4.5`

**Fichiers à générer :**
- `backend/db/database.py`
- `backend/db/__init__.py`

**Acceptance criteria :**
- SQLAlchemy async engine : `create_async_engine` avec `aiomysql` driver
- URL : `mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}`
- Toutes les variables via `os.getenv()` avec valeurs par défaut pour dev local
- `AsyncSessionLocal` : `async_sessionmaker`
- Dependency injection FastAPI : `async def get_db() -> AsyncGenerator`
- `requirements.txt` mis à jour : sqlalchemy[asyncio], aiomysql, fastapi, uvicorn, pydantic, httpx, python-dotenv

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E2-US2, agent_name=fmc-backend, sprint_id=sprint-2
```

---

## US E2-US3 — POST /search endpoint

**Modèle worker :** `claude-sonnet-4.6` (logique async complexe + upsert)

**Fichiers à générer :**
- `backend/routers/search.py`
- `backend/services/search_service.py`

**Acceptance criteria :**
- `POST /search` accepte `SearchRequest`, retourne `SearchResult`
- Appel async au scraper : `httpx.AsyncClient` vers `{SCRAPER_URL}/scrape` (timeout 120s)
- Si scraper timeout ou erreur → retourne `{"error": "scraper_unavailable", "listings": []}`
- Upsert listings : `INSERT ... ON DUPLICATE KEY UPDATE` sur `lbc_id`
- Pour chaque listing : lookup `vehicle` par brand+model dans BDD
  - Si absent : appel scraper `GET /vehicle-info` → insert dans `vehicles`
  - Si scraper fiches-auto échoue : `vehicle_id = NULL`, pas de blocage
- Crée `search_session` avec filters JSON + count résultats
- Retourne listings enrichis avec vehicle data

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E2-US3, agent_name=fmc-backend, sprint_id=sprint-2
```

---

## US E2-US4 — GET /listings + /vehicles + CRUD /patterns

**Modèle worker :** `claude-haiku-4.5`

**Fichiers à générer :**
- `backend/routers/listings.py`
- `backend/routers/vehicles.py`
- `backend/routers/patterns.py`
- `backend/main.py`

**Acceptance criteria :**
- `GET /listings?session_id=X&page=1&limit=20` → paginated ListingResponse
- `GET /vehicles?brand=X&model=Y` → VehicleResponse ou 404
- `GET /patterns` → list[PatternResponse]
- `POST /patterns` : valide regex avec `re.compile()` avant save — retourne 422 si invalide
- `DELETE /patterns/{id}` : interdit sur `is_default=True` patterns → 403
- `GET /health` → `{"status": "ok"}` (utilisé par Docker health check)
- `main.py` : FastAPI app, monte tous les routers avec prefix `/api` pour cohérence Traefik
- CORS : autorise `*` en dev (configurable par env var `CORS_ORIGINS`)

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E2-US4, agent_name=fmc-backend, sprint_id=sprint-2
```

---

## Gate Sprint 2

Après chaque US, exécuter :
```
Read: {project-root}/_byan/workflows/fmc/gate-workflow.md
```

Après E2-US4 :
```
SPRINT 2 TERMINÉ — Backend généré.

Prochaine étape : Sprint 3 — Frontend
Read: {project-root}/_byan/workflows/fmc/sprints/sprint-3-frontend.md

[BYAN] Valider avant de lancer Sprint 3 ?
```
