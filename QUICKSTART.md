# find_my_car — État du projet & Guide de démarrage

> Généré le 2026-03-06 | Stack : React · FastAPI · MariaDB · Docker · Traefik

---

## Ce qui a été construit

### Architecture

```
find_my_car/
├── frontend/          → React (SearchForm, PatternSelector, ListingCard, VehicleScore)
├── backend/           → FastAPI async + SQLAlchemy 2.x + MariaDB
├── scraper/           → FastAPI + LBC scraper + fiches-auto.fr + regex engine
├── infra/             → Docker Compose (dev + prod) + Traefik + MariaDB DDL
└── .github/workflows/ → CI/CD GitHub Actions (build ARM64 + deploy SSH)
```

### Services Docker

| Service | Image | Port exposé | Rôle |
|---------|-------|-------------|------|
| `fmc-frontend` | build depuis `./frontend` | `3000` (dev) / `80` (prod via Traefik) | React SPA |
| `fmc-backend` | build depuis `./backend` | `8000` (dev) / interne (prod) | API FastAPI |
| `fmc-scraper` | build depuis `./scraper` | interne uniquement | Scraping LBC + fiches-auto |
| `fmc-mariadb` | `mariadb:11` | `3306` (dev) / interne (prod) | Base de données |
| `fmc-registry` | `registry:2` | `5000` | Registry Docker self-hosted (prod) |
| `fmc-traefik` | `traefik:v3.0` | `80`, `8080` | Reverse proxy (prod) |

### Base de données (MariaDB)

4 tables — `infra/db/init.sql` :

- `vehicles` — marque, modèle, score fiabilité, pannes fréquentes (source fiches-auto.fr)
- `listings` — annonces LBC (prix, km, année, URL, description)
- `regex_patterns` — patterns de filtrage (7 patterns par défaut insérés)
- `search_sessions` — historique des recherches

**7 patterns par défaut :** CT valide · Carte grise · Premier propriétaire · Carnet entretien · Factures garage · Non fumeur · Révision récente

### API Backend (FastAPI)

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/search` | Lance un scraping + filtre + retourne les résultats |
| `GET` | `/listings` | Annonces paginées en base |
| `GET` | `/vehicles` | Données fiabilité véhicule |
| `GET/POST/DELETE` | `/patterns` | Gestion des regex patterns |
| `GET` | `/health` | Healthcheck |

### Frontend React

- **SearchForm** — filtres marque/modèle/prix/km/année/chevaux/boîte
- **PatternSelector** — checkboxes patterns pré-définis + mode avancé regex custom
- **ListingCard** — affichage annonce avec badges (prix, km, année)
- **VehicleScore** — score fiabilité coloré + top 3 pannes fréquentes
- **ResultsGrid** — grille résultats + spinner + état vide

### Tests

- `scraper/tests/test_regex_engine.py` — 12 cas de test
- `scraper/tests/test_lbc_scraper.py` — tests LBC mockés
- `backend/tests/test_search_e2e.py` — 7 tests e2e (SQLite in-memory)

### CI/CD (GitHub Actions)

- `.github/workflows/build-scraper.yml` — build image ARM64 + push registry
- `.github/workflows/build-backend.yml` — idem backend
- `.github/workflows/build-frontend.yml` — idem frontend
- `.github/workflows/deploy.yml` — deploy SSH vers Raspberry Pi

---

## Lancer le site en local (DEV)

### Pré-requis

- Docker + Docker Compose installés
- Ports libres : `3000`, `8000`, `3306`

### Commandes

```bash
# 1. Se placer dans le dossier infra
cd infra/

# 2. Lancer tous les services (build depuis les sources)
docker compose -f docker-compose.dev.yml up --build

# La première fois : ~3-5 min (npm install + pip install dans les images)
# Les fois suivantes : ~30 secondes (cache Docker)
```

### Accès

| Service | URL |
|---------|-----|
| **Frontend (site)** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API docs (Swagger)** | http://localhost:8000/docs |
| **MariaDB** | localhost:3306 (user: `fmc`, pass: `devpassword`) |

### Arrêter

```bash
docker compose -f docker-compose.dev.yml down

