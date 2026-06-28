import { useEffect, useState } from "react";
import { ApiError, api, type Commande } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Layout from "../components/Layout";
import {
  STATUT_COULEUR,
  STATUT_LABELS,
  actionsDisponibles,
  formatFCFA,
} from "../lib/ui";

export default function CommandesPage() {
  const { token, user } = useAuth();
  const [commandes, setCommandes] = useState<Commande[]>([]);
  const [erreur, setErreur] = useState<string | null>(null);

  async function charger() {
    if (!token) return;
    setCommandes(await api.mesCommandes(token));
  }

  useEffect(() => {
    charger().catch(() => setErreur("Chargement impossible"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function transition(id: string, action: string) {
    if (!token) return;
    setErreur(null);
    try {
      await api.transitionCommande(token, id, action);
      await charger();
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Action impossible");
    }
  }

  return (
    <Layout>
      <h1 className="mb-4 text-xl font-bold">Mes commandes</h1>
      {erreur && <div className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{erreur}</div>}

      <div className="space-y-3">
        {commandes.length === 0 && <p className="text-sm text-gray-500">Aucune commande.</p>}
        {commandes.map((c) => {
          const actions = user ? actionsDisponibles(c.statut, user.role) : [];
          return (
            <div key={c.id} className="rounded-xl bg-white p-4 shadow">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-medium">{formatFCFA(c.montant_total)}</div>
                  <div className="text-xs text-gray-400">
                    {c.lignes.map((l) => `${l.quantite} × ${l.produit.nom}`).join(", ")}
                  </div>
                  <div className="text-xs text-gray-400">
                    {new Date(c.created_at).toLocaleString("fr-FR")} · {c.mode_paiement}
                  </div>
                </div>
                <span className={`rounded-full px-2 py-1 text-xs font-medium ${STATUT_COULEUR[c.statut] ?? "bg-gray-100 text-gray-600"}`}>
                  {STATUT_LABELS[c.statut] ?? c.statut}
                </span>
              </div>
              {actions.length > 0 && (
                <div className="mt-3 flex gap-2">
                  {actions.map((a) => (
                    <button
                      key={a.action}
                      onClick={() => transition(c.id, a.action)}
                      className="rounded-lg bg-terra-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-terra-800"
                    >
                      {a.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Layout>
  );
}
