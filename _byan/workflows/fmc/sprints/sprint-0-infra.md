---
name: "sprint-0-infra"
description: "Sprint 0 — Infrastructure: Docker Compose, Traefik, GitHub Actions, MariaDB, Registry"
agent: fmc-infra
model_context: claude-sonnet-4.6
model_worker: claude-haiku-4.5
---

# Sprint 0 — Infrastructure

**Agent responsable :** `fmc-infra`
**Dépendance :** aucune — premier sprint
**Livrables :** infra/ complète, .github/workflows/ complets

---

## Ordre d'exécution

```
E0-US4 (init.sql + Registry)
  ↓
E0-US1 (docker-compose.yml)
  ↓
E0-US2 (Traefik config)
  ↓
E0-US3 (GitHub Actions)
```

> init.sql en premier — docker-compose dépend du schéma DB pour healthcheck.

---

## US E0-US4 — MariaDB init.sql + Docker Registry

**Modèle worker :** `claude-haiku-4.5`

**Fichiers à générer :**
- `infra/db/init.sql`
- Ajout service `registry` dans docker-compose (géré en US1)

**Acceptance criteria :**
- init.sql contient les 4 tables : `vehicles`, `listings`, `regex_patterns`, `search_sessions`
- DDL complet avec indexes sur brand+model (vehicles), lbc_id UNIQUE (listings)
- Données initiales : INSERT des regex_patterns par défaut (CT valide, carte grise, premier propriétaire)
- Registry v2 configuré avec volume persistant

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E0-US4, agent_name=fmc-infra, sprint_id=sprint-0
```

---

## US E0-US1 — docker-compose.yml complet

**Modèle worker :** `claude-haiku-4.5`

**Fichiers à générer :**
- `infra/docker-compose.yml`
- `infra/docker-compose.prod.yml`
- `infra/.env.example`

**Acceptance criteria :**
- 6 services : traefik, frontend, backend, scraper, mariadb, registry
- 2 réseaux : `proxy` (traefik+frontend+backend), `internal` (backend+scraper+mariadb+registry)
- Volumes : `mariadb_data`, `registry_data`
- Health checks sur mariadb (mysqladmin ping) et backend (GET /health)
- `restart: unless-stopped` sur tous les services
- Env vars via `.env` file (jamais hardcodées)
- Image tags : `${REGISTRY_URL}/fmc-{service}:${TAG:-latest}`

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E0-US1, agent_name=fmc-infra, sprint_id=sprint-0
```

---

## US E0-US2 — Traefik config + labels

**Modèle worker :** `claude-haiku-4.5`

**Fichiers à générer :**
- `infra/traefik/traefik.yml`
- Annotations Traefik labels dans docker-compose.yml (patch)

**Acceptance criteria :**
- Entrée web sur :80
- Provider Docker avec watch auto
- Dashboard Traefik sur :8080 (interne uniquement, pas de label Traefik dessus)
- Frontend : `Host('find-my-car.local')` → port 80 Nginx
- Backend : `Host('find-my-car.local') && PathPrefix('/api')` → port 8000 FastAPI + middleware stripprefix `/api`
- Scraper : PAS de label Traefik (interne only)
- MariaDB / Registry : PAS de label Traefik

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E0-US2, agent_name=fmc-infra, sprint_id=sprint-0
```

---

## US E0-US3 — GitHub Actions CI/CD

**Modèle worker :** `claude-haiku-4.5`

**Fichiers à générer :**
- `.github/workflows/build-scraper.yml`
- `.github/workflows/build-backend.yml`
- `.github/workflows/build-frontend.yml`
- `.github/workflows/deploy.yml`

**Acceptance criteria :**
- Trigger : push sur `main`, path filter par service (`scraper/**`, `backend/**`, `frontend/**`)
- Build avec `docker buildx` platform `linux/arm64`
- Tag : `{REGISTRY_URL}/fmc-{service}:{github.sha}` + `latest`
- Push vers registry Pi (via SSH tunnel ou secret `REGISTRY_URL`)
- `deploy.yml` : SSH sur Pi → `docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml pull && docker compose up -d`
- Secrets GitHub requis : `PI_HOST`, `PI_USER`, `PI_SSH_KEY`, `REGISTRY_URL`
- Jamais de secret dans les fichiers yml

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E0-US3, agent_name=fmc-infra, sprint_id=sprint-0
```

---

## Gate Sprint 0

Après chaque US, exécuter :
```
Read: {project-root}/_byan/workflows/fmc/gate-workflow.md
```

Après la dernière US du sprint (E0-US3) :
```
SPRINT 0 TERMINÉ — Infra générée.

Prochaine étape : Sprint 1 — Scraper
Read: {project-root}/_byan/workflows/fmc/sprints/sprint-1-scraper.md

[BYAN] Valider avant de lancer Sprint 1 ?
```
