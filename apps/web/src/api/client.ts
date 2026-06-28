// Petit client HTTP. Aucune logique métier ici — le front n'est qu'un affichage
// (CLAUDE.md §9 : pas de logique d'argent côté client).
import type { Role } from "../auth/roles";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export interface UserPublic {
  id: string;
  telephone: string;
  nom: string;
  email: string | null;
  role: Role;
  statut: string;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse {
  user: UserPublic;
  tokens: TokenPair;
}

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = `Erreur ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) {
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      /* corps non-JSON */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export interface RegisterPayload {
  telephone: string;
  nom: string;
  mot_de_passe: string;
  role: Role;
  email?: string;
}

// --- Phase 1 : catalogue & commandes ---

export interface Produit {
  id: string;
  nom: string;
  categorie: string;
  unite: string;
}

export interface Offre {
  id: string;
  producteur_id: string;
  produit: Produit;
  producteur: { id: string; nom: string };
  quantite_disponible: number;
  prix_unitaire: number;
  qualite: string | null;
  dispo_le: string;
  lat: number | null;
  lng: number | null;
  statut: "DISPONIBLE" | "EPUISEE" | "RETIREE";
  created_at: string;
}

export interface CatalogueItem {
  offre: Offre;
  distance_km: number | null;
}

export interface OffrePayload {
  produit_id: string;
  quantite_disponible: number;
  prix_unitaire: number;
  qualite?: string | null;
  dispo_le: string;
  lat?: number | null;
  lng?: number | null;
}

export interface LigneCommande {
  id: string;
  offre_id: string;
  produit: Produit;
  quantite: number;
  prix_unitaire: number;
}

export interface Commande {
  id: string;
  acheteur_id: string;
  producteur_id: string;
  statut: string;
  montant_total: number;
  mode_paiement: "COMPTANT" | "DIFFERE";
  lignes: LigneCommande[];
  created_at: string;
  updated_at: string;
}

export interface CatalogueQuery {
  produit_id?: string;
  dispo_avant?: string;
  lat?: number;
  lng?: number;
  rayon_km?: number;
}

export const api = {
  register: (data: RegisterPayload) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (telephone: string, mot_de_passe: string) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ telephone, mot_de_passe }),
    }),

  me: (token: string) => request<UserPublic>("/users/me", {}, token),

  dashboard: (token: string) =>
    request<{
      role: Role;
      nom: string;
      sections: string[];
      message: string;
    }>("/dashboard", {}, token),

  // --- Produits ---
  produits: (token: string) => request<Produit[]>("/produits", {}, token),

  // --- Offres (producteur) ---
  mesOffres: (token: string) => request<Offre[]>("/offres/mes", {}, token),

  creerOffre: (token: string, data: OffrePayload) =>
    request<Offre>("/offres", { method: "POST", body: JSON.stringify(data) }, token),

  retirerOffre: (token: string, id: string) =>
    request<Offre>(`/offres/${id}`, { method: "DELETE" }, token),

  // --- Catalogue (acheteur) ---
  catalogue: (token: string, q: CatalogueQuery = {}) => {
    const params = new URLSearchParams();
    Object.entries(q).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") params.set(k, String(v));
    });
    const qs = params.toString();
    return request<CatalogueItem[]>(`/catalogue${qs ? `?${qs}` : ""}`, {}, token);
  },

  // --- Commandes ---
  creerCommande: (
    token: string,
    lignes: { offre_id: string; quantite: number }[],
    mode_paiement: "COMPTANT" | "DIFFERE" = "COMPTANT"
  ) =>
    request<Commande>(
      "/commandes",
      { method: "POST", body: JSON.stringify({ lignes, mode_paiement }) },
      token
    ),

  mesCommandes: (token: string) => request<Commande[]>("/commandes/mes", {}, token),

  transitionCommande: (token: string, id: string, action: string) =>
    request<Commande>(
      `/commandes/${id}/transition`,
      { method: "POST", body: JSON.stringify({ action }) },
      token
    ),

  // --- Escrow (Phase 2) ---
  payerCommande: (token: string, id: string) =>
    request<Escrow>(`/commandes/${id}/payer`, { method: "POST" }, token),

  escrow: (token: string, id: string) =>
    request<Escrow>(`/commandes/${id}/escrow`, {}, token),
};

export interface Escrow {
  id: string;
  commande_id: string;
  montant: number;
  commission: number;
  montant_net: number;
  statut: "EN_ATTENTE" | "SEQUESTRE" | "LIBERE" | "REMBOURSE";
  ref_depot: string | null;
  ref_paiement: string | null;
}

// --- Phase 3 : logistique ---

export interface Transporteur {
  id: string;
  user_id: string;
  vehicule: string;
  immatriculation: string;
  caution_deposee: number;
  statut: "EN_ATTENTE" | "VALIDE" | "REJETE";
  note: number | null;
}

export interface Livraison {
  id: string;
  commande_id: string;
  transporteur_id: string;
  statut: "ASSIGNEE" | "EN_COURS" | "LIVREE";
  assurance_ref: string | null;
  gps_traces: { lat: number; lng: number; ts: string }[];
  livree_at: string | null;
}

export interface AssignationResponse {
  livraison: Livraison;
  code_remise: string;
}

export const logistique = {
  transporteursValides: (token: string) =>
    request<Transporteur[]>("/transporteurs/valides", {}, token),

  transporteursTous: (token: string) =>
    request<Transporteur[]>("/transporteurs", {}, token),

  monProfil: (token: string) =>
    request<Transporteur>("/transporteurs/mon-profil", {}, token),

  creerProfil: (
    token: string,
    data: { vehicule: string; immatriculation: string; caution_deposee: number }
  ) =>
    request<Transporteur>(
      "/transporteurs/profil",
      { method: "POST", body: JSON.stringify(data) },
      token
    ),

  valider: (token: string, id: string) =>
    request<Transporteur>(`/transporteurs/${id}/valider`, { method: "POST" }, token),

  rejeter: (token: string, id: string) =>
    request<Transporteur>(`/transporteurs/${id}/rejeter`, { method: "POST" }, token),

  assigner: (token: string, commandeId: string, transporteurId: string) =>
    request<AssignationResponse>(
      `/commandes/${commandeId}/assigner-transporteur`,
      { method: "POST", body: JSON.stringify({ transporteur_id: transporteurId }) },
      token
    ),

  confirmerReception: (token: string, commandeId: string, code: string) =>
    request<Commande>(
      `/commandes/${commandeId}/confirmer-reception`,
      { method: "POST", body: JSON.stringify({ code }) },
      token
    ),

  resoudre: (token: string, commandeId: string, sens: "REMBOURSE" | "LIBERE") =>
    request<Commande>(
      `/commandes/${commandeId}/resoudre`,
      { method: "POST", body: JSON.stringify({ sens }) },
      token
    ),
};

export { ApiError };
