# Checklist de validation — find_my_car déploiement Pi

Exécuter dans l'ordre après `docker compose up -d`.

---

## Infrastructure

- [ ] `docker compose ps` → 6 services `Up` (traefik, frontend, backend, scraper, mariadb, registry)
- [ ] `docker compose logs mariadb | grep "ready for connections"` → MariaDB initialisé
- [ ] `curl -s http://localhost:8080/api/http/routers` → Traefik dashboard accessible

## Backend

- [ ] `curl -s http://find-my-car.local/api/health` → `{"status":"ok"}`
- [ ] `curl -s http://find-my-car.local/api/patterns | python3 -m json.tool` → liste des 7 patterns par défaut
- [ ] `curl -s -X POST http://find-my-car.local/api/patterns -H "Content-Type: application/json" -d '{"name":"Test","pattern":"\\btest\\b"}' | python3 -m json.tool` → pattern créé avec `is_default: false`
- [ ] `curl -s -X POST http://find-my-car.local/api/patterns -H "Content-Type: application/json" -d '{"name":"Bad","pattern":"[invalid("}' | python3 -m json.tool` → status 422

## Frontend

- [ ] Ouvrir `http://find-my-car.local` dans le navigateur → SearchForm visible
- [ ] Les checkboxes patterns s'affichent (CT valide, Carte grise, etc.)
- [ ] Le bouton "Chercher" est cliquable
- [ ] Cliquer "Mode avancé" → champ regex apparaît

## Recherche réelle

- [ ] Lancer une recherche (ex: Peugeot 308, prix max 8000) → spinner visible pendant la recherche
- [ ] Au moins un résultat affiché OU message "Aucune annonce trouvée"
- [ ] Si résultat : vérifier qu'au moins un badge keyword est affiché sur une annonce avec "CT" dans la description
- [ ] Cliquer "Voir l'annonce" → LeBonCoin s'ouvre dans un nouvel onglet
- [ ] Si données fiches-auto disponibles : VehicleScore affiché avec couleur (vert/orange/rouge)

## Robustesse

- [ ] Lancer une recherche avec regex invalide dans le champ avancé → erreur affichée côté client, pas d'envoi
- [ ] Couper le container scraper (`docker stop fmc-scraper`) → relancer une recherche → message d'erreur gracieux affiché, pas de crash
- [ ] Relancer scraper (`docker start fmc-scraper`) → recherche refonctionne

## CI/CD

- [ ] Push un commit sur `main` → GitHub Actions lance les 3 build jobs
- [ ] Les images sont poussées vers le registry Pi (`curl http://localhost:5000/v2/_catalog`)
- [ ] `deploy.yml` se déclenche → `docker compose pull && up -d` s'exécute sur le Pi
