// Archived from .github/workflows/src/config/env.ts during repository structure cleanup.
// Preserved verbatim below.

import Constants from 'expo-constants';

export const ENV = {
  API_URL: Constants.expoConfig?.extra?.apiUrl || process.env.API_URL || 'http://localhost:8000',
  ENVIRONMENT: Constants.expoConfig?.extra?.environment || process.env.NODE_ENV || 'development',
  SENTRY_DSN: Constants.expoConfig?.extra?.sentryDsn || process.env.SENTRY_DSN || '',
};

export const isProduction = ENV.ENVIRONMENT === 'production';
