# TerraLink CI — Spécification de construction (Claude Code)

> Document de cadrage pour Claude Code. Il décrit **quoi** construire, dans **quel ordre**, et avec **quelles contraintes non négociables**. Construire par phases. Ne pas tout générer d'un coup. Valider chaque phase (tests + revue) avant de passer à la suivante.

---

## 1. Contexte produit

TerraLink CI est une place de marché B2B agricole pour la Côte d'Ivoire. Elle connecte des **producteurs** (coopératives, fermes, éleveurs) à des **acheteurs professionnels** (hôtels, restaurants, supermarchés, usines de transformation).

La valeur de la plateforme ne réside PAS dans la simple mise en relation, mais dans **l'infrastructure de confiance et de trésorerie** :

1. **Escrow** : l'acheteur paie la plateforme, qui séquestre les fonds et ne les libère au producteur qu'après livraison conforme.
2. **Trésorerie / paiement différé** : la plateforme peut avancer le paiement au producteur immédiatement et se faire rembourser par l'acheteur à 30–60 jours.
3. **Logistique opérée** : organisation de la livraison via transporteurs tiers filtrés, avec code de remise et traçabilité.
4. **Catalogue géolocalisé** : stocks disponibles publiés par les producteurs, recherche par produit/proximité/délai.

Marché : francophone, contexte ivoirien (FCFA, Mobile Money, conformité OHADA). Interface **en français**.

---

## 2. Contraintes NON NÉGOCIABLES

Ces règles priment sur toute autre considération de rapidité ou de simplicité.

