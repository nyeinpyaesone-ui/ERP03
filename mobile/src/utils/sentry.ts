import * as Sentry from '@sentry/react-native';
import { env } from './config/env';

export const initSentry = () => {
  if (!env.enableLogging) {
    Sentry.init({
      dsn: env.sentryDsn,
      environment: env.appVariant,
      debug: false,
      tracesSampleRate: env.appVariant === 'production' ? 0.1 : 1.0,
      enableNative: true,
      enableNativeCrashHandling: true,
    });
  }
};

export const captureException = (error: Error, context?: Record<string, any>) => {
  Sentry.captureException(error, { extra: context });
};

export const setUserContext = (userId: string, email: string, role: string) => {
  Sentry.setUser({ id: userId, email, role });
};

---


