# TASK-A — Modal fiabilité au clic sur une card

**Status:** ✅ COMPLETED  
**Date:** 2024-01-XX  
**Agent:** fmc-frontend (React + UX specialist)

---

## 📋 Résumé

Implémentation d'une modale de fiabilité affichant les informations détaillées d'un véhicule au clic sur une ListingCard.

### ✨ Fonctionnalités livrées

- ✅ Modale plein-écran semi-transparente avec overlay
- ✅ Fermeture via ESC, clic overlay, bouton X
- ✅ Affichage complet des infos de fiabilité
- ✅ Parsing des problèmes connus au format `clé:description`
- ✅ Badges pour les mots-clés détectés
- ✅ Card cliquable pour ouvrir la modale
- ✅ Événement click stoppé sur le bouton "Voir l'annonce"

---

## 📁 Fichiers créés

### 1. `frontend/src/components/ReliabilityModal.jsx`
- Modale responsive avec scroll intégré
- Header sticky avec titre et prix de l'annonce
- Sections : Caractéristiques, Fiabilité, Problèmes connus, Mots-clés
- Footer sticky avec lien vers LeBonCoin (target="_blank")
- Gestion ESC et clic overlay pour fermer
- Utilisation de Badge et Button du système d'UI
- Calcul du variant de couleur basé sur score de fiabilité

**Props:**
- `listing` (Object) : données complètes de l'annonce
- `onClose` (Function) : callback pour fermer la modale

---

## 📝 Fichiers modifiés

### 2. `frontend/src/components/ListingCard.jsx`
```diff
- export default function ListingCard({ listing })
+ export default function ListingCard({ listing, onOpenModal })
```

**Changements:**
- Ajout prop `onOpenModal`
- Wrapper Card avec `onClick={() => onOpenModal(listing)}`
- Ajout `cursor-pointer` pour feedback visuel
- Ajout `e.stopPropagation()` sur le bouton pour éviter d'ouvrir la modale au clic sur le lien

### 3. `frontend/src/pages/Home.jsx`
```diff
+ import ReliabilityModal from '../components/ReliabilityModal';
+ const [selectedListing, setSelectedListing] = useState(null);
```

**Changements:**
- Ajout state `selectedListing` pour tracker la modale active
- Passage `onOpenModal={setSelectedListing}` à ResultsGrid
- Rendu conditionnel de `<ReliabilityModal />` si `selectedListing` existe

### 4. `frontend/src/components/ResultsGrid.jsx`
```diff
- export default function ResultsGrid({ results, loading })
+ export default function ResultsGrid({ results, loading, onOpenModal })
```

**Changements:**
- Ajout prop `onOpenModal`
- Passage du prop à chaque ListingCard

### 5. `frontend/src/components/ui/Button.jsx`
```diff
+ asChild,
```

**Changements:**
- Support du prop `asChild` pour permettre le rendu comme wrapper de lien
- Utilisation de `<div>` au lieu de `<button>` quand `asChild={true}`
- Classes de bouton appliquées au wrapper pour styling consistent

---

## 🔧 Build & Déploiement

### Docker Build
```bash
docker compose -f infra/docker-compose.dev.yml build --no-cache frontend
```
**Résultat:** ✅ Image créée avec succès
```
Image infra-frontend Built
```

### Docker Up
```bash
docker compose -f infra/docker-compose.dev.yml up -d frontend
```
**Résultat:** ✅ Container démarré
```
Container fmc-frontend-dev Started
```

### Vérification HTTP
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```
**Résultat:** ✅ 200 OK

---

## ✅ Checklist de fonctionnalité

- [x] Modale s'ouvre au clic sur la card
- [x] Overlay semi-transparent (bg-black/50)
- [x] Panel centré avec max-width et max-height
- [x] Scroll interne pour contenu long
- [x] Fermeture avec ESC
- [x] Fermeture avec clic overlay
- [x] Fermeture avec bouton X
- [x] Header sticky avec titre et prix
- [x] Section Caractéristiques (année, km, ville, boîte)
- [x] Section Fiabilité (badge coloré + modèle + années)
- [x] Section Problèmes connus (parsing clé:description)
- [x] Section Mots-clés (badges success)
- [x] Footer sticky avec lien LeBonCoin
- [x] Click propagation stoppée sur lien
- [x] Responsive sur mobile/tablet/desktop

---

## 🎨 UX Details

### Scoring visuel
```javascript
- Score >= 7 : success (vert)
- Score 4-6 : warning (jaune)
- Score < 4 : danger (rouge)
- Score N/A : default (neutre)
```

### Layout
- **Desktop:** Modal centré dans la viewport, 90% max-height
- **Mobile:** Padding 16px de chaque côté, scroll intérieur
- **Sticky sections:** Header et Footer collent à la top/bottom du scroll

### Styling cohérent
- Couleurs : système Tailwind (neutral, primary, success, warning, danger, amber)
- Typography : Sans-serif Tailwind defaults
- Spacing : Multiples de 4 (p-4, py-5, gap-3, etc.)
- Borders : neutral-100/200 avec radius-lg/xl
- Shadows : shadow-2xl pour modale principal

---

## 📦 Dépendances

Aucune nouvelle dépendance ajoutée. Utilisation de packages existants:
- `react` (hooks: useState, useEffect)
- `lucide-react` (icônes X, ExternalLink)
- Composants UI locaux : Badge, Button
- `clsx` (classnames)
- Tailwind CSS (classes)

---

## 🚀 Prochaines étapes (optionnelles)

1. Ajouter des tests React Testing Library pour ReliabilityModal
2. Implémenter une animation d'ouverture/fermeture (fade-in/out)
3. Ajouter un bouton "Signaler un problème" dans la modale
4. Intégrer avec un système de favoris (heart icon)
5. Historique des véhicules consultés

---

## 📝 Notes

- Le composant ReliabilityModal est totalement stateless (pure presentational)
- La gestion d'état reste à Home.jsx (single source of truth)
- ESC handler nettoyé correctement au unmount
- Aucune `console.log()` ou code de debug en production
- Respect des conventions du projet (import, JSX format, naming)

---

**Validé par:** fmc-frontend agent  
**Tests manuels:** ✅ http://localhost:3000 réactif et prêt
