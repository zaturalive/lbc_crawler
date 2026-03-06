# Audit fiches-auto.fr — Données disponibles
> Basé sur l'analyse HTML réelle de `https://www.fiches-auto.fr/fiabilite-renault/fiabilite-106-pannes-renault-clio-3.php` (encodage : `iso-8859-1`)

---

## Structure d'une page fiabilité

URL type : `https://www.fiches-auto.fr/fiabilite-{marque}/fiabilite-{N}-pannes-{marque}-{modele}-{generation}.php`

Exemple : `https://www.fiches-auto.fr/fiabilite-renault/fiabilite-106-pannes-renault-clio-3.php`

**⚠️ Encodage** : les pages fiches-auto.fr sont servies en `iso-8859-1`. BeautifulSoup avec `resp.content` gère cela automatiquement.

---

## Sections de la page (table des matières)

| Ancre | Section |
|-------|---------|
| `#problemes_connus` | Problèmes les plus connus (texte narratif) |
| `#chifres_fiabilite` | Chiffres fiabilité (tables stats, toutes versions) |
| `#par_moteur` | Accès à la fiabilité par variant moteur |
| `#fiabilite_adac` | Indice fiabilité ADAC |
| `#rappels` | Rappels constructeur |
| `#controle_technique` | Contrôle technique |

---

## Données disponibles sur la page

### 1. ✅ SCRAPÉ — Identité du véhicule

| Champ | Source HTML | Stocké en DB | Champ DB |
|-------|-------------|--------------|----------|
| `brand` | Déduit du slug URL | ✅ | `vehicles.brand` |
| `model` | `<title>` → regex `r'sur\s+\S+\s+(.+?)\s+\d{4}'` | ✅ | `vehicles.model` |
| `year_start` | `<title>` → regex `r'(\d{4})\s*[-–]\s*(\d{4})?'` | ✅ | `vehicles.year_start` |
| `year_end` | Idem | ✅ | `vehicles.year_end` |

Exemple titre réel : `"Tous les problèmes sur Renault CLIO 3 2005-2012 (858 témoignages)"`

---

### 2. ✅ SCRAPÉ — Statistiques de fiabilité (tables)

Source : `<table class="tab_fiabili">` — structure :
```html
<table class="tab_fiabili">
  <tr>
    <td class="intiu_fiabilite">Casse Moteur</td>
    <td class="intiu_fiabilite">Boîte de vit.</td>
    ...
  </tr>
  <tr>
    <td class="donnee_fiabilite" style="background-color:#B10202;">
      <span class="redim_16_to_30">32</span>
    </td>
    ...
  </tr>
</table>
```

**Couleurs de sévérité** dans `background-color` des `td.donnee_fiabilite` :

| Couleur | Hex | Niveau |
|---------|-----|--------|
| Rouge critique | `#B10202` | Très fréquent |
| Orange | `#FF7F00` | Fréquent |
| Gris | `#8F8F8F` | Moyen |
| Vert clair | `#62935D` | Rare |
| Vert | `#0D8902` | Très rare / 0 |
| Rouge vif | `#FB1702` | (variante critique) |

| Champ | Source | Stocké en DB | Champ DB |
|-------|--------|--------------|----------|
| `reliability_score` | Calculé : `max(0, 10 - total_issues/5)` | ✅ | `vehicles.reliability_score` |
| `common_issues` | Pannes avec count > 0, triées desc | ✅ JSON | `vehicles.common_issues` |
| `total_testimonials` | Somme de tous les `td.donnee_fiabilite` | ✅ (scraper) | `vehicles.total_testimonials` ⚠️ colonne à ajouter |

Exemple `common_issues` :
```json
[
  "Casse Moteur: 32 témoignages",
  "Climatisation: 44 témoignages",
  "Electronique: 64 témoignages"
]
```

**Note score** : `reliability_score = None` si aucune table trouvée (pas de données). `10` si total = 0 (parfait).

---

### 3. ✅ SCRAPÉ — Texte narratif "Problèmes les plus connus"

Source : `<a name='problemes_connus'></a><h2>Problèmes les plus connus</h2>` suivi d'un `<p>` contenant :

