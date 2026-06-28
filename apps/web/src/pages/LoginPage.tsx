import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [telephone, setTelephone] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErreur(null);
    setEnCours(true);
    try {
      await login(telephone, motDePasse);
      navigate("/", { replace: true });
    } catch (err) {
      setErreur(
        err instanceof ApiError ? err.message : "Connexion impossible"
      );
    } finally {
      setEnCours(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col justify-center px-4">
      <div className="mx-auto w-full max-w-sm">
        <h1 className="mb-1 text-center text-2xl font-bold text-terra-700">
          TerraLink CI
        </h1>
        <p className="mb-6 text-center text-sm text-gray-500">
          La marketplace agricole de confiance
        </p>

        <form onSubmit={onSubmit} className="space-y-4 rounded-xl bg-white p-6 shadow">
          <h2 className="text-lg font-semibold">Connexion</h2>

          {erreur && (
            <div className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">
              {erreur}
            </div>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium">Téléphone</label>
            <input
              type="tel"
              required
              value={telephone}
              onChange={(e) => setTelephone(e.target.value)}
              placeholder="+225 07 00 00 00 00"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-terra-600 focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Mot de passe</label>
            <input
              type="password"
              required
              value={motDePasse}
              onChange={(e) => setMotDePasse(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-terra-600 focus:outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={enCours}
            className="w-full rounded-lg bg-terra-700 py-2.5 font-medium text-white hover:bg-terra-800 disabled:opacity-60"
          >
            {enCours ? "Connexion…" : "Se connecter"}
          </button>

          <p className="text-center text-sm text-gray-500">
            Pas encore de compte ?{" "}
            <Link to="/inscription" className="font-medium text-terra-700">
              Créer un compte
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
