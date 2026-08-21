import { MD3LightTheme, MD3DarkTheme } from 'react-native-paper';

export const lightTheme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: '#3B82F6',
    primaryContainer: '#DBEAFE',
    secondary: '#8B5CF6',
    secondaryContainer: '#EDE9FE',
    surface: '#FFFFFF',
    surfaceVariant: '#F1F5F9',
    background: '#F8FAFC',
    error: '#EF4444',
    errorContainer: '#FEE2E2',
    success: '#10B981',
    warning: '#F59E0B',
    info: '#06B6D4',
    onSurface: '#1E293B',
    onSurfaceVariant: '#64748B',
    outline: '#E2E8F0',
    elevation: {
      level0: 'transparent',
      level1: '#FFFFFF',
      level2: '#FFFFFF',
      level3: '#FFFFFF',
      level4: '#FFFFFF',
      level5: '#FFFFFF',
    },
  },
  fonts: {
    ...MD3LightTheme.fonts,
    bodyLarge: { ...MD3LightTheme.fonts.bodyLarge, fontFamily: 'Inter' },
    bodyMedium: { ...MD3LightTheme.fonts.bodyMedium, fontFamily: 'Inter' },
    titleLarge: { ...MD3LightTheme.fonts.titleLarge, fontFamily: 'Inter', fontWeight: '700' },
    titleMedium: { ...MD3LightTheme.fonts.titleMedium, fontFamily: 'Inter', fontWeight: '600' },
    labelLarge: { ...MD3LightTheme.fonts.labelLarge, fontFamily: 'Inter', fontWeight: '600' },
  },
};

export const darkTheme = {
  ...MD3DarkTheme,
  colors: {
    ...MD3DarkTheme.colors,
    primary: '#60A5FA',
    primaryContainer: '#1E3A8A',
    secondary: '#A78BFA',
    secondaryContainer: '#4C1D95',
    surface: '#1E293B',
    surfaceVariant: '#334155',
    background: '#0F172A',
    error: '#F87171',
    errorContainer: '#7F1D1D',
    success: '#34D399',
    warning: '#FBBF24',
    info: '#22D3EE',
    onSurface: '#F8FAFC',
    onSurfaceVariant: '#94A3B8',
    outline: '#334155',
  },
};

export const theme = lightTheme;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const borderRadius = {
  sm: 6,
  md: 10,
  lg: 16,
  xl: 24,
  full: 9999,
};

