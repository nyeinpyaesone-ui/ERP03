import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  avatar?: string;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  token: null,
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      // Replace with actual API call
      const response = await fetch('https://your-api-domain.com/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) throw new Error('Login failed');

      const data = await response.json();
      await SecureStore.setItemAsync('auth_token', data.access_token);
      await SecureStore.setItemAsync('user_data', JSON.stringify(data.user));

      set({
        isAuthenticated: true,
        user: data.user,
        token: data.access_token,
        isLoading: false,
      });
      return true;
    } catch (error) {
      set({ isLoading: false });
      return false;
    }
  },

  logout: async () => {
    await SecureStore.deleteItemAsync('auth_token');
    await SecureStore.deleteItemAsync('user_data');
    set({ isAuthenticated: false, user: null, token: null });
  },

  checkAuth: async () => {
    const token = await SecureStore.getItemAsync('auth_token');
    const userData = await SecureStore.getItemAsync('user_data');
    if (token && userData) {
      set({
        isAuthenticated: true,
        token,
        user: JSON.parse(userData),
      });
    }
  },
}));

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { checkAuth } = useAuthStore();

  React.useEffect(() => {
    checkAuth();
  }, []);

  return <>{children}</>;
};

