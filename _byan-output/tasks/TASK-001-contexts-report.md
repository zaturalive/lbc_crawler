# 📄 RAPPORT TÂCHE — TASK-001
**Date :** 2025-07-21  
**Tâche :** Création des 5 fichiers de contexte find_my_car  
**Exécuté par :** Copilot CLI (claude-sonnet-4.6) via 4 workers parallèles  
**Statut :** ✅ TERMINÉ

---

## 🎯 Objectif

Créer les fichiers de contexte structurés pour que les agents IA puissent intervenir sur le projet sans charger la totalité du codebase.

---

## ✅ Fichiers créés

| Fichier | Emplacement | Statut |
|---------|-------------|--------|
| `project-context.md` | `_byan/_output/fmc/context/` | ✅ Créé |
| `scraper-context.md` | `_byan/_output/fmc/context/` | ✅ Créé |
| `backend-context.md` | `_byan/_output/fmc/context/` | ✅ Créé |
| `frontend-context.md` | `_byan/_output/fmc/context/` | ✅ Créé |
| `infra-context.md` | `_byan/_output/fmc/context/` | ✅ Créé |

---

## 📋 Contenu par contexte

### project-context.md
- Vision du projet (Dimitry, entourage, find_my_car)
- Stack complète (React, FastAPI, MariaDB, Docker, Traefik)
- Architecture des services
- Contraintes absolues (tests, modèles IA, délégation stricte)
- État actuel (ce qui fonctionne, bugs connus)
- Tableau modèles IA : Sonnet pour réflexion, Haiku pour workers
- Politique de tests

### scraper-context.md
- LBC scraper : lib `lbc`, attributs Ad, clés voiture
- **BUG-01 documenté** : filtres prix/km/année non appliqués à lbc.Client
- Fiches-auto : bulk scraper, URLs, sélecteurs CSS
- Endpoints API scraper (port 8001)
- Tests à écrire

### backend-context.md
- Tous les endpoints FastAPI (search + admin routers)
- Schémas Pydantic (SearchRequest)
- Tables SQLAlchemy (vehicles, listings, regex_patterns, search_sessions)
- **BUG-04 documenté** : UNIQUE KEY manquante sur vehicles(brand, model)
- Flux complet POST /search → scraper → regex → DB
- Config et variables d'env

### frontend-context.md
- Stack : React 18, CRA (pas Vite), JS pur
- Composants détectés : SearchForm, ResultsGrid, ListingCard, VehicleScore, PatternSelector
- API client wrapper (`request()`)
- Flux UX complet
- 0 test jest actuellement — liste des tests à écrire

### infra-context.md
- Docker compose : 4 services, ports, credentials
- Commandes usuelles (up, build, logs, DB shell)
- Patterns regex par défaut (7 patterns)
- **BUG-04 fix** : ALTER TABLE vehicles ADD UNIQUE KEY uk_brand_model
- Plan CI/CD GitHub Actions → Raspberry Pi (ARM64)

---

## 🔴 Bugs critiques découverts / confirmés

| ID | Description | Fichier | Priorité |
|----|-------------|---------|----------|
| BUG-01 | Filtres prix/km/année non passés à lbc.Client.search() | `scraper/lbc_scraper.py` | 🔴 HIGH |
| BUG-04 | UNIQUE KEY manquante sur vehicles(brand, model) → doublons | `infra/db/init.sql` | 🔴 HIGH |
| BUG-06 | Lookup brand/model case-sensitive dans _resolve_vehicle | `backend/services/search_service.py` | 🟡 MEDIUM |
| BUG-10 | Pas de volume persistant nommé pour MariaDB | `infra/docker-compose.dev.yml` | 🟡 MEDIUM |

---

## 📌 Prochaines tâches recommandées

1. **TASK-002** — Corriger BUG-01 : appliquer filtres dans `lbc_scraper.py`
2. **TASK-003** — Corriger BUG-04 : UNIQUE KEY dans `init.sql`
3. **TASK-004** — Écrire tests scraper (`test_lbc_scraper.py`, `test_fiches_auto_scraper.py`)
4. **TASK-005** — Écrire tests backend (`test_search_service.py`, `test_admin_routes.py`)
5. **TASK-006** — Écrire tests frontend (jest, react-testing-library)