```html
<h2>Problèmes les plus connus</h2>
<p>
  <strong class="ombrage_un">1.2 :</strong>
  <div>Ce moteur est fiable mais il a quelques ratés côté consommation d'huile...</div>
  <strong class="ombrage_un">1.5 dCi :</strong>
  Ce moteur connait plusieurs faiblesses. Premièrement les coussinets de bielles...
  <strong class="ombrage_un">Train roulant :</strong>
  La conception du train roulant avant provoque une usure prématurée des pneumatiques.
  ...
</p>
```

| Champ | Source | Stocké en DB | Champ DB |
|-------|--------|--------------|----------|
| `known_issues_text` | `<strong class="ombrage_un">` + texte suivant | ✅ (scraper) | `vehicles.known_issues_text` ⚠️ colonne à ajouter |

Le scraper extrait le texte brut de ce `<p>`. Format recommandé final : liste de dicts `[{"label": "1.5 dCi", "text": "..."}]`.

---

### 4. ✅ SCRAPÉ — Source URL

| Champ | Valeur | Stocké en DB |
|-------|--------|--------------|
| `source_url` | URL de la page fiches-auto | ✅ (scraper) | `vehicles.source_url` ⚠️ colonne à ajouter |

---

### 5. ❌ NON SCRAPÉ — Disponible sur la page

#### 5a. Stats par variant moteur

La page a une section `#par_moteur` avec des ancres `<a name='clio-3-12-60-ch'>` et des stats `tab_fiabili` spécifiques à chaque motorisation (ex: "Clio 3 1.2 60ch", "Clio 3 1.5 dCi 90ch").

```html
<a name='clio-3-12-60-ch'></a>
<p class='imite_h2'>Clio 3 <u>1.2 60 ch</u> (Essence)</p>
<p>Statistiques fiabilité Clio 3 1.2 60 appuyées sur les 4 avis écrits...</p>
<table class="tab_fiabili">...</table>
```

⇒ Permet de savoir si **c'est ce moteur précis** qui a des problèmes.

#### 5b. Avis utilisateurs (témoignages)

```html
<p><strong>Vos témoignages :</strong></p>
<p>- Marche arrière un peu plus difficile à enclencher après 100000km...
  <a href='/avis-renault/avis-unique-...'>Lire la suite >></a></p>
```

⇒ Textes libres d'utilisateurs. Trop verbeux pour être stocké en DB de façon utile.

#### 5c. Synthèse des avis (likes/dislikes)

```html
<h2>Synthèse de vos avis sur la fiabilité</h2>
<p>
  Fiabilité : 134 aiment / 81 n'aiment pas
  Service après vente : 6 aiment / 15 n'aiment pas
  Entretien (coût) : 60 aiment / 22 n'aiment pas
  Prix pièces détach. : 18 aiment / 7 n'aiment pas
  Coût assurance : 7 aiment / 6 n'aiment pas
  Accessibilité moteur : 2 aiment / 13 n'aiment pas
</p>
```

⇒ Données structurées intéressantes pour un affichage de sentiment global.

#### 5d. Indice fiabilité ADAC (`#fiabilite_adac`)

Données de fiabilité issues du club automobile allemand ADAC. Indépendant des témoignages utilisateurs.

#### 5e. Rappels constructeur (`#rappels`)

Liste des rappels officiels du constructeur.

#### 5f. Résultats contrôle technique (`#controle_technique`)

Points de défaillance fréquents au CT.

---

## Résumé — Décision : Quoi stocker ?

### À stocker maintenant (colonnes à ajouter)

| Champ | Type DB | Pourquoi |
|-------|---------|---------|
| `total_testimonials` | `INT DEFAULT 0` | Contexte du score : "7/10 basé sur 858 avis" |
| `source_url` | `VARCHAR(500)` | Lien direct vers fiches-auto depuis la card |
| `known_issues_text` | `JSON` | Texte narratif qualitatif par variant moteur |

### À faire plus tard (si besoin)

| Champ | Complexité | Utilité |
|-------|-----------|---------|
| Stats par variant moteur | Haute (JSON imbriqué) | Utile si l'utilisateur cherche un moteur précis |
| Synthèse avis (likes/dislikes) | Moyenne | Bon indicateur général |
| Rappels constructeur | Haute | Important pour la sécurité |

### À ne pas stocker

