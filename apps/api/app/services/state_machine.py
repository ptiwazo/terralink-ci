"""Machine à états des commandes (CLAUDE.md §5), implémentée explicitement.

Aucune transition libre : seules les entrées de `TRANSITIONS` sont possibles.
Chaque transition déclare ses statuts source, son statut cible, les rôles
autorisés, la « propriété » requise (acheteur/producteur — OPS/ADMIN exemptés),
et `expose` : True si l'action est déclenchable via l'endpoint générique
`/transition`, False si elle est pilotée par un service dédié (paiement,
confirmation par code de remise, résolution de litige).

Passages NON manuels (expose=False) :
- CREEE → PAYEE_SEQUESTRE : piloté par l'escrow (dépôt confirmé par webhook).
- EN_LIVRAISON → LIVREE_CONFORME : via /confirmer-reception, validé par le
  **code de remise** (Phase 3).
- LITIGE → RESOLUE_* : via /resoudre (OPS/ADMIN), avec mouvement de fonds.
"""
from dataclasses import dataclass

from app.models.enums import CommandeStatut as S
from app.models.enums import Role


@dataclass(frozen=True)
class Transition:
    action: str
    sources: tuple[S, ...]
    cible: S
    roles: tuple[Role, ...]
    proprietaire: str  # "acheteur" | "producteur" | "any"
    expose: bool  # True = déclenchable via /transition ; False = service dédié


ROLES_INTERNES = (Role.OPS, Role.ADMIN)

TRANSITIONS: dict[str, Transition] = {
    "PREPARER": Transition(
        action="PREPARER",
        sources=(S.PAYEE_SEQUESTRE, S.AVANCE_VERSEE),
        cible=S.EN_PREPARATION,
        roles=(Role.PRODUCTEUR,),
        proprietaire="producteur",
        expose=True,
    ),
    "EXPEDIER": Transition(
        action="EXPEDIER",
        sources=(S.EN_PREPARATION,),
        cible=S.EN_LIVRAISON,
        roles=(Role.PRODUCTEUR,),
        proprietaire="producteur",
        expose=True,
    ),
    "SIGNALER_LITIGE": Transition(
        action="SIGNALER_LITIGE",
        sources=(S.EN_LIVRAISON,),
        cible=S.LITIGE,
        roles=(Role.ACHETEUR,),
        proprietaire="acheteur",
        expose=True,
    ),
    # --- pilotées par services dédiés (expose=False) ---
    "CONFIRMER_RECEPTION": Transition(
        action="CONFIRMER_RECEPTION",
        sources=(S.EN_LIVRAISON,),
        cible=S.LIVREE_CONFORME,
        roles=(Role.ACHETEUR,),
        proprietaire="acheteur",
        expose=False,
    ),
    "RESOUDRE_LIBERATION": Transition(
        action="RESOUDRE_LIBERATION",
        sources=(S.LITIGE,),
        cible=S.RESOLUE_LIBEREE,
        roles=(),  # OPS/ADMIN uniquement (rôles internes)
        proprietaire="any",
        expose=False,
    ),
    "RESOUDRE_REMBOURSEMENT": Transition(
        action="RESOUDRE_REMBOURSEMENT",
        sources=(S.LITIGE,),
        cible=S.RESOLUE_REMBOURSEE,
        roles=(),
        proprietaire="any",
        expose=False,
    ),
}

# Actions déclenchables via l'endpoint générique /transition.
ACTIONS_DISPONIBLES = tuple(a for a, t in TRANSITIONS.items() if t.expose)


class TransitionError(Exception):
    """Transition refusée (mappée en HTTP par la route)."""

    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def transition_autorisee(action: str, *, interne: bool = False) -> Transition:
    t = TRANSITIONS.get(action)
    if t is None:
        raise TransitionError(f"Action inconnue : {action}", 400)
    if not interne and not t.expose:
        raise TransitionError(f"Action indisponible via /transition : {action}", 400)
    return t


def verifier_et_cibler(
    *,
    action: str,
    statut_courant: S,
    role_acteur: Role,
    acteur_id,
    acheteur_id,
    producteur_id,
    interne: bool = False,
) -> S:
    """Valide une transition et renvoie le statut cible.

    `interne=True` permet aux services dédiés de déclencher des transitions
    non exposées (paiement, code de remise, résolution de litige).
    Lève `TransitionError` si interdite. Ne modifie rien.
    """
    t = transition_autorisee(action, interne=interne)

    if role_acteur not in t.roles and role_acteur not in ROLES_INTERNES:
        raise TransitionError("Rôle non autorisé pour cette action", 403)

    if role_acteur not in ROLES_INTERNES:
        if t.proprietaire == "acheteur" and acteur_id != acheteur_id:
            raise TransitionError("Vous n'êtes pas l'acheteur de cette commande", 403)
        if t.proprietaire == "producteur" and acteur_id != producteur_id:
            raise TransitionError("Vous n'êtes pas le producteur de cette commande", 403)

    if statut_courant not in t.sources:
        raise TransitionError(
            f"Transition '{action}' impossible depuis le statut {statut_courant.value}",
            409,
        )

    return t.cible
