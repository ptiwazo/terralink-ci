import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, type AuthResponse, type UserPublic } from "../api/client";

interface AuthState {
  user: UserPublic | null;
  token: string | null;
  loading: boolean;
  login: (telephone: string, motDePasse: string) => Promise<void>;
  register: (data: Parameters<typeof api.register>[0]) => Promise<void>;
  logout: () => void;
}

const STORAGE_KEY = "terralink.auth";
const AuthContext = createContext<AuthState | null>(null);

interface Stored {
  token: string;
  refresh: string;
  user: UserPublic;
}

function load(): Stored | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Stored) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = load();
    if (stored) {
      setToken(stored.token);
      setUser(stored.user);
      // Revalide le jeton auprès du serveur; déconnecte si invalide/expiré.
      api
        .me(stored.token)
        .then((u) => setUser(u))
        .catch(() => {
          localStorage.removeItem(STORAGE_KEY);
          setToken(null);
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const persist = useCallback((res: AuthResponse) => {
    const stored: Stored = {
      token: res.tokens.access_token,
      refresh: res.tokens.refresh_token,
      user: res.user,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
    setToken(stored.token);
    setUser(stored.user);
  }, []);

  const login = useCallback(
    async (telephone: string, motDePasse: string) => {
      persist(await api.login(telephone, motDePasse));
    },
    [persist]
  );

  const register = useCallback(
    async (data: Parameters<typeof api.register>[0]) => {
      persist(await api.register(data));
    },
    [persist]
  );

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, token, loading, login, register, logout }),
    [user, token, loading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth doit être utilisé dans <AuthProvider>");
  return ctx;
}
