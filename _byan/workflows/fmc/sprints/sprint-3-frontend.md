---
name: "sprint-3-frontend"
description: "Sprint 3 — Frontend: React SPA, SearchForm, PatternSelector, ListingCard, VehicleScore"
agent: fmc-frontend
model_context: claude-sonnet-4.6
model_worker: claude-haiku-4.5
depends_on: sprint-2-backend
---

# Sprint 3 — Frontend

**Agent responsable :** `fmc-frontend`
**Dépendance :** Sprint 2 terminé (API contracts disponibles dans backend/schemas/)
**Livrables :** `frontend/` complet, React SPA buildable

---

## Ordre d'exécution

```
E3-US1 (API client)
  ↓
E3-US2 (SearchForm + PatternSelector)
  ↓
E3-US3 (ResultsGrid + ListingCard + VehicleScore)
  ↓
E3-US4 (Dockerfile ARM64 Nginx)
```

---

## US E3-US1 — API client (src/api/client.js)

**Modèle worker :** `claude-haiku-4.5`

**Fichiers à générer :**
- `frontend/src/api/client.js`

**Acceptance criteria :**
- Base URL : `process.env.REACT_APP_API_URL` (défaut: `http://localhost:8000/api`)
- Fonctions exportées :
  - `searchListings(params)` → POST `/search`
  - `getPatterns()` → GET `/patterns`
  - `createPattern(data)` → POST `/patterns`
  - `deletePattern(id)` → DELETE `/patterns/{id}`
  - `getVehicle(brand, model)` → GET `/vehicles?brand=X&model=Y`
- Gestion erreurs centralisée : si status >= 400 → throw Error avec message lisible
- Pas de fetch() dispersé dans les composants

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E3-US1, agent_name=fmc-frontend, sprint_id=sprint-3
```

---

## US E3-US2 — SearchForm + PatternSelector

**Modèle worker :** `claude-sonnet-4.6` (UX non-technique + logique état complexe)

**Fichiers à générer :**
- `frontend/src/components/SearchForm.jsx`
- `frontend/src/components/PatternSelector.jsx`

**Acceptance criteria :**
- `SearchForm` : formulaire avec champs brand (select), model (select filtré par brand), price_min, price_max, mileage_max, year_min, horsepower_min, horsepower_max, gearbox (radio: manuelle/automatique/les deux)
- Tous les labels en français, aucun terme technique visible
- `PatternSelector` : checkboxes pour chaque pattern pré-configuré (chargés via `getPatterns()`)
- Mode avancé (lien "Mode avancé" → collapsible) : champ texte pour regex custom
- Validation regex côté client avant submit (ne pas envoyer une regex invalide)
- Bouton "Chercher" : disabled pendant le chargement
- État de loading visible : spinner + texte "Recherche en cours..."
- Submit appelle `searchListings()` via props callback `onResults(data)`
- Pas de logique API dans le composant — tout passe par props/callbacks

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E3-US2, agent_name=fmc-frontend, sprint_id=sprint-3
```

---

## US E3-US3 — ResultsGrid + ListingCard + VehicleScore

**Modèle worker :** `claude-haiku-4.5`

**Fichiers à générer :**
- `frontend/src/components/ResultsGrid.jsx`
- `frontend/src/components/ListingCard.jsx`
- `frontend/src/components/VehicleScore.jsx`
- `frontend/src/pages/Home.jsx`

**Acceptance criteria :**
- `ResultsGrid` : grid responsive (CSS grid ou flexbox), affiche count résultats en header
- Message "Aucune annonce trouvée — essayez d'élargir vos critères" si count = 0
- `ListingCard` : titre, prix (€), année, km (formaté: "45 000 km"), ville
  - Badges keywords déclenchés (ex: "CT valide" en vert, "Carte grise" en bleu)
  - Bouton "Voir l'annonce" → `window.open(url, '_blank')` (LBC)
  - Si vehicle data disponible : affiche `VehicleScore`
- `VehicleScore` : score fiabilité /10 avec couleur (vert ≥7, orange 4-6, rouge ≤3)
  - Top 3 pannes fréquentes en liste
  - Si score null : "Données fiabilité non disponibles" (grisé discret)
- `Home.jsx` : page principale, compose SearchForm + ResultsGrid, gère l'état global

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E3-US3, agent_name=fmc-frontend, sprint_id=sprint-3
```

---

## US E3-US4 — Dockerfile ARM64 Nginx + nginx.conf

**Modèle worker :** `claude-haiku-4.5`

**Fichiers à générer :**
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `frontend/.env.example`

**Acceptance criteria :**
- Dockerfile multi-stage : stage `build` (node:18-alpine) + stage `serve` (nginx:alpine)
- Platform : `linux/arm64`
- `nginx.conf` : `try_files $uri /index.html` pour React Router SPA
- Gzip activé pour les assets JS/CSS
- Port Nginx : 80
- `.env.example` : `REACT_APP_API_URL=http://find-my-car.local/api`

**Prompt worker :**
```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with: task_id=E3-US4, agent_name=fmc-frontend, sprint_id=sprint-3
```

---

## Gate Sprint 3

Après chaque US, exécuter :
```
Read: {project-root}/_byan/workflows/fmc/gate-workflow.md
```

Après E3-US4 :
```
SPRINT 3 TERMINÉ — Frontend généré.

Prochaine étape : Sprint 4 — Integration & Deploy
Read: {project-root}/_byan/workflows/fmc/sprints/sprint-4-integration.md

[BYAN] Valider avant de lancer Sprint 4 ?
```
