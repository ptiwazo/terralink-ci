import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ROLE_LABELS, type Role } from "../auth/roles";

interface Lien {
  to: string;
  label: string;
}

const LIENS_PAR_ROLE: Record<Role, Lien[]> = {
  ADMIN: [
    { to: "/", label: "Accueil" },
    { to: "/commandes", label: "Commandes" },
    { to: "/transporteurs", label: "Transporteurs" },
    { to: "/tresorerie", label: "Trésorerie" },
    { to: "/kpis", label: "KPIs" },
  ],
  OPS: [
    { to: "/", label: "Accueil" },
    { to: "/commandes", label: "Commandes" },
    { to: "/transporteurs", label: "Transporteurs" },
    { to: "/tresorerie", label: "Trésorerie" },
    { to: "/kpis", label: "KPIs" },
  ],
  PRODUCTEUR: [
    { to: "/", label: "Accueil" },
    { to: "/offres", label: "Mes offres" },
    { to: "/commandes", label: "Commandes" },
    { to: "/paiements", label: "Mes paiements" },
    { to: "/previsions", label: "Prévisions" },
  ],
  ACHETEUR: [
    { to: "/", label: "Accueil" },
    { to: "/catalogue", label: "Catalogue" },
    { to: "/commandes", label: "Commandes" },
    { to: "/acheteur", label: "Mon compte" },
  ],
  TRANSPORTEUR: [
    { to: "/", label: "Accueil" },
    { to: "/mes-courses", label: "Mes courses" },
    { to: "/transporteur", label: "Mon profil" },
  ],
};

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const liens = user ? LIENS_PAR_ROLE[user.role] : [];

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 bg-terra-700 text-white shadow">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <span className="text-lg font-bold">TerraLink CI</span>
          {user && (
            <div className="flex items-center gap-3 text-sm">
              <span className="hidden sm:inline">
                {user.nom} · {ROLE_LABELS[user.role]}
              </span>
              <button
                onClick={logout}
                className="rounded bg-terra-800 px-3 py-1 font-medium hover:bg-terra-600"
              >
                Déconnexion
              </button>
            </div>
          )}
        </div>
        {liens.length > 0 && (
          <nav className="mx-auto flex max-w-3xl gap-1 px-2 pb-2 text-sm">
            {liens.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.to === "/"}
                className={({ isActive }) =>
                  `rounded px-3 py-1.5 font-medium ${
                    isActive ? "bg-white text-terra-800" : "text-white/90 hover:bg-terra-600"
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
          </nav>
        )}
      </header>
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-6">{children}</main>
      <footer className="py-4 text-center text-xs text-gray-400">
        TerraLink CI — Phase 1
      </footer>
    </div>
  );
}
