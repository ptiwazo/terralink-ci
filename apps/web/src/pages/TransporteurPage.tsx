import { useEffect, useState } from "react";
import { ApiError, logistique, type Transporteur } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Layout from "../components/Layout";
import { formatFCFA } from "../lib/ui";

const STATUT_LABEL: Record<string, string> = {
  EN_ATTENTE: "En attente de validation",
  VALIDE: "Validé",
  REJETE: "Rejeté",
};

export default function TransporteurPage() {
  const { token } = useAuth();
  const [profil, setProfil] = useState<Transporteur | null>(null);
  const [charge, setCharge] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [form, setForm] = useState({ vehicule: "", immatriculation: "", caution_deposee: "" });

  useEffect(() => {
    if (!token) return;
    logistique
      .monProfil(token)
      .then(setProfil)
      .catch(() => setProfil(null))
      .finally(() => setCharge(true));
  }, [token]);

  async function creer(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setErreur(null);
    try {
      const p = await logistique.creerProfil(token, {
        vehicule: form.vehicule,
        immatriculation: form.immatriculation,
        caution_deposee: Number(form.caution_deposee || 0),
      });
      setProfil(p);
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Création impossible");
    }
  }

  const champ = "w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-terra-600 focus:outline-none";

  return (
    <Layout>
      <h1 className="mb-4 text-xl font-bold">Mon profil transporteur</h1>
      {erreur && <div className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{erreur}</div>}

      {charge && profil && (
        <div className="space-y-2 rounded-xl bg-white p-5 shadow">
          <div className="text-lg font-medium">{profil.vehicule}</div>
          <div className="text-sm text-gray-500">Immatriculation : {profil.immatriculation}</div>
          <div className="text-sm text-gray-500">Caution : {formatFCFA(profil.caution_deposee)}</div>
          <div className="text-sm text-gray-500">
            Note moyenne : {profil.note != null ? `★ ${profil.note} / 5` : "pas encore notée"}
          </div>
          <div className="mt-2">
            <span className={`rounded-full px-3 py-1 text-sm font-medium ${
              profil.statut === "VALIDE" ? "bg-green-100 text-green-700"
                : profil.statut === "REJETE" ? "bg-red-100 text-red-700"
                : "bg-amber-100 text-amber-700"}`}>
              {STATUT_LABEL[profil.statut]}
            </span>
          </div>
          {profil.statut === "EN_ATTENTE" && (
            <p className="pt-2 text-xs text-gray-400">
              Votre profil sera vérifié par l'équipe TerraLink (caution) avant de pouvoir recevoir des courses.
            </p>
          )}
        </div>
      )}

      {charge && !profil && (
        <form onSubmit={creer} className="space-y-3 rounded-xl bg-white p-5 shadow">
          <h2 className="font-semibold">Créer mon profil</h2>
          <label className="block text-sm">
            Véhicule
            <input required value={form.vehicule} onChange={(e) => setForm((f) => ({ ...f, vehicule: e.target.value }))} placeholder="ex: Camionnette 3T" className={champ} />
          </label>
          <label className="block text-sm">
            Immatriculation
            <input required value={form.immatriculation} onChange={(e) => setForm((f) => ({ ...f, immatriculation: e.target.value }))} placeholder="CI-1234-AB" className={champ} />
          </label>
          <label className="block text-sm">
            Caution déposée (FCFA)
            <input type="number" min={0} value={form.caution_deposee} onChange={(e) => setForm((f) => ({ ...f, caution_deposee: e.target.value }))} className={champ} />
          </label>
          <button className="rounded-lg bg-terra-700 px-4 py-2 font-medium text-white hover:bg-terra-800">
            Créer mon profil
          </button>
        </form>
      )}
    </Layout>
  );
}
