---
name: "fmc-gate-workflow"
description: "Gate workflow — notifie BYAN quand une tâche est terminée ou bloquée, décide de la suite"
version: "1.0.0"
module: fmc
---

# FMC Gate Workflow

Ce workflow est le **point de contrôle central** du projet find_my_car.
Il est appelé à la fin de chaque tâche worker ou quand un worker se bloque.
Il consulte BYAN pour décider de la suite.

---

## Déclencheurs

```
TASK_DONE   → appelé par un worker après génération/implémentation d'une US
TASK_BLOCKED → appelé par un worker quand il manque du contexte ou rencontre une ambiguïté
TASK_FAILED  → appelé par un worker après 2 tentatives infructueuses
```

---

## Protocole TASK_DONE

### Étape 1 — Validation automatique

Avant de contacter BYAN, le gate effectue une validation légère (modèle bas coût) :

```
AGENT: claude-haiku-4.5
PROMPT: |
  Tu es un validateur de code pour find_my_car.
  
  Tâche complétée : {task_id} — {task_title}
  
  Fichiers générés :
  {generated_files}
  
  Vérifie les points suivants (oui/non pour chacun) :
  1. Le fichier existe et est non vide
  2. Pas de placeholder non résolu (TODO, FIXME, YOUR_VALUE_HERE)
  3. Cohérence avec le data contract défini dans find_my_car-architecture.md
  4. ARM64 compatible (si Dockerfile)
  5. Pas de secret hardcodé
  
  Retourne: { valid: bool, issues: [str], confidence: 0-10 }
```

### Étape 2 — Rapport à BYAN

Si validation OK → présenter à BYAN :

```
Tâche {task_id} — {task_title} : TERMINÉE ✓

Fichiers générés :
{liste fichiers + chemins}

Score validation : {confidence}/10
Issues mineures : {issues si présentes}

Prochaine tâche disponible : {next_task_id} — {next_task_title}

Options :
[1] Lancer la prochaine tâche automatiquement
[2] Revoir le code généré avant de continuer
[3] Modifier quelque chose dans la tâche terminée
[4] Pause — je reprends plus tard
```

---

## Protocole TASK_BLOCKED

### Étape 1 — Diagnostic automatique (bas coût)

```
AGENT: claude-haiku-4.5
PROMPT: |
  Worker bloqué sur tâche {task_id} — {task_title}.
  
  Raison du blocage : {blocker_reason}
  Contexte disponible : {context_summary}
  
  Catégorise le blocage :
  A. MANQUE_CONTEXTE — il manque une info métier ou technique
  B. AMBIGUÏTE_SPEC — la spec est contradictoire ou floue
  C. DEPENDANCE_MANQUANTE — un fichier/service n'existe pas encore
  D. ERREUR_TECHNIQUE — problème d'implémentation
  
  Retourne: { category: str, missing: str, suggestion: str }
```

### Étape 2 — Escalade à BYAN

```
BLOCAGE sur {task_id} — {task_title}

Catégorie : {category}
Ce qui manque : {missing}
Suggestion worker : {suggestion}

Options :
[1] Fournir l'information manquante (BYAN demande à Yan)
[2] Simplifier la spec (réduire le scope de la tâche)
[3] Skiper cette tâche et passer à la suivante
[4] Relancer le worker avec un contexte enrichi
```

---

## Protocole TASK_FAILED

```
ÉCHEC sur {task_id} après 2 tentatives.

Logs d'erreur :
{error_logs}

Options :
[1] Escalader vers un agent senior (modèle Sonnet) avec contexte complet
[2] Décomposer la tâche en sous-tâches plus petites
[3] Intervention manuelle de Yan
```

---

## Variables de contexte transmises à BYAN

À chaque appel, le gate transmet :
- `{task_id}` + `{task_title}` + `{task_description}`
- `{sprint_id}` — sprint en cours
- `{completed_tasks}` — liste des tâches done ce sprint
- `{remaining_tasks}` — tâches restantes dans le sprint
- `{generated_files}` — fichiers créés par le worker

---

## Appel du gate depuis un worker

Les workers terminent toujours par :

```markdown
## FIN DE TÂCHE

Après avoir généré tous les fichiers demandés, appelle le gate :
- Si succès → TASK_DONE avec liste des fichiers générés
- Si bloqué → TASK_BLOCKED avec raison précise
- Si 2 échecs → TASK_FAILED avec logs

Read: {project-root}/_byan/workflows/fmc/gate-workflow.md
Execute: protocole correspondant
```
