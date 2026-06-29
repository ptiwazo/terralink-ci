import { useEffect, useState } from "react";
import { paiementsApi, type MesPaiements } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Layout from "../components/Layout";
import { formatFCFA } from "../lib/ui";

export default function MesPaiementsPage() {
  const { token } = useAuth();
  const [data, setData] = useState<MesPaiements | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    paiementsApi
      .mesPaiements(token)
      .then(setData)
      .catch(() => setErreur("Chargement impossible"));
  }, [token]);

  return (
    <Layout>
      <h1 className="mb-4 text-xl font-bold">Mes paiements</h1>
      {erreur && <div className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{erreur}</div>}

      {data && (
        <>
          <div className="mb-4 rounded-xl bg-white p-5 shadow">
            <div className="text-xs text-gray-400">Total reçu</div>
            <div className="text-2xl font-bold text-terra-700">{formatFCFA(data.total_recu)}</div>
            <div className="text-xs text-gray-400">{data.nb} versement(s)</div>
          </div>

          <div className="space-y-3">
            {data.paiements.length === 0 && (
              <p className="text-sm text-gray-500">Aucun paiement reçu pour le moment.</p>
            )}
            {data.paiements.map((p, i) => (
              <div key={`${p.commande_id}-${i}`} className="rounded-xl bg-white p-4 shadow">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium">{formatFCFA(p.montant)}</div>
                    <div className="text-xs text-gray-400">{p.produits}</div>
                    {p.date && (
                      <div className="text-xs text-gray-400">
                        {new Date(p.date).toLocaleString("fr-FR")}
                      </div>
                    )}
                  </div>
                  <div className="text-right">
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${
                        p.type === "ESCROW" ? "bg-green-100 text-green-700" : "bg-blue-100 text-blue-700"
                      }`}
                    >
                      {p.type === "ESCROW" ? "Vente (escrow)" : "Avance"}
                    </span>
                    <div className="mt-1 text-xs text-gray-400">{p.statut}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </Layout>
  );
}
