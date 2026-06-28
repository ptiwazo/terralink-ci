import { useEffect, useState } from "react";
import {
  ApiError,
  tresorerie,
  type AcheteurProfil,
  type Eligibilite,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Layout from "../components/Layout";
import { formatFCFA } from "../lib/ui";

const TYPES = ["HOTEL", "RESTAURANT", "SUPERMARCHE", "USINE", "AUTRE"];

export default function AcheteurPage() {
  const { token } = useAuth();
  const [profil, setProfil] = useState<AcheteurProfil | null>(null);
  const [elig, setElig] = useState<Eligibilite | null>(null);
  const [charge, setCharge] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [form, setForm] = useState({ type: "RESTAURANT", adresse: "" });

  async function recharger() {
    if (!token) return;
    setElig(await tresorerie.monEligibilite(token));
  }

  useEffect(() => {
    if (!token) return;
    tresorerie
      .monProfil(token)
      .then(setProfil)
      .catch(() => setProfil(null))
      .finally(() => setCharge(true));
    recharger().catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function creer(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setErreur(null);
    try {
      setProfil(await tresorerie.creerProfil(token, { type: form.type, adresse: form.adresse }));
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Création impossible");
    }
  }

  const champ = "w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-terra-600 focus:outline-none";

  return (
    <Layout>
      <h1 className="mb-4 text-xl font-bold">Mon compte acheteur</h1>
      {erreur && <div className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{erreur}</div>}

      {elig && (
        <div className="mb-4 rounded-xl bg-white p-5 shadow">
          <h2 className="mb-3 font-semibold">Crédit / paiement différé</h2>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <Info label="Plafond effectif" valeur={formatFCFA(elig.plafond_effectif)} />
            <Info label="Disponible" valeur={formatFCFA(elig.disponible)} fort />
            <Info label="Encours" valeur={formatFCFA(elig.encours)} />
            <Info label="Score (commandes comptant)" valeur={String(elig.score)} />
          </div>
          <p className="mt-3 text-xs text-gray-400">
            Le plafond augmente avec votre historique de commandes comptant menées à terme.
          </p>
        </div>
      )}

      {charge && profil ? (
        <div className="rounded-xl bg-white p-5 shadow">
          <div className="text-lg font-medium">{profil.type}</div>
          {profil.adresse && <div className="text-sm text-gray-500">{profil.adresse}</div>}
        </div>
      ) : charge ? (
        <form onSubmit={creer} className="space-y-3 rounded-xl bg-white p-5 shadow">
          <h2 className="font-semibold">Compléter mon profil</h2>
          <label className="block text-sm">
            Type d'établissement
            <select value={form.type} onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))} className={champ}>
              {TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            Adresse
            <input value={form.adresse} onChange={(e) => setForm((f) => ({ ...f, adresse: e.target.value }))} placeholder="Cocody, Abidjan" className={champ} />
          </label>
          <button className="rounded-lg bg-terra-700 px-4 py-2 font-medium text-white hover:bg-terra-800">
            Enregistrer
          </button>
        </form>
      ) : null}
    </Layout>
  );
}

function Info({ label, valeur, fort }: { label: string; valeur: string; fort?: boolean }) {
  return (
    <div className="rounded-lg bg-gray-50 px-3 py-2">
      <div className="text-xs text-gray-400">{label}</div>
      <div className={fort ? "font-semibold text-terra-700" : "font-medium"}>{valeur}</div>
    </div>
  );
}
