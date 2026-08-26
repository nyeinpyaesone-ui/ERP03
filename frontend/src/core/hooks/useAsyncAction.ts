/**
 * Async Action Hook
 * Provides standardized async action handling with loading, error, and success states
 * 
 * @module core/hooks/useAsyncAction
 */

import { useState, useCallback } from 'react';

/**
 * Status of an async action
 */
export type AsyncStatus = 'idle' | 'loading' | 'success' | 'error';

/**
 * Result of an async action
 */
export interface AsyncActionResult<T = any> {
  status: AsyncStatus;
  data: T | null;
  error: Error | null;
  isLoading: boolean;
  isSuccess: boolean;
  isError: boolean;
}

/**
 * Options for async action
 */
export interface AsyncActionOptions {
  /** Reset state after successful completion (ms) */
  resetOnSuccess?: number | false;
  /** Reset state after error (ms) */
  resetOnError?: number | false;
  /** Callback on success */
  onSuccess?: (data: any) => void | Promise<void>;
  /** Callback on error */
  onError?: (error: Error) => void | Promise<void>;
}

/**
 * Execute an async action with standardized state management
 * 
 * @example
 * ```typescript
 * const { execute, reset, result } = useAsyncAction<User>();
 * 
 * await execute(async () => {
 *   const response = await api.login(credentials);
 *   return response.user;
 * });
 * 
 * if (result.isSuccess) {
 *   console.log('Logged in:', result.data);
 * }
 * ```
 */
export function useAsyncAction<T = any>(options?: AsyncActionOptions) {
  const [status, setStatus] = useState<AsyncStatus>('idle');
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const isLoading = status === 'loading';
  const isSuccess = status === 'success';
  const isError = status === 'error';

  const execute = useCallback(
    async (action: () => Promise<T>, overrideOptions?: Partial<AsyncActionOptions>) => {
      const mergedOptions = { ...options, ...overrideOptions };
      
      try {
        setStatus('loading');
        setError(null);
        
        const result = await action();
        setData(result);
        setStatus('success');
        
        // Handle success callback
        if (mergedOptions.onSuccess) {
          await mergedOptions.onSuccess(result);
        }
        
        // Auto-reset on success
        if (typeof mergedOptions.resetOnSuccess === 'number' && mergedOptions.resetOnSuccess > 0) {
          setTimeout(reset, mergedOptions.resetOnSuccess);
        }
        
        return result;
      } catch (err) {
        const actionError = err instanceof Error ? err : new Error(String(err));
        setError(actionError);
        setStatus('error');
        
        // Handle error callback
        if (mergedOptions.onError) {
          await mergedOptions.onError(actionError);
        }
        
        // Auto-reset on error
        if (typeof mergedOptions.resetOnError === 'number' && mergedOptions.resetOnError > 0) {
          setTimeout(reset, mergedOptions.resetOnError);
        }
        
        throw actionError;
      }
    },
    [options]
  );

  const reset = useCallback(() => {
    setStatus('idle');
    setData(null);
    setError(null);
  }, []);

  const result: AsyncActionResult<T> = {
    status,
    data,
    error,
    isLoading,
    isSuccess,
    isError,
  };

  return {
    execute,
    reset,
    result,
    status,
    data,
    error,
    isLoading,
    isSuccess,
    isError,
  };
}
