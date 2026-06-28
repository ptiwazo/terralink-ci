"""Machine à états des commandes (CLAUDE.md §5), implémentée explicitement.

Aucune transition libre : seules les entrées de `TRANSITIONS` sont possibles.
Chaque transition déclare :
  - les statuts source autorisés,
  - le statut cible,
  - les rôles autorisés à la déclencher,
  - la « propriété » requise (l'acteur doit être l'acheteur ou le producteur
    de la commande — sauf OPS/ADMIN qui peuvent agir sur toutes).

Phase 1 : parcours jusqu'à LIVREE_CONFORME, sans mouvement de fonds. Le passage
CREEE → PAYEE_SEQUESTRE est une **simulation** (pas d'écriture au grand livre ;
cela viendra en Phase 2). Les transitions monétaires/litige restent définies
mais ne sont pas exposées tant que leur phase n'est pas implémentée.
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
    phase: int


# Acteurs internes toujours autorisés (en plus des rôles déclarés).
ROLES_INTERNES = (Role.OPS, Role.ADMIN)

TRANSITIONS: dict[str, Transition] = {
    # --- Phase 1 ---
    "SIMULER_PAIEMENT": Transition(
        action="SIMULER_PAIEMENT",
        sources=(S.CREEE,),
        cible=S.PAYEE_SEQUESTRE,
        roles=(Role.ACHETEUR,),
        proprietaire="acheteur",
        phase=1,
    ),
    "PREPARER": Transition(
        action="PREPARER",
        sources=(S.PAYEE_SEQUESTRE, S.AVANCE_VERSEE),
        cible=S.EN_PREPARATION,
        roles=(Role.PRODUCTEUR,),
        proprietaire="producteur",
        phase=1,
    ),
    "EXPEDIER": Transition(
        action="EXPEDIER",
        sources=(S.EN_PREPARATION,),
        cible=S.EN_LIVRAISON,
        roles=(Role.PRODUCTEUR,),
        proprietaire="producteur",
        phase=1,
    ),
    "CONFIRMER_RECEPTION": Transition(
        action="CONFIRMER_RECEPTION",
        sources=(S.EN_LIVRAISON,),
        cible=S.LIVREE_CONFORME,
        roles=(Role.ACHETEUR,),
        proprietaire="acheteur",
        phase=1,
    ),
}

# Actions exposées par l'API à ce stade du projet (Phase 1).
ACTIONS_DISPONIBLES = tuple(a for a, t in TRANSITIONS.items() if t.phase <= 1)


class TransitionError(Exception):
    """Transition refusée (mappée en HTTP par la route)."""

    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def transition_autorisee(action: str) -> Transition:
    t = TRANSITIONS.get(action)
    if t is None or action not in ACTIONS_DISPONIBLES:
        raise TransitionError(f"Action inconnue ou indisponible : {action}", 400)
    return t


def verifier_et_cibler(
    *,
    action: str,
    statut_courant: S,
    role_acteur: Role,
    acteur_id,
    acheteur_id,
    producteur_id,
) -> S:
    """Valide une transition et renvoie le statut cible.

    Lève `TransitionError` si la transition est interdite. Ne modifie rien :
    l'appelant applique le changement dans sa transaction.
    """
    t = transition_autorisee(action)

    # Rôle
    if role_acteur not in t.roles and role_acteur not in ROLES_INTERNES:
        raise TransitionError("Rôle non autorisé pour cette action", 403)

    # Propriété (OPS/ADMIN exemptés)
    if role_acteur not in ROLES_INTERNES:
        if t.proprietaire == "acheteur" and acteur_id != acheteur_id:
            raise TransitionError("Vous n'êtes pas l'acheteur de cette commande", 403)
        if t.proprietaire == "producteur" and acteur_id != producteur_id:
            raise TransitionError(
                "Vous n'êtes pas le producteur de cette commande", 403
            )

    # Statut source
    if statut_courant not in t.sources:
        raise TransitionError(
            f"Transition '{action}' impossible depuis le statut {statut_courant.value}",
            409,
        )

    return t.cible
