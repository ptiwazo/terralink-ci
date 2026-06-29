import { useEffect, useState } from "react";
import { ApiError, api, type Offre, type Produit } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Layout from "../components/Layout";
import MapPicker from "../components/MapPicker";
import { formatFCFA } from "../lib/ui";
import { CENTRE_CI, VILLES_CI } from "../lib/villes";

export default function OffresPage() {
  const { token } = useAuth();
  const [produits, setProduits] = useState<Produit[]>([]);
  const [offres, setOffres] = useState<Offre[]>([]);
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  const [form, setForm] = useState({
    produit_id: "",
    quantite_disponible: "",
    prix_unitaire: "",
    qualite: "",
    dispo_le: "",
    ville: "",
  });
  const [position, setPosition] = useState<{ lat: number; lng: number } | null>(null);
  const [centre, setCentre] = useState(CENTRE_CI);

  async function charger() {
    if (!token) return;
    const [p, o] = await Promise.all([api.produits(token), api.mesOffres(token)]);
    setProduits(p);
    setOffres(o);
    if (!form.produit_id && p.length) setForm((f) => ({ ...f, produit_id: p[0].id }));
  }

  useEffect(() => {
    charger().catch(() => setErreur("Chargement impossible"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function set<K extends keyof typeof form>(k: K, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  function choisirVille(nom: string) {
    set("ville", nom);
    const v = VILLES_CI.find((x) => x.nom === nom);
    if (v) {
      setCentre({ lat: v.lat, lng: v.lng });
      setPosition({ lat: v.lat, lng: v.lng }); // point pré-placé, affinable sur la carte
    }
  }

  function positionActuelle() {
    if (!navigator.geolocation) {
      setErreur("Géolocalisation indisponible — choisissez une ville ou cliquez sur la carte");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (p) => {
        const c = { lat: p.coords.latitude, lng: p.coords.longitude };
        setPosition(c);
        setCentre(c);
      },
      () => setErreur("Position refusée — choisissez une ville ou cliquez sur la carte")
    );
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setErreur(null);
    setEnCours(true);
    try {
      await api.creerOffre(token, {
        produit_id: form.produit_id,
        quantite_disponible: Number(form.quantite_disponible),
        prix_unitaire: Number(form.prix_unitaire),
        qualite: form.qualite || null,
        dispo_le: form.dispo_le,
        ville: form.ville || null,
        lat: position?.lat ?? null,
        lng: position?.lng ?? null,
      });
      setForm((f) => ({ ...f, quantite_disponible: "", prix_unitaire: "", qualite: "" }));
      setPosition(null);
      await charger();
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Création impossible");
    } finally {
      setEnCours(false);
    }
  }

  async function retirer(id: string) {
    if (!token) return;
    try {
      await api.retirerOffre(token, id);
      await charger();
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Retrait impossible");
    }
  }

  const champ = "w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-terra-600 focus:outline-none";

  return (
    <Layout>
      <h1 className="mb-4 text-xl font-bold">Mes offres</h1>
      {erreur && (
        <div className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{erreur}</div>
      )}

      <form onSubmit={onSubmit} className="mb-6 space-y-3 rounded-xl bg-white p-4 shadow">
        <h2 className="font-semibold">Publier une offre</h2>
        <div className="grid grid-cols-2 gap-3">
          <label className="col-span-2 text-sm">
            Produit
            <select value={form.produit_id} onChange={(e) => set("produit_id", e.target.value)} className={champ}>
              {produits.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nom} ({p.unite})
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Quantité
            <input type="number" min={1} required value={form.quantite_disponible} onChange={(e) => set("quantite_disponible", e.target.value)} className={champ} />
          </label>
          <label className="text-sm">
            Prix unitaire (FCFA)
            <input type="number" min={1} required value={form.prix_unitaire} onChange={(e) => set("prix_unitaire", e.target.value)} className={champ} />
          </label>
          <label className="text-sm">
            Disponible le
            <input type="date" required value={form.dispo_le} onChange={(e) => set("dispo_le", e.target.value)} className={champ} />
          </label>
          <label className="text-sm">
            Qualité
            <input value={form.qualite} onChange={(e) => set("qualite", e.target.value)} placeholder="ex: Premier choix" className={champ} />
          </label>
          <label className="col-span-2 text-sm">
            Ville
            <select value={form.ville} onChange={(e) => choisirVille(e.target.value)} className={champ}>
              <option value="">— Choisir une ville —</option>
              {VILLES_CI.map((v) => (
                <option key={v.nom} value={v.nom}>{v.nom}</option>
              ))}
            </select>
          </label>
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium">Position du produit</span>
            <button type="button" onClick={positionActuelle}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50">
              📍 Ma position actuelle
            </button>
          </div>
          <p className="mb-2 text-xs text-gray-400">
            Choisissez votre ville puis, si besoin, cliquez sur la carte (ou déplacez le repère) pour préciser l'emplacement exact.
          </p>
          <MapPicker value={position} center={centre} onChange={(lat, lng) => setPosition({ lat, lng })} />
          {position && (
            <p className="mt-1 text-xs text-gray-400">
              Point sélectionné : {position.lat.toFixed(4)}, {position.lng.toFixed(4)}
            </p>
          )}
        </div>

        <button disabled={enCours} className="rounded-lg bg-terra-700 px-4 py-2 font-medium text-white hover:bg-terra-800 disabled:opacity-60">
          {enCours ? "Publication…" : "Publier l'offre"}
        </button>
      </form>

      <div className="space-y-3">
        {offres.length === 0 && <p className="text-sm text-gray-500">Aucune offre publiée.</p>}
        {offres.map((o) => (
          <div key={o.id} className="flex items-center justify-between rounded-xl bg-white p-4 shadow">
            <div>
              <div className="font-medium">
                {o.produit.nom} · {formatFCFA(o.prix_unitaire)}/{o.produit.unite}
              </div>
              <div className="text-sm text-gray-500">
                Stock : {o.quantite_disponible} · dispo {o.dispo_le}
                {o.ville ? ` · ${o.ville}` : ""} ·{" "}
                <span className={o.statut === "DISPONIBLE" ? "text-green-600" : "text-gray-400"}>{o.statut}</span>
              </div>
            </div>
            {o.statut !== "RETIREE" && (
              <button onClick={() => retirer(o.id)} className="rounded border border-red-200 px-3 py-1 text-sm text-red-600 hover:bg-red-50">
                Retirer
              </button>
            )}
          </div>
        ))}
      </div>
    </Layout>
  );
}
