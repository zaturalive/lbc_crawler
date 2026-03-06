---
name: "fmc-master-workflow"
description: "Workflow maître find_my_car — point d'entrée unique pour Hermes et les agents"
version: "1.0.0"
module: fmc
---

# find_my_car — Master Workflow

Point d'entrée unique. Hermes lit ce fichier pour dispatcher vers le bon sprint/agent.

---

## Vue d'ensemble

```
fmc-master-workflow.md
    │
    ├── context-builder.md      (Sonnet — prépare contexte avant chaque worker)
    ├── gate-workflow.md         (Haiku — validation + notification BYAN)
    │
    └── sprints/
        ├── sprint-0-infra.md    → agent: fmc-infra
        ├── sprint-1-scraper.md  → agent: fmc-scraper
        ├── sprint-2-backend.md  → agent: fmc-backend
        ├── sprint-3-frontend.md → agent: fmc-frontend
        └── sprint-4-integration.md → agent: fmc-infra
```

---

## Attribution modèles

| Rôle | Modèle | Coût |
|---|---|---|
| Context builder (prépare prompt worker) | `claude-sonnet-4.6` | 1x par tâche |
| Worker standard (scaffolding, CRUD, templates) | `claude-haiku-4.5` | Principal |
| Worker complexe (async, ORM, UX, debug) | `claude-sonnet-4.6` | Ciblé |
| Gate validator | `claude-haiku-4.5` | Léger |
| BYAN (décision humain) | Interface Yan | Gate only |

**Règle d'or : Sonnet prépare, Haiku exécute. Sonnet n'exécute que si Haiku ne peut pas.**

---

## Démarrage

Pour lancer le développement depuis zéro :

```
1. Lire ce fichier
2. Vérifier état des todos (SQL: SELECT * FROM todos WHERE status != 'done')
3. Identifier le premier sprint non démarré
4. Lancer le context-builder pour la première tâche du sprint
5. Exécuter le worker
6. Passer par le gate après chaque tâche
7. Notifier BYAN à la fin de chaque sprint
```

---

## Commandes Hermes

Depuis Hermes, utiliser :

| Commande | Action |
|---|---|
| `@fmc start` | Démarre depuis le premier sprint non terminé |
| `@fmc sprint-0` | Lance Sprint 0 Infra |
| `@fmc sprint-1` | Lance Sprint 1 Scraper |
| `@fmc sprint-2` | Lance Sprint 2 Backend |
| `@fmc sprint-3` | Lance Sprint 3 Frontend |
| `@fmc sprint-4` | Lance Sprint 4 Integration |
| `@fmc status` | Affiche l'état de toutes les tâches |
| `@fmc task E0-US1` | Lance une tâche spécifique |

---

## Règles de coordination

1. **Un sprint à la fois** — ne pas lancer sprint N+1 sans validation BYAN du sprint N
2. **Gate obligatoire** — chaque tâche worker finit par gate-workflow.md
3. **Context builder systématique** — jamais de worker sans context builder avant
4. **Bloquage = escalade immédiate** — pas de tentative silencieuse de contournement
5. **Maximum 2 workers simultanés** — respecter les ressources Pi lors des tests

---

## Architecture de référence

Toujours disponible : `{project-root}/_byan-output/find_my_car-architecture.md`
