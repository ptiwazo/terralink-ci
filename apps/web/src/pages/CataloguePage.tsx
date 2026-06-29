import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api, type CatalogueItem, type Produit } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Layout from "../components/Layout";
import { formatFCFA } from "../lib/ui";

export default function CataloguePage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [produits, setProduits] = useState<Produit[]>([]);
  const [items, setItems] = useState<CatalogueItem[]>([]);
  const [produitId, setProduitId] = useState("");
  const [quantites, setQuantites] = useState<Record<string, string>>({});
  const [mode, setMode] = useState<"COMPTANT" | "DIFFERE">("COMPTANT");
  const [erreur, setErreur] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  async function rechercher() {
    if (!token) return;
    setErreur(null);
    const data = await api.catalogue(token, produitId ? { produit_id: produitId } : {});
    setItems(data);
  }

  useEffect(() => {
    if (!token) return;
    api.produits(token).then(setProduits).catch(() => {});
    rechercher().catch(() => setErreur("Recherche impossible"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function commander(offreId: string) {
    if (!token) return;
    const q = Number(quantites[offreId]);
    if (!q || q <= 0) {
      setErreur("Saisir une quantité valide");
      return;
    }
    setErreur(null);
    setInfo(null);
    try {
      const cmd = await api.creerCommande(token, [{ offre_id: offreId, quantite: q }], mode);
      setInfo(`Commande créée (${mode === "DIFFERE" ? "différé" : "comptant"}) : ${formatFCFA(cmd.montant_total)}`);
      setTimeout(() => navigate("/commandes"), 800);
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Commande impossible");
    }
  }

  return (
    <Layout>
      <h1 className="mb-4 text-xl font-bold">Catalogue</h1>

      <div className="mb-4 flex gap-2">
        <select
          value={produitId}
          onChange={(e) => setProduitId(e.target.value)}
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2"
        >
          <option value="">Tous les produits</option>
          {produits.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nom}
            </option>
          ))}
        </select>
        <button onClick={() => rechercher()} className="rounded-lg bg-terra-700 px-4 py-2 font-medium text-white hover:bg-terra-800">
          Rechercher
        </button>
      </div>

      <div className="mb-4 flex items-center gap-2 text-sm">
        <span className="text-gray-500">Paiement :</span>
        <select value={mode} onChange={(e) => setMode(e.target.value as "COMPTANT" | "DIFFERE")}
          className="rounded-lg border border-gray-300 px-3 py-1.5">
          <option value="COMPTANT">Comptant (séquestre)</option>
          <option value="DIFFERE">Différé (crédit 30-60 j)</option>
        </select>
      </div>

      {erreur && <div className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{erreur}</div>}
      {info && <div className="mb-4 rounded bg-green-50 px-3 py-2 text-sm text-green-700">{info}</div>}

      <div className="space-y-3">
        {items.length === 0 && <p className="text-sm text-gray-500">Aucune offre disponible.</p>}
        {items.map(({ offre, distance_km }) => (
          <div key={offre.id} className="rounded-xl bg-white p-4 shadow">
            <div className="flex items-start justify-between">
              <div>
                <div className="font-medium">{offre.produit.nom}</div>
                <div className="text-sm text-gray-500">
                  {formatFCFA(offre.prix_unitaire)}/{offre.produit.unite} · {offre.producteur.nom}
                  {offre.qualite ? ` · ${offre.qualite}` : ""}
                </div>
                <div className="text-xs text-gray-400">
                  Stock {offre.quantite_disponible} · dispo {offre.dispo_le}
                  {offre.ville ? ` · ${offre.ville}` : ""}
                  {distance_km != null ? ` · ${distance_km.toFixed(1)} km` : ""}
                </div>
              </div>
            </div>
            <div className="mt-3 flex gap-2">
              <input
                type="number"
                min={1}
                max={offre.quantite_disponible}
                placeholder="Qté"
                value={quantites[offre.id] ?? ""}
                onChange={(e) => setQuantites((q) => ({ ...q, [offre.id]: e.target.value }))}
                className="w-24 rounded-lg border border-gray-300 px-3 py-2"
              />
              <button onClick={() => commander(offre.id)} className="rounded-lg bg-terra-700 px-4 py-2 font-medium text-white hover:bg-terra-800">
                Commander
              </button>
            </div>
          </div>
        ))}
      </div>
    </Layout>
  );
}
