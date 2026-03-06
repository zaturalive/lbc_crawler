# 📋 SOMMAIRE — backend-context.md
> ⚡ LIS CE SOMMAIRE EN PREMIER. Charge uniquement la section dont tu as besoin.

| Section | Contenu | Ligne |
|---------|---------|-------|
| ENDPOINTS | Toutes les routes FastAPI | ~20 |
| MODELS | Schémas SQLAlchemy + DB | ~55 |
| SEARCH_FLOW | Flux complet d'une recherche | ~90 |
| CONFIG | Variables d'env, connexions | ~115 |
| BUGS | Bugs actifs | ~130 |
| TESTS | Tests existants + à écrire | ~145 |

---

# 🔌 ENDPOINTS

**Port :** 8000 (Docker) / `http://localhost:8000`

### Router : search (`backend/routers/search.py`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/search` | Lance une recherche complète |
| GET | `/search/{session_id}` | Récupère une session |
| GET | `/search/{session_id}/listings` | Listings d'une session |

### Router : admin (`backend/routers/admin.py`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/admin/sync-vehicles` | Lance sync fiches-auto (background) |
| GET | `/admin/sync-status` | Statut du sync |
| POST | `/admin/sync-vehicles/store` | Stocke les véhicules scrappés en DB |

### Schemas Pydantic

**SearchRequest**
```python
brand: str
model: str
price_min: Optional[float] = None
price_max: Optional[float] = None
mileage_max: Optional[float] = None
year_min: Optional[int] = None
horsepower_min: Optional[int] = None
horsepower_max: Optional[int] = None
gearbox: Optional[str] = None  # "manual" | "automatic"
extra_patterns: Optional[List[str]] = []
```

---

# 🗃️ MODELS

**Fichier :** `backend/models/__init__.py` (SQLAlchemy async)

### Table `vehicles`
```
id (int PK), brand (str), model (str),
reliability_score (float 0-10), known_issues (JSON),
year_start (int), year_end (int),
created_at, updated_at
```
⚠️ **Manque UNIQUE KEY sur (brand, model)** — upserts peuvent créer des doublons

### Table `listings`
```
id (int PK), lbc_id (str UNIQUE), brand, model,
title, description, price (float), mileage (float),
year (int), gearbox (str), horsepower (float),
city, url, matched_patterns (JSON), reliability_score (float),
search_session_id (FK), created_at, updated_at
```

### Table `regex_patterns`
```
id (int PK), name (str), pattern (str), is_active (bool)
```
7 patterns par défaut : CT valide, non-fumeur, garage, premiere main, etc.

### Table `search_sessions`
```
id (int PK), brand, model, filters (JSON),
status (str), results_count (int), created_at, updated_at
```

### Schéma DB
**Fichier :** `infra/db/init.sql`  
DB : `find_my_car` | User : `fmc` | Password : `devpassword`

---

# 🔄 SEARCH_FLOW

**Fichier :** `backend/services/search_service.py`

```
POST /search
  └─ create SearchSession (DB)
  └─ _call_scraper() → POST http://scraper:8001/scrape
      └─ retourne {"listings": [...], "count": N}
  └─ load regex_patterns actifs (DB)
  └─ pour chaque listing:
      └─ _apply_regex(listing, patterns) → matched_patterns[]
      └─ _resolve_vehicle(brand, model) → vehicle DB lookup
      └─ enrichissement avec reliability_score
      └─ filtre HP (horsepower_min/max) ← seul filtre appliqué ici
  └─ upsert listings (DB)
  └─ update SearchSession (results_count, status="done")
  └─ retourne ListingsResponse
```

### _call_scraper()
```python
async def _call_scraper(filters: SearchFilters) -> list:
    resp = await client.post("http://scraper:8001/scrape", json=payload)
    raw = resp.json()
    return raw.get("listings", raw) if isinstance(raw, dict) else raw
```

### _resolve_vehicle()
```python
async def _resolve_vehicle(brand, model) -> Optional[Vehicle]:
    # DB lookup only (pas de scrape à la volée)
    return await Vehicle.query.filter_by(brand=brand, model=model).first()
```

---

# ⚙️ CONFIG

**Fichier :** `backend/config.py` (ou env vars dans docker-compose.dev.yml)

| Variable | Valeur dev | Description |
|----------|------------|-------------|
| `DATABASE_URL` | `mysql+aiomysql://fmc:devpassword@mariadb:3306/find_my_car` | |
| `SCRAPER_URL` | `http://scraper:8001` | URL interne Docker |
| `DEBUG` | `true` | |

---

# 🐛 BUGS ACTIFS

| ID | Description | Priorité |
|----|-------------|----------|
| BUG-04 | Table `vehicles` manque UNIQUE KEY (brand, model) → doublons possibles | 🔴 HIGH |
| BUG-05 | Filtres HP (horsepower) post-scraping : si scraper ne renvoie pas le champ, le filtre est silencieusement ignoré | 🟡 MEDIUM |
| BUG-06 | `_resolve_vehicle` : lookup case-sensitive sur brand/model (Renault ≠ renault) | 🟡 MEDIUM |

---

# 🧪 TESTS

**Existants :**
- `backend/tests/test_search.py` — coverage faible

**À écrire (priorité) :**
- `test_search_service.py` : mock scraper + DB, teste `run_search()`, filtres HP, regex matching
- `test_admin_routes.py` : teste sync-vehicles + store
- `test_search_routes.py` : teste POST /search, GET /search/{id}/listings

**Framework :** pytest + pytest-asyncio + httpx (TestClient async)
