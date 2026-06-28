# Déploiement TerraLink CI

Cible : **front sur Netlify**, **API + PostgreSQL sur Render**, déploiement depuis **GitHub**.

Le front appelle `/api/v1` ; Netlify proxifie `/api/*` vers l'API Render
(défini dans `netlify.toml`) → pas de CORS, pas de rebuild quand l'URL d'API est connue.

---

## 1. Pousser le code sur GitHub

Crée un dépôt **vide** sur GitHub (ex. `terralink-ci`), puis depuis le dossier `TERRALINK/` :

```bash
git remote add origin https://github.com/<ton-compte>/terralink-ci.git
git push -u origin main
```

> Le `.gitignore` exclut déjà `.env`, `.venv`, `node_modules`, les binaires/volumes
> Postgres et les PDF de factures : le dépôt est propre.

## 2. API + PostgreSQL sur Render

1. Sur https://render.com → **New +** → **Blueprint** → connecte le dépôt GitHub.
2. Render lit `render.yaml` et propose : un service web **terralink-api** + une base
   **terralink-db**. Valide la création.
3. Les secrets `JWT_SECRET` / `WEBHOOK_SECRET` sont **générés automatiquement**.
   `DATABASE_URL` est injectée depuis la base managée.
4. Au déploiement, `alembic upgrade head` crée le schéma, puis l'API démarre.
5. Récupère l'**URL publique** de l'API (ex. `https://terralink-api.onrender.com`).
   Vérifie `https://terralink-api.onrender.com/health` → `{"status":"ok"}`.

> Plan **free** : la base expire après 90 j et l'API se met en veille après inactivité
> (1er appel ~50 s). Passe en plan payant pour une vraie prod.

## 3. Front sur Netlify

1. Mets à jour `netlify.toml` : remplace `https://terralink-api.onrender.com`
   par l'URL réelle de ton API Render (dans la règle `[[redirects]] /api/*`).
   Commit + push.
2. Sur https://netlify.com → **Add new site** → **Import from GitHub** → ce dépôt.
   Netlify lit `netlify.toml` (base `apps/web`, build `npm run build`, publish `dist`).
3. Déploie. Récupère l'URL du site (ex. `https://terralink-ci.netlify.app`).

## 4. Relier les deux

- Sur **Render** → service `terralink-api` → **Environment** → mets
  `FRONTEND_ORIGIN` = l'URL Netlify réelle. (Redéploiement automatique.)

## 5. Créer le premier administrateur

ADMIN/OPS ne sont pas auto-inscriptibles. Sur **Render** → service → **Shell** :

```bash
python scripts/creer_admin.py +2250700000099 "Agent OPS" UnMotDePasseFort OPS
```

## 6. Vérification de bout en bout

1. Ouvre l'URL Netlify → page de connexion.
2. Crée un compte **Producteur**, publie une offre.
3. Crée un compte **Acheteur**, commande, **Payer (séquestre)**.
4. Connecte-toi en **OPS** (compte créé à l'étape 5) → valide un transporteur,
   suis les KPIs, émets une facture.

---

## Notes de production

- **Stockage des PDF** : `apps/api/factures/` est sur un disque **éphémère** (Render
  free). Acceptable pour un pilote (re-générable). Pour la prod : monter un disque
  persistant Render, ou stocker sur un bucket (S3/R2) et adapter `facture_service`.
- **Mobile Money** : `PAYMENT_PROVIDER=sandbox`. Pour du réel, implémenter les TODO
  de `app/payments/mobile_money.py` et passer la variable à `mobile_money` + clés.
- **Webhooks paiement** : l'agrégateur devra appeler
  `https://<api>/api/v1/webhooks/paiement` (signature HMAC `WEBHOOK_SECRET`).
- **Sauvegardes** : activer les backups de la base Render.
- **Domaine** : brancher un domaine perso sur Netlify (front) et Render (API),
  puis mettre à jour le proxy et `FRONTEND_ORIGIN`.
