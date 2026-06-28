import { useEffect, useState } from "react";
import { analytics, type Prevision } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Layout from "../components/Layout";

export default function PrevisionsPage() {
  const { token } = useAuth();
  const [prevs, setPrevs] = useState<Prevision[]>([]);
  const [erreur, setErreur] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    analytics.previsions(token).then(setPrevs).catch(() => setErreur("Chargement impossible"));
  }, [token]);

  return (
    <Layout>
      <h1 className="mb-1 text-xl font-bold">Prévisions de récolte</h1>
      <p className="mb-4 text-sm text-gray-500">Offres disponibles à venir, agrégées par produit.</p>
      {erreur && <div className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{erreur}</div>}

      <div className="space-y-2">
        {prevs.length === 0 && <p className="text-sm text-gray-500">Aucune offre à venir.</p>}
        {prevs.map((p) => (
          <div key={p.produit} className="flex items-center justify-between rounded-xl bg-white p-4 shadow">
            <div className="font-medium">{p.produit}</div>
            <div className="text-sm text-gray-600">
              <b>{p.quantite_totale.toLocaleString("fr-FR")}</b> {p.unite} · {p.nb_offres} offre(s)
            </div>
          </div>
        ))}
      </div>
    </Layout>
  );
}
