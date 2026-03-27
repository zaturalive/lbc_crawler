# IA — Authentification et Quota Journalier

## Vue d'ensemble

Toutes les requêtes vers les endpoints d'analyse IA nécessitent une authentification.
Un quota journalier par utilisateur limite le nombre d'appels, configurable via variable d'environnement.

---

## Accès à la base de données (Adminer)

Adminer n'est pas inclus dans le `docker-compose.yml` par défaut. Pour l'ajouter localement :

```yaml
# infra/docker-compose.yml — ajouter dans services:
adminer:
  image: adminer:latest
  container_name: fmc-adminer
  restart: unless-stopped
  ports:
    - "8082:8080"
  networks:
    - internal
```

Accès : `http://localhost:8082`
- Système : `MySQL`
- Serveur : `mariadb`
- Utilisateur : valeur de `DB_USER` (`.env`)
- Mot de passe : valeur de `DB_PASSWORD` (`.env`)
- Base : `find_my_car`

---

## Authentification sur les endpoints IA

### Règle

Tous les endpoints IA exigent un token JWT valide via header `Authorization: Bearer <token>`.
Sans token valide : réponse `401 Unauthorized`.

### Endpoints concernés

| Méthode | Endpoint | Auth requise |
|---------|----------|-------------|
| `POST` | `/listings/{id}/analyze` | Oui |
| `POST` | `/search/{id}/analyze` | Oui |
| `POST` | `/listings/{id}/scan-immat` | Oui |
| `GET` | `/ai/analyses` | Oui |
| `GET` | `/ai/quota` | Oui |
| `GET` | `/search/{id}/analyze` | Non (lecture publique) |

### Comment obtenir un token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=monmotdepasse"
# Retourne: {"access_token": "eyJ...", "token_type": "bearer"}
```

### Utiliser le token

```bash
curl -X POST http://localhost:8000/listings/42/analyze \
  -H "Authorization: Bearer eyJ..."
```

---

## Quota journalier de requêtes IA

### Variable d'environnement

```
DAILY_AI_REQUESTS_MAX=5   # par défaut: 5 requêtes/jour/utilisateur
```

Configurable dans `.env` ou dans le `docker-compose.yml` (backend).

### Logique

1. L'utilisateur se connecte (token JWT).
2. À chaque requête IA (`/analyze`, `/scan-immat`) :
   - Si l'utilisateur possède déjà l'analyse (cache personnel) → retour gratuit, **quota non consommé**.
   - Vérification quota journalier → si atteint → `429 Too Many Requests`.
   - Vérification crédits d'analyse → si épuisés → `402 Payment Required`.
   - Si cache global disponible (autre user a déjà payé) → 1 crédit consommé + 1 quota consommé, zéro appel API.
   - Sinon → appel IA réel, 1 crédit consommé + 1 quota consommé.
3. Le quota se réinitialise à minuit UTC.
4. Les admins (définis via `ADMIN_USER_IDS`) sont exemptés de quota.

### Réponse en cas de quota dépassé

```json
HTTP 429 Too Many Requests
{
  "code": "daily_ai_quota_exceeded",
  "message": "Quota journalier atteint (5 requêtes/jour). Revenez demain.",
  "used": 5,
  "max": 5
}
```

### Réponse en cas de crédits insuffisants

```json
HTTP 402 Payment Required
{
  "code": "no_analysis_credits",
  "message": "Crédits d'analyse insuffisants. Achetez un pack pour continuer.",
  "balance": 0
}
```

---

## Endpoint quota utilisateur

`GET /ai/quota` — retourne le quota complet de l'utilisateur connecté.

```json
{
  "listing_analyses_used": 3,
  "listing_analyses_max": 8,
  "search_analyses_used": 1,
  "search_analyses_max": 3,
  "analysis_credits_remaining": 5,
  "daily_ai_requests_used": 2,
  "daily_ai_requests_max": 5,
  "daily_ai_requests_remaining": 3
}
```

---

## Modèle de données — `user_credits`

| Colonne | Type | Description |
|---------|------|-------------|
| `daily_ai_requests_used` | `INT DEFAULT 0` | Nombre de requêtes IA aujourd'hui |
| `daily_reset_date` | `DATE` | Date du dernier reset (UTC) |
| `analysis_credits` | `INT DEFAULT 5` | Crédits payants restants |

### Migration à appliquer

```sql
-- backend/migrations/add_daily_ai_requests_to_user_credits.sql
ALTER TABLE user_credits
    ADD COLUMN daily_ai_requests_used INT NOT NULL DEFAULT 0;
```

---

## Configuration admin

Les utilisateurs admins sont exemptés de tous les quotas (IA, recherches, résultats).

```
ADMIN_USER_IDS=1,2   # liste d'IDs séparés par virgule
```

---

## Ordre de vérification dans les endpoints IA

```
requête reçue
    │
    ├─ Token JWT absent ou invalide → 401 Unauthorized
    │
    ├─ User possède déjà l'analyse ? → retour cache (gratuit, quota non consommé)
    │
    ├─ Quota journalier atteint ? → 429 Too Many Requests
    │
    ├─ Crédits d'analyse = 0 ? → 402 Payment Required
    │
    ├─ Cache global disponible ? → retour cache + consume(crédit + quota)
    │
    └─ Appel IA réel + consume(crédit + quota) → 200 OK
```
