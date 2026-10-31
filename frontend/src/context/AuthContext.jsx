/* ── Auth context ──
   Manages the JWT access token across the app and attaches it to every
   API request via a small fetch wrapper. Token lives in memory only
   (session-scoped) to keep the surface minimal and secure.
*/

import { createContext, useContext, useState, useCallback } from "react";

const AuthContext = createContext(null);

/** @type {import("react").Context<{ token: string | null; setToken: (t: string | null) => void; isAuthenticated: boolean; login: (t: string) => void; logout: () => void }>} */
export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(() => {
    try {
      return sessionStorage.getItem("erp03_token") ?? null;
    } catch {
      return null;
    }
  });

  const setToken = useCallback((t) => {
    setTokenState(t);
    try {
      if (t === null) sessionStorage.removeItem("erp03_token");
      else sessionStorage.setItem("erp03_token", t);
    } catch {
      // storage unavailable; in-memory only
    }
  }, []);

  const login = useCallback((t) => setToken(t), [setToken]);
  const logout = useCallback(() => setToken(null), [setToken]);

  const isAuthenticated = Boolean(token);

  const value = { token, setToken, isAuthenticated, login, logout };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
