import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, ApiError } from '../services/api';
import {
  clearActiveAuthProvider,
  clearSupabaseSession,
  getSupabaseAccessToken,
  saveSupabaseSession,
  selectErpProvider,
  selectSupabaseProvider,
  signOutSupabase,
} from '../services/supabaseAuth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [probeError, setProbeError] = useState(false);

  const loadUser = useCallback(async () => {
    setLoading(true);
    setProbeError(false);
    try {
      setUser(await api.me());
    } catch (error) {
      if (error instanceof ApiError && [401, 403].includes(error.status)) {
        setUser(null);
      } else {
        setProbeError(true);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadUser(); }, [loadUser]);

  const login = async (credentials) => {
    clearSupabaseSession();
    const data = await api.login(credentials);
    localStorage.setItem('erp03_token', data.access_token);
    selectErpProvider();
    setUser(data.user);
    setProbeError(false);
    return data;
  };

  const loginWithSupabase = async (session) => {
    const data = await api.me({ authToken: session.access_token });
    saveSupabaseSession(session);
    selectSupabaseProvider();
    localStorage.removeItem('erp03_token');
    setUser(data);
    setProbeError(false);
    return data;
  };

  const logout = useCallback(() => {
    // Capture the current token only; remote revocation starts after local
    // credentials and in-memory identity are cleared.
    const revocationToken = getSupabaseAccessToken().catch(() => null);
    clearSupabaseSession();
    clearActiveAuthProvider();
    localStorage.removeItem('erp03_token');
    setUser(null);
    setProbeError(false);
    void revocationToken.then((token) => signOutSupabase(token)).catch(() => {});
    window.location.href = '/login';
  }, []);

  return (
    <AuthContext.Provider value={{
      user, loading, probeError, login, loginWithSupabase, logout,
      isAuthenticated: Boolean(user), refreshUser: loadUser,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
