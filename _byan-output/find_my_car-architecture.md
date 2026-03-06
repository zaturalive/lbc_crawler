# Architecture Technique — find_my_car
*Généré par BYAN après interview. Validé par Yan. 2026-03-05.*

---

## Vision

Agrégateur d'annonces automobiles self-hosted. L'utilisateur filtre des milliers d'annonces LBC en quelques clics et obtient une dizaine de résultats pertinents enrichis des données fiabilité fiches-auto.fr.

---

## Contraintes

| Contrainte | Décision |
|---|---|
| Hébergement | Raspberry Pi (self-hosted) |
| Pas de cloud DB | MariaDB dans Docker local |
| Utilisateurs | Non-techniques, interface simple |
| Auth | Aucune (MVP) — à ajouter si exposition publique |
| Rate limiting LBC | Simple (délais entre requêtes) |
| POC existant | Ignoré — full rewrite |

---

## Stack Technique

| Couche | Techno | Justification |
|---|---|---|
| Frontend | React (SPA) | UI paramétrage + résultats |
| Backend API | FastAPI (Python) | Léger, async, dockerisable |
| Scraping | Python + lib `lbc` + requests/BS4 | POC validé, adapté Pi |
| Base de données | MariaDB (Docker) | SQL classique, self-hosted |
| Reverse proxy | Traefik | Auto-discovery Docker, SSL |
| Containerisation | Docker Compose | Multi-services Pi |
| Registry | Docker Registry self-hosted (Pi) | Stockage images local |
| CI/CD | GitHub Actions | Build → push → deploy |

---

## Architecture Applicative

```
Internet
    │
    ▼
[Traefik] ←─ SSL + routing
    ├──► [React (Nginx)] :80     → frontend
    └──► [FastAPI] :8000          → API
              │
              ├──► [MariaDB] :3306
              └──► [Scraper Service] (internal)
                        ├──► LBC API (externe)
                        └──► fiches-auto.fr (externe)

[Docker Registry] :5000  ← GitHub Actions push
```

---

## Structure du Projet

```
find_my_car/
├── scraper/
│   ├── lbc_scraper.py          # Scraping LBC via lib lbc
│   ├── fiches_auto_scraper.py  # Scraping fiches-auto.fr
│   ├── regex_engine.py         # Gestion patterns/regex
│   ├── requirements.txt
│   └── Dockerfile
├── backend/
│   ├── main.py
│   ├── routers/
│   │   ├── search.py           # POST /search → lance scraping
│   │   ├── listings.py         # GET /listings → résultats BDD
│   │   ├── vehicles.py         # GET /vehicles → données fiches-auto
│   │   └── patterns.py         # CRUD regex patterns
│   ├── models/
│   │   ├── listing.py
│   │   ├── vehicle.py
│   │   └── pattern.py
│   ├── db/
│   │   └── database.py         # SQLAlchemy + MariaDB
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchForm.jsx   # Formulaire critères
│   │   │   ├── ListingCard.jsx  # Carte annonce
│   │   │   ├── VehicleScore.jsx # Score fiabilité + pannes
│   │   │   └── PatternSelector.jsx # Cases à cocher + regex custom
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   └── Results.jsx
│   │   └── api/
│   │       └── client.js
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── traefik/
│   │   └── traefik.yml
│   └── db/
│       └── init.sql
└── .github/
    └── workflows/
        ├── build-scraper.yml
        ├── build-backend.yml
        ├── build-frontend.yml
        └── deploy.yml
```

---

## Schéma Base de Données

### `vehicles` — Données fiches-auto.fr
```sql
CREATE TABLE vehicles (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    brand       VARCHAR(100) NOT NULL,
    model       VARCHAR(100) NOT NULL,
    year_start  INT,
    year_end    INT,
    reliability_score   TINYINT,          -- /10
    common_issues       TEXT,             -- JSON array
    fuel_type   VARCHAR(50),
    scraped_at  DATETIME DEFAULT NOW(),
    INDEX idx_brand_model (brand, model)
);
```

