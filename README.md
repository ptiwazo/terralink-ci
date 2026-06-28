# TerraLink CI — Monorepo

Place de marché B2B agricole pour la Côte d'Ivoire (escrow, trésorerie, logistique).
Interface en français. Voir [CLAUDE.md](./CLAUDE.md) pour la spécification complète.

> **État actuel : Phase 1 — Catalogue & commandes (sans argent).**
> Phase 0 : auth téléphone, rôles, contrôle d'accès serveur, tableau de bord.
> Phase 1 : catalogue de référence, offres géolocalisées (CRUD producteur),
> recherche acheteur (produit/proximité/délai), commandes avec montant calculé
> serveur + décrément de stock atomique, et **machine à états** explicite
> jusqu'à `LIVREE_CONFORME` (paiement *simulé*, sans mouvement de fonds).
> Les phases suivantes (escrow réel, logistique, trésorerie) ne sont pas encore
> implémentées.

### Parcours Phase 1 (dans le navigateur)

1. Créer un compte **Producteur** → onglet **Mes offres** → publier une offre
   (produit, quantité, prix FCFA, géoloc).
2. Créer un compte **Acheteur** → onglet **Catalogue** → rechercher, saisir une
   quantité, **Commander**.
3. Suivre dans **Commandes** : l'acheteur « Paie (simulation) », le producteur
   « Prépare » puis « Expédie », l'acheteur « Confirme réception ».
   Chaque action n'est permise qu'au bon rôle (vérifié côté serveur).

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

### Option A — Docker (conforme docker-compose.yml)

```bash
cd infra
cp .env.example .env          # PowerShell : copy .env.example .env
docker compose up -d
```

Postgres écoute sur `localhost:5432`. La base de test `terralink_test`
est créée automatiquement au premier démarrage.

### Option B — PostgreSQL portable, sans Docker (setup dev actuel)

Cette machine n'a pas Docker : on utilise une instance PostgreSQL 16 portable
(binaires Zonky, sans installation ni service). C'est le mode déjà en place.

- Binaires dans `infra/pg/` (ignorés par git), cluster dans `infra/pgdata/`.
- Démarrer / arrêter / état :

```powershell
cd infra
.\db.ps1 start     # démarre Postgres sur le port 5432
.\db.ps1 status
.\db.ps1 stop
```

Le rôle `terralink` (mot de passe `terralink`) et les bases `terralink` +
`terralink_test` ont déjà été créés. Pour repartir de zéro, supprimer
`infra/pgdata/`, relancer `initdb`, puis recréer rôle + bases.

> ⚠️ `initdb` échoue sur cette machine si la locale système (« fr-CI ») est
> active, à cause de l'apostrophe de « Côte d'Ivoire ». Contournement appliqué :
> basculer temporairement `HKCU:\Control Panel\International\LocaleName` sur
> `en-US` le temps de l'`initdb`, puis restaurer `fr-CI`.

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
