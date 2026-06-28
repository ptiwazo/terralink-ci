# TerraLink CI — Monorepo

Place de marché B2B agricole pour la Côte d'Ivoire (escrow, trésorerie, logistique).
Interface en français. Voir [CLAUDE.md](./CLAUDE.md) pour la spécification complète.

> **État actuel : Phase 0 — Fondations.** Auth (inscription/connexion par téléphone),
> rôles, contrôle d'accès serveur, tableau de bord par rôle (vide). Les phases
> suivantes (catalogue, escrow, logistique…) ne sont pas encore implémentées.

## Stack figée

| Couche      | Choix                                                        |
| ----------- | ----------------------------------------------------------- |
| Frontend    | React + TypeScript + Vite + Tailwind (mobile-first)         |
| Backend     | Python + FastAPI + SQLAlchemy 2.0                           |
| Base        | PostgreSQL 16 (via docker-compose)                          |
| Migrations  | Alembic                                                     |
| Auth        | JWT (access + refresh) · mots de passe hachés Argon2        |
| Tests       | pytest + httpx                                              |

## Arborescence

```
TERRALINK/
  apps/
    api/        # backend FastAPI
    web/        # frontend React
  packages/
    shared/     # (réservé pour plus tard)
  infra/        # docker-compose PostgreSQL
  README.md
```

## Prérequis

- **Docker Desktop** (pour PostgreSQL) — https://www.docker.com/products/docker-desktop/
- **Python 3.11+** — https://www.python.org/downloads/ (cocher « Add python.exe to PATH »)
- **Node.js 18+** (déjà installé)

## 1. Lancer la base de données

```bash
cd infra
cp .env.example .env          # PowerShell : copy .env.example .env
docker compose up -d
```

Postgres écoute sur `localhost:5432`. La base de test `terralink_test`
est créée automatiquement au premier démarrage.

## 2. Backend (API)

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate         # Windows PowerShell
# source .venv/bin/activate    # macOS/Linux
pip install -r requirements-dev.txt
copy .env.example .env         # cp .env.example .env

# Appliquer les migrations
alembic upgrade head

# Démarrer l'API (http://localhost:8000, docs : /docs)
uvicorn app.main:app --reload
```

### Lancer les tests

La base `terralink_test` (créée à l'étape 1) doit être accessible.

```bash
cd apps/api
pytest
```

Les tests couvrent l'inscription, la connexion, le rafraîchissement de jeton,
la protection des routes et le **contrôle d'accès par rôle** (CLAUDE.md §2.2).

## 3. Frontend (Web)

```bash
cd apps/web
npm install
npm run dev          # http://localhost:5173
```

Le proxy Vite redirige `/api` vers `http://localhost:8000` — pas de config CORS
à faire en dev.

## Parcours de démonstration Phase 0

1. Ouvrir http://localhost:5173 → redirige vers **Connexion**.
2. **Créer un compte** (nom, téléphone, rôle Producteur/Acheteur/Transporteur, mot de passe).
3. Redirection automatique vers le **tableau de bord** : sections adaptées au rôle (vides).
4. **Déconnexion** puis reconnexion avec le téléphone + mot de passe.

## Décisions d'architecture (Phase 0)

- **Téléphone = identifiant principal** (contexte ivoirien). Unique en base.
- **ADMIN / OPS ne s'auto-inscrivent pas** : refusés à l'inscription publique
  (créés par l'équipe interne — à faire en Phase 0+/admin).
- **Rôles & autorisation 100 % côté serveur** via `require_roles(...)`. Le front
  n'utilise les rôles que pour l'affichage.
- **Enum stockés en VARCHAR + CHECK** (`native_enum=False`) pour des migrations
  simples et portables.
- **Refresh token** : actuellement non révocable côté serveur (JWT pur). Une
  table de révocation/sessions pourra être ajoutée avant la mise en production.

## Prochaine étape

Phase 1 — Catalogue et commandes (sans argent). Voir CLAUDE.md §7.
**Ne pas démarrer la Phase 1 avant validation de la Phase 0.**
