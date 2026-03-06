# 📋 SOMMAIRE — frontend-context.md
> ⚡ LIS CE SOMMAIRE EN PREMIER. Charge uniquement la section dont tu as besoin.

| Section | Contenu | Ligne |
|---------|---------|-------|
| STACK | Techno + dépendances frontend | ~20 |
| COMPONENTS | Composants existants + responsabilités | ~35 |
| API_CLIENT | Appels HTTP vers backend | ~60 |
| STATE | Gestion d'état | ~80 |
| UX | Flux utilisateur | ~95 |
| TESTS | Tests à écrire | ~110 |
| BUGS | Problèmes connus | ~125 |

---

# ⚛️ STACK

- React 18 + Vite
- Port : 3000 (Docker)
- Pas de TypeScript actuellement (JS pur)
- Pas de library de state management (useState/useEffect)
- Fetch natif ou axios pour les appels API

---

# 🧩 COMPONENTS

> Note : structure à affiner après lecture des fichiers src/

**Composants attendus :**
- `SearchForm` — Formulaire : marque, modèle, prix min/max, km max, année min, boîte
- `ResultsList` — Affichage des annonces retournées
- `ListingCard` — Carte individuelle : titre, prix, km, ville, score fiabilité, patterns matchés
- `ReliabilityBadge` — Affiche le score 0-10 avec couleur
- `PatternMatchBadge` — Liste des mots-clés détectés dans l'annonce

---

# 📡 API_CLIENT

**Base URL :** `http://localhost:8000` (dev) ou via variable d'env Vite

### Appels principaux
```javascript
// POST /search
const response = await fetch('/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    brand, model, price_min, price_max,
    mileage_max, year_min, gearbox,
    extra_patterns: []
  })
});
```

### Response shape attendue
```json
{
  "session_id": "...",
  "listings": [{
    "lbc_id": "...",
    "title": "...",
    "price": 4500.0,
    "mileage": 120000.0,
    "year": 2015,
    "city": "Paris",
    "url": "...",
    "matched_patterns": ["CT valide", "non-fumeur"],
    "reliability_score": 7.0,
    "gearbox": "manual"
  }],
  "count": 42
}
```

---

# 🔄 STATE

Gestion côté composant (useState) :
- `searchParams` — formulaire
- `listings` — résultats
- `loading` — état de chargement
- `error` — message d'erreur

---

# 👤 UX

### Flux utilisateur
1. Remplir le formulaire (marque obligatoire, reste optionnel)
2. Cliquer "Rechercher" → spinner → résultats
3. Chaque carte affiche : titre, prix, km, ville, score fiabilité coloré, badges patterns
4. Clic sur carte → ouvre l'annonce LBC dans un nouvel onglet

### Règles UX
- Résultats triés par pertinence (patterns matchés > score fiabilité > prix)
- Score fiabilité : rouge < 5, orange 5-7, vert ≥ 7
- Si score inconnu : "N/A" gris

---

# 🧪 TESTS

**Existants :** Aucun test jest actuellement

**À écrire (priorité) :**
- `SearchForm.test.jsx` — teste soumission formulaire, validation champs
- `ResultsList.test.jsx` — teste rendu avec fixtures de listings
- `ListingCard.test.jsx` — teste affichage score, badges patterns
- `api.test.js` — teste appels fetch avec mock

**Framework :** jest + react-testing-library (déjà dans create-react-app / vite)

---

# 🐛 BUGS / AMÉLIORATIONS

| ID | Description | Priorité |
|----|-------------|----------|
| BUG-07 | Pas de gestion d'erreur si backend down | 🟡 MEDIUM |
| BUG-08 | Filtres non reflétés dans l'URL (pas de shareable search) | 🟢 LOW |
| FEAT-01 | Tri des résultats côté frontend (prix asc/desc, km, score) | 🟢 LOW |
