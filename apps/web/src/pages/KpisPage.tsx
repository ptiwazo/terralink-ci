import { useEffect, useState } from "react";
import { analytics, type Kpis } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Layout from "../components/Layout";
import { formatFCFA } from "../lib/ui";

export default function KpisPage() {
  const { token } = useAuth();
  const [k, setK] = useState<Kpis | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    analytics.kpis(token).then(setK).catch(() => setErreur("Chargement impossible"));
  }, [token]);

  return (
    <Layout>
      <h1 className="mb-4 text-xl font-bold">Tableau de bord</h1>
      {erreur && <div className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{erreur}</div>}

      {k && (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <Carte label="GMV (ventes réalisées)" valeur={formatFCFA(k.gmv)} fort />
            <Carte label="Commandes" valeur={String(k.nb_commandes)} />
            <Carte label="Acheteurs" valeur={String(k.nb_acheteurs)} />
            <Carte label="Rétention" valeur={`${(k.retention * 100).toFixed(0)} %`} />
            <Carte label="Sinistralité" valeur={`${(k.sinistralite * 100).toFixed(1)} %`} />
            <Carte label="Litiges" valeur={String(k.nb_litiges)} />
            <Carte label="Impayés" valeur={`${k.impayes_nb} · ${formatFCFA(k.impayes_montant)}`} />
          </div>

          <h2 className="mb-2 mt-6 font-semibold">Revenus</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Carte label="Commission" valeur={formatFCFA(k.revenus.commission)} />
            <Carte label="Décote" valeur={formatFCFA(k.revenus.decote)} />
            <Carte label="Abonnements" valeur={formatFCFA(k.revenus.abonnement)} />
            <Carte label="Pertes" valeur={formatFCFA(k.revenus.pertes)} />
          </div>

          <h2 className="mb-2 mt-6 font-semibold">Commandes par statut</h2>
          <div className="flex flex-wrap gap-2">
            {Object.entries(k.par_statut).map(([s, n]) => (
              <span key={s} className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700">
                {s} : {n}
              </span>
            ))}
          </div>
        </>
      )}
    </Layout>
  );
}

function Carte({ label, valeur, fort }: { label: string; valeur: string; fort?: boolean }) {
  return (
    <div className="rounded-xl bg-white p-4 shadow">
      <div className="text-xs text-gray-400">{label}</div>
      <div className={fort ? "text-lg font-bold text-terra-700" : "text-base font-semibold"}>{valeur}</div>
    </div>
  );
}
