---
name: "sprint-4-integration"
description: "Sprint 4 — Integration & Deploy: tests end-to-end, déploiement Pi, validation"
agent: fmc-infra
model_context: claude-sonnet-4.6
model_worker: claude-sonnet-4.6
depends_on: sprint-3-frontend
---

# Sprint 4 — Integration & Deploy

**Agent responsable :** `fmc-infra` (+ tous agents en support)
**Dépendance :** Sprints 0-3 terminés — tous les services générés
**Livrables :** Application déployée et validée sur Raspberry Pi

---

## Ordre d'exécution

```
E4-US1 (Tests intégration)
  ↓
E4-US2 (Déploiement Pi + validation)
```

> Sprint 4 = Sonnet pour les deux tâches (débogage + intégration = raisonnement nécessaire)

---

## US E4-US1 — Tests intégration end-to-end

**Modèle worker :** `claude-sonnet-4.6`

**Fichiers à générer :**
- `backend/tests/test_search_e2e.py`
- `backend/tests/conftest.py`
- `scraper/tests/test_regex_engine.py`
- `scraper/tests/test_lbc_scraper.py`

**Acceptance criteria :**

Backend (pytest + httpx) :
- `test_search_e2e.py` : mock scraper → POST /search → vérifie listings retournés et stockés en BDD test
- `test_patterns_crud.py` : test create/delete pattern, test protection is_default, test validation regex invalide
- `conftest.py` : setup BDD test en mémoire (SQLite async pour tests), mock SCRAPER_URL

Scraper :
- `test_regex_engine.py` : 10 cas de test — CT valide (variantes orthographe), carte grise, pattern custom, pattern invalide
- `test_lbc_scraper.py` : mock `lbc.Client` → vérifie data contract respecté, vérifie rate limiting appelé

Couverture cible : > 80% sur regex_engine.py et search_service.py

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E4-US1, agent_name=fmc-infra, sprint_id=sprint-4
```

---

## US E4-US2 — Déploiement Pi + validation

**Modèle worker :** `claude-sonnet-4.6`

**Fichiers à générer :**
- `infra/deploy-checklist.md`
- `infra/pi-setup.md`

**Acceptance criteria :**

`pi-setup.md` — guide installation initiale Pi :
- Docker + Docker Compose installation sur Raspberry Pi OS
- Configuration DNS local (find-my-car.local → IP Pi)
- Ouverture port 80 sur le routeur (si accès externe souhaité)
- Clone du repo sur Pi
- Création du `.env` depuis `.env.example`
- Génération SSH key pour GitHub Actions deploy

`deploy-checklist.md` — checklist de validation post-déploiement :
- [ ] `docker compose up -d` sans erreur
- [ ] `docker ps` : 6 containers UP
- [ ] `curl http://find-my-car.local/health` → 200
- [ ] `curl http://find-my-car.local/api/health` → {"status": "ok"}
- [ ] `curl http://find-my-car.local/api/patterns` → liste des patterns par défaut
- [ ] Ouvrir http://find-my-car.local dans un navigateur → SearchForm visible
- [ ] Lancer une vraie recherche LBC → au moins 1 résultat ou message "Aucune annonce"
- [ ] Vérifier qu'une annonce avec "CT" dans la description remonte avec badge "CT valide"
- [ ] Vérifier données fiches-auto affichées sur au moins 1 annonce (ou message gracieux si absent)

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E4-US2, agent_name=fmc-infra, sprint_id=sprint-4
```

---

## Gate Sprint 4 — Fin de projet

```
SPRINT 4 TERMINÉ — find_my_car v1 déployé.

Récapitulatif :
  Sprint 0 : Infra (Docker, Traefik, CI/CD, MariaDB) ✓
  Sprint 1 : Scraper (LBC, fiches-auto, regex) ✓
  Sprint 2 : Backend (FastAPI, SQLAlchemy, endpoints) ✓
  Sprint 3 : Frontend (React, SearchForm, ListingCard) ✓
  Sprint 4 : Tests + déploiement Pi ✓

[BYAN] Projet terminé. Que veux-tu faire ensuite ?

Options :
[1] Ajouter une fonctionnalité (→ FD workflow)
[2] Améliorer un agent existant (→ EA workflow)
[3] Rien pour l'instant
```
