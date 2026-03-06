# Guide d'installation — Raspberry Pi

## Prérequis

- Raspberry Pi 4 (recommandé) avec Raspberry Pi OS 64-bit
- Accès SSH au Pi
- Git installé sur ton poste

---

## Étape 1 — Docker sur le Pi

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Reconnexion nécessaire
```

Vérifier :
```bash
docker --version
docker compose version
```

---

## Étape 2 — Cloner le repo sur le Pi

```bash
git clone https://github.com/TON_USER/find_my_car.git ~/find_my_car
cd ~/find_my_car/infra
```

---

## Étape 3 — Configurer les variables d'environnement

```bash
cp .env.example .env
nano .env
```

Remplir :
- `DB_PASSWORD` — mot de passe fort pour MariaDB
- `DB_ROOT_PASSWORD` — mot de passe root MariaDB
- `DOMAIN` — domaine ou IP du Pi (ex: `192.168.1.42` ou `find-my-car.local`)
- `REGISTRY_URL` — `localhost:5000`

---

## Étape 4 — DNS local (optionnel)

Pour accéder via `find-my-car.local` depuis les autres appareils du réseau,
ajouter dans le fichier `hosts` de chaque machine :

```
# Windows : C:\Windows\System32\drivers\etc\hosts
# Mac/Linux : /etc/hosts
192.168.1.XX    find-my-car.local
```

Remplacer `192.168.1.XX` par l'IP de ton Pi.

---

## Étape 5 — Premier démarrage

```bash
cd ~/find_my_car/infra
docker compose up -d
```

Vérifier que tous les containers démarrent :
```bash
docker compose ps
```

---

## Étape 6 — Clé SSH pour GitHub Actions

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_deploy  # Copier la clé privée → GitHub Secret PI_SSH_KEY
```

**Secrets GitHub à configurer** (Settings → Secrets → Actions) :
- `PI_HOST` — IP ou hostname du Pi
- `PI_USER` — utilisateur SSH (ex: `pi`)
- `PI_SSH_KEY` — clé privée générée ci-dessus
- `REGISTRY_URL` — adresse registry (ex: `192.168.1.XX:5000`)
- `REGISTRY_USER` — (laisser vide si registry sans auth)
- `REGISTRY_PASSWORD` — (laisser vide si registry sans auth)
