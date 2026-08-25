/**
 * Async Utilities
 * Debounce, throttle, retry, and other async helpers
 * 
 * @module core/utils/async
 */

/**
 * Options for retry function
 */
export interface RetryOptions {
  /** Maximum number of retries (default: 3) */
  maxRetries?: number;
  /** Initial delay in ms (default: 1000) */
  initialDelay?: number;
  /** Backoff multiplier (default: 2) */
  backoffMultiplier?: number;
  /** Maximum delay cap in ms (default: 30000) */
  maxDelay?: number;
  /** Only retry on these error codes/statuses */
  retryOn?: number[] | ((error: any) => boolean);
  /** Callback on each retry attempt */
  onRetry?: (attempt: number, error: any) => void;
}

/**
 * Execute a function with exponential backoff retry
 * 
 * @example
 * ```typescript
 * // Simple retry
 * const result = await retry(() => api.fetchData(), { maxRetries: 3 });
 * 
 * // Retry with custom conditions
 * const result = await retry(
 *   () => api.fetchData(),
 *   { 
 *     maxRetries: 5,
 *     initialDelay: 500,
 *     retryOn: [429, 500, 503],
 *     onRetry: (attempt, error) => console.log(`Retry ${attempt}`)
 *   }
 * );
 * ```
 */
export async function retry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    backoffMultiplier = 2,
    maxDelay = 30000,
    retryOn,
    onRetry,
  } = options;

  let lastError: any;
  let delay = initialDelay;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Check if we should retry
      const shouldRetry = !retryOn || (
        Array.isArray(retryOn)
          ? retryOn.includes((error as any)?.status || error?.code)
          : retryOn(error)
      );

      if (!shouldRetry || attempt === maxRetries) {
        throw error;
      }

      // Call retry callback
      onRetry?.(attempt + 1, error);

      // Wait with exponential backoff and jitter
      const jitter = Math.random() * 0.3 * delay;
      await sleep(Math.min(delay + jitter, maxDelay));
      
      // Increase delay for next iteration
      delay *= backoffMultiplier;
    }
  }

  throw lastError;
}

/**
 * Delay execution for specified milliseconds
 * 
 * @example
 * ```typescript
 * await sleep(1000);
 * // Waits 1 second
 * ```
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Create a debounced version of a function
 * 
 * @example
 * ```typescript
 * const debouncedSearch = debounce((query) => {
 *   api.search(query);
 * }, 500);
 * 
 * // Will only execute after 500ms of no calls
 * debouncedSearch('react');
 * debouncedSearch('react query');
 * debouncedSearch('react query hooks');
 * ```
 */
export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  wait: number,
  options: { leading?: boolean; trailing?: boolean; immediate?: boolean } = {}
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  let lastCallTime: number | null = null;
  
  const { leading = false, trailing = true, immediate = false } = options;

  const cancel = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  };

  const debounced = function (this: any, ...args: Parameters<T>) {
    const now = Date.now();
    const isLeading = leading && !lastCallTime;
    
    if (immediate) {
      // Execute immediately, then ignore calls until wait period passes
      const callNow = !timeoutId;
      
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      
      timeoutId = setTimeout(() => {
        timeoutId = null;
      }, wait);
      
      if (callNow) {
        return fn.apply(this, args);
      }
    } else {
      // Standard debounce behavior
      if (isLeading && leading) {
        fn.apply(this, args);
      } else if (trailing) {
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
        
        timeoutId = setTimeout(() => {
          lastCallTime = Date.now();
          fn.apply(this, args);
        }, wait);
      }
    }
    
    lastCallTime = now;
  };

  debounced.cancel = cancel;
  
  return debounced as any;
}

/**
 * Create a throttled version of a function
 * 
 * @example
 * ```typescript
 * const throttledScroll = throttle((e) => {
 *   handleScroll(e);
 * }, 100);
 * 
 * window.addEventListener('scroll', throttledScroll);
 * // Executes at most once every 100ms
 * ```
 */
export function throttle<T extends (...args: any[]) => any>(
  fn: T,
  limit: number,
  options: { leading?: boolean; trailing?: boolean } = {}
): (...args: Parameters<T>) => void {
  let inThrottle = false;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  let lastArgs: Parameters<T> | null = null;
  
  const { leading = true, trailing = true } = options;

  const throttled = function (this: any, ...args: Parameters<T>) {
    if (!inThrottle) {
      if (leading) {
        fn.apply(this, args);
      }
      inThrottle = true;
      
      if (trailing) {
        timeoutId = setTimeout(() => {
          if (lastArgs) {
            fn.apply(this, lastArgs);
            lastArgs = null;
          }
          inThrottle = false;
        }, limit);
      } else {
        setTimeout(() => {
          inThrottle = false;
        }, limit);
      }
    } else if (trailing) {
      lastArgs = args;
    }
  };

  return throttled;
}

/**
 * Create a promise with timeout
 * 
 * @example
 * ```typescript
 * const result = await withTimeout(api.slowRequest(), 5000);
 * // Resolves with result or rejects after 5 seconds
 * ```
 */
export function withTimeout<T>(promise: Promise<T>, ms: number, message = 'Timeout'): Promise<T> {
  const timeout = new Promise<never>((_, reject) => {
    setTimeout(() => reject(new Error(message)), ms);
  });
  
  return Promise.race([promise, timeout]);
}

/**
 * Execute promises in sequence instead of parallel
 * 
 * @example
 * ```typescript
 * const results = await promiseSequence(
 *   [1, 2, 3],
 *   async (item) => api.process(item)
 * );
 * ```
 */
export async function promiseSequence<T, R>(
  items: T[],
  processor: (item: T, index: number) => Promise<R>
): Promise<R[]> {
  const results: R[] = [];
  
  for (let i = 0; i < items.length; i++) {
    results.push(await processor(items[i], i));
  }
  
  return results;
}

/**
 * Run promises with concurrency limit
 * 
 * @example
 * ```typescript
 * const results = await promisePool(
 *   urls,
 *   (url) => fetch(url),
 *   5 // Max 5 concurrent requests
 * );
 * ```
 */
export async function promisePool<T, R>(
  items: T[],
  processor: (item: T, index: number) => Promise<R>,
  concurrency: number
): Promise<R[]> {
  const results: R[] = [];
  const executing: Promise<any>[] = [];
  
  for (let i = 0; i < items.length; i++) {
    const promise = processor(items[i], i).then(result => {
      results.push(result);
      executing.splice(executing.indexOf(promise), 1);
      return result;
    });
    
    executing.push(promise);
    
    if (executing.length >= concurrency) {
      await Promise.race(executing);
    }
  }
  
  await Promise.all(executing);
  return results;
}
