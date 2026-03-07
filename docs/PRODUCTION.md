# Guide de mise en production — find_my_car

> Ce guide couvre le déploiement sur un serveur auto-hébergé (Raspberry Pi ou VPS)
> avec tunnel Cloudflare, images Docker depuis `ghcr.io`, et CI/CD automatique via GitHub Actions.

---

## Architecture de prod

```
Internet
   │
   ▼
Cloudflare Tunnel  ←── cloudflared (daemon sur le serveur)
   │
   ▼
Traefik (reverse proxy, port 80/443)
   ├── find-my-car.ton-domaine.fr  →  frontend (React)
   ├── find-my-car.ton-domaine.fr/api  →  backend (FastAPI)
   └── (interne) scraper, mariadb
```

Les images sont buildées par GitHub Actions et publiées sur `ghcr.io`.
Le serveur pull ces images via `docker compose pull` à chaque déploiement.

---

## Étape 1 — Prérequis serveur

```bash
# Docker + Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# cloudflared (tunnel Cloudflare)
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared jammy main' | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install cloudflared -y

# Git
sudo apt install git -y
```

---

## Étape 2 — Cloner le repo sur le serveur

```bash
git clone https://github.com/TON_USER/find_my_car.git ~/find_my_car
cd ~/find_my_car/infra
```

---

## Étape 3 — Créer et configurer le `.env`

```bash
cp .env.example .env
nano .env
```

Remplir **toutes** les valeurs :

```env
# Domaine public (tunnel Cloudflare)
DOMAIN=find-my-car.ton-domaine.fr

# Base de données — utiliser des mots de passe forts !
DB_USER=fmc
DB_PASSWORD=MOT_DE_PASSE_FORT_ICI
DB_ROOT_PASSWORD=ROOT_MOT_DE_PASSE_FORT_ICI

# GitHub Container Registry
GITHUB_OWNER=ton_username_github

# Clé API GitHub Models (IA)
GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXX

# Modèle IA (par défaut gpt-4o-mini)
GITHUB_MODEL=gpt-4o-mini

# Admin — IDs des utilisateurs admins (séparés par virgule)
ADMIN_USER_IDS=1,6

# CORS — mettre le domaine exact en prod
CORS_ORIGINS=https://find-my-car.ton-domaine.fr

# User-agent scraper LBC
LBC_USER_AGENT=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

> ⚠️ Le fichier `.env` est dans `.gitignore` — ne jamais le committer.

---

## Étape 4 — Tunnel Cloudflare

### 4.1 Créer le tunnel

Sur le **tableau de bord Cloudflare** (zero-trust.cloudflare.com) :

1. `Networks` → `Tunnels` → `Create a tunnel`
2. Nommer le tunnel : `find-my-car`
3. Copier la commande d'installation (elle contient le token)

Sur le **serveur** :

```bash
# Installer et authentifier cloudflared
cloudflared tunnel login
cloudflared tunnel create find-my-car

# Noter le UUID du tunnel affiché, ex: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 4.2 Configurer le tunnel

```bash
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

Contenu :

```yaml
tunnel: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   # UUID du tunnel
credentials-file: /home/TON_USER/.cloudflared/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json

ingress:
  # Frontend (route principale)
  - hostname: find-my-car.ton-domaine.fr
    service: http://localhost:80

  # Catch-all obligatoire
  - service: http_status:404
```

### 4.3 DNS Cloudflare

Dans le dashboard Cloudflare → DNS, ajouter un enregistrement CNAME :

| Type  | Nom          | Cible                                          |
|-------|--------------|------------------------------------------------|
| CNAME | find-my-car  | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.cfargotunnel.com` |

### 4.4 Démarrer le tunnel en service

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
sudo systemctl status cloudflared
```

---

## Étape 5 — Configurer Traefik pour HTTPS Cloudflare

Modifier `infra/traefik/traefik.yml` pour la prod :

```yaml
api:
  dashboard: false   # Désactiver en prod

entryPoints:
  web:
    address: ":80"
    # Cloudflare gère le HTTPS → Traefik reçoit du HTTP en interne

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    watch: true

log:
  level: WARN
```

> Cloudflare termine le SSL/TLS côté Cloudflare. Le trafic interne
> (Cloudflare → serveur) passe en HTTP port 80 via le tunnel.
> Aucun certificat Let's Encrypt nécessaire côté serveur.

---

## Étape 6 — Ajouter les variables d'environnement manquantes au `docker-compose.yml`

Le `docker-compose.yml` base doit transmettre les nouvelles variables au backend.
Vérifier que ces variables sont bien dans la section `environment` du service `backend` :

```yaml
  backend:
    environment:
      - DB_HOST=mariadb
      - DB_PORT=3306
      - DB_NAME=find_my_car
      - DB_USER=${DB_USER:-fmc}
      - DB_PASSWORD=${DB_PASSWORD}
      - SCRAPER_URL=http://scraper:8001
      - CORS_ORIGINS=${CORS_ORIGINS:-*}
      - GITHUB_TOKEN=${GITHUB_TOKEN:-}
      - GITHUB_MODEL=${GITHUB_MODEL:-gpt-4o-mini}
      - ADMIN_USER_IDS=${ADMIN_USER_IDS:-1}
