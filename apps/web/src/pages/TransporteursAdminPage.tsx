import { useEffect, useState } from "react";
import { ApiError, logistique, type Transporteur } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Layout from "../components/Layout";
import { formatFCFA } from "../lib/ui";

const COULEUR: Record<string, string> = {
  EN_ATTENTE: "bg-amber-100 text-amber-700",
  VALIDE: "bg-green-100 text-green-700",
  REJETE: "bg-red-100 text-red-700",
};

export default function TransporteursAdminPage() {
  const { token } = useAuth();
  const [liste, setListe] = useState<Transporteur[]>([]);
  const [erreur, setErreur] = useState<string | null>(null);

  async function charger() {
    if (!token) return;
    setListe(await logistique.transporteursTous(token));
  }

  useEffect(() => {
    charger().catch(() => setErreur("Chargement impossible"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function action(id: string, valider: boolean) {
    if (!token) return;
    setErreur(null);
    try {
      if (valider) await logistique.valider(token, id);
      else await logistique.rejeter(token, id);
      await charger();
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Action impossible");
    }
  }

  return (
    <Layout>
      <h1 className="mb-4 text-xl font-bold">Transporteurs</h1>
      {erreur && <div className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{erreur}</div>}

      <div className="space-y-3">
        {liste.length === 0 && <p className="text-sm text-gray-500">Aucun transporteur.</p>}
        {liste.map((t) => (
          <div key={t.id} className="flex items-center justify-between rounded-xl bg-white p-4 shadow">
            <div>
              <div className="font-medium">
                {t.vehicule} · {t.immatriculation}
                {t.note != null && <span className="ml-2 text-amber-500">★ {t.note}</span>}
              </div>
              <div className="text-sm text-gray-500">Caution : {formatFCFA(t.caution_deposee)}</div>
              <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${COULEUR[t.statut]}`}>
                {t.statut}
              </span>
            </div>
            {t.statut === "EN_ATTENTE" && (
              <div className="flex gap-2">
                <button onClick={() => action(t.id, true)} className="rounded-lg bg-terra-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-terra-800">
                  Valider
                </button>
                <button onClick={() => action(t.id, false)} className="rounded border border-red-200 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50">
                  Rejeter
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </Layout>
  );
}
