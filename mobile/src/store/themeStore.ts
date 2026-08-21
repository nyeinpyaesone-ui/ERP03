import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface ThemeState {
  isDarkMode: boolean;
  fontSize: 'small' | 'medium' | 'large';
  toggleTheme: () => Promise<void>;
  setFontSize: (size: 'small' | 'medium' | 'large') => Promise<void>;
  loadPreferences: () => Promise<void>;
}

export const useThemeStore = create<ThemeState>((set) => ({
  isDarkMode: false,
  fontSize: 'medium',

  toggleTheme: async () => {
    set((state) => {
      const newValue = !state.isDarkMode;
      AsyncStorage.setItem('dark_mode', JSON.stringify(newValue));
      return { isDarkMode: newValue };
    });
  },

  setFontSize: async (size) => {
    await AsyncStorage.setItem('font_size', size);
    set({ fontSize: size });
  },

  loadPreferences: async () => {
    const darkMode = await AsyncStorage.getItem('dark_mode');
    const fontSize = await AsyncStorage.getItem('font_size');
    set({
      isDarkMode: darkMode ? JSON.parse(darkMode) : false,
      fontSize: (fontSize as any) || 'medium',
    });
  },
}));

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { loadPreferences } = useThemeStore();

  React.useEffect(() => {
    loadPreferences();
  }, []);

  return <>{children}</>;
};

