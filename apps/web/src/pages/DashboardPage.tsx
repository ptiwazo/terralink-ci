import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ROLE_LABELS } from "../auth/roles";
import Layout from "../components/Layout";

// Sections du tableau de bord qui mènent à une page implémentée (Phase 1).
const SECTION_LIENS: Record<string, string> = {
  "Mes offres": "/offres",
  Catalogue: "/catalogue",
  "Mes commandes": "/commandes",
  Commandes: "/commandes",
  Transporteurs: "/transporteurs",
  "Mes courses": "/mes-courses",
  "Livraisons à confirmer": "/mes-courses",
};

interface Dashboard {
  role: string;
  nom: string;
  sections: string[];
  message: string;
}

export default function DashboardPage() {
  const { token, user } = useAuth();
  const [data, setData] = useState<Dashboard | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .dashboard(token)
      .then(setData)
      .catch(() => setErreur("Impossible de charger le tableau de bord"));
  }, [token]);

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-xl font-bold">
          Bonjour {user?.nom?.split(" ")[0]} 👋
        </h1>
        <p className="text-sm text-gray-500">
          Espace {user ? ROLE_LABELS[user.role] : ""}
        </p>
      </div>

      {erreur && (
        <div className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">
          {erreur}
        </div>
      )}

      {data && (
        <div className="rounded-lg bg-terra-700/5 px-4 py-3 text-sm text-terra-800">
          {data.message}
        </div>
      )}

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {(data?.sections ?? []).map((section) => {
          const lien = SECTION_LIENS[section];
          const classe =
            "flex min-h-20 items-center justify-center rounded-xl border bg-white p-4 text-center text-sm font-medium";
          return lien ? (
            <Link
              key={section}
              to={lien}
              className={`${classe} border-terra-600 text-terra-800 hover:bg-terra-700/5`}
            >
              {section}
            </Link>
          ) : (
            <div
              key={section}
              className={`${classe} border-dashed border-gray-300 text-gray-600`}
            >
              {section}
              <span className="ml-1 text-xs text-gray-300">(bientôt)</span>
            </div>
          );
        })}
      </div>
    </Layout>
  );
}