### 2.1 Sécurité financière
- **Toute la logique monétaire est côté serveur.** Aucun calcul de solde, de commission, de libération de fonds ou de crédit ne doit jamais dépendre du client. Le client n'est qu'un affichage.
- **Toute mutation d'argent passe par une transaction SQL atomique.** Un mouvement de fonds (séquestre → libération, avance → remboursement) doit être tout-ou-rien. Jamais d'état intermédiaire persistant incohérent.
- **Grand livre append-only.** Tenir un registre de toutes les écritures financières (ledger) en insertion seule — aucune ligne n'est modifiée ou supprimée. Les corrections se font par écriture inverse. C'est la base de l'auditabilité.
- **Idempotence des paiements.** Toute opération de paiement/webhook doit être idempotente (clé d'idempotence) pour résister aux doubles appels et aux reprises réseau.
- **Double validation des montants.** Le montant attendu est recalculé côté serveur et comparé à ce qui revient du fournisseur de paiement avant toute libération.

### 2.2 Contrôle d'accès
- Authentification obligatoire sur toutes les routes sauf l'inscription/connexion.
- Rôles : `ADMIN`, `OPS` (équipe terrain/opérations), `PRODUCTEUR`, `ACHETEUR`, `TRANSPORTEUR`.
- Autorisation vérifiée **côté serveur** sur chaque ressource (un producteur ne voit que ses commandes, etc.). Ne jamais se fier à un filtre client.

### 2.3 Données et conformité
- Devise : **FCFA (XOF)**, entiers (pas de flottants pour l'argent — stocker en plus petite unité ou en entier FCFA). Jamais de `float` pour des montants.
- Horodatage UTC en base, affichage en heure d'Abidjan (GMT+0).
- Numérotation des factures conforme et séquentielle (exigence OHADA) : suite continue, sans trou, par exercice.
- Journalisation d'audit (qui a fait quoi, quand) sur les actions sensibles.

### 2.4 Robustesse terrain
- L'app productrice/transporteur doit tolérer une **connexion faible** : file d'attente locale, synchronisation différée, indications d'état clair.
- Pensé **mobile-first** pour les producteurs et transporteurs.

---

## 3. Architecture cible

Choisir une stack simple, robuste et largement documentée. Recommandation :

- **Frontend** : React + TypeScript + Vite. Tailwind pour le style. Mobile-first.
- **Backend** : Node.js + TypeScript (Fastify ou Express) **ou** Python (FastAPI). Choisir UNE option et s'y tenir. API REST versionnée (`/api/v1`).
- **Base de données** : PostgreSQL. Migrations versionnées (ex. Prisma, Drizzle, ou Alembic). PostgreSQL est obligatoire pour les transactions atomiques et l'intégrité référentielle — pas de NoSQL pour le cœur financier.
- **Auth** : JWT court + refresh token, ou sessions serveur. Hash des mots de passe avec Argon2 ou bcrypt.
- **Paiement** : couche d'abstraction `PaymentProvider` (voir §6). Implémenter d'abord un **provider simulé (sandbox)** pour développer sans dépendre d'un vrai agrégateur Mobile Money.
- **Tests** : tests unitaires sur toute la logique financière (couverture quasi totale exigée sur le module ledger/escrow), tests d'intégration sur les parcours critiques.

Structure de dossiers suggérée :

```
/terralink
  /apps
    /api          # backend
    /web          # frontend React
  /packages
    /shared       # types partagés, schémas de validation (zod)
  /infra          # docker-compose (postgres), migrations
  README.md
```

---

## 4. Modèle de données (cœur)

Tables minimales à créer (adapter les noms selon l'ORM). Tous les montants en entiers FCFA.

- **users** — id, role, nom, téléphone (identifiant principal en CI), email (optionnel), mot_de_passe_hash, statut, created_at.
- **cooperatives / producteurs** — profil producteur, zone géo (lat/lng), rattachement user.
- **acheteurs** — profil acheteur, type (hôtel/resto/super/usine), adresse, plafond_credit (pour la trésorerie).
- **transporteurs** — profil, véhicule, immatriculation, **caution_deposee**, statut de validation, note.
- **produits** — catalogue de référence (manioc, igname, plantain, tomate, poulet de chair…), unité.
- **offres (stocks)** — producteur_id, produit_id, quantité, prix_unitaire, qualité, dispo_le, lat/lng, statut.
- **commandes** — acheteur_id, producteur_id, statut (voir machine à états §5), montant_total, mode_paiement (`COMPTANT` | `DIFFERE`), created_at.
- **lignes_commande** — commande_id, offre_id, quantité, prix_unitaire.
- **livraisons** — commande_id, transporteur_id, statut, code_remise (haché), gps_traces, assurance_ref.
- **escrow_transactions** — commande_id, montant, statut (`SEQUESTRE` | `LIBERE` | `REMBOURSE`), idempotency_key.
- **ledger_entries** *(append-only)* — compte, contrepartie, montant (signé), type, ref_commande, ref_idempotence, created_at. **Jamais d'UPDATE/DELETE.**
- **avances_tresorerie** — commande_id, montant_avance, decote, commission, echeance, statut (`AVANCEE` | `REMBOURSEE` | `IMPAYEE`).
- **factures** — numéro séquentiel OHADA, commande_id, montant, tva éventuelle, pdf_ref, created_at.
- **abonnements_premium** — acheteur_id, formule, période, statut.
- **audit_log** — acteur, action, ressource, payload, created_at.

---

## 5. Machine à états des commandes

Implémenter explicitement (pas d'états libres). Transitions autorisées seulement :

```
CREEE
  → PAYEE_SEQUESTRE        (escrow : acheteur a payé, fonds bloqués)
  → AVANCE_VERSEE          (trésorerie : producteur payé d'avance)   [optionnel selon mode]
PAYEE_SEQUESTRE / AVANCE_VERSEE
  → EN_PREPARATION
  → EN_LIVRAISON           (transporteur assigné, code de remise généré)
EN_LIVRAISON
  → LIVREE_CONFORME        (code de remise validé par l'acheteur)
  → LITIGE                 (problème signalé)
LIVREE_CONFORME
  → FONDS_LIBERES          (producteur payé OU, en différé, créance acheteur ouverte)
  → CLOTUREE
LITIGE
  → RESOLUE_REMBOURSEE | RESOLUE_LIBEREE
```

Chaque transition vérifie le rôle autorisé, écrit dans le ledger si mouvement de fonds, et journalise.

---

## 6. Couche paiement (abstraction)

Définir une interface `PaymentProvider` avec au minimum :
- `initierDepot(montant, payeur, idempotencyKey)` → réf transaction
- `verifierStatut(refTransaction)`
- `effectuerPaiement(montant, beneficiaire, idempotencyKey)` (payout vers producteur/transporteur)
- gestion des **webhooks** entrants (confirmation asynchrone), avec vérification de signature et idempotence.

Implémenter deux providers :
1. `SandboxProvider` — simule dépôts/payouts en local (à utiliser pour tout le développement et les tests).
2. `MobileMoneyProvider` — squelette pour Orange/MTN/Moov/Wave via un agrégateur. **Laisser les appels réels en TODO clairement marqués** ; ne pas inventer d'API. Documenter où brancher les clés.

> Important : ne jamais coder en dur de clés d'API. Variables d'environnement uniquement (`.env`, non commité).

---

## 7. Découpage en phases (CONSTRUIRE DANS CET ORDRE)

### Phase 0 — Fondations
- Initialiser le monorepo, docker-compose avec PostgreSQL, migrations, lint, CI basique.
- Auth (inscription/connexion par téléphone + mot de passe), rôles, middleware d'autorisation.
- Page de connexion FR, layout mobile-first, squelette de navigation par rôle.
- **Livrable** : on peut créer un compte, se connecter, et voir un tableau de bord vide selon son rôle.

### Phase 1 — Catalogue et commandes (sans argent)
- CRUD offres/stocks côté producteur (avec géoloc).
- Recherche/filtre côté acheteur (produit, proximité, délai).
- Création de commande + machine à états jusqu'à `EN_LIVRAISON` / `LIVREE_CONFORME`, **sans** paiement réel (statuts simulés).
- **Livrable** : un acheteur peut commander un stock publié par un producteur, suivre l'état.

### Phase 2 — Escrow (cœur financier)
- Module ledger append-only + tests unitaires exhaustifs.
- Intégration du `SandboxProvider` : dépôt séquestré à la commande, libération à `LIVREE_CONFORME`, calcul de commission côté serveur.
- Idempotence + webhooks simulés.
- **Livrable** : cycle escrow complet en sandbox, prouvé par tests (le solde ne fuit jamais, double appel sans effet).

### Phase 3 — Logistique sécurisée
- Profils transporteurs + validation + caution.
- Assignation transporteur, génération du **code de remise** (haché en base), validation à la livraison.
- Traçabilité simple (suite de positions GPS), référence d'assurance, gestion `LITIGE`.
- **Livrable** : une livraison ne peut être confirmée que par le bon code ; un litige bloque la libération.

### Phase 4 — Trésorerie / paiement différé
- Plafond de crédit par acheteur, scoring simple basé sur l'historique de paiements comptants.
- Avance au producteur, création de créance acheteur, échéance 30–60 j, commission + décote.
- Suivi des impayés, écritures ledger correspondantes.
- **Livrable** : un acheteur éligible peut commander en différé ; les marges et créances sont correctement comptabilisées.

### Phase 5 — Facturation, premium, tableau de bord
- Factures séquentielles OHADA (PDF), abonnements premium, prévisions de récolte (agrégation simple des offres à venir).
- Tableau de bord KPIs (GMV, commandes, rétention, impayés, sinistralité).
- **Livrable** : sortie comptable conforme + pilotage.

> Pour le **pilote réel**, les Phases 0 à 3 suffisent (marketplace + escrow + logistique). Les Phases 4–5 viennent ensuite.

---

## 8. Définition de « terminé » pour chaque phase

Une phase n'est finie que si :
1. Le parcours utilisateur cible fonctionne de bout en bout en local.
2. La logique financière de la phase est couverte par des tests qui passent.
3. Aucun montant n'est manipulé côté client.
4. Les rôles/permissions sont vérifiés côté serveur et testés.
5. Un court README explique comment lancer et tester la phase.

---

## 9. Ce qu'il NE FAUT PAS faire

- Ne pas mettre de logique d'argent dans le frontend.
- Ne pas utiliser de `float` pour des montants.
- Ne pas inventer d'API Mobile Money réelle — laisser des TODO documentés.
- Ne pas stocker de secrets dans le code.
- Ne pas court-circuiter la machine à états (pas de passage direct d'un statut à un autre non autorisé).
- Ne pas tout construire d'un coup : respecter le découpage en phases et s'arrêter pour revue à la fin de chacune.

---

## 10. Première action attendue de Claude Code

Commencer par la **Phase 0 uniquement** :
1. Proposer la stack définitive choisie (et s'y tenir).
2. Générer la structure du monorepo + docker-compose PostgreSQL + migrations initiales.
3. Implémenter l'auth et les rôles avec tests.
4. S'arrêter, montrer comment lancer le projet, et attendre validation avant la Phase 1.
