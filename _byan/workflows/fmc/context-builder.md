---
name: "fmc-context-builder"
description: "Prépare un contexte riche et précis pour les workers bas coût — évite le gaspillage de tokens"
version: "1.0.0"
module: fmc
---

# FMC Context Builder

**Rôle :** Construire un contexte chirurgical pour chaque worker avant exécution.
**Modèle :** claude-sonnet-4.6 (qualité, appelé une seule fois par tâche)
**Objectif :** Le worker (Haiku) reçoit exactement ce dont il a besoin — ni plus, ni moins.

---

## Principe

```
Sonnet (context builder)          Haiku (worker)
      │                                │
      │── lit architecture.md ────────►│
      │── extrait uniquement           │
      │   ce qui concerne {task_id}    │
      │── résout les dépendances       │
      │── prépare le prompt worker ───►│ exécute
      │                                │
      │◄────────────── résultat ───────│
      │
      └── gate-workflow.md
```

---

## Protocole d'exécution

### Étape 1 — Identifier la tâche

```
Tâche courante : {task_id} — {task_title}
Description : {task_description}
Sprint : {sprint_id}
Agent responsable : {agent_name} (fmc-scraper|fmc-backend|fmc-frontend|fmc-infra)
```

### Étape 2 — Extraire le contexte pertinent

Lire dans cet ordre, extraire uniquement ce qui est pertinent pour {task_id} :

1. `{project-root}/_byan-output/find_my_car-architecture.md`
   - Section stack techno
   - Section DB schema (si tâche backend/infra)
   - Section structure projet (répertoire concerné uniquement)
   - Section flux applicatif (si tâche scraper/backend)

2. Fichiers déjà générés dans le sprint courant (contexte d'intégration)
   - Lister les fichiers existants dans le scope de l'agent
   - Extraire les interfaces/contrats exposés

3. Dépendances résolues de {task_id}
   - Quels fichiers/contrats cette tâche consomme ?

### Étape 3 — Assembler le prompt worker

```markdown
# Contexte find_my_car — {task_id}

## Ton rôle
Tu es un {role} expert sur le projet find_my_car.
Tu implémente une seule tâche : {task_title}.

## Stack concernée
{stack_extrait_pertinent}

## Fichiers existants à respecter
{fichiers_existants_avec_interfaces}

## Data contract
{contrat_données_pertinent}

## Ta tâche
{task_description_complète}

## Fichiers à générer
{liste_fichiers_attendus_avec_chemins_absolus}

## Contraintes absolues
- ARM64: {oui/non selon tâche}
- No secrets hardcodés
- No emojis dans le code ou les commits
- {contraintes_spécifiques_agent}

## Critères d'acceptation
{acceptance_criteria_de_la_US}

## FIN DE TÂCHE
Après génération, lire et exécuter : {project-root}/_byan/workflows/fmc/gate-workflow.md
Protocole : TASK_DONE | TASK_BLOCKED | TASK_FAILED
```

### Étape 4 — Passer au worker

Le prompt assemblé est envoyé au worker via l'agent spécialisé correspondant.

**Attribution modèles :**

| Type de tâche | Modèle worker | Justification |
|---|---|---|
| Scaffolding (structure dossiers, fichiers vides) | `claude-haiku-4.5` | Simple, répétitif |
| Implémentation standard (scraper, endpoints CRUD) | `claude-haiku-4.5` | Contexte bien préparé suffit |
| Logique complexe (async, ORM relations, regex engine) | `claude-sonnet-4.6` | Besoin de raisonnement |
| Dockerfile ARM64 + CI/CD | `claude-haiku-4.5` | Template-like |
| Tests (unitaires simples) | `claude-haiku-4.5` | Pattern connu |
| Intégration end-to-end / débogage | `claude-sonnet-4.6` | Debugging = raisonnement |

---

## Appel du context builder

Depuis un sprint workflow ou depuis Hermes :

```
Read: {project-root}/_byan/workflows/fmc/context-builder.md
Execute with:
  task_id: {task_id}
  task_title: {task_title}
  task_description: {task_description}
  agent_name: {fmc-scraper|fmc-backend|fmc-frontend|fmc-infra}
  sprint_id: {sprint_id}
```
