// Rôles miroir du backend (CLAUDE.md §2.2). Pour l'affichage uniquement —
// l'autorisation réelle est TOUJOURS faite côté serveur.
export const ROLES = [
  "PRODUCTEUR",
  "ACHETEUR",
  "TRANSPORTEUR",
] as const;

export type Role =
  | "ADMIN"
  | "OPS"
  | "PRODUCTEUR"
  | "ACHETEUR"
  | "TRANSPORTEUR";

export const ROLE_LABELS: Record<Role, string> = {
  ADMIN: "Administrateur",
  OPS: "Opérations",
  PRODUCTEUR: "Producteur",
  ACHETEUR: "Acheteur",
  TRANSPORTEUR: "Transporteur",
};
