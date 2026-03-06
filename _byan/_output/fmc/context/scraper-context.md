# 📋 SOMMAIRE — scraper-context.md
> ⚡ LIS CE SOMMAIRE EN PREMIER. Charge uniquement la section dont tu as besoin.

| Section | Contenu | Ligne |
|---------|---------|-------|
| LBC_SCRAPER | Architecture, filtres, problèmes connus | ~20 |
| FICHES_AUTO | Bulk scraper, URLs, structure | ~65 |
| API_ENDPOINTS | Endpoints FastAPI du scraper | ~110 |
| TESTS | Tests existants + à écrire | ~130 |
| BUGS | Bugs actifs à corriger | ~145 |

---

# 🕷️ LBC_SCRAPER

**Fichier :** `scraper/lbc_scraper.py`

### Fonctionnement actuel
- Utilise la lib Python `lbc` (non-officielle)
- Recherche par `text="brand model"` + `category=VEHICULES_VOITURES`
- `lbc.Client.search()` retourne un objet `Search`, pas une liste — itérer via `.ads`
- Rate limit : 1.0–2.0s entre pages (env `LBC_RATE_MIN`, `LBC_RATE_MAX`)
- Max pages : 5 (env `LBC_MAX_PAGES`)

### Structure `SearchFilters` (dataclass)
```python
brand, model, price_min, price_max, mileage_max, year_min,
horsepower_min, horsepower_max, gearbox, extra_patterns
```

### Attributs d'une annonce LBC (`Ad`)
| Attribut | Type | Note |
|----------|------|------|
| `ad.id` | str | ID unique LBC |
| `ad.subject` | str | Titre annonce |
| `ad.body` | str | Description |
| `ad.price` | float | FLOAT, pas string |
| `ad.url` | str | URL annonce |
| `ad.location` | Location obj | `.city` ou `.city_label` |
| `ad.attributes` | List[Attribute] | `.key` + `.value` |

### Clés d'attributs voiture
`brand`, `model`, `regdate`, `mileage`, `gearbox` (1=manuelle/2=auto), `horse_power_din`

### ⚠️ BUG ACTIF — Filtres non appliqués
`price_min/max`, `mileage_max`, `year_min`, `gearbox` sont dans `SearchFilters` mais **non passés à `lbc.Client.search()`**.  
La lib `lbc` supporte : `price` (tuple), `mileage` (tuple), `regdate` (str "YYYY-max").  
**À corriger en priorité.**

### Filtrage post-scraping (contournement temporaire)
`horsepower_min/max` filtrés côté backend (`search_service.py` ligne ~44).

---

# 📰 FICHES_AUTO

**Fichier :** `scraper/fiches_auto_scraper.py`

### Architecture bulk
1. `scrape_all_brands()` → GET `https://www.fiches-auto.fr/fiabilite-auto/` → liste URLs marques
2. `scrape_brand_models(brand_url)` → GET brand page → liste modèles avec URL
3. `scrape_vehicle_page(url, brand_slug)` → GET page modèle → score + problèmes + années
4. `bulk_scrape_vehicles()` → itère tout → retourne liste dicts

### URL patterns fiches-auto
- Base : `https://www.fiches-auto.fr`
- Toutes marques : `/fiabilite-auto/`
- Marque : `/fiabilite-{brand}/`
- Modèle : `/fiabilite-{brand}/fiabilite-{id}-pannes-{brand}-{model}.php`

### Extraction données
| Donnée | Sélecteur CSS / méthode |
|--------|------------------------|
| Score fiabilité | `td.verre_chiffres_cellules` — 1er float valide |
| Conversion score | `max(0, round(10 - val/5))` → échelle 0-10 |
| Années | Regex `(\d{4})[^\d]+(\d{4})` dans `<title>` |
| Problèmes connus | `<p>` après `<h2>` contenant "connus" |

### Rate limit
1.5s entre requêtes (`RATE_LIMIT = 1.5`)

### Durée sync complète
~25-35 min (38 marques × ~51 modèles × 1.5s)

---

# 🔌 API_ENDPOINTS

**Fichier :** `scraper/main.py` — FastAPI port 8001

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Healthcheck + sync_status |
| POST | `/scrape` | Scrape LBC, retourne `{"listings": [...], "count": N}` |
| POST | `/scrape/vehicles-catalog` | Lance bulk fiches-auto (background) |
| GET | `/scrape/vehicles-status` | Statut sync : running/done/error/idle |

### Payload POST /scrape
```json
{
  "brand": "Renault", "model": "clio",
  "price_min": 1000, "price_max": 5000,
  "mileage_max": 150000, "year_min": 2010,
  "horsepower_min": null, "horsepower_max": null,
  "gearbox": "manual",
  "patterns": [{"name": "CT valide", "pattern": "..."}],
  "custom_regex": null
}
```

---

# 🧪 TESTS

**Existants :**
- `scraper/tests/test_lbc_scraper.py` — coverage faible
- `scraper/tests/test_regex_engine.py` — OK

**À écrire (priorité) :**
- `test_lbc_scraper.py` : mock `lbc.Client`, teste filtres appliqués, teste `_parse_ad`
- `test_fiches_auto_scraper.py` : mock HTTP (responses), teste extraction score/années/problèmes
- `test_scraper_api.py` : teste endpoints `/scrape` et `/scrape/vehicles-catalog`

**Framework :** pytest + `pytest-asyncio` + `responses` (mock HTTP)

---

# 🐛 BUGS ACTIFS

| ID | Description | Fichier | Priorité |
|----|-------------|---------|----------|
| BUG-01 | Filtres prix/km/année/boîte non appliqués à lbc.Client | `lbc_scraper.py` | 🔴 HIGH |
| BUG-02 | `lbc.model.enums.OwnerType` peut ne pas exister selon version lib | `lbc_scraper.py` | 🟡 MEDIUM |
| BUG-03 | `scrape_vehicle_page` : brand_name extrait depuis slug peut être mal formaté | `fiches_auto_scraper.py` | 🟡 MEDIUM |
