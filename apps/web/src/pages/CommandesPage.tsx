import { useEffect, useRef, useState } from "react";
import {
  ApiError,
  api,
  facturation,
  logistique,
  tresorerie,
  type Commande,
  type Suivi,
  type Transporteur,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Layout from "../components/Layout";
import MapTrace from "../components/MapTrace";
import {
  STATUT_COULEUR,
  STATUT_LABELS,
  actionsDisponibles,
  formatFCFA,
} from "../lib/ui";

export default function CommandesPage() {
  const { token, user } = useAuth();
  const [commandes, setCommandes] = useState<Commande[]>([]);
  const [transporteurs, setTransporteurs] = useState<Transporteur[]>([]);
  const [erreur, setErreur] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [choixTransporteur, setChoixTransporteur] = useState<Record<string, string>>({});
  const [codeRevele, setCodeRevele] = useState<Record<string, string>>({});
  const [codeSaisi, setCodeSaisi] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState<Record<string, number>>({});
  const [suiviOuvert, setSuiviOuvert] = useState<Record<string, boolean>>({});
  const [suivis, setSuivis] = useState<Record<string, Suivi | null>>({});
  const dejaProche = useRef<Set<string>>(new Set());

  const role = user?.role;
  const estProducteur = role === "PRODUCTEUR";

  async function charger() {
    if (!token) return;
    setCommandes(await api.mesCommandes(token));
  }

  useEffect(() => {
    charger().catch(() => setErreur("Chargement impossible"));
    if (token && estProducteur) {
      logistique.transporteursValides(token).then(setTransporteurs).catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function wrap(fn: () => Promise<unknown>, msg: string) {
    return async () => {
      if (!token) return;
      setErreur(null);
      try {
        await fn();
        await charger();
      } catch (err) {
        setErreur(err instanceof ApiError ? err.message : msg);
      }
    };
  }

  async function assigner(cid: string) {
    if (!token) return;
    const tid = choixTransporteur[cid] || transporteurs[0]?.id;
    if (!tid) {
      setErreur("Aucun transporteur validé disponible");
      return;
    }
    setErreur(null);
    try {
      const res = await logistique.assigner(token, cid, tid);
      setCodeRevele((c) => ({ ...c, [cid]: res.code_remise }));
      await charger();
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Assignation impossible");
    }
  }

  async function confirmer(cid: string) {
    if (!token) return;
    const code = codeSaisi[cid];
    if (!code) {
      setErreur("Saisir le code de remise");
      return;
    }
    setErreur(null);
    try {
      await logistique.confirmerReception(token, cid, code);
      await charger();
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Confirmation impossible");
    }
  }

  const peutPayer = role === "ACHETEUR" || role === "OPS" || role === "ADMIN";
  const estOps = role === "OPS" || role === "ADMIN";

  // Créance différée encore à régler (acheteur/OPS).
  const STATUTS_CREANCE = ["AVANCE_VERSEE", "EN_PREPARATION", "EN_LIVRAISON", "LIVREE_CONFORME"];
  function peutRembourser(c: Commande) {
    return (
      c.mode_paiement === "DIFFERE" &&
      STATUTS_CREANCE.includes(c.statut) &&
      (role === "ACHETEUR" || estOps)
    );
  }

  const FACTURABLES = ["FONDS_LIBERES", "CLOTUREE", "RESOLUE_LIBEREE"];

  async function emettreFacture(cid: string) {
    if (!token) return;
    setErreur(null);
    try {
      const f = await facturation.emettre(token, cid);
      await facturation.telechargerPdf(token, cid, f.numero);
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Émission impossible");
    }
  }

  async function telechargerFacture(cid: string) {
    if (!token) return;
    setErreur(null);
    try {
      const f = await facturation.getFacture(token, cid);
      await facturation.telechargerPdf(token, cid, f.numero);
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Facture non disponible");
    }
  }

  const NOTABLES = ["LIVREE_CONFORME", "FONDS_LIBERES", "CLOTUREE", "RESOLUE_LIBEREE"];

  async function noter(cid: string, note: number) {
    if (!token) return;
    setErreur(null);
    try {
      await logistique.noterTransporteur(token, cid, note);
      setNotes((n) => ({ ...n, [cid]: note }));
    } catch (err) {
      setErreur(err instanceof ApiError ? err.message : "Notation impossible");
    }
  }

  // --- Suivi de la livraison sur carte (acheteur/producteur) ---
  const SUIVABLES = ["EN_LIVRAISON", "LIVREE_CONFORME", "FONDS_LIBERES", "CLOTUREE", "RESOLUE_LIBEREE"];

  async function chargerSuivi(cid: string) {
    if (!token) return;
    try {
      const s = await logistique.getSuivi(token, cid);
      setSuivis((m) => ({ ...m, [cid]: s }));
      // Alerte à l'approche (une fois par course).
      if (s.proche && !dejaProche.current.has(cid)) {
        dejaProche.current.add(cid);
        setInfo("🔔 Le véhicule approche de votre adresse de livraison !");
        if ("Notification" in window && Notification.permission === "granted") {
          new Notification("TerraLink CI", { body: "Votre livraison approche !" });
        }
      }
    } catch {
      setSuivis((m) => ({ ...m, [cid]: null }));
    }
  }

  function toggleSuivi(cid: string) {
    setSuiviOuvert((s) => {
      const open = !s[cid];
      if (open) {
        if ("Notification" in window && Notification.permission === "default") {
          Notification.requestPermission().catch(() => {});
        }
        chargerSuivi(cid);
      }
      return { ...s, [cid]: open };
    });
  }

  // Rafraîchit les suivis ouverts toutes les 15 s (suivi quasi temps réel).
  useEffect(() => {
    const ouverts = Object.keys(suiviOuvert).filter((c) => suiviOuvert[c]);
    if (ouverts.length === 0 || !token) return;
    const id = setInterval(() => ouverts.forEach((c) => chargerSuivi(c)), 15000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [suiviOuvert, token]);

  return (
    <Layout>
      <h1 className="mb-4 text-xl font-bold">Mes commandes</h1>
      {erreur && <div className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{erreur}</div>}
      {info && <div className="mb-4 rounded bg-green-50 px-3 py-2 text-sm text-green-700">{info}</div>}

      <div className="space-y-3">
        {commandes.length === 0 && <p className="text-sm text-gray-500">Aucune commande.</p>}
        {commandes.map((c) => {
          const actions = role ? actionsDisponibles(c.statut, role) : [];
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

              {/* Paiement (acheteur) */}
              {c.statut === "CREEE" && peutPayer && (
                <button onClick={wrap(() => api.payerCommande(token!, c.id), "Paiement impossible")}
                  className="mt-3 rounded-lg bg-terra-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-terra-800">
                  Payer (séquestre)
                </button>
              )}

              {/* Assignation transporteur (producteur) */}
              {estProducteur && c.statut === "EN_PREPARATION" && (
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <select
                    value={choixTransporteur[c.id] ?? ""}
                    onChange={(e) => setChoixTransporteur((s) => ({ ...s, [c.id]: e.target.value }))}
                    className="rounded-lg border border-gray-300 px-2 py-1.5 text-sm"
                  >
                    <option value="">Choisir un transporteur…</option>
                    {transporteurs.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.vehicule} ({t.immatriculation}){t.note != null ? ` — ★${t.note}` : ""}
                      </option>
                    ))}
                  </select>
                  <button onClick={() => assigner(c.id)}
                    className="rounded-lg bg-terra-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-terra-800">
                    Assigner
                  </button>
                </div>
              )}

              {/* Code de remise révélé (une fois) */}
              {codeRevele[c.id] && (
                <div className="mt-2 rounded bg-amber-50 px-3 py-2 text-sm text-amber-800">
                  Code de remise : <b>{codeRevele[c.id]}</b> — à remettre au transporteur.
                </div>
              )}

              {/* Confirmation par code (acheteur) */}
              {role === "ACHETEUR" && c.statut === "EN_LIVRAISON" && (
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <input
                    placeholder="Code de remise"
                    value={codeSaisi[c.id] ?? ""}
                    onChange={(e) => setCodeSaisi((s) => ({ ...s, [c.id]: e.target.value }))}
                    className="w-36 rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
                  />
                  <button onClick={() => confirmer(c.id)}
                    className="rounded-lg bg-terra-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-terra-800">
                    Confirmer réception
                  </button>
                </div>
              )}

              {/* Remboursement de créance (différé) */}
              {peutRembourser(c) && (
                <div className="mt-3">
                  <button onClick={wrap(() => tresorerie.rembourserCreance(token!, c.id), "Remboursement impossible")}
                    className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700">
                    Rembourser la créance
                  </button>
                </div>
              )}

              {/* Résolution de litige (OPS) */}
              {estOps && c.statut === "LITIGE" && (
                <div className="mt-3 flex gap-2">
                  <button onClick={wrap(() => logistique.resoudre(token!, c.id, "REMBOURSE"), "Échec")}
                    className="rounded-lg bg-orange-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-orange-700">
                    Rembourser l'acheteur
                  </button>
                  <button onClick={wrap(() => logistique.resoudre(token!, c.id, "LIBERE"), "Échec")}
                    className="rounded-lg bg-terra-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-terra-800">
                    Libérer au producteur
                  </button>
                </div>
              )}

              {/* Suivi de la livraison sur carte */}
              {SUIVABLES.includes(c.statut) && (
                <div className="mt-3">
                  <button onClick={() => toggleSuivi(c.id)}
                    className="text-sm font-medium text-terra-700 hover:underline">
                    {suiviOuvert[c.id] ? "Masquer le suivi" : "📍 Suivre la livraison"}
                  </button>
                  {suiviOuvert[c.id] && (
                    <div className="mt-2">
                      {suivis[c.id] === undefined ? (
                        <p className="text-sm text-gray-400">Chargement…</p>
                      ) : suivis[c.id] && suivis[c.id]!.positions.length > 0 ? (
                        <>
                          {suivis[c.id]!.proche && (
                            <div className="mb-2 rounded bg-amber-100 px-3 py-2 text-sm font-medium text-amber-800">
                              🔔 Le véhicule approche !
                            </div>
                          )}
                          <MapTrace
                            traces={suivis[c.id]!.positions}
                            destination={suivis[c.id]!.destination}
                          />
                          <div className="mt-1 flex flex-wrap gap-3 text-xs text-gray-500">
                            {suivis[c.id]!.distance_km != null && (
                              <span>Distance : <b>{suivis[c.id]!.distance_km} km</b></span>
                            )}
                            {suivis[c.id]!.eta_minutes != null && (
                              <span>Arrivée estimée : <b>~{suivis[c.id]!.eta_minutes} min</b></span>
                            )}
                            {suivis[c.id]!.destination == null && (
                              <span className="text-amber-600">
                                Définissez votre adresse de livraison (Mon compte) pour la distance et l'ETA.
                              </span>
                            )}
                            <span>· actualisé toutes les 15 s</span>
                          </div>
                        </>
                      ) : (
                        <p className="text-sm text-gray-500">Position non encore disponible.</p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Facturation (émission OPS, téléchargement parties) */}
              {FACTURABLES.includes(c.statut) && (
                <div className="mt-3 flex gap-2">
                  {estOps && (
                    <button onClick={() => emettreFacture(c.id)}
                      className="rounded-lg bg-gray-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-800">
                      Émettre la facture
                    </button>
                  )}
                  <button onClick={() => telechargerFacture(c.id)}
                    className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50">
                    Télécharger la facture
                  </button>
                </div>
              )}

              {/* Notation du transporteur (acheteur, après livraison) */}
              {role === "ACHETEUR" && NOTABLES.includes(c.statut) && (
                <div className="mt-3 flex items-center gap-1 text-sm">
                  <span className="mr-1 text-gray-500">Noter le transporteur :</span>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button key={n} onClick={() => noter(c.id, n)} title={`${n}/5`}
                      className={`text-lg ${notes[c.id] && n <= notes[c.id] ? "text-amber-500" : "text-gray-300 hover:text-amber-400"}`}>
                      ★
                    </button>
                  ))}
                  {notes[c.id] && <span className="ml-2 text-xs text-green-600">Merci !</span>}
                </div>
              )}

              {/* Transitions génériques (préparer/expédier/litige) */}
              {actions.length > 0 && (
                <div className="mt-3 flex gap-2">
                  {actions.map((a) => (
                    <button key={a.action}
                      onClick={wrap(() => api.transitionCommande(token!, c.id, a.action), "Action impossible")}
                      className={`rounded-lg px-3 py-1.5 text-sm font-medium text-white ${
                        a.action === "SIGNALER_LITIGE" ? "bg-red-600 hover:bg-red-700" : "bg-terra-700 hover:bg-terra-800"
                      }`}>
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
