import type { ReactNode } from "react";
import { useAuth } from "../auth/AuthContext";
import { ROLE_LABELS } from "../auth/roles";

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 bg-terra-700 text-white shadow">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold">TerraLink CI</span>
          </div>
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
      </header>
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-6">{children}</main>
      <footer className="py-4 text-center text-xs text-gray-400">
        TerraLink CI — Phase 0
      </footer>
    </div>
  );
}
