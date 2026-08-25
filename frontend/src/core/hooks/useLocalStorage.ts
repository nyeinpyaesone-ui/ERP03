/**
 * Local Storage Hook
 * Persist state to localStorage with automatic synchronization
 * 
 * @module core/hooks/useLocalStorage
 */

import { useState, useEffect, useCallback } from 'react';

/**
 * Configuration for local storage hook
 */
export interface UseLocalStorageOptions<T> {
  /** Deserialize function (default: JSON.parse) */
  deserialize?: (value: string) => T;
  /** Serialize function (default: JSON.stringify) */
  serialize?: (value: T) => string;
  /** Handle storage event synchronization */
  syncAcrossTabs?: boolean;
}

/**
 * Use localStorage with React state synchronization
 * 
 * @example
 * ```typescript
 * const [theme, setTheme] = useLocalStorage<'light' | 'dark'>('theme', 'light');
 * 
 * // Usage
 * setTheme('dark');
 * ```
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  options?: UseLocalStorageOptions<T>
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  const {
    deserialize = (value: string) => JSON.parse(value) as T,
    serialize = (value: T) => JSON.stringify(value),
    syncAcrossTabs = true,
  } = options || {};

  // Get initial value from storage or use provided default
  const readValue = useCallback((): T => {
    if (typeof window === 'undefined') {
      return initialValue;
    }

    try {
      const item = window.localStorage.getItem(key);
      return item ? deserialize(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  }, [initialValue, key, deserialize]);

  const [storedValue, setStoredValue] = useState<T>(readValue);

  // Return a wrapped version of useState's setter function that persists to localStorage
  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      if (typeof window === 'undefined') {
        console.warn(
          `Tried setting localStorage key "${key}" even though environment is not a client`
        );
      }

      try {
        const newValue = value instanceof Function ? value(storedValue) : value;
        
        // Save to state
        setStoredValue(newValue);
        
        // Save to localStorage
        window.localStorage.setItem(key, serialize(newValue));
        
        // Dispatch custom event for cross-tab synchronization
        window.dispatchEvent(new Event('local-storage'));
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, serialize, storedValue]
  );

  // Remove value from localStorage
  const removeValue = useCallback(() => {
    if (typeof window === 'undefined') {
      console.warn(
        `Tried removing localStorage key "${key}" even though environment is not a client`
      );
    }

    try {
      window.localStorage.removeItem(key);
      setStoredValue(initialValue);
      window.dispatchEvent(new Event('local-storage'));
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  // Handle changes from other tabs
  useEffect(() => {
    if (!syncAcrossTabs) return;

    const handleStorageChange = () => {
      setStoredValue(readValue());
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('local-storage', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('local-storage', handleStorageChange);
    };
  }, [readValue, syncAcrossTabs]);

  return [storedValue, setValue, removeValue];
}

/**
 * Use session storage with React state synchronization
 * 
 * @example
 * ```typescript
 * const [sessionData, setSessionData] = useSessionStorage('session', null);
 * ```
 */
export function useSessionStorage<T>(
  key: string,
  initialValue: T,
  options?: Omit<UseLocalStorageOptions<T>, 'syncAcrossTabs'>
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  const {
    deserialize = (value: string) => JSON.parse(value) as T,
    serialize = (value: T) => JSON.stringify(value),
  } = options || {};

  const readValue = useCallback((): T => {
    if (typeof window === 'undefined') {
      return initialValue;
    }

    try {
      const item = window.sessionStorage.getItem(key);
      return item ? deserialize(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading sessionStorage key "${key}":`, error);
      return initialValue;
    }
  }, [initialValue, key, deserialize]);

  const [storedValue, setStoredValue] = useState<T>(readValue);

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      if (typeof window === 'undefined') {
        console.warn(
          `Tried setting sessionStorage key "${key}" even though environment is not a client`
        );
      }

      try {
        const newValue = value instanceof Function ? value(storedValue) : value;
        setStoredValue(newValue);
        window.sessionStorage.setItem(key, serialize(newValue));
      } catch (error) {
        console.warn(`Error setting sessionStorage key "${key}":`, error);
      }
    },
    [key, serialize, storedValue]
  );

  const removeValue = useCallback(() => {
    if (typeof window === 'undefined') {
      console.warn(
        `Tried removing sessionStorage key "${key}" even though environment is not a client`
      );
    }

    try {
      window.sessionStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.warn(`Error removing sessionStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue];
}
