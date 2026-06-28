import type { Role } from "../auth/roles";

export function formatFCFA(montant: number): string {
  return new Intl.NumberFormat("fr-FR").format(montant) + " FCFA";
}

export const STATUT_LABELS: Record<string, string> = {
  CREEE: "Créée",
  PAYEE_SEQUESTRE: "Payée (séquestre)",
  AVANCE_VERSEE: "Avance versée",
  EN_PREPARATION: "En préparation",
  EN_LIVRAISON: "En livraison",
  LIVREE_CONFORME: "Livrée conforme",
  LITIGE: "Litige",
  FONDS_LIBERES: "Fonds libérés",
  CLOTUREE: "Clôturée",
  RESOLUE_REMBOURSEE: "Résolue (remboursée)",
  RESOLUE_LIBEREE: "Résolue (libérée)",
};

export const STATUT_COULEUR: Record<string, string> = {
  CREEE: "bg-gray-100 text-gray-700",
  PAYEE_SEQUESTRE: "bg-blue-100 text-blue-700",
  EN_PREPARATION: "bg-amber-100 text-amber-700",
  EN_LIVRAISON: "bg-indigo-100 text-indigo-700",
  LIVREE_CONFORME: "bg-green-100 text-green-700",
  FONDS_LIBERES: "bg-green-100 text-green-800",
  CLOTUREE: "bg-green-100 text-green-800",
  LITIGE: "bg-red-100 text-red-700",
  RESOLUE_REMBOURSEE: "bg-orange-100 text-orange-700",
  RESOLUE_LIBEREE: "bg-green-100 text-green-800",
};

interface ActionDispo {
  action: string;
  label: string;
}

// Actions proposées selon le statut et le rôle (affichage seulement —
// l'autorisation réelle est vérifiée côté serveur).
export function actionsDisponibles(statut: string, role: Role): ActionDispo[] {
  switch (statut) {
    // CREEE → le paiement passe par l'escrow (bouton dédié, pas une transition).
    case "PAYEE_SEQUESTRE":
    case "AVANCE_VERSEE":
      return role === "PRODUCTEUR" || role === "OPS" || role === "ADMIN"
        ? [{ action: "PREPARER", label: "Préparer" }]
        : [];
    case "EN_PREPARATION":
      return role === "PRODUCTEUR" || role === "OPS" || role === "ADMIN"
        ? [{ action: "EXPEDIER", label: "Expédier" }]
        : [];
    case "EN_LIVRAISON":
      // La confirmation de réception passe par un code de remise (UI dédiée).
      // Ici on n'expose que le signalement de litige.
      return role === "ACHETEUR" || role === "OPS" || role === "ADMIN"
        ? [{ action: "SIGNALER_LITIGE", label: "Signaler un litige" }]
        : [];
    default:
      return [];
  }
}
