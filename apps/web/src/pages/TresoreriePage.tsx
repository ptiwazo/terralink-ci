import { useEffect, useState } from "react";
import { ApiError, tresorerie, type Avance } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Layout from "../components/Layout";
import { formatFCFA } from "../lib/ui";

export default function TresoreriePage() {
  const { token } = useAuth();
  const [impayes, setImpayes] = useState<Avance[]>([]);
  const [erreur, setErreur] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  async function charger() {
    if (!token) return;
    setImpayes(await tresorerie.impayes(token));
  }

  useEffect(() => {
    charger().catch(() => setErreur("Chargement impossible"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function marquer() {
    if (!token) return;
    setErreur(null);
    setInfo(null);
    try {
      const res = await tresorerie.marquerImpayes(token);
      setInfo(`${res.impayes_marques} créance(s) basculée(s) en impayé.`);
      await charger();
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Action impossible");
    }
  }

  return (
    <Layout>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Trésorerie — impayés</h1>
        <button onClick={marquer} className="rounded-lg bg-terra-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-terra-800">
          Marquer les échéances dépassées
        </button>
      </div>
      {erreur && <div className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{erreur}</div>}
      {info && <div className="mb-4 rounded bg-green-50 px-3 py-2 text-sm text-green-700">{info}</div>}

      <div className="space-y-3">
        {impayes.length === 0 && <p className="text-sm text-gray-500">Aucun impayé.</p>}
        {impayes.map((a) => (
          <div key={a.id} className="rounded-xl bg-white p-4 shadow">
            <div className="font-medium">{formatFCFA(a.montant)}</div>
            <div className="text-sm text-gray-500">
              Échéance : {new Date(a.echeance).toLocaleDateString("fr-FR")} · avance versée {formatFCFA(a.montant_avance)}
            </div>
            <span className="mt-1 inline-block rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
              {a.statut}
            </span>
          </div>
        ))}
      </div>
    </Layout>
  );
}
