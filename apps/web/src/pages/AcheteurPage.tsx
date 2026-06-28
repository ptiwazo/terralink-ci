import { useEffect, useState } from "react";
import {
  ApiError,
  premiumApi,
  tresorerie,
  type AcheteurProfil,
  type Abonnement,
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
  const [abo, setAbo] = useState<Abonnement | null>(null);
  const [charge, setCharge] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [form, setForm] = useState({ type: "RESTAURANT", adresse: "" });
  const [coords, setCoords] = useState({ lat: "", lng: "" });

  async function recharger() {
    if (!token) return;
    setElig(await tresorerie.monEligibilite(token));
  }

  useEffect(() => {
    if (!token) return;
    tresorerie
      .monProfil(token)
      .then((p) => {
        setProfil(p);
        if (p) setCoords({ lat: p.lat != null ? String(p.lat) : "", lng: p.lng != null ? String(p.lng) : "" });
      })
      .catch(() => setProfil(null))
      .finally(() => setCharge(true));
    recharger().catch(() => {});
    premiumApi.monAbonnement(token).then(setAbo).catch(() => setAbo(null));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function positionActuelle() {
    if (!navigator.geolocation) {
      setErreur("Géolocalisation indisponible sur cet appareil");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (p) => setCoords({ lat: String(p.coords.latitude), lng: String(p.coords.longitude) }),
      () => setErreur("Position refusée — saisir manuellement")
    );
  }

  async function enregistrerPosition() {
    if (!token) return;
    setErreur(null);
    setInfo(null);
    try {
      const p = await tresorerie.majProfil(token, {
        lat: coords.lat ? Number(coords.lat) : undefined,
        lng: coords.lng ? Number(coords.lng) : undefined,
      });
      setProfil(p);
      setInfo("Adresse de livraison enregistrée.");
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Enregistrement impossible");
    }
  }

  async function souscrire() {
    if (!token) return;
    setErreur(null);
    try {
      setAbo(await premiumApi.souscrire(token, "PREMIUM"));
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Souscription impossible");
    }
  }

  const premiumActif = abo?.statut === "ACTIF" && new Date(abo.fin) > new Date();

  async function creer(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setErreur(null);
    try {
      setProfil(
        await tresorerie.creerProfil(token, {
          type: form.type,
          adresse: form.adresse,
          lat: coords.lat ? Number(coords.lat) : undefined,
          lng: coords.lng ? Number(coords.lng) : undefined,
        })
      );
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Création impossible");
    }
  }

  const champ = "w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-terra-600 focus:outline-none";

  return (
    <Layout>
      <h1 className="mb-4 text-xl font-bold">Mon compte acheteur</h1>
      {erreur && <div className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{erreur}</div>}
      {info && <div className="mb-4 rounded bg-green-50 px-3 py-2 text-sm text-green-700">{info}</div>}

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

      <div className="mb-4 rounded-xl bg-white p-5 shadow">
        <h2 className="mb-2 font-semibold">Abonnement premium</h2>
        {premiumActif ? (
          <p className="text-sm text-green-700">
            Premium actif jusqu'au {new Date(abo!.fin).toLocaleDateString("fr-FR")}.
          </p>
        ) : (
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">25 000 FCFA / mois — accès prioritaire.</p>
            <button onClick={souscrire} className="rounded-lg bg-terra-700 px-4 py-2 text-sm font-medium text-white hover:bg-terra-800">
              Souscrire
            </button>
          </div>
        )}
      </div>

      {charge && profil ? (
        <div className="space-y-4">
          <div className="rounded-xl bg-white p-5 shadow">
            <div className="text-lg font-medium">{profil.type}</div>
            {profil.adresse && <div className="text-sm text-gray-500">{profil.adresse}</div>}
          </div>

          <div className="rounded-xl bg-white p-5 shadow">
            <h2 className="mb-2 font-semibold">Adresse de livraison (suivi & ETA)</h2>
            <p className="mb-3 text-sm text-gray-500">
              Ces coordonnées servent à afficher la destination sur la carte et estimer l'arrivée.
              {profil.lat != null ? " ✓ définie" : " — non définie"}
            </p>
            <div className="flex flex-wrap items-center gap-2">
              <button onClick={positionActuelle} className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
                Position actuelle
              </button>
              <input value={coords.lat} onChange={(e) => setCoords((s) => ({ ...s, lat: e.target.value }))} placeholder="lat" className="w-28 rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              <input value={coords.lng} onChange={(e) => setCoords((s) => ({ ...s, lng: e.target.value }))} placeholder="lng" className="w-28 rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              <button onClick={enregistrerPosition} className="rounded-lg bg-terra-700 px-4 py-2 text-sm font-medium text-white hover:bg-terra-800">
                Enregistrer
              </button>
            </div>
          </div>
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
