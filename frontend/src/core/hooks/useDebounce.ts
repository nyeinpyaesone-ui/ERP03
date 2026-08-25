/**
 * Debounce Hook
 * Delays execution of a value change until after a specified wait time
 * 
 * @module core/hooks/useDebounce
 */

import { useState, useEffect } from 'react';

/**
 * Configuration for debounce hook
 */
export interface UseDebounceOptions {
  /** Delay in milliseconds */
  delay: number;
  /** Skip debouncing for specific values */
  skip?: (value: any) => boolean;
}

/**
 * Debounce a value with configurable delay
 * 
 * @example
 * ```typescript
 * const [searchTerm, setSearchTerm] = useState('');
 * const debouncedSearch = useDebounce(searchTerm, { delay: 500 });
 * 
 * useEffect(() => {
 *   if (debouncedSearch) {
 *     api.search(debouncedSearch);
 *   }
 * }, [debouncedSearch]);
 * ```
 */
export function useDebounce<T>(value: T, options: number | UseDebounceOptions): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  
  const delay = typeof options === 'number' ? options : options.delay;
  const skip = typeof options === 'object' && 'skip' in options ? options.skip : undefined;

  useEffect(() => {
    // Skip debouncing if condition is met
    if (skip?.(value)) {
      setDebouncedValue(value);
      return;
    }

    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay, skip]);

  return debouncedValue;
}

/**
 * Debounce a callback function
 * 
 * @example
 * ```typescript
 * const debouncedSave = useDebounceCallback(async (data) => {
 *   await api.save(data);
 * }, 1000);
 * 
 * // Will only execute after 1 second of no changes
 * debouncedSave(formData);
 * ```
 */
export function useDebounceCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const [timeoutId, setTimeoutId] = useState<NodeJS.Timeout | null>(null);

  const debouncedCallback = ((...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    const newTimeoutId = setTimeout(() => {
      callback(...args);
    }, delay);

    setTimeoutId(newTimeoutId);
  }) as T;

  return debouncedCallback;
}
