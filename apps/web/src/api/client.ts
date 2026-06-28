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
};

export { ApiError };
