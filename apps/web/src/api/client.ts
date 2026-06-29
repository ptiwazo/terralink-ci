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
  ville: string | null;
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
  ville?: string | null;
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
  note_transporteur: number | null;
}

export interface AssignationResponse {
  livraison: Livraison;
  code_remise: string;
}

export interface Course {
  livraison: Livraison;
  commande_id: string;
  commande_statut: string;
  montant: number;
  produits: string;
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

  mesCourses: (token: string) => request<Course[]>("/transporteurs/mes-courses", {}, token),

  getLivraison: (token: string, commandeId: string) =>
    request<Livraison>(`/commandes/${commandeId}/livraison`, {}, token),

  getSuivi: (token: string, commandeId: string) =>
    request<Suivi>(`/commandes/${commandeId}/suivi`, {}, token),

  ajouterPosition: (token: string, commandeId: string, lat: number, lng: number) =>
    request<Livraison>(
      `/commandes/${commandeId}/position`,
      { method: "POST", body: JSON.stringify({ lat, lng }) },
      token
    ),

  noterTransporteur: (token: string, commandeId: string, note: number) =>
    request<Livraison>(
      `/commandes/${commandeId}/noter-transporteur`,
      { method: "POST", body: JSON.stringify({ note }) },
      token
    ),

  resoudre: (token: string, commandeId: string, sens: "REMBOURSE" | "LIBERE") =>
    request<Commande>(
      `/commandes/${commandeId}/resoudre`,
      { method: "POST", body: JSON.stringify({ sens }) },
      token
    ),
};

// --- Phase 4 : trésorerie / paiement différé ---

export interface Eligibilite {
  score: number;
  plafond_credit: number;
  plafond_suggere: number;
  plafond_effectif: number;
  encours: number;
  disponible: number;
}

export interface AcheteurProfil {
  id: string;
  user_id: string;
  type: string;
  adresse: string | null;
  lat: number | null;
  lng: number | null;
  plafond_credit: number;
}

export interface Suivi {
  statut: string;
  positions: { lat: number; lng: number; ts: string }[];
  destination: { lat: number; lng: number } | null;
  distance_km: number | null;
  eta_minutes: number | null;
  proche: boolean;
}

export interface Avance {
  id: string;
  commande_id: string;
  acheteur_id: string;
  montant: number;
  montant_avance: number;
  commission: number;
  decote: number;
  echeance: string;
  statut: "AVANCEE" | "REMBOURSEE" | "IMPAYEE" | "ANNULEE";
}

export const tresorerie = {
  monProfil: (token: string) =>
    request<AcheteurProfil>("/acheteurs/mon-profil", {}, token),

  creerProfil: (
    token: string,
    data: { type: string; adresse?: string; lat?: number; lng?: number }
  ) =>
    request<AcheteurProfil>(
      "/acheteurs/profil",
      { method: "POST", body: JSON.stringify(data) },
      token
    ),

  majProfil: (
    token: string,
    data: { adresse?: string; lat?: number; lng?: number }
  ) =>
    request<AcheteurProfil>(
      "/acheteurs/mon-profil",
      { method: "PATCH", body: JSON.stringify(data) },
      token
    ),

  monEligibilite: (token: string) =>
    request<Eligibilite>("/acheteurs/mon-eligibilite", {}, token),

  getAvance: (token: string, commandeId: string) =>
    request<Avance>(`/commandes/${commandeId}/avance`, {}, token),

  rembourserCreance: (token: string, commandeId: string) =>
    request<Avance>(
      `/commandes/${commandeId}/rembourser-creance`,
      { method: "POST" },
      token
    ),

  impayes: (token: string) => request<Avance[]>("/tresorerie/impayes", {}, token),

  marquerImpayes: (token: string) =>
    request<{ impayes_marques: number }>(
      "/tresorerie/marquer-impayes",
      { method: "POST" },
      token
    ),
};

// --- Phase 5 : facturation, premium, analytics ---

export interface Facture {
  id: string;
  numero: string;
  exercice: number;
  sequence: number;
  commande_id: string;
  montant_ht: number;
  tva: number;
  montant_ttc: number;
  pdf_ref: string | null;
  created_at: string;
}

export interface Abonnement {
  id: string;
  formule: string;
  debut: string;
  fin: string;
  prix: number;
  statut: string;
}

export interface Prevision {
  produit: string;
  unite: string;
  quantite_totale: number;
  nb_offres: number;
}

export interface Kpis {
  gmv: number;
  nb_commandes: number;
  par_statut: Record<string, number>;
  nb_litiges: number;
  sinistralite: number;
  impayes_nb: number;
  impayes_montant: number;
  nb_acheteurs: number;
  retention: number;
  revenus: { commission: number; decote: number; abonnement: number; pertes: number };
}

const BASE2 = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export const facturation = {
  emettre: (token: string, commandeId: string) =>
    request<Facture>(`/commandes/${commandeId}/facture`, { method: "POST" }, token),

  getFacture: (token: string, commandeId: string) =>
    request<Facture>(`/commandes/${commandeId}/facture`, {}, token),

  lister: (token: string) => request<Facture[]>("/factures", {}, token),

  // Télécharge le PDF (avec authentification) et déclenche l'enregistrement.
  telechargerPdf: async (token: string, commandeId: string, numero: string) => {
    const res = await fetch(`${BASE2}/factures/${commandeId}/pdf`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new ApiError(res.status, "PDF indisponible");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${numero}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  },
};

export const premiumApi = {
  souscrire: (token: string, formule = "PREMIUM") =>
    request<Abonnement>("/premium/souscrire", { method: "POST", body: JSON.stringify({ formule }) }, token),

  monAbonnement: (token: string) =>
    request<Abonnement | null>("/premium/mon-abonnement", {}, token),
};

export const analytics = {
  previsions: (token: string) => request<Prevision[]>("/previsions", {}, token),
  kpis: (token: string) => request<Kpis>("/kpis", {}, token),
};

export interface PaiementItem {
  commande_id: string;
  type: "ESCROW" | "AVANCE";
  montant: number;
  statut: string;
  date: string | null;
  produits: string;
}

export interface MesPaiements {
  total_recu: number;
  nb: number;
  paiements: PaiementItem[];
}

export const paiementsApi = {
  mesPaiements: (token: string) => request<MesPaiements>("/paiements/mes", {}, token),
};

export { ApiError };
