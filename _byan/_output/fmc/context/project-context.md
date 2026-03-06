# 📋 SOMMAIRE — project-context.md
> ⚡ LIS CE SOMMAIRE EN PREMIER. Charge uniquement la section dont tu as besoin.

| Section | Contenu | Ligne |
|---------|---------|-------|
| VISION | But du projet, utilisateurs cibles | ~20 |
| STACK | Technologies utilisées | ~35 |
| ARCHITECTURE | Vue d'ensemble des services | ~50 |
| CONTRAINTES | Règles absolues du projet | ~70 |
| ÉTAT ACTUEL | Ce qui fonctionne / ce qui est cassé | ~85 |
| MODÈLES IA | Quel agent utilise quel modèle | ~105 |
| TESTS | Politique de tests | ~115 |

---

# 🎯 VISION

**Projet :** find_my_car  
**Propriétaire :** Dimitry  
**But :** Automatiser la recherche de voitures d'occasion sur LeBonCoin. Filtrage intelligent par marque/modèle/prix/km/année/boîte + détection de mots-clés dans les annonces (CT valide, non-fumeur, etc.) + score de fiabilité depuis fiches-auto.fr.

**Utilisateurs cibles :** Dimitry + entourage qui galèrent à chercher une voiture. Outil perso, pas SaaS.

**Phrase fondatrice :** *"Je fais ça pour moi et pour tout ceux qui m'entourent et qui galèrent."*

---

# 🛠️ STACK

| Couche | Techno | Version |
|--------|--------|---------|
| Frontend | React | 18 |
| Backend API | FastAPI (Python) | 3.11 |
| Scraper | FastAPI (Python) | 3.11 |
| Base de données | MariaDB | 11 |
| Reverse proxy | Traefik | v3.0 |
| Conteneurisation | Docker + Compose | - |
| CI/CD | GitHub Actions | ARM64 (Raspberry Pi) |
| ORM | SQLAlchemy async | - |

---

# 🏗️ ARCHITECTURE

```
[Browser] → React :3000
    ↓ POST /search
[Backend FastAPI] :8000
    ↓ POST /scrape
[Scraper FastAPI] :8001
    ↓ lbc-python lib
[LeBonCoin] (externe)

[Backend] ↔ [MariaDB] :3306
    - vehicles (fiches-auto.fr, refresh mensuel)
    - listings (annonces LBC, upsert à chaque search)
    - regex_patterns (mots-clés configurables)
    - search_sessions (historique)

[POST /admin/sync-vehicles] → scraper bulk fiches-auto → stockage DB
```

**Fichiers clés :**
- `scraper/lbc_scraper.py` — scraping LBC
- `scraper/fiches_auto_scraper.py` — scraping fiches-auto (bulk)
- `scraper/main.py` — API scraper
- `backend/services/search_service.py` — orchestration recherche
- `backend/models/__init__.py` — modèles SQLAlchemy
- `infra/docker-compose.dev.yml` — stack dev locale

---

# ⛔ CONTRAINTES (RÈGLES ABSOLUES)

1. **Tests obligatoires** — chaque feature doit avoir des tests (pytest backend/scraper, jest frontend)
2. **Workers = Haiku** — agents d'exécution sur `claude-haiku-4.5`
3. **Conception = Sonnet** — agents de réflexion sur `claude-sonnet-4.6`
4. **Sommaires en tête de fichier** — tout fichier de contexte/doc doit avoir un sommaire avec numéros de lignes
5. **Pas de charge totale** — les agents lisent le sommaire, puis chargent uniquement la section utile
6. **Délégation stricte** — un agent ne fait pas le travail d'un autre (l'analyste n'écrit pas de code, etc.)
7. **Semi-auto** — validation humaine aux étapes critiques (archi, prod)
8. **Rate limiting scraper** — 1.5s entre requêtes fiches-auto, 1-2s pour LBC
9. **Pas de registry Docker** — dev local uniquement pour l'instant

---

# 🔦 ÉTAT ACTUEL

### ✅ Fonctionne
- Stack Docker (4 services : mariadb, scraper, backend, frontend)
- Recherche LBC : texte `brand + model` → `category=VEHICULES_VOITURES`
- 175 annonces retournées pour "Renault Clio"
- Frontend accessible `http://localhost:3000`
- Backend API `http://localhost:8000`
- Admin sync-vehicles déclenché (fiches-auto en cours de scraping)

### ⚠️ Problèmes connus
- **Filtres non appliqués côté scraper** : prix/km/année envoyés dans payload mais non utilisés dans la requête lbc.Client — les annonces hors-critères passent
- **Fiabilité toujours N/A** : DB `vehicles` vide (sync en cours, ~30min)
- **Tests incomplets** : `test_lbc_scraper.py` et `test_search_e2e.py` existent mais coverage faible
- **Frontend** : aucun test jest

### 🚧 À faire (priorité)
1. Appliquer les filtres prix/km/année/boîte dans `lbc_scraper.py`
2. Attendre fin sync fiches-auto → vérifier scores
3. Écrire tests complets backend + scraper
4. Écrire tests frontend (jest)

---

# 🤖 MODÈLES IA

| Agent | Rôle | Modèle |
|-------|------|--------|
| Hermes | Dispatcher / réflexion | `claude-sonnet-4.6` |
| BYAN | Conception agents | `claude-sonnet-4.6` |
| PM, Architect, SM | Planification | `claude-sonnet-4.6` |
| fmc-backend | Worker dev backend | `claude-haiku-4.5` |
| fmc-scraper | Worker dev scraper | `claude-haiku-4.5` |
| fmc-frontend | Worker dev frontend | `claude-haiku-4.5` |
| fmc-infra | Worker dev infra | `claude-haiku-4.5` |
| Tea, Quinn | Worker tests | `claude-haiku-4.5` |

---

# 🧪 POLITIQUE DE TESTS

- **Chaque feature** → tests obligatoires avant merge
- **Backend** : pytest, couvre les endpoints + services
- **Scraper** : pytest, mock HTTP, teste parsing + filtres
- **Frontend** : jest + react-testing-library, teste composants + appels API
- **E2E** : à définir (playwright si besoin)
- **Règle** : 0 feature sans test. L'agent de test valide avant que Dev marque "done".
