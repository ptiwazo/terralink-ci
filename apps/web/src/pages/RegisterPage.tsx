import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ROLES, ROLE_LABELS, type Role } from "../auth/roles";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    nom: "",
    telephone: "",
    mot_de_passe: "",
    role: "PRODUCTEUR" as Role,
  });
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErreur(null);
    setEnCours(true);
    try {
      await register(form);
      navigate("/", { replace: true });
    } catch (err) {
      setErreur(
        err instanceof ApiError ? err.message : "Inscription impossible"
      );
    } finally {
      setEnCours(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col justify-center px-4">
      <div className="mx-auto w-full max-w-sm">
        <h1 className="mb-6 text-center text-2xl font-bold text-terra-700">
          TerraLink CI
        </h1>

        <form onSubmit={onSubmit} className="space-y-4 rounded-xl bg-white p-6 shadow">
          <h2 className="text-lg font-semibold">Créer un compte</h2>

          {erreur && (
            <div className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">
              {erreur}
            </div>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium">Nom complet</label>
            <input
              required
              value={form.nom}
              onChange={(e) => set("nom", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-terra-600 focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Téléphone</label>
            <input
              type="tel"
              required
              value={form.telephone}
              onChange={(e) => set("telephone", e.target.value)}
              placeholder="+225 07 00 00 00 00"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-terra-600 focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Je suis…</label>
            <select
              value={form.role}
              onChange={(e) => set("role", e.target.value as Role)}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 focus:border-terra-600 focus:outline-none"
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABELS[r]}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Mot de passe</label>
            <input
              type="password"
              required
              minLength={8}
              value={form.mot_de_passe}
              onChange={(e) => set("mot_de_passe", e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-terra-600 focus:outline-none"
            />
            <p className="mt-1 text-xs text-gray-400">8 caractères minimum</p>
          </div>

          <button
            type="submit"
            disabled={enCours}
            className="w-full rounded-lg bg-terra-700 py-2.5 font-medium text-white hover:bg-terra-800 disabled:opacity-60"
          >
            {enCours ? "Création…" : "Créer mon compte"}
          </button>

          <p className="text-center text-sm text-gray-500">
            Déjà inscrit ?{" "}
            <Link to="/connexion" className="font-medium text-terra-700">
              Se connecter
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