```

---

## Étape 7 — GitHub Actions : configurer les secrets

Dans le repo GitHub → `Settings` → `Secrets and variables` → `Actions` :

| Secret          | Valeur                                        |
|-----------------|-----------------------------------------------|
| `PI_HOST`       | IP ou hostname SSH du serveur                 |
| `PI_USER`       | Utilisateur SSH (ex: `pi`, `ubuntu`)          |
| `PI_SSH_KEY`    | Clé privée SSH (voir ci-dessous)              |
| `GITHUB_TOKEN`  | Automatique (fourni par GitHub Actions)       |

### Générer la clé SSH pour le déploiement

Sur le **serveur** :

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Afficher la clé PRIVÉE à copier dans GitHub Secrets → PI_SSH_KEY
cat ~/.ssh/github_deploy
```

---

## Étape 8 — Premier déploiement manuel

```bash
cd ~/find_my_car/infra

# Connexion au registry ghcr.io
echo "TON_GITHUB_TOKEN" | docker login ghcr.io -u TON_USERNAME --password-stdin

# Pull et démarrage
export GITHUB_OWNER=ton_username_github
export TAG=latest
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Vérifier
docker compose ps
```

---

## Étape 9 — Vérification

```bash
# Tous les services Up ?
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Backend répond ?
curl -s http://localhost/api/health
# → {"status":"ok"}

# Frontend accessible ?
curl -s -o /dev/null -w "%{http_code}" http://localhost/
# → 200

# Tunnel Cloudflare actif ?
sudo systemctl status cloudflared

# Tester depuis l'extérieur
curl -s https://find-my-car.ton-domaine.fr/api/health
# → {"status":"ok"}
```

---

## Étape 10 — CI/CD automatique

Après configuration des secrets GitHub, tout push sur `main` déclenche automatiquement :

1. **Build** des 3 images (frontend, backend, scraper) → publiées sur `ghcr.io`
2. **Deploy** : SSH sur le serveur → `docker compose pull` + `up -d`

Vérifier dans l'onglet `Actions` du repo GitHub que les 4 workflows passent au vert.

---

## Gestion de la base de données en prod

### Backup automatique

```bash
# Ajouter dans crontab : crontab -e
0 3 * * * docker exec fmc-mariadb mysqldump -u fmc -p'MOT_DE_PASSE' find_my_car > ~/backups/fmc_$(date +\%Y\%m\%d).sql
```

### Restaurer un backup

```bash
docker exec -i fmc-mariadb mysql -u fmc -p'MOT_DE_PASSE' find_my_car < ~/backups/fmc_20260307.sql
```

### Migrations manuelles

Si des colonnes ont été ajoutées en dev, les appliquer manuellement sur la prod **avant** de déployer :

```bash
docker exec -it fmc-mariadb mariadb -u fmc -p'MOT_DE_PASSE' find_my_car
```

Puis exécuter les `ALTER TABLE` nécessaires. Les migrations actuelles sont documentées dans `infra/db/init.sql`.

---

## Variables `.env` complètes — référence prod

```env
# ── Domaine ──────────────────────────────────────────────
DOMAIN=find-my-car.ton-domaine.fr

# ── Base de données ───────────────────────────────────────
DB_USER=fmc
DB_PASSWORD=                    # OBLIGATOIRE — mot de passe fort
DB_ROOT_PASSWORD=               # OBLIGATOIRE — mot de passe root fort

# ── Images Docker ─────────────────────────────────────────
GITHUB_OWNER=                   # ton username GitHub (ex: dimigithub)
TAG=latest                      # ou le SHA d'un commit précis

# ── API IA GitHub Models ──────────────────────────────────
GITHUB_TOKEN=                   # ghp_xxxx — token GitHub avec accès models
GITHUB_MODEL=gpt-4o-mini        # modèle à utiliser

# ── Admin ─────────────────────────────────────────────────
ADMIN_USER_IDS=1,6              # IDs des users admin (séparés par virgule)

# ── CORS ──────────────────────────────────────────────────
CORS_ORIGINS=https://find-my-car.ton-domaine.fr

# ── Scraper ───────────────────────────────────────────────
LBC_USER_AGENT=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

---

## Checklist rapide avant go-live

- [ ] `.env` créé avec tous les champs remplis (pas de valeur vide)
- [ ] `DB_PASSWORD` et `DB_ROOT_PASSWORD` sont des mots de passe forts
- [ ] `GITHUB_TOKEN` valide avec accès GitHub Models
- [ ] `CORS_ORIGINS` pointe sur le domaine exact (pas `*`)
- [ ] Tunnel Cloudflare actif et DNS configuré
- [ ] Secrets GitHub Actions configurés (PI_HOST, PI_USER, PI_SSH_KEY)
- [ ] Premier `docker compose pull && up -d` réussi
- [ ] `curl https://find-my-car.ton-domaine.fr/api/health` → `{"status":"ok"}`
- [ ] Backup automatique configuré (crontab)
- [ ] Dashboard Traefik désactivé (`api.dashboard: false`)
