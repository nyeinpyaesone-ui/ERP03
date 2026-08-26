/**
 * ERP03 Frontend Core API Service
 * Shared API utilities for all frontend modules
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

// Token storage key
const TOKEN_STORAGE_KEY = 'erp03_auth_token';
const REFRESH_TOKEN_STORAGE_KEY = 'erp03_refresh_token';

// Token refresh threshold (5 minutes before expiry)
const TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000;

// Refresh token promise to prevent multiple simultaneous refreshes
let refreshPromise: Promise<string> | null = null;

/**
 * Get stored auth token
 */
export async function getAuthToken(): Promise<string | null> {
  try {
    // Try to get from secure storage first (react-native-keychain or similar)
    // For now, use AsyncStorage as fallback
    const { AsyncStorage } = await import('@react-native-async-storage/async-storage');
    const token = await AsyncStorage.getItem(TOKEN_STORAGE_KEY);
    return token;
  } catch (error) {
    console.warn('Failed to retrieve auth token:', error);
    return null;
  }
}

/**
 * Store auth token
 */
export async function setAuthToken(token: string): Promise<void> {
  try {
    const { AsyncStorage } = await import('@react-native-async-storage/async-storage');
    await AsyncStorage.setItem(TOKEN_STORAGE_KEY, token);
  } catch (error) {
    console.error('Failed to store auth token:', error);
    throw error;
  }
}

/**
 * Clear stored tokens
 */
export async function clearAuthTokens(): Promise<void> {
  try {
    const { AsyncStorage } = await import('@react-native-async-storage/async-storage');
    await AsyncStorage.multiRemove([TOKEN_STORAGE_KEY, REFRESH_TOKEN_STORAGE_KEY]);
  } catch (error) {
    console.error('Failed to clear auth tokens:', error);
  }
}

/**
 * Refresh access token using refresh token
 */
async function refreshAccessToken(baseURL: string): Promise<string> {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const { AsyncStorage } = await import('@react-native-async-storage/async-storage');
      const refreshToken = await AsyncStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);

      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await axios.post(`${baseURL}/auth/refresh`, {
        refresh_token: refreshToken,
      });

      const { access_token } = response.data;
      await setAuthToken(access_token);

      return access_token;
    } catch (error) {
      // Clear tokens on refresh failure
      await clearAuthTokens();
      throw error;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

/**
 * Create API client with built-in auth and error handling
 */
export function createAPIClient(baseURL: string, timeout: number = 30000): AxiosInstance {
  const api = axios.create({
    baseURL,
    headers: {
      'Content-Type': 'application/json',
    },
    timeout,
  });

  // Request interceptor - add auth token
  api.interceptors.request.use(
    async (config: InternalAxiosRequestConfig) => {
      // Skip auth for public endpoints
      const skipAuthPaths = ['/auth/login', '/auth/register', '/health', '/public'];
      if (skipAuthPaths.some(path => config.url?.includes(path))) {
        return config;
      }

      const token = await getAuthToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error: AxiosError) => Promise.reject(error)
  );

  // Response interceptor - handle 401 and refresh token
  api.interceptors.response.use(
    (response: AxiosResponse) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

      // If error is 401 and we haven't retried yet
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          // Attempt to refresh token
          const newToken = await refreshAccessToken(baseURL);
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed - redirect to login
          console.error('Token refresh failed:', refreshError);
          // Optionally trigger navigation to login screen
          // NavigationService.navigate('Login');
          return Promise.reject(refreshError);
        }
      }

      // Handle other errors
      return handleError(error);
    }
  );

  return api;
}

/**
 * Unified error handler for API responses
 */
export function handleError(error: AxiosError): Promise<never> {
  let errorMessage = 'An unexpected error occurred';
  let errorCode = 'UNKNOWN_ERROR';

  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;

    switch (status) {
      case 400:
        errorMessage = (data as any)?.message || 'Invalid request';
        errorCode = 'BAD_REQUEST';
        break;
      case 401:
        errorMessage = 'Authentication required';
        errorCode = 'UNAUTHORIZED';
        break;
      case 403:
        errorMessage = 'Access denied';
        errorCode = 'FORBIDDEN';
        break;
      case 404:
        errorMessage = 'Resource not found';
        errorCode = 'NOT_FOUND';
        break;
      case 409:
        errorMessage = (data as any)?.message || 'Conflict';
        errorCode = 'CONFLICT';
        break;
      case 422:
        errorMessage = (data as any)?.message || 'Validation error';
        errorCode = 'VALIDATION_ERROR';
        break;
      case 429:
        errorMessage = 'Too many requests';
        errorCode = 'RATE_LIMIT';
        break;
      case 500:
        errorMessage = 'Server error';
        errorCode = 'SERVER_ERROR';
        break;
      case 502:
        errorMessage = 'Bad gateway';
        errorCode = 'BAD_GATEWAY';
        break;
      case 503:
        errorMessage = 'Service unavailable';
        errorCode = 'SERVICE_UNAVAILABLE';
        break;
      default:
        errorMessage = (data as any)?.message || `Error ${status}`;
        errorCode = `HTTP_${status}`;
    }
  } else if (error.request) {
    // Request made but no response
    if ((error as any).code === 'ECONNABORTED') {
      errorMessage = 'Request timeout';
      errorCode = 'TIMEOUT';
    } else if ((error as any).code === 'ENOTFOUND') {
      errorMessage = 'Network error - please check your connection';
      errorCode = 'NETWORK_ERROR';
    } else {
      errorMessage = 'No response from server';
      errorCode = 'NO_RESPONSE';
    }
  } else {
    // Request setup error
    errorMessage = error.message || 'Request configuration error';
    errorCode = 'REQUEST_ERROR';
  }

  // Log error for debugging
  console.error('API Error:', {
    message: errorMessage,
    code: errorCode,
    status: error.response?.status,
    url: error.config?.url,
    method: error.config?.method,
  });

  // Create enhanced error object
  const enhancedError = new Error(errorMessage) as any;
  enhancedError.code = errorCode;
  enhancedError.status = error.response?.status;
  enhancedError.originalError = error;

  return Promise.reject(enhancedError);
}

/**
 * Retry failed requests with exponential backoff
 */
export async function retryRequest<T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  let lastError: Error;
  let delay = initialDelay;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error as Error;

      // Don't retry on client errors (4xx except 429)
      if ((error as any).status >= 400 && (error as any).status < 500 && (error as any).status !== 429) {
        throw error;
      }

      // Wait before retrying (exponential backoff with jitter)
      const jitter = Math.random() * 0.3 * delay;
      await new Promise(resolve => setTimeout(resolve, delay + jitter));
      delay *= 2;
    }
  }

  throw lastError!;
}

/**
 * API response wrapper for consistent typing
 */
export interface APIResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

/**
 * Paginated response type
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  totalPages: number;
  limit?: number;
}

/**
 * Create paginated API response handler
 */
export function handlePaginatedResponse<T>(response: AxiosResponse<PaginatedResponse<T>>): PaginatedResponse<T> {
  return response.data;
}

/**
 * Create standard API response handler
 */
export function handleResponse<T>(response: AxiosResponse<T>): T {
  return response.data;
}