### `listings` — Annonces LBC
```sql
CREATE TABLE listings (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    lbc_id          VARCHAR(50) UNIQUE,
    title           VARCHAR(255),
    price           INT,
    year            INT,
    mileage         INT,
    horsepower      INT,
    gearbox         ENUM('manual','automatic'),
    location        VARCHAR(100),
    description     TEXT,
    url             VARCHAR(500),
    matched_keywords JSON,               -- patterns déclenchés
    vehicle_id      INT,                 -- FK → vehicles
    scraped_at      DATETIME DEFAULT NOW(),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);
```

### `regex_patterns` — Patterns configurés
```sql
CREATE TABLE regex_patterns (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100),           -- "CT valide", "Carte grise"
    pattern     VARCHAR(500),           -- regex
    description VARCHAR(255),
    is_default  BOOLEAN DEFAULT FALSE,
    created_at  DATETIME DEFAULT NOW()
);
```

### `search_sessions` — Historique recherches
```sql
CREATE TABLE search_sessions (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    filters     JSON,                   -- critères structurés
    patterns    JSON,                   -- patterns sélectionnés
    result_count INT,
    created_at  DATETIME DEFAULT NOW()
);
```

---

## Flux Applicatif

```
1. Utilisateur ouvre find_my_car.local (ou domaine)
2. Remplit SearchForm :
   - Marque / Modèle
   - Prix min/max
   - Kilométrage max
   - Année min
   - Chevaux min/max
   - Cases à cocher patterns (CT, carte grise, etc.)
   - [optionnel] regex custom
3. Clique "Rechercher"
4. POST /search → FastAPI
5. FastAPI → Scraper Service :
   a. Construit URL LBC avec filtres structurés
   b. Scrape pages résultats (délai entre requêtes)
   c. Pour chaque annonce : applique regex sur description
   d. Conserve uniquement les annonces matchant les patterns
   e. Pour chaque annonce retenue : cherche vehicle_id dans BDD
      - Si absent → scrape fiches-auto.fr → insère dans vehicles
   f. Insère listings en BDD
6. FastAPI → retourne les listings enrichis au frontend
7. React affiche :
   - Titre, prix, km, année, chevaux, ville
   - Score fiabilité + top 3 pannes fréquentes
   - Lien LBC direct
8. Utilisateur clique → LBC → achète
```

---

## CI/CD Pipeline

```
Dev push → GitHub
    │
    ▼
GitHub Actions
    ├── Build image (linux/arm64 pour Pi)
    ├── Tag : registry.local:5000/fmc-{service}:sha
    └── Push → Docker Registry sur Pi
    
Pi (deploy.yml trigger)
    └── docker compose pull && docker compose up -d
```

---

## Agents Spécialisés

| Agent | Fichier | Domaine |
|---|---|---|
| fmc-scraper | `_byan/agents/fmc-scraper.md` | Scraping LBC + fiches-auto, regex engine |
| fmc-backend | `_byan/agents/fmc-backend.md` | FastAPI, modèles BDD, endpoints |
| fmc-frontend | `_byan/agents/fmc-frontend.md` | React, composants UI/UX |
| fmc-infra | `_byan/agents/fmc-infra.md` | Docker, Traefik, GitHub Actions, Registry |

Orchestration : **Hermes** dispatche selon le domaine.

---

## Ordre de Build Recommandé

```
Sprint 0 : Infra
  → docker-compose.yml (MariaDB + Traefik + Registry)
  → init.sql
  → GitHub Actions build pipeline

Sprint 1 : Scraper
  → lbc_scraper.py (port POC)
  → fiches_auto_scraper.py
  → regex_engine.py
  → API interne scraper

Sprint 2 : Backend
  → Modèles SQLAlchemy
  → Endpoints /search, /listings, /vehicles, /patterns

Sprint 3 : Frontend
  → SearchForm + PatternSelector
  → Results + ListingCard + VehicleScore

Sprint 4 : Integration & Polish
  → Tests end-to-end
  → Déploiement Pi final
```
