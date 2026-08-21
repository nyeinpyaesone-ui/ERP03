import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNetInfo } from '@react-native-community/netinfo';
import { useTranslation } from 'react-i18next';
import { useTheme } from 'react-native-paper';

// Network status hook with offline queue
export const useNetworkStatus = () => {
  const netInfo = useNetInfo();
  const [wasOffline, setWasOffline] = useState(false);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (netInfo.isConnected === false) {
      setWasOffline(true);
      // Pause background refetches
      queryClient.setDefaultOptions({
        queries: { networkMode: 'offlineFirst' },
      });
    } else if (netInfo.isConnected === true && wasOffline) {
      // Back online - resume normal operation and invalidate stale queries
      queryClient.setDefaultOptions({
        queries: { networkMode: 'online' },
      });
      queryClient.invalidateQueries();
      setWasOffline(false);
    }
  }, [netInfo.isConnected, wasOffline, queryClient]);

  return {
    isConnected: netInfo.isConnected,
    isInternetReachable: netInfo.isInternetReachable,
    type: netInfo.type,
    isOffline: netInfo.isConnected === false,
    isOnline: netInfo.isConnected === true,
  };
};

// Debounced search hook
export const useDebounce = <T>(value: T, delay: number = 500): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
};

// Infinite scroll hook
export const useInfiniteScroll = <T>(
  fetchFn: (page: number) => Promise<{ data: T[]; hasNext: boolean }>,
  initialPage: number = 1
) => {
  const [data, setData] = useState<T[]>([]);
  const [page, setPage] = useState(initialPage);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    setError(null);

    try {
      const result = await fetchFn(page);
      setData((prev) => (page === initialPage ? result.data : [...prev, ...result.data]));
      setHasMore(result.hasNext);
      setPage((prev) => prev + 1);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [fetchFn, page, loading, hasMore, initialPage]);

  const refresh = useCallback(() => {
    setPage(initialPage);
    setHasMore(true);
    setData([]);
    loadMore();
  }, [initialPage, loadMore]);

  useEffect(() => {
    loadMore();
  }, []); // Initial load

  return { data, loading, hasMore, error, loadMore, refresh };
};

// Pull-to-refresh hook
export const usePullToRefresh = (onRefresh: () => Promise<void>) => {
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setRefreshing(false);
    }
  }, [onRefresh]);

  return { refreshing, handleRefresh };
};

// Permission check hook
export const usePermission = (requiredPermission: string) => {
  const { user } = useAuthStore(); // Assuming auth store has user with permissions

  const hasPermission = useCallback(() => {
    if (!user?.permissions) return false;
    return user.permissions.includes(requiredPermission) || user.permissions.includes('admin');
  }, [user, requiredPermission]);

  const checkPermission = useCallback((action: string) => {
    if (!user?.permissions) return false;
    const permissionKey = `${requiredPermission}:${action}`;
    return user.permissions.includes(permissionKey) || user.permissions.includes('admin');
  }, [user, requiredPermission]);

  return { hasPermission, checkPermission };
};

// Form validation hook
export const useFormValidation = <T extends Record<string, any>>(
  initialValues: T,
  validators: Record<keyof T, (value: any) => string | undefined>
) => {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({});

  const validate = useCallback(() => {
    const newErrors: Partial<Record<keyof T, string>> = {};
    let isValid = true;

    (Object.keys(validators) as Array<keyof T>).forEach((key) => {
      const error = validators[key](values[key]);
      if (error) {
        newErrors[key] = error;
        isValid = false;
      }
    });

    setErrors(newErrors);
    return isValid;
  }, [values, validators]);

  const setValue = useCallback(<K extends keyof T>(key: K, value: T[K]) => {
    setValues((prev) => ({ ...prev, [key]: value }));
    setTouched((prev) => ({ ...prev, [key]: true }));

    // Validate single field
    const error = validators[key]?.(value);
    setErrors((prev) => ({ ...prev, [key]: error }));
  }, [validators]);

  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  }, [initialValues]);

  return { values, errors, touched, setValue, validate, reset, isValid: Object.keys(errors).length === 0 };
};

// Optimistic update hook for TanStack Query
export const useOptimisticUpdate = <T>(
  queryKey: string[],
  updateFn: (oldData: T, newData: Partial<T>) => T
) => {
  const queryClient = useQueryClient();

  const optimisticUpdate = useCallback(async (
    mutationFn: () => Promise<any>,
    newData: Partial<T>
  ) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey });

    // Snapshot previous value
    const previousData = queryClient.getQueryData<T>(queryKey);

    // Optimistically update
    if (previousData) {
      queryClient.setQueryData<T>(queryKey, (old) => updateFn(old as T, newData));
    }

    try {
      await mutationFn();
    } catch (error) {
      // Rollback on error
      queryClient.setQueryData(queryKey, previousData);
      throw error;
    }
  }, [queryClient, queryKey, updateFn]);

  return { optimisticUpdate };
};

// Keyboard-aware hook
export const useKeyboard = () => {
  const [keyboardVisible, setKeyboardVisible] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0);

  useEffect(() => {
    const showSubscription = Keyboard.addListener('keyboardDidShow', (e) => {
      setKeyboardVisible(true);
      setKeyboardHeight(e.endCoordinates.height);
    });
    const hideSubscription = Keyboard.addListener('keyboardDidHide', () => {
      setKeyboardVisible(false);
      setKeyboardHeight(0);
    });

    return () => {
      showSubscription.remove();
      hideSubscription.remove();
    };
  }, []);

  return { keyboardVisible, keyboardHeight };
};

// Biometric auth hook
export const useBiometric = () => {
  const [isAvailable, setIsAvailable] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    checkAvailability();
  }, []);

  const checkAvailability = async () => {
    try {
      const compatible = await LocalAuthentication.hasHardwareAsync();
      const enrolled = await LocalAuthentication.isEnrolledAsync();
      setIsAvailable(compatible && enrolled);
    } catch {
      setIsAvailable(false);
    }
  };

  const authenticate = async (): Promise<boolean> => {
    if (!isAvailable) return false;

    setIsLoading(true);
    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Authenticate to access ERP SOLUTION',
        fallbackLabel: 'Use passcode',
      });
      return result.success;
    } catch {
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  return { isAvailable, isLoading, authenticate };
};

// Import from react-native
import { Keyboard } from 'react-native';
import * as LocalAuthentication from 'expo-local-authentication';
import { useAuthStore } from '../store/authStore';

---

