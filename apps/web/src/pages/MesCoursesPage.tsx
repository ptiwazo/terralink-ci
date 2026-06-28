import { useEffect, useState } from "react";
import { ApiError, logistique, type Course } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Layout from "../components/Layout";
import { STATUT_COULEUR, STATUT_LABELS, formatFCFA } from "../lib/ui";

export default function MesCoursesPage() {
  const { token } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [erreur, setErreur] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [pos, setPos] = useState<Record<string, { lat: string; lng: string }>>({});

  async function charger() {
    if (!token) return;
    setCourses(await logistique.mesCourses(token));
  }

  useEffect(() => {
    charger().catch(() => setErreur("Chargement impossible"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function setChamp(cid: string, k: "lat" | "lng", v: string) {
    setPos((p) => ({ ...p, [cid]: { ...(p[cid] ?? { lat: "", lng: "" }), [k]: v } }));
  }

  function positionActuelle(cid: string) {
    if (!navigator.geolocation) {
      setErreur("Géolocalisation indisponible sur cet appareil");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (p) =>
        setPos((s) => ({
          ...s,
          [cid]: { lat: String(p.coords.latitude), lng: String(p.coords.longitude) },
        })),
      () => setErreur("Position refusée — saisir manuellement")
    );
  }

  async function envoyer(cid: string) {
    if (!token) return;
    const v = pos[cid];
    if (!v?.lat || !v?.lng) {
      setErreur("Saisir une position");
      return;
    }
    setErreur(null);
    setInfo(null);
    try {
      await logistique.ajouterPosition(token, cid, Number(v.lat), Number(v.lng));
      setInfo("Position enregistrée.");
      await charger();
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Envoi impossible");
    }
  }

  return (
    <Layout>
      <h1 className="mb-4 text-xl font-bold">Mes courses</h1>
      {erreur && <div className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{erreur}</div>}
      {info && <div className="mb-4 rounded bg-green-50 px-3 py-2 text-sm text-green-700">{info}</div>}

      <div className="space-y-3">
        {courses.length === 0 && (
          <p className="text-sm text-gray-500">
            Aucune course assignée. (Votre profil doit être validé pour recevoir des courses.)
          </p>
        )}
        {courses.map(({ livraison, commande_id, commande_statut, montant, produits }) => (
          <div key={livraison.id} className="rounded-xl bg-white p-4 shadow">
            <div className="flex items-start justify-between">
              <div>
                <div className="font-medium">{produits}</div>
                <div className="text-sm text-gray-500">{formatFCFA(montant)}</div>
                <div className="text-xs text-gray-400">
                  Assurance {livraison.assurance_ref ?? "—"} · {livraison.gps_traces.length} position(s) GPS
                </div>
              </div>
              <span className={`rounded-full px-2 py-1 text-xs font-medium ${STATUT_COULEUR[commande_statut] ?? "bg-gray-100 text-gray-600"}`}>
                {STATUT_LABELS[commande_statut] ?? commande_statut}
              </span>
            </div>

            {livraison.statut === "EN_COURS" && (
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <button onClick={() => positionActuelle(commande_id)}
                  className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50">
                  Position actuelle
                </button>
                <input placeholder="lat" value={pos[commande_id]?.lat ?? ""} onChange={(e) => setChamp(commande_id, "lat", e.target.value)}
                  className="w-24 rounded-lg border border-gray-300 px-2 py-1.5 text-sm" />
                <input placeholder="lng" value={pos[commande_id]?.lng ?? ""} onChange={(e) => setChamp(commande_id, "lng", e.target.value)}
                  className="w-24 rounded-lg border border-gray-300 px-2 py-1.5 text-sm" />
                <button onClick={() => envoyer(commande_id)}
                  className="rounded-lg bg-terra-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-terra-800">
                  Pointer
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </Layout>
  );
}
