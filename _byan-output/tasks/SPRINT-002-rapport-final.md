# 🏁 RAPPORT SPRINT 002 — find_my_car
**Date :** 2026-03-06  
**Orchestrateur :** Hermes (claude-sonnet-4.6)  
**Statut :** ✅ 6/6 TÂCHES COMPLÉTÉES

---

## 📊 RÉSULTATS

| Task | Fix | Avant | Après |
|------|-----|-------|-------|
| Fiabilité N/A | `_resolve_vehicle` fuzzy LIKE match | 0/175 scores | **350/350 scores** ✅ |
| 175 annonces | `LBC_MAX_PAGES` 5 → 10 | 175 | **350** ✅ |
| Filtrage mots-clés | Exclure si `matched_keywords` vide | Tout affiché | **Seulement ceux qui matchent** ✅ |
| Frontend moche | Docker rebuild `--no-cache` | Cache ancien | **Tailwind + shadcn actif** ✅ |
| WebDB UI | Ajout service `webdb/app` | - | **http://localhost:22072** ✅ |
| Données protégées | Volume nommé confirmé | - | **`mariadb_dev_data` sécurisé** ✅ |

---

## 🔧 MODIFICATIONS TECHNIQUES

### `backend/services/search_service.py`
1. **`_resolve_vehicle` — 3 niveaux de match :**
   - Exact match avec score (priorité)  
   - Fuzzy: `LOWER(brand) == brand AND LOWER(model) LIKE %model%` avec score  
   - Fallback exact sans filtre score
2. **Filtre mots-clés :** `if pattern_ids: upserted = [l for l in upserted if l.matched_keywords]`
3. Import `func` de SQLAlchemy ajouté

### `infra/docker-compose.dev.yml`
- `LBC_MAX_PAGES=10` ajouté pour le scraper
- `LBC_RATE_MIN=1.0`, `LBC_RATE_MAX=2.0` explicités
- Service `webdb` ajouté (port 22072:22071)

---

## 🌐 SERVICES ACTIFS

| Service | URL | Statut |
|---------|-----|--------|
| Frontend (shadcn/ui) | http://localhost:3000 | ✅ Healthy |
| Backend API | http://localhost:8000 | ✅ Healthy |
| Scraper | http://localhost:8001 | ✅ Healthy |
| MariaDB | localhost:3306 | ✅ Healthy |
| WebDB UI | http://localhost:22072 | ✅ Running |

---

## 🗄️ CONNEXION WEBDB

Dans WebDB (http://localhost:22072) :
- **Driver :** MySQL/MariaDB
- **Host :** mariadb (ou 127.0.0.1 si accès local)
- **Port :** 3306
- **Database :** find_my_car
- **User :** fmc
- **Password :** devpassword

---

## ✅ DONNÉES PROTÉGÉES

- Volume `mariadb_dev_data` confirmé → données persistantes
- **490 véhicules** en DB, **264 avec scores** — aucune perte
- Sync fiches-auto : `last_count: 627` (dernière exécution)
- Le sync utilise `ON DUPLICATE KEY UPDATE` → safe à relancer

---

## 🔴 PROBLÈMES RESTANTS

| ID | Description | Priorité |
|----|-------------|----------|
| PERF-01 | 490 vehicles en DB mais seulement 264 avec scores → relancer sync partiel | 🟡 |
| TEST-WIP | 32 tests frontend en WIP (SearchForm, UI, API client) | 🟡 |
| BUG-06 | Lookup case-sensitive → résolu par fuzzy mais idéalement normaliser brand/model à l'ingestion | 🟢 |