| Champ | Raison |
|-------|--------|
| Témoignages textuels | Trop verbeux, peu structuré |
| Images | Pas d'images véhicules sur fiches-auto |
| HTML brut | Inutile |

---

## Affichage recommandé

### Sur la card :
- ✅ Score fiabilité (0-10) — déjà présent
- ➕ `total_testimonials` en sous-texte : "basé sur 858 avis"

### Dans le modal "Détails" :
- ✅ `common_issues` (pannes avec compteurs) — déjà présent
- ➕ `known_issues_text` (texte narratif par variant)
- ➕ Lien "Voir sur fiches-auto.fr" via `source_url`

---

## SQL — Colonnes à ajouter

```sql
ALTER TABLE vehicles ADD COLUMN total_testimonials INT DEFAULT 0 AFTER reliability_score;
ALTER TABLE vehicles ADD COLUMN known_issues_text JSON AFTER common_issues;
ALTER TABLE vehicles ADD COLUMN source_url VARCHAR(500) AFTER known_issues_text;
```

---

*Document mis à jour après analyse HTML réelle — en attente de validation par Dimitry*

---

## Structure d'une page fiabilité

URL type : `https://www.fiches-auto.fr/fiabilite-{marque}/fiabilite-{N}-pannes-{marque}-{modele}-{generation}.php`

Exemple : `https://www.fiches-auto.fr/fiabilite-renault/fiabilite-84-pannes-renault-clio-4-2012-2019.php`

---

## Données disponibles sur la page

### 1. ✅ DÉJÀ SCRAPÉ — Identité du véhicule

| Champ | Source HTML | Stocké en DB | Champ DB |
|-------|-------------|--------------|----------|
| `brand` | Déduit du slug URL / titre | ✅ | `vehicles.brand` |
| `model` | Titre de page (`<title>`) | ✅ | `vehicles.model` |
| `year_start` | Titre / lien modèle | ✅ | `vehicles.year_start` |
| `year_end` | Titre / lien modèle | ✅ | `vehicles.year_end` |

---

### 2. ✅ DÉJÀ SCRAPÉ — Fiabilité

| Champ | Source HTML | Stocké en DB | Champ DB | Valeur exemple |
|-------|-------------|--------------|----------|----------------|
| `reliability_score` | Calculé : `max(0, 10 - total_issues/5)` | ✅ | `vehicles.reliability_score` | `7` (0-10) |
| `common_issues` | `table.tab_fiabili` > `td.intiu_fiabilite` + `td.donnee_fiabilite` | ✅ JSON | `vehicles.common_issues` | `["Électronique: 10 témoignages", ...]` |

Exemple `common_issues` actuellement stocké :
```json
[
  "Adblue: 2 témoignages",
  "Batterie: 2 témoignages",
  "Electronique: 2 témoignages",
  "Boîte de Vit.: 1 témoignage"
]
```

---

### 3. ❌ PAS ENCORE SCRAPÉ — Disponible sur la page

#### 3a. Nombre total de témoignages

| Champ | Source HTML | Utilité |
|-------|-------------|---------|
| `total_testimonials` | Somme de tous les compteurs dans `td.donnee_fiabilite` | Afficher "X témoignages au total" — contexte pour le score |

> **Note** : Le score actuel divise par 5 mais ne stocke pas le total brut. Or `total_issues = 50` avec 1000 propriétaires ≠ `total_issues = 50` avec 50 propriétaires.

---

#### 3b. Variants moteurs (tableaux séparés)

Chaque table `tab_fiabili` correspond à **un variant moteur** (ex : "1.5 dCi 75ch", "1.2 TCe 130ch", etc.).

| Champ | Source HTML | Utilité |
|-------|-------------|---------|
| `engine_variants` | Titre/légende au-dessus de chaque `table.tab_fiabili` | Savoir quel moteur est fiable/non fiable spécifiquement |

Exemple de structure :
```html
<h3>Clio 4 1.5 dCi 75ch (2012-2019)</h3>
<table class="tab_fiabili">
  <tr>
    <td class="intiu_fiabilite">Electronique</td>
    <td class="intiu_fiabilite">Batterie</td>
    ...
  </tr>
  <tr>
    <td class="donnee_fiabilite">3</td>
    <td class="donnee_fiabilite">1</td>
    ...
  </tr>
</table>
```

