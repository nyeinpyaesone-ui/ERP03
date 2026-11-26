import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { clearSupabaseSession, saveSupabaseSession, signOutSupabase } from '../services/supabaseAuth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    try {
      setUser(await api.me());
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadUser(); }, [loadUser]);

  const login = async (credentials) => {
    clearSupabaseSession();
    localStorage.removeItem('erp03_token');
    const data = await api.login(credentials);
    localStorage.setItem('erp03_token', data.access_token);
    setUser(data.user);
    return data;
  };

  const loginWithSupabase = async (session) => {
    const data = await api.me({ authToken: session.access_token });
    saveSupabaseSession(session);
    setUser(data);
    return data;
  };

  const logout = useCallback(async () => {
    await signOutSupabase();
    localStorage.removeItem('erp03_token');
    setUser(null);
    window.location.href = '/login';
  }, []);

  return (
    <AuthContext.Provider value={{
      user, loading, login, loginWithSupabase, logout, isAuthenticated: Boolean(user),
      refreshUser: loadUser,
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
