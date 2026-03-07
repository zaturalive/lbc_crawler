# find_my_car — Documentation Technique Complète

> Agrégateur d'annonces de voitures d'occasion auto-hébergé.  
> Stack : **React 18 + Tailwind** (frontend) · **FastAPI + SQLAlchemy** (backend) · **MariaDB** (BDD) · **Docker Compose** (infrastructure)

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture](#2-architecture)
3. [Features fonctionnelles](#3-features-fonctionnelles)
4. [Base de données — schéma complet](#4-base-de-données--schéma-complet)
5. [Backend — API REST](#5-backend--api-rest)
6. [Frontend — composants et pages](#6-frontend--composants-et-pages)
7. [Système d'authentification](#7-système-dauthentification)
8. [Système IA](#8-système-ia)
9. [Scraper LeBonCoin](#9-scraper-leboncoin)
10. [Infrastructure Docker](#10-infrastructure-docker)
11. [Variables d'environnement](#11-variables-denvironnement)

---

## 1. Vue d'ensemble

**find_my_car** permet de rechercher des voitures d'occasion sur LeBonCoin avec :
- Filtres avancés (prix, km, année, carburant, boîte, ville + rayon géographique)
- Enrichissement automatique avec les données de fiabilité **fiches-auto.fr**
- Analyse IA des annonces via **GitHub Models (gpt-4o-mini)**
- Système de crédits IA par utilisateur
- Favoris, historique de recherches, historique de fiches consultées

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         NAVIGATEUR                              │
│                    React 18 + Tailwind                          │
│              (port 3000 dev · port 80 prod via Nginx)           │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP REST (fetch)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND FastAPI                               │
│              Python 3.12 · SQLAlchemy async                     │
│                        port 8000                                │
└──────┬──────────────────────────────────────┬───────────────────┘
       │                                      │
       ▼                                      ▼
┌──────────────┐                  ┌─────────────────────────────┐
│   MariaDB    │                  │   SCRAPER FastAPI           │
│  (port 3306) │                  │  Python · httpx · regex     │
│  find_my_car │                  │  port 8001 (interne)        │
└──────────────┘                  └──────────────┬──────────────┘
                                                 │ HTTP
                                                 ▼
                                    LeBonCoin / fiches-auto.fr
                                    GitHub Models API (IA)
```

### Services Docker

| Service         | Image                  | Port    | Rôle                          |
|-----------------|------------------------|---------|-------------------------------|
| `fmc-frontend`  | React/Nginx baked      | 3000    | SPA React                     |
| `fmc-backend`   | Python/FastAPI baked   | 8000    | API REST + logique métier     |
| `fmc-scraper`   | Python baked           | 8001    | Scraping LBC + fiches-auto    |
| `fmc-mariadb`   | mariadb:11             | 3306    | Base de données principale    |
| `fmc-traefik`   | traefik:v3.0           | 80/8080 | Reverse proxy (prod)          |
| `fmc-registry`  | registry:2             | 5000    | Registry Docker local         |

> ⚠️ **Pas de volumes pour le code source** — tout est baked dans les images. Un changement de code = rebuild obligatoire.

---

## 3. Features fonctionnelles

### 3.1 Recherche avancée

- Marque + modèle (auto-complétion à partir du catalogue fiches-auto)
- Fourchette de prix (min / max)
- Fourchette de kilométrage (min / max)
- Année minimum
- Puissance (min / max)
- Boîte de vitesse : manuelle / automatique
- Carburant : essence, diesel, hybride, électrique…
- **Géolocalisation** : ville + rayon en km (résolution via l'API Nominatim/OSM intégrée au scraper)
- Tri : pertinence, prix croissant/décroissant, plus récent, plus ancien
- Limite de résultats : 50 à 600

### 3.2 Patterns regex (mots-clés)

Patterns préconfigurés (défauts actifs) et patterns personnalisés :

| Pattern            | Ce qu'il détecte                          |
|--------------------|-------------------------------------------|
| CT valide          | Contrôle technique valide mentionné       |
| Carte grise        | Carte grise disponible                    |
| Premier propriétaire | 1ère main                               |
| Carnet entretien   | Carnet d'entretien présent                |
| Factures garage    | Factures d'entretien disponibles          |
| Non fumeur         | Véhicule non-fumeur                       |
| Révision récente   | Révision effectuée récemment              |

Les patterns sont appliqués sur le **titre + description** de chaque annonce. Les `matched_keywords` sont stockés en BDD.

### 3.3 Enrichissement fiabilité

Chaque annonce est automatiquement associée à sa fiche fiches-auto.fr (table `vehicles`) via la marque et le modèle. Les données affichées :
- **Score fiabilité** / 100
- Nombre de témoignages
- Top défauts signalés (classés par fréquence)
- Rang dans la catégorie

### 3.4 Filtre de la barre de résultats

La barre de filtres au-dessus des cards permet de filtrer **sans nouvelle requête LBC** :
- Recherche par titre (substring)
- Kilométrage minimum
- Cases à cocher multi-sélection :
  - CT valide
  - Entretien (carnet/factures)
  - 1ère main
  - Révision récente
  - Non fumeur
  - Carte grise
- **✨ Déjà analysée IA** (filtre les annonces pour lesquelles une analyse IA a été faite)
- Bouton **Réinitialiser** (remet tous les filtres à zéro)
- Bouton **✕ Fermer** (supprime les résultats et revient à l'état initial)

### 3.5 Badges sur les cards

Chaque card affiche des badges d'état visibles sous le titre :
- **👁 Vue** (gris/zinc) — l'utilisateur a déjà ouvert cette fiche dans la session courante
- **✨ IA** (violet) — une analyse IA existe pour cette annonce (appartenant à l'utilisateur)
- Badge **❤️** (like) dans la partie basse de la card

### 3.6 Système de likes / favoris

- Like/unlike depuis la card ou la modal
- Persisté en BDD (table `likes`, lié à `user_id`)
- Page **Compte** liste tous les favoris avec détails complets

### 3.7 Historique

- **Historique de recherches** : 20 dernières recherches, paramètres sauvegardés, relance en un clic
- **Fiches consultées** : 20 dernières annonces ouvertes en modal

### 3.8 Analyse IA d'une annonce

Via la modal d'une annonce → onglet **✨ Analyse IA** :
- Analyse basée sur : titre, description, km, année, prix + données de fiabilité du modèle
- Résultat structuré :
  - Résumé état général (4-5 phrases)
  - Réparations/interventions déjà faites (citées dans l'annonce)
  - Points de vigilance et révisions à prévoir
  - Niveau de risque global : `low` / `medium` / `high`

### 3.9 Analyse IA d'une recherche complète

Depuis la page **Historique** → bouton sur une recherche passée :
- Analyse globale du lot d'annonces (jusqu'à 50)
- Synthèse globale, thèmes mentionnés/absents, réparations à prévoir

### 3.10 Système de crédits IA

Quota par utilisateur (configurable) :
- **10 crédits** pour les analyses d'annonces individuelles
- **3 crédits** pour les analyses de recherche globale

Logique de débit (annonce individuelle) :
1. L'user a déjà payé cette annonce → **gratuit** (cache)
2. Quota dépassé → **erreur 429**
3. Cache global disponible (autre user l'a déjà analysé) → **1 crédit débité, 0 appel API**
4. Pas de cache → **1 crédit + appel API réel**

### 3.11 Administration

Page `/admin` protégée par token JWT (admins définis par `ADMIN_USER_IDS`) :
- Liste de toutes les analyses IA (toutes annonces, tous utilisateurs)
- Statistiques d'utilisation
- Déclenchement de scraping de masse (marques/modèles)

---

## 4. Base de données — schéma complet

### `vehicles` — Modèles de véhicules (fiches-auto.fr)

| Colonne              | Type           | Description                                      |
|----------------------|----------------|--------------------------------------------------|
| `id`                 | INT PK AI      |                                                  |
| `brand`              | VARCHAR(100)   | Marque (ex: Toyota)                              |
| `model`              | VARCHAR(100)   | Modèle (ex: Yaris)                               |
| `year_start`         | INT            | Année début de production                        |
| `year_end`           | INT            | Année fin de production (NULL si toujours produit)|
| `reliability_score`  | TINYINT        | Score fiabilité /100                             |
| `total_testimonials` | INT            | Nombre de témoignages sur fiches-auto            |
| `common_issues`      | JSON           | Liste des défauts fréquents avec compteurs       |
| `known_issues_text`  | JSON           | Texte détaillé de chaque défaut                  |
| `source_url`         | VARCHAR(500)   | URL source sur fiches-auto.fr                    |
| `reliability_rank`   | VARCHAR(20)    | Rang de fiabilité (ex: "A+", "B", "C")           |
| `fuel_type`          | VARCHAR(50)    | Type de carburant principal                      |
| `scraped_at`         | DATETIME       | Date de scraping                                 |
| `category`           | VARCHAR(50)    | Catégorie (citadine, berline, SUV…)              |
| `rank_in_category`   | INT            | Rang parmi les voitures de la catégorie          |
| `total_in_category`  | INT            | Total de voitures dans la catégorie              |

**Index** : `uk_brand_model` (UNIQUE sur brand+model), `idx_brand_model`

---

### `listings` — Annonces LeBonCoin

| Colonne           | Type              | Description                                       |
|-------------------|-------------------|---------------------------------------------------|
| `id`              | INT PK AI         |                                                   |
| `lbc_id`          | VARCHAR(50) UNIQ  | ID unique de l'annonce sur LBC                    |
| `title`           | VARCHAR(255)      | Titre de l'annonce                                |
| `price`           | INT               | Prix en euros                                     |
| `year`            | INT               | Année du véhicule                                 |
| `mileage`         | INT               | Kilométrage                                       |
| `horsepower`      | INT               | Puissance en chevaux                              |
| `gearbox`         | ENUM              | `manual` ou `automatic`                           |
| `fuel_type`       | VARCHAR(50)       | Type de carburant                                 |
| `doors`           | INT               | Nombre de portes                                  |
| `seats`           | INT               | Nombre de places                                  |
| `color`           | VARCHAR(50)       | Couleur                                           |
| `location`        | VARCHAR(100)      | Localisation (ville)                              |
| `description`     | TEXT              | Description complète de l'annonce                 |
| `url`             | VARCHAR(500)      | URL de l'annonce sur LBC                          |
| `matched_keywords`| JSON              | Liste des patterns regex correspondants           |
| `images`          | JSON              | Liste d'URLs des images de l'annonce              |
| `vehicle_id`      | INT FK            | Référence vers `vehicles.id` (SET NULL si supprimé)|
| `scraped_at`      | DATETIME          | Date de scraping                                  |

**Index** : `uk_lbc_id` (UNIQUE), `idx_price`, `idx_year`, `idx_mileage`, `idx_scraped_at`

---

### `users` — Comptes utilisateurs

| Colonne              | Type           | Description                             |
|----------------------|----------------|-----------------------------------------|
| `id`                 | INT PK AI      |                                         |
| `email`              | VARCHAR(255) UNIQ | Email de l'utilisateur               |
| `hashed_password`    | VARCHAR(255)   | Mot de passe hashé (bcrypt)             |
| `is_verified`        | BOOLEAN        | Email vérifié ?                         |
| `verification_token` | VARCHAR(100)   | Token de vérification email (one-time)  |
| `created_at`         | DATETIME       |                                         |

---

### `likes` — Favoris

| Colonne      | Type      | Description                              |
|--------------|-----------|------------------------------------------|
| `id`         | INT PK AI |                                          |
| `user_id`    | INT       | ID utilisateur                           |
| `listing_id` | INT FK    | Référence vers `listings.id` (CASCADE)   |
| `created_at` | DATETIME  |                                          |

**Contrainte** : `uk_user_listing` UNIQUE (user_id, listing_id)  
**Index** : `idx_likes_user`, `idx_likes_listing`

---

### `regex_patterns` — Patterns de mots-clés

| Colonne      | Type           | Description                            |
|--------------|----------------|----------------------------------------|
| `id`         | INT PK AI      |                                        |
| `name`       | VARCHAR(100)   | Nom du pattern (ex: "CT valide")       |
| `pattern`    | VARCHAR(500)   | Expression régulière                   |
| `description`| VARCHAR(255)   | Description lisible                    |
| `is_default` | BOOLEAN        | Pattern pré-installé (non supprimable) |
| `created_at` | DATETIME       |                                        |

---

### `search_history` — Historique des recherches

| Colonne       | Type      | Description                                        |
|---------------|-----------|----------------------------------------------------|
| `id`          | INT PK    |                                                    |
| `user_id`     | INT       | ID utilisateur (défaut 1)                          |
| `params`      | JSON      | Paramètres de recherche (SearchRequest complet)    |
| `listing_ids` | JSON      | IDs des annonces retournées (pour analyse IA)      |
| `patterns`    | JSON      | Patterns actifs lors de la recherche               |
| `result_count`| INT       | Nombre de résultats                                |
| `created_at`  | DATETIME  |                                                    |

---

### `viewed_listings` — Fiches consultées

| Colonne      | Type      | Description                              |
|--------------|-----------|------------------------------------------|
| `id`         | INT PK    |                                          |
| `user_id`    | INT       | ID utilisateur (défaut 1)                |
| `listing_id` | INT FK    | Référence vers `listings.id`             |
| `viewed_at`  | DATETIME  | Horodatage de la dernière consultation   |

**Contrainte** : `uk_vl_user_listing` UNIQUE (user_id, listing_id) — upsert sur viewed_at

---

### `requete_ia` — Demandes d'analyse IA (annonce)

| Colonne      | Type           | Description                             |
|--------------|----------------|-----------------------------------------|
| `id`         | INT PK         |                                         |
| `listing_id` | INT FK         | Référence vers `listings.id`            |
| `user_id`    | INT            | User ayant déclenché l'analyse initiale |
| `prompt_text`| TEXT           | Prompt complet envoyé au LLM            |
| `model`      | VARCHAR(100)   | Modèle IA utilisé (ex: gpt-4o-mini)     |
| `status`     | VARCHAR(20)    | `pending` / `done` / `error`            |
| `created_at` | DATETIME       |                                         |

**Relation** : → `reponse_ia` (one-to-one), → `listing` (lazy selectin)

---

### `reponse_ia` — Réponses d'analyse IA (annonce)

| Colonne               | Type        | Description                               |
|-----------------------|-------------|-------------------------------------------|
| `id`                  | INT PK      |                                           |
| `requete_id`          | INT FK UNIQ | Référence vers `requete_ia.id`            |
| `repairs_found`       | JSON        | Liste des réparations citées (list[str])  |
| `upcoming_maintenance`| JSON        | Points de vigilance à prévoir (list[str]) |
| `condition_summary`   | TEXT        | Résumé état général (4-5 phrases)         |
| `risk_level`          | VARCHAR(20) | `low` / `medium` / `high`                 |
| `raw_response`        | TEXT        | Réponse brute du LLM                      |
| `created_at`          | DATETIME    |                                           |

---

### `listing_analysis_users` — Crédits IA par utilisateur/annonce

| Colonne      | Type      | Description                                           |
|--------------|-----------|-------------------------------------------------------|
| `id`         | INT PK AI |                                                       |
| `listing_id` | INT FK    | Référence vers `listings.id` (CASCADE)                |
| `user_id`    | INT FK    | Référence vers `users.id` (CASCADE)                   |
| `used_cache` | BOOLEAN   | TRUE = l'analyse existait déjà (pas d'appel API réel) |
| `created_at` | DATETIME  |                                                       |

**Contrainte** : `uk_lau_listing_user` UNIQUE (listing_id, user_id)  
> Cette table est la source de vérité des crédits consommés. `COUNT(*) WHERE user_id=X` = crédits utilisés.

---

### `analyse_recherche` — Demandes d'analyse IA (recherche globale)

| Colonne       | Type           | Description                               |
|---------------|----------------|-------------------------------------------|
| `id`          | INT PK         |                                           |
| `search_id`   | INT FK UNIQ    | Référence vers `search_history.id`        |
| `user_id`     | INT            | User ayant déclenché l'analyse            |
| `listing_ids` | JSON           | IDs analysés (liste, max 50)              |
| `prompt_text` | TEXT           | Prompt envoyé au LLM                      |
| `model`       | VARCHAR(100)   | Modèle IA utilisé                         |
| `status`      | VARCHAR(20)    | `pending` / `done` / `error`              |
| `created_at`  | DATETIME       |                                           |

---

### `reponse_recherche_ia` — Réponses d'analyse IA (recherche globale)

| Colonne                  | Type        | Description                                |
|--------------------------|-------------|--------------------------------------------|
| `id`                     | INT PK      |                                            |
| `analyse_id`             | INT FK UNIQ | Référence vers `analyse_recherche.id`      |
| `synthese_globale`       | TEXT        | Synthèse narrative du lot d'annonces       |
| `themes_mentionnes`      | JSON        | Thèmes récurrents cités (list[str])        |
| `themes_absents`         | JSON        | Thèmes attendus mais absents (list[str])   |
| `prochaines_reparations` | JSON        | Réparations probables (list[str])          |
| `risk_level`             | VARCHAR(20) | `low` / `medium` / `high`                  |
| `raw_response`           | TEXT        | Réponse brute du LLM                       |
| `created_at`             | DATETIME    |                                            |

---

### `search_sessions` — Sessions de recherche (legacy)

| Colonne       | Type     | Description                                |
|---------------|----------|--------------------------------------------|
| `id`          | INT PK   |                                            |
| `filters`     | JSON     | Filtres de recherche                       |
| `patterns`    | JSON     | Patterns actifs                            |
| `result_count`| INT      | Nombre de résultats                        |
| `created_at`  | DATETIME |                                            |

---

### Diagramme de relations

```
vehicles ─────────────────────────────── listings
                                            │   │   │
                              likes ────────┘   │   │
                   viewed_listings ─────────────┘   │
                  listing_analysis_users ────────────┘
                          │                     │
                       users              requete_ia ── reponse_ia
                                               │
                                    search_history ── analyse_recherche ── reponse_recherche_ia
```

---

## 5. Backend — API REST

Base URL : `http://localhost:8000` (dev)

### 5.1 Authentification — `/auth`

| Méthode | Endpoint              | Auth | Description                                    |
|---------|-----------------------|------|------------------------------------------------|
| POST    | `/auth/register`      | Non  | Inscription. Retourne `verification_token` (dev) |
| POST    | `/auth/verify-email`  | Non  | Vérifie l'email avec le token. Retourne JWT    |
| POST    | `/auth/login`         | Non  | Connexion. Retourne JWT + user                 |
| GET     | `/auth/me`            | JWT  | Retourne l'utilisateur connecté                |

**Réponse login/verify** :
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "email": "...", "is_verified": true }
}
```

---

### 5.2 Recherche — `/search`

| Méthode | Endpoint  | Auth | Description                                    |
|---------|-----------|------|------------------------------------------------|
| POST    | `/search` | Non  | Lance une recherche LBC avec enrichissement    |

**Corps de la requête** (`SearchRequest`) :

```json
{
  "brand": "Toyota",
  "model": "Yaris",
  "price_min": 5000,
  "price_max": 15000,
  "mileage_min": 0,
  "mileage_max": 100000,
  "year_min": 2015,
  "horsepower_min": 70,
  "horsepower_max": 120,
  "gearbox": "automatic",
  "fuel": "hybride",
  "city": "Lyon",
  "radius": 50,
  "sort_by": "price_asc",
  "condition": "good",
  "pattern_ids": [1, 3],
  "custom_regex": "\\bgarage\\b",
  "limit": 100
}
```

**Réponse** :
```json
{
  "session_id": 42,
  "history_id": 7,
  "count": 23,
  "limit": 100,
  "listings": [ { "id": 1, "title": "...", "vehicle": {...}, ... } ]
}
```

---

### 5.3 Annonces — `/listings`

| Méthode | Endpoint                           | Auth    | Description                     |
|---------|------------------------------------|---------|---------------------------------|
| POST    | `/listings/{id}/like`              | Optionnel| Liker une annonce              |
| DELETE  | `/listings/{id}/like`              | Optionnel| Unliker une annonce            |
| POST    | `/listings/{id}/analyze`           | Optionnel| Analyse IA de l'annonce        |
| POST    | `/listings/{id}/scan-immat`        | Non     | Détection plaque d'immatriculation (vision)|

---

### 5.4 Analyse IA — `/ai`

| Méthode | Endpoint                               | Auth    | Description                              |
|---------|----------------------------------------|---------|------------------------------------------|
| GET     | `/ai/analyses?listing_ids=1,2,3`       | Optionnel| Analyses IA déjà payées par cet user   |
| GET     | `/ai/quota`                            | Optionnel| Quota IA de l'utilisateur              |
| POST    | `/search/{search_id}/analyze`          | Optionnel| Analyse IA d'une recherche complète    |
| GET     | `/search/{search_id}/analyze`          | Non     | Récupère l'analyse d'une recherche      |

**Réponse `/ai/quota`** :
```json
{
  "listing_analyses_used": 3,
  "listing_analyses_max": 10,
  "search_analyses_used": 1,
  "search_analyses_max": 3
}
```

**Logique crédits** (voir [§3.10](#310-système-de-crédits-ia)) :
- `used_cache=true` → crédit consommé mais pas d'appel API
- `used_cache=false` → crédit + appel API réel

---

### 5.5 Favoris — `/likes`

| Méthode | Endpoint               | Auth    | Description                        |
|---------|------------------------|---------|------------------------------------|
| GET     | `/likes`               | Optionnel| IDs des annonces likées           |
| GET     | `/likes/listings`      | Non     | Annonces likées complètes          |

---

### 5.6 Utilisateur — `/users`

| Méthode | Endpoint                | Auth | Description                         |
|---------|-------------------------|------|-------------------------------------|
| GET     | `/users/me/searches`    | JWT  | 50 dernières recherches de l'user   |
| GET     | `/users/me/likes`       | JWT  | Annonces likées de l'user           |

---

### 5.7 Historique — `/history`

| Méthode | Endpoint                      | Auth | Description                            |
|---------|-------------------------------|------|----------------------------------------|
| GET     | `/history/searches`           | Non  | 20 dernières recherches (user_id=1)    |
| POST    | `/history/searches`           | Non  | Ajoute une recherche à l'historique    |
| DELETE  | `/history/searches`           | Non  | Vide l'historique de recherches        |
| GET     | `/history/listings`           | Non  | 20 dernières fiches consultées         |
| POST    | `/history/listings/{id}`      | Non  | Marque une fiche comme consultée       |
| DELETE  | `/history/listings`           | Non  | Vide l'historique des fiches           |

---

### 5.8 Patterns — `/patterns`

| Méthode | Endpoint           | Auth | Description                        |
|---------|--------------------|------|------------------------------------|
| GET     | `/patterns`        | Non  | Liste tous les patterns            |
| POST    | `/patterns`        | Non  | Crée un pattern personnalisé       |
| DELETE  | `/patterns/{id}`   | Non  | Supprime un pattern                |

---

### 5.9 Véhicules — `/vehicles`

| Méthode | Endpoint                            | Auth | Description                       |
|---------|-------------------------------------|------|-----------------------------------|
| GET     | `/vehicles?brand=X&model=Y`         | Non  | Fiche fiabilité d'un modèle       |

---

### 5.10 Administration — `/admin` ⚠️ JWT requis (admin)

| Méthode | Endpoint                          | Auth  | Description                                    |
|---------|-----------------------------------|-------|------------------------------------------------|
| GET     | `/admin/ai-analyses`              | Admin | Liste toutes les analyses IA (200 dernières)   |
| POST    | `/admin/scrape`                   | Admin | Lance un scraping de masse                     |
| GET     | `/admin/vehicles`                 | Admin | Liste les véhicules en BDD                     |
| POST    | `/admin/vehicles/scrape-fiches`   | Admin | Scrape les données fiches-auto d'un modèle     |

Les admins sont définis par `ADMIN_USER_IDS` (variable d'environnement).

---

### 5.11 Santé

| Méthode | Endpoint   | Description                 |
|---------|------------|-----------------------------|
| GET     | `/health`  | `{"status": "ok"}`          |

---

## 6. Frontend — composants et pages

### 6.1 Pages

| Page              | Route           | Description                                          |
|-------------------|-----------------|------------------------------------------------------|
| `Home`            | `/`             | Page principale : formulaire de recherche + résultats|
| `Login`           | `/login`        | Connexion                                            |
| `Register`        | `/register`     | Inscription                                          |
| `VerifyEmail`     | `/verify-email` | Vérification email via token (lien URL)              |
| `Account`         | `/account`      | Profil, favoris, recherches sauvegardées             |
| `History`         | `/history`      | Historique des recherches + analyse IA globale       |
| `AdminAI`         | `/admin`        | Dashboard admin (accès restreint)                    |

---

### 6.2 Composants principaux

#### `SearchForm`
Formulaire de recherche principal. Props : `onResults(data)`, `onLoading(bool)`.  
Gère tous les champs `SearchRequest`, le selector de patterns, et la soumission.

#### `ResultsGrid`
Grille d'affichage des annonces. Reçoit `results`, `token`, `viewedIds`, `onClearSearch`.  
- Auto-charge les analyses IA cachées au montage (`getCachedAnalyses`)
- Affiche la barre de stats + bouton "✕ Fermer"
- Passe `isViewed` et `hasAiAnalysis` à chaque `ListingCard`

#### `ListingsFilterBar`
Barre de filtres locaux (sans aller au backend). Props : `analyzedIds`, `onFilter`.  
États internes : `titleSearch`, `minKm`, `checkedKeywords[]`, `onlyWithAI`.

#### `ListingCard`
Card d'une annonce. Props : `listing`, `isLiked`, `isViewed`, `hasAiAnalysis`, `onLike`, `onOpen`.  
- Badges : `👁 Vue` (zinc), `✨ IA` (violet)
- Score fiabilité affiché en bas

#### `ReliabilityModal`
Modal détail complet d'une annonce. Onglets :
1. **Détails** — informations de l'annonce, photos
2. **Fiabilité** — score, défauts, rang catégorie (`VehicleScore`)
3. **✨ Analyse IA** — analyse individuelle avec gestion des crédits

La logique de désactivation du bouton IA : `disabled` seulement si `!aiAnalysis?.reponse && quota_reached`.

#### `VehicleScore`
Affiche le score de fiabilité avec jauge visuelle, liste des défauts, rang dans catégorie.

#### `PatternSelector`
Sélecteur multi-case pour les patterns regex. Permet d'activer/désactiver les patterns par défaut et d'en créer de nouveaux.

#### `Header`
Barre de navigation. Affiche le lien Admin uniquement si `ADMIN_USER_IDS.includes(user?.id)`.

---

### 6.3 Contexte d'authentification (`useAuth`)

Fournit à toute l'appli :
- `user` — objet utilisateur (ou null)
- `token` — JWT Bearer
- `login(token, user)` — stocke dans localStorage + state
- `logout()` — vide le state et localStorage

---

### 6.4 Client API (`src/api/client.js`)

Toutes les fonctions utilisent un helper `request(method, path, body, token)` interne.

```js
// Recherche
searchListings(params)

// Patterns
getPatterns()
createPattern(data)
deletePattern(id)

// Véhicules
getVehicle(brand, model)

// Likes
getLikes(token)
getLikedListings()
addLike(id, token)
removeLike(id, token)

// Auth
register(email, password)
verifyEmail(token)
loginApi(email, password)
getMe(token)
getSavedSearches(token)

// IA
analyzeListingAI(listingId, token)
getCachedAnalyses(listingIds[], token)
getAiQuota(token)
getAdminAiAnalyses(token)
analyzeSearch(searchHistoryId)

// Historique
getSearchHistory()
getViewedListings()
markListingViewed(id)
clearSearchHistory()
clearViewedHistory()
```

---

## 7. Système d'authentification

### Flux inscription

```
1. POST /auth/register  →  user créé (is_verified=false) + verification_token généré
2. En dev : le token est retourné directement dans la réponse
3. POST /auth/verify-email { token }  →  is_verified=true + JWT retourné
```

### Flux connexion

```
POST /auth/login { email, password }
→ Vérification email + hash bcrypt
→ JWT signé (sub = user_id, exp = 7 jours)
→ Stocké dans localStorage côté frontend
```

### Tokens JWT

- Algorithme : HS256
- Payload : `{ "sub": "user_id", "exp": timestamp }`
- Clé de signature : `SECRET_KEY` (variable d'environnement)
- Durée : configurable (défaut 7 jours)

### Accès admin

`_require_admin()` est une dépendance FastAPI qui :
1. Extrait le Bearer token
2. Décode le JWT → `user_id`
3. Vérifie que `user_id ∈ ADMIN_USER_IDS`

```
ADMIN_USER_IDS=1,6  (variable d'env, séparés par virgule)
```

---

## 8. Système IA

### Modèle utilisé

**GitHub Models API** → `gpt-4o-mini` (configurable via `GITHUB_MODEL`)  
URL : `https://models.inference.ai.azure.com/chat/completions`  
Authentification : `GITHUB_TOKEN` (token GitHub avec accès aux modèles)

### Prompt système (analyse annonce)

Le prompt est construit en 2 parties :

**1. Prompt de base** : demande un JSON structuré avec 4 champs :
- `repairs_found` — réparations déjà faites (citées dans l'annonce)
- `upcoming_maintenance` — points de vigilance à prévoir (minimum 3)
- `condition_summary` — état général en 4-5 phrases
- `risk_level` — `low` / `medium` / `high`

**2. Contexte fiabilité** (injecté si le véhicule est trouvé en BDD) :
- Score fiabilité + interprétation
- Top défauts signalés (classés par fréquence, dédupliqués)
- Détail des problèmes connus
- Règles obligatoires : chaque défaut fréquent doit être cité

### Prompt recherche globale

Analyse un lot d'annonces (jusqu'à 50) et retourne :
- `synthese_globale` — analyse narrative du marché
- `themes_mentionnes` — thèmes récurrents
- `themes_absents` — ce qui manque souvent
- `prochaines_reparations` — risques collectifs
- `risk_level`

---

## 9. Scraper LeBonCoin

Le scraper est un service FastAPI interne (port 8001, non exposé à l'extérieur).

### Endpoints internes

| Méthode | Endpoint  | Description                              |
|---------|-----------|------------------------------------------|
| POST    | `/scrape` | Lance un scraping avec les paramètres    |
| GET     | `/health` | Santé du service                         |

### Paramètres de scraping

```json
{
  "brand": "Toyota",
  "model": "Yaris",
  "price_min": 5000,
  "price_max": 15000,
  "mileage_max": 100000,
  "mileage_min": 0,
  "year_min": 2015,
  "horsepower_min": 70,
  "horsepower_max": 120,
  "gearbox": "automatic",
  "fuel": "hybride",
  "city": "Lyon",
  "radius": 50,
  "condition": "good",
  "pattern_ids": [1, 3],
  "custom_regex": "...",
  "limit": 100
}
```

### Enrichissement

Pour chaque annonce récupérée sur LBC :
1. Extraction de la marque/modèle via le titre
2. Résolution géographique (ville → coordonnées via Nominatim)
3. Application des patterns regex sur titre + description
4. Matching avec `vehicles` en BDD via marque + modèle

### Déduplication

Le champ `lbc_id` est UNIQUE en BDD. Le `search_service.py` filtre également les doublons côté Python (`seen_lbc_ids` set) avant l'upsert.

---

## 10. Infrastructure Docker

### Fichiers de configuration

| Fichier                        | Usage                                    |
|--------------------------------|------------------------------------------|
| `infra/docker-compose.yml`     | Base commune (prod)                      |
| `infra/docker-compose.dev.yml` | Override dev (ports exposés, variables)  |
| `infra/docker-compose.prod.yml`| Override prod (images ghcr.io)           |
| `infra/traefik/traefik.yml`    | Configuration Traefik (prod)             |
| `infra/db/init.sql`            | Schéma initial de la BDD                 |
| `infra/.env.example`           | Template des variables d'environnement   |

### Commandes dev

```bash
# Démarrage
cd infra
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Rebuild après modification de code
docker compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache backend
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --no-deps backend

# Logs
docker compose logs -f backend
docker compose logs -f scraper

# Accès BDD
docker exec -it fmc-mariadb-dev mariadb -u fmc -pdevpassword find_my_car
```

### CI/CD GitHub Actions

| Workflow              | Déclencheur         | Action                                       |
|-----------------------|---------------------|----------------------------------------------|
| `build-backend.yml`   | Push sur `main`     | Build + push `ghcr.io/*/fmc-backend`         |
| `build-frontend.yml`  | Push sur `main`     | Build + push `ghcr.io/*/fmc-frontend`        |
| `build-scraper.yml`   | Push sur `main`     | Build + push `ghcr.io/*/fmc-scraper`         |
| `deploy.yml`          | Fin des 3 builds    | SSH → serveur → `docker compose pull + up`   |

---

## 11. Variables d'environnement

### Backend

| Variable          | Défaut         | Description                                    |
|-------------------|----------------|------------------------------------------------|
| `DB_HOST`         | `mariadb`      | Hostname MariaDB                               |
| `DB_PORT`         | `3306`         | Port MariaDB                                   |
| `DB_NAME`         | `find_my_car`  | Nom de la base de données                      |
| `DB_USER`         | `fmc`          | Utilisateur BDD                                |
| `DB_PASSWORD`     | —              | Mot de passe BDD (obligatoire)                 |
| `SCRAPER_URL`     | `http://scraper:8001` | URL interne du scraper                  |
| `CORS_ORIGINS`    | `*`            | Origines CORS autorisées (virgule-séparées)    |
| `GITHUB_TOKEN`    | —              | Token GitHub pour l'API GitHub Models          |
| `GITHUB_MODEL`    | `gpt-4o-mini`  | Modèle IA à utiliser                           |
| `ADMIN_USER_IDS`  | `1`            | IDs des admins (virgule-séparés, ex: `1,6`)    |
| `SECRET_KEY`      | —              | Clé de signature JWT (obligatoire en prod)     |

### Scraper

| Variable          | Défaut                                  | Description           |
|-------------------|-----------------------------------------|-----------------------|
| `LBC_USER_AGENT`  | `Mozilla/5.0...`                        | User-agent pour LBC   |

### Frontend

| Variable                 | Défaut                    | Description              |
|--------------------------|---------------------------|--------------------------|
| `REACT_APP_API_URL`      | `http://localhost:8000`   | URL du backend           |

### Dev uniquement (`docker-compose.dev.yml`)

| Variable          | Valeur dev      |
|-------------------|-----------------|
| `DB_PASSWORD`     | `devpassword`   |
| `DB_ROOT_PASSWORD`| `rootpassword`  |
| `ADMIN_USER_IDS`  | `1,6`           |
