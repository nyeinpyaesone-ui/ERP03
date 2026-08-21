import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { PaperProvider, MD3LightTheme, MD3DarkTheme } from 'react-native-paper';
import { NavigationContainer } from '@react-navigation/native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useColorScheme } from 'react-native';

// i18n initialization (must be before any component imports)
import './src/i18n';

// Sentry
import { initSentry } from './src/utils/sentry';

// Store
import { useAuthStore } from './src/store/authStore';
import { useThemeStore } from './src/store/themeStore';

// Navigation
import { RootNavigator } from './src/navigation/RootNavigator';

// Utils
import { env } from './src/config/env';
import { useLanguage } from './src/hooks/useLanguage';

// Initialize Sentry in production
if (!env.enableLogging) {
  initSentry();
}

// Create QueryClient with default options
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: 2,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

// Custom theme with Myanmar font support
const createTheme = (isDark: boolean, isMyanmar: boolean) => {
  const baseTheme = isDark ? MD3DarkTheme : MD3LightTheme;

  return {
    ...baseTheme,
    fonts: {
      ...baseTheme.fonts,
      regular: {
        fontFamily: isMyanmar ? 'Pyidaungsu' : 'Roboto',
        fontWeight: '400' as const,
      },
      medium: {
        fontFamily: isMyanmar ? 'Pyidaungsu' : 'Roboto-Medium',
        fontWeight: '500' as const,
      },
      bold: {
        fontFamily: isMyanmar ? 'Pyidaungsu' : 'Roboto-Bold',
        fontWeight: '700' as const,
      },
      bodyLarge: {
        ...baseTheme.fonts.bodyLarge,
        fontFamily: isMyanmar ? 'Pyidaungsu' : 'Roboto',
      },
      bodyMedium: {
        ...baseTheme.fonts.bodyMedium,
        fontFamily: isMyanmar ? 'Pyidaungsu' : 'Roboto',
      },
      bodySmall: {
        ...baseTheme.fonts.bodySmall,
        fontFamily: isMyanmar ? 'Pyidaungsu' : 'Roboto',
      },
      titleLarge: {
        ...baseTheme.fonts.titleLarge,
        fontFamily: isMyanmar ? 'Pyidaungsu' : 'Roboto',
      },
      titleMedium: {
        ...baseTheme.fonts.titleMedium,
        fontFamily: isMyanmar ? 'Pyidaungsu' : 'Roboto',
      },
      titleSmall: {
        ...baseTheme.fonts.titleSmall,
        fontFamily: isMyanmar ? 'Pyidaungsu' : 'Roboto',
      },
      headlineLarge: {
        ...baseTheme.fonts.headlineLarge,
        fontFamily: isMyanmar ? 'Pyidaungsu' : 'Roboto',
      },
      headlineMedium: {
        ...baseTheme.fonts.headlineMedium,
        fontFamily: isMyanmar ? 'Pyidaungsu' : 'Roboto',
      },
      headlineSmall: {
        ...baseTheme.fonts.headlineSmall,
        fontFamily: isMyanmar ? 'Pyidaungsu' : 'Roboto',
      },
    },
    colors: {
      ...baseTheme.colors,
      primary: '#6200ee',
      primaryContainer: '#eaddff',
      secondary: '#03dac6',
      secondaryContainer: '#cefaf8',
      error: '#b00020',
      errorContainer: '#ffdad6',
      success: '#4caf50',
      warning: '#ff9800',
      info: '#2196f3',
    },
  };
};

export default function App() {
  const colorScheme = useColorScheme();
  const { isDarkMode } = useThemeStore();
  const { isMyanmar } = useLanguage();
  const { initializeAuth } = useAuthStore();

  // Determine theme
  const isDark = isDarkMode ?? colorScheme === 'dark';
  const theme = createTheme(isDark, isMyanmar);

  // Initialize auth on mount
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <PaperProvider theme={theme}>
          <NavigationContainer>
            <RootNavigator />
            <StatusBar style={isDark ? 'light' : 'dark'} />
          </NavigationContainer>
        </PaperProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}