# Tout supprimer (volumes inclus — repart de zéro)
docker compose -f docker-compose.dev.yml down -v
```

### Voir les logs

```bash
# Tous les services
docker compose -f docker-compose.dev.yml logs -f

# Un service spécifique
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f scraper
docker compose -f docker-compose.dev.yml logs -f frontend
```

---

## Lancer en production (Raspberry Pi)

### Pré-requis Pi

Voir `infra/pi-setup.md` pour l'installation complète.

```bash
# 1. Copier l'env
cp infra/.env.example infra/.env
# Éditer infra/.env : DOMAIN, DB_PASSWORD, DB_ROOT_PASSWORD, REGISTRY_URL

# 2. Builder et pousser les images vers le registry
docker buildx build --platform linux/arm64 -t localhost:5000/fmc-frontend:latest ./frontend --push
docker buildx build --platform linux/arm64 -t localhost:5000/fmc-backend:latest ./backend --push
docker buildx build --platform linux/arm64 -t localhost:5000/fmc-scraper:latest ./scraper --push

# 3. Déployer
cd infra/
docker compose up -d
```

### Accès prod

- Site : `http://VOTRE_DOMAINE` (configurer `DOMAIN` dans `.env`)
- Traefik dashboard : `http://IP_PI:8080`

---

## Ce qui reste à faire

### Priorité haute

- [ ] **Tester le scraper LBC** — l'API `lbc` (lib Python) peut avoir changé depuis le POC. Vérifier que `lbc.Client.search()` retourne toujours le bon format.
- [ ] **Tester fiches-auto.fr** — les sélecteurs CSS sont best-effort. Valider sur un vrai véhicule (ex: Renault Clio).
- [ ] **Variables d'environnement prod** — remplir `infra/.env` avec les vraies valeurs avant deploy Pi.

### Priorité moyenne

- [ ] **GitHub Actions secrets** — configurer dans le repo GitHub : `REGISTRY_URL`, `PI_HOST`, `PI_USER`, `PI_SSH_KEY`, `DB_PASSWORD`, `DB_ROOT_PASSWORD`
- [ ] **Nom de domaine / DNS local** — configurer le router pour pointer le domaine vers le Pi, ou utiliser `/etc/hosts` pour les tests locaux.
- [ ] **HTTPS** — ajouter Let's Encrypt dans `traefik.yml` pour un vrai certificat SSL en prod.

### Priorité basse (futures features)

- [ ] **Auth simple** — HTTP Basic Auth via Traefik middleware (1 ligne de config) pour protéger l'accès.
- [ ] **Pagination infinie** — le ResultsGrid charge tout d'un coup, ajouter un "load more".
- [ ] **Notifications** — email/webhook quand une nouvelle annonce match les critères.
- [ ] **Scraping planifié** — cron job Docker pour refresh automatique toutes les N heures.
- [ ] **Comparateur** — sélectionner plusieurs annonces et les comparer côte à côte.

---

## Fichiers clés

| Fichier | Rôle |
|---------|------|
| `infra/docker-compose.dev.yml` | **Démarrage local** — build depuis sources |
| `infra/docker-compose.yml` | Deploy prod (images depuis registry) |
| `infra/db/init.sql` | DDL MariaDB + 7 patterns par défaut |
| `infra/traefik/traefik.yml` | Config reverse proxy prod |
| `scraper/regex_engine.py` | Moteur de filtrage par regex |
| `scraper/lbc_scraper.py` | Client LBC scraper |
| `scraper/fiches_auto_scraper.py` | Scraper fiches-auto.fr (cache 7j) |
| `backend/services/search_service.py` | Orchestration scraper + BDD |
| `frontend/src/api/client.js` | Client HTTP centralisé |
| `_byan-output/find_my_car-architecture.md` | Architecture complète du projet |

---

## Commande de démarrage rapide (TL;DR)

```bash
cd infra && docker compose -f docker-compose.dev.yml up --build
```

Puis ouvrir : **http://localhost:3000**
