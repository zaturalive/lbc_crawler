# 📋 SOMMAIRE — infra-context.md
> ⚡ LIS CE SOMMAIRE EN PREMIER. Charge uniquement la section dont tu as besoin.

| Section | Contenu | Ligne |
|---------|---------|-------|
| DOCKER | Services, ports, réseaux | ~20 |
| DB | Schéma SQL, credentials | ~55 |
| TRAEFIK | Config reverse proxy | ~85 |
| CICD | GitHub Actions, Raspberry Pi | ~100 |
| BUGS | Problèmes connus | ~115 |

---

# 🐳 DOCKER

**Fichier :** `infra/docker-compose.dev.yml`

### Services

| Service | Image | Port | Healthcheck |
|---------|-------|------|-------------|
| `mariadb` | mariadb:11 | 3306 | mysqladmin ping |
| `scraper` | ./scraper | 8001 | GET /health |
| `backend` | ./backend | 8000 | GET /health |
| `frontend` | ./frontend | 3000 | - |

### Réseau
Tous sur le réseau interne `fmc-network`. Le frontend appelle le backend via le hostname Docker `backend:8000`.

### Variables d'environnement
```yaml
# mariadb
MYSQL_ROOT_PASSWORD: rootpassword
MYSQL_DATABASE: find_my_car
MYSQL_USER: fmc
MYSQL_PASSWORD: devpassword

# scraper
DATABASE_URL: mysql+aiomysql://fmc:devpassword@mariadb:3306/find_my_car
LBC_RATE_MIN: "1.0"
LBC_RATE_MAX: "2.0"
LBC_MAX_PAGES: "5"

# backend
DATABASE_URL: mysql+aiomysql://fmc:devpassword@mariadb:3306/find_my_car
SCRAPER_URL: http://scraper:8001
```

### Commandes usuelles
```bash
# Start stack
docker compose -f infra/docker-compose.dev.yml up -d

# Rebuild un service
docker compose -f infra/docker-compose.dev.yml up -d --build backend

# Logs
docker compose -f infra/docker-compose.dev.yml logs -f backend

# DB shell
docker exec -it fmc-mariadb mysql -u fmc -pdevpassword find_my_car
```

---

# 🗄️ DB

**Fichier :** `infra/db/init.sql`

### Tables
- `vehicles` — données fiches-auto.fr (brand, model, score, issues, years)
- `listings` — annonces LBC (prix, km, année, patterns, score)
- `regex_patterns` — 7 patterns par défaut
- `search_sessions` — historique des recherches

### Patterns par défaut
1. CT valide — `(ct|contrôle technique).{0,30}(valide|ok|passé)`
2. Non fumeur — `non.?fumeur`
3. Garage / Pro — `(garage|concessionnaire|professionnel)`
4. Première main — `(première|1ère|1ere).{0,20}main`
5. Carnet entretien — `(carnet|entretien).{0,30}(complet|suivi|tamponné)`
6. Révisé — `(révisé|revision|vidange).{0,30}(fait|récent|neuve?)`
7. Véhicule propre — `(propre|bien entretenu|aucun défaut)`

### ⚠️ BUG-04 : UNIQUE KEY manquante
La table `vehicles` a un INDEX sur (brand, model) mais pas de UNIQUE KEY → l'ON DUPLICATE KEY UPDATE ne fonctionne pas → upserts créent des doublons.

**Fix :**
```sql
ALTER TABLE vehicles ADD UNIQUE KEY uk_brand_model (brand, model);
```
Ou corriger dans `init.sql` :
```sql
UNIQUE KEY uk_brand_model (brand, model)
```

---

# 🔀 TRAEFIK

Traefik v3.0 est dans le docker-compose mais configuré en mode **dev** (pas de TLS).  
En production (Raspberry Pi), Traefik gérerait Let's Encrypt.

Actuellement :
- Pas de labels Traefik dans le compose dev — accès direct par ports
- En prod : routing par hostname (`api.find-my-car.local`, etc.)

---

# 🔄 CICD

**Cible :** Raspberry Pi (ARM64) auto-hébergé  
**Outil :** GitHub Actions avec runner self-hosted

### À implémenter
```yaml
# .github/workflows/deploy.yml
on: [push to main]
jobs:
  deploy:
    runs-on: self-hosted  # Raspberry Pi runner
    steps:
      - docker compose pull
      - docker compose up -d --build
```

**Registry :** Pas encore configuré — build direct sur le Pi pour l'instant.

---

# 🐛 BUGS ACTIFS

| ID | Description | Priorité |
|----|-------------|----------|
| BUG-04 | `vehicles` table manque UNIQUE KEY → doublons lors du sync fiches-auto | 🔴 HIGH |
| BUG-09 | `init.sql` rechargé à chaque `down -v` → perte des données sync fiches-auto | 🟡 MEDIUM |
| BUG-10 | Pas de volume persistant nommé pour MariaDB → données perdues si container supprimé | 🟡 MEDIUM |
