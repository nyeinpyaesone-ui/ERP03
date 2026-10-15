import Constants from 'expo-constants';

interface EnvConfig {
  apiUrl: string;
  appVariant: 'development' | 'staging' | 'production';
  enableLogging: boolean;
  sentryDsn: string;
  enableAnalytics: boolean;
}

const ENV: Record<string, EnvConfig> = {
  development: {
    apiUrl: 'https://dev-api.erp-domain.com/api/v1',
    appVariant: 'development',
    enableLogging: true,
    sentryDsn: 'https://dev-sentry-dsn@sentry.io/123456',
    enableAnalytics: false,
  },
  staging: {
    apiUrl: 'https://staging-api.erp-domain.com/api/v1',
    appVariant: 'staging',
    enableLogging: true,
    sentryDsn: 'https://staging-sentry-dsn@sentry.io/123456',
    enableAnalytics: true,
  },
  production: {
    apiUrl: 'https://api.erp-domain.com/api/v1',
    appVariant: 'production',
    enableLogging: false,
    sentryDsn: 'https://prod-sentry-dsn@sentry.io/123456',
    enableAnalytics: true,
  },
};

export const getEnvVars = (): EnvConfig => {
  const releaseChannel = Constants.expoConfig?.releaseChannel || 'default';
  const appVariant = (Constants.expoConfig?.extra?.appVariant as string) || 'development';

  if (appVariant === 'production' || releaseChannel.includes('prod')) {
    return ENV.production;
  }
  if (appVariant === 'staging' || releaseChannel.includes('staging')) {
    return ENV.staging;
  }
  return ENV.development;
};

export const env = getEnvVars();

