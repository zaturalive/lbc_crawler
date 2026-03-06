# TASK-002 — Rapport de Vérification des Données fiches-auto en DB

**Date du rapport :** 2025-01-14  
**Conteneur inspecté :** `fmc-mariadb-dev`  
**Base de données :** `find_my_car`  
**Table :** `vehicles`

---

## 1. RÉSULTATS DES REQUÊTES SQL

### 1.1 Statistiques Globales

| Métrique | Valeur |
|----------|--------|
| **Total de véhicules** | 1 |
| **Véhicules avec reliability_score > 0** | 0 |
| **Véhicules avec NULL score** | 1 |
| **Combinaisons brand-model uniques** | 1 |
| **Doublons (brand+model)** | 0 |

### 1.2 Distribution par Marque (Top 20)

| Brand | Nombre de modèles | Score moyen |
|-------|-------------------|-------------|
| Renault | 1 | NULL |

### 1.3 Top 10 Véhicules par Score

| Brand | Model | Reliability Score | Year Start | Year End |
|-------|-------|-------------------|------------|----------|
| Renault | clio | NULL | NULL | NULL |

### 1.4 Véhicules sans Score (Sample)

| Brand | Model | Reliability Score | Year Start | Year End |
|-------|-------|-------------------|------------|----------|
| Renault | clio | NULL | NULL | NULL |

### 1.5 Schéma de la Table `vehicles`

| Field | Type | Null | Key | Default | Extra |
|-------|------|------|-----|---------|-------|
| id | int(11) | NO | PRI | NULL | auto_increment |
| brand | varchar(100) | NO | MUL | NULL | |
| model | varchar(100) | NO | | NULL | |
| year_start | int(11) | YES | | NULL | |
| year_end | int(11) | YES | | NULL | |
| reliability_score | tinyint(4) | YES | | NULL | |
| common_issues | longtext | YES | | NULL | |
| fuel_type | varchar(50) | YES | | NULL | |
| scraped_at | datetime | YES | | current_timestamp() | |

### 1.6 Index sur la Table

| Key_name | Unique? | Columns |
|----------|---------|---------|
| PRIMARY | ✓ Oui (Unique) | id |
| idx_brand_model | ✗ Non (Composite) | brand, model |

---

## 2. ANALYSE DES RÉSULTATS

### 2.1 État du Synchronisation

**STATUT : AUCUNE SYNCHRONISATION — Base VIDE**

- ✗ **Sync VIDE** : Seul 1 enregistrement test existe (`Renault clio`)
- ✗ **Aucun score fiches-auto** : 0 véhicule avec `reliability_score > 0`
- ✗ **Aucune donnée de fiches-auto.fr** : Pas de scraping exécuté
- ✓ **Schéma correct** : La table possède tous les champs attendus

### 2.2 Cohérence des Scores

| Critère | Résultat |
|---------|----------|
| **Plage 0-10** | N/A (aucun score) |
| **Type de données** | ✓ Correct : `tinyint(4)` (0-255, ok pour 0-10) |
| **Valeurs NULL** | ✓ Autorisées (100% NULL dans les données) |
| **Min/Max détecté** | N/A |

### 2.3 Doublons (brand + model)

**Résultat : AUCUN DOUBLON**

- Requête `GROUP BY brand, model HAVING COUNT(*) > 1` : **0 résultats**
- ✓ Pas de duplication detectable

### 2.4 Clé Unique sur (brand, model)

**Résultat : INDEX COMPOSITE EXISTANT, PAS DE CONSTRAINT UNIQUE**

| Type | Nom | Colonnes | Statut |
|------|-----|----------|--------|
| **Primary Key** | PRIMARY | id | ✓ Existe |
| **Composite Index** | idx_brand_model | brand, model | ✓ Existe (NON-UNIQUE) |
| **Unique Constraint** | (brand, model) | - | ✗ N'existe pas |

**Recommandation** : Ajouter une contrainte `UNIQUE KEY uk_brand_model (brand, model)` pour empêcher les doublons au niveau base de données.

---

## 3. RECOMMANDATIONS

### 3.1 Priorité Critique 🔴

1. **Activer le scraper fiches-auto.fr**
   - Lancez le scraper pour récupérer les données fiches-auto
   - Cible : ~3000-5000 marques/modèles français courants

2. **Ajouter la contrainte UNIQUE sur (brand, model)**
   ```sql
   ALTER TABLE vehicles ADD UNIQUE KEY uk_brand_model (brand, model);
   ```

3. **Vérifier la chaîne de sync**
   - Backend expose-t-il l'endpoint `POST /sync/fiches-auto` ?
   - Scraper exécute-t-il le scraping ?
   - Y a-t-il des erreurs dans les logs ?

### 3.2 Priorité Haute 🟠

4. **Valider les scores**
   - Les scores doivent être entre 0 et 10
   - Ajouter une contrainte CHECK :
   ```sql
   ALTER TABLE vehicles ADD CHECK (reliability_score IS NULL OR (reliability_score >= 0 AND reliability_score <= 10));
   ```

5. **Tester le pipeline complet**
   - Lancer un scraping test sur 100 véhicules
   - Vérifier que les données arrivent en DB
   - Valider que l'API les retourne correctement

### 3.3 Priorité Moyenne 🟡

6. **Améliorer la performance**
   - Index primaire sur `id` : OK
   - Index composite sur `(brand, model)` : OK pour les recherches
   - Envisager un index sur `reliability_score` si recherches fréquentes

7. **Ajouter du monitoring**
   - Compteur de véhicules importés par jour
   - Taux de véhicules avec score
   - Alertes si sync absent pendant > 7 jours

---

## 4. RÉSUMÉ EXÉCUTIF

| Métrique | Valeur | Statut |
|----------|--------|--------|
| **Total véhicules** | 1 (test only) | 🔴 Critique |
| **% avec reliability_score > 0** | 0% | 🔴 Critique |
| **Unique Key (brand, model)** | Index existant, pas de contrainte UNIQUE | 🟠 Haute |
| **État du Sync fiches-auto** | **AUCUN SYNC EFFECTUÉ** | 🔴 Critique |

### Conclusion

**La base de données est prête structurellement mais vide de données.** Le scraper fiches-auto.fr n'a jamais été exécuté ou n'a pas synchronisé les données avec succès. Une action immédiate est requise pour :

1. Lancer le scraper fiches-auto.fr
2. Ajouter la contrainte UNIQUE sur (brand, model)
3. Valider la chaîne de synchronisation backend ↔ scraper ↔ DB

---

**Rapport généré par :** FMC-Backend Agent  
**Contexte :** TASK-002 — Vérification données fiches-auto en DB