---

#### 3c. Catégories de pannes

Les pannes sont regroupées par **catégorie** sur la page (visible dans l'interface utilisateur) :

| Catégorie | Exemples de pannes |
|-----------|-------------------|
| Moteur | Conso/Fuite Huile, Démarrage difficile, Fumée |
| Boîte de vitesse | Boîte de Vit., Transm. (Diff./BDT) |
| Électronique | Electronique, Tableau de Bord, Démarrage |
| Batterie / Charge | Batterie, Alternateur |
| Consommation | Conso. Huile, AdBlue |
| Carrosserie / Habitacle | Lève vitre, Climatisation, Vitre |
| Freins | Freins, ABS |

> Le scraper actuel ne capture pas ces catégories — il prend toutes les pannes à plat.

---

#### 3d. Source URL

| Champ | Valeur | Stocké |
|-------|--------|--------|
| `source_url` | URL de la page fiches-auto | ❌ Pas en DB (retourné par le scraper mais pas inséré dans `vehicles`) |

**Action recommandée** : Ajouter colonne `source_url VARCHAR(500)` dans `vehicles`.

---

#### 3e. Métadonnées de page

| Champ | Source | Utilité |
|-------|--------|---------|
| `page_title` | `<title>` | Nom complet du modèle avec années |
| `meta_description` | `<meta name="description">` | Description courte fiches-auto |
| `h1_text` | Première balise `<h1>` | Titre principal affiché |

> Utilité limitée pour find_my_car — non prioritaire.

---

## Résumé — Décision : Quoi stocker ?

### Ce que je recommande de stocker (et d'afficher)

| Champ | Décision | Raison |
|-------|----------|--------|
| `total_testimonials` | ✅ **Stocker + Afficher** | Contexte crucial pour interpréter le score |
| `source_url` | ✅ **Stocker** | Lien direct vers fiches-auto (lien externe sur la card) |
| `engine_variants` (JSON) | ⚠️ **Optionnel** | Complexe, utile seulement si l'utilisateur cherche un moteur spécifique |
| Catégories de pannes | ⚠️ **Optionnel** | Plus de contexte mais ajoute de la complexité UI |
| `page_title` / meta | ❌ **Non** | Peu de valeur ajoutée |

### Ce que je NE recommande PAS de stocker

| Champ | Raison |
|-------|--------|
| `meta_description` | Aucune valeur pour le use case |
| HTML brut | Trop lourd, inutile |
| Images | fiches-auto n'a pas d'images véhicules |

---

## Affichage actuel sur les cards vs ce qu'on pourrait montrer

### Actuellement sur les cards :
- ✅ Score fiabilité (0-10) via `VehicleScore`
- ✅ `common_issues` via `ReliabilityModal` (clic sur Détails)

### Améliorations proposées :
1. **Sur la card** : Afficher les 3 premiers problèmes avec compteur (ex: "⚠ Electronique (10) · Batterie (5)")
2. **Dans le modal** : Afficher `total_testimonials` pour contextualiser le score
3. **Dans le modal** : Lien "Voir sur fiches-auto.fr" via `source_url`
4. **Futur** : Filtre par variant moteur si on scrape `engine_variants`

---

## Champs à ajouter en DB (proposition)

```sql
ALTER TABLE vehicles ADD COLUMN total_testimonials INT DEFAULT 0 AFTER reliability_score;
ALTER TABLE vehicles ADD COLUMN source_url VARCHAR(500) AFTER fuel_type;
```

Et dans le scraper, retourner :
```python
return {
    ...
    "total_testimonials": total_issues,   # int brut
    "source_url": url,                    # déjà calculé, juste pas stocké
}
```

---

## Conclusion

**Pour l'instant, fiches-auto.fr nous donne l'essentiel.** Le plus utile à ajouter immédiatement :
1. `total_testimonials` — contexte pour le score (ex: "score 7/10 basé sur 8 témoignages" vs "basé sur 800 témoignages")
2. `source_url` — lien direct vers la page fiches-auto depuis le modal

Le reste (variants moteurs, catégories) est optionnel et peut être fait plus tard si besoin.

---

*Document généré le 2026-03-06 — À compléter après validation par Dimitry*
