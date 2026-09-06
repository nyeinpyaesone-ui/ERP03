/**
 * Base API client configuration
 * Shared across all modules for consistent API communication
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { getAuthToken, clearAuthToken } from '../utils/auth';

export interface ApiConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
}

/**
 * Create a configured API client instance
 * @param config - API configuration including base URL and headers
 * @returns Configured Axios instance with interceptors
 */
export const createApiClient = (config: ApiConfig): AxiosInstance => {
  const apiClient = axios.create({
    baseURL: config.baseURL,
    timeout: config.timeout || 30000,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...config.headers,
    },
  });

  // Request interceptor - add auth token
  apiClient.interceptors.request.use(
    async (requestConfig: InternalAxiosRequestConfig) => {
      try {
        const token = await getAuthToken();
        if (token) {
          requestConfig.headers.Authorization = `Bearer ${token}`;
        }
        return requestConfig;
      } catch (error) {
        console.error('Error in request interceptor:', error);
        return requestConfig;
      }
    },
    (error: AxiosError) => Promise.reject(error)
  );

  // Response interceptor - handle errors globally
  apiClient.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      if (error.response?.status === 401) {
        // Token expired or invalid - clear and trigger re-authentication
        await clearAuthToken();
        
        // Dispatch custom event for app-wide auth handling
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        }
      }
      
      // Enhance error with additional context
      const enhancedError = {
        ...error,
        message: getErrorMessage(error),
        timestamp: new Date().toISOString(),
      };
      
      console.error('API Error:', enhancedError);
      return Promise.reject(enhancedError);
    }
  );

  return apiClient;
};

/**
 * Extract meaningful error message from Axios error
 * @param error - Axios error object
 * @returns User-friendly error message
 */
export const getErrorMessage = (error: AxiosError): string => {
  if (error.response) {
    // Server responded with error status
    const data = error.response.data as any;
    return data?.message || data?.detail || 'An unexpected error occurred';
  } else if (error.request) {
    // Request made but no response received
    return 'Network error. Please check your connection.';
  } else {
    // Something else happened
    return error.message || 'An unexpected error occurred';
  }
};

/**
 * Handle API response with standardized error handling
 * @param promise - Axios promise
 * @returns Promise with typed response data
 */
export const handleApiResponse = async <T>(promise: Promise<any>): Promise<T> => {
  try {
    const response = await promise;
    return response.data as T;
  } catch (error) {
    throw error;
  }
};

/**
 * Retry failed requests with exponential backoff
 * @param fn - Function to retry
 * @param maxRetries - Maximum number of retries
 * @param delay - Initial delay in milliseconds
 * @returns Promise with result
 */
export const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> => {
  let lastError: Error;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      // Don't retry on 4xx errors (client errors)
      const axiosError = error as AxiosError;
      if (axiosError.response?.status && axiosError.response.status >= 400 && axiosError.response.status < 500) {
        throw error;
      }
      
      // Wait before retrying (exponential backoff)
      const waitTime = delay * Math.pow(2, i);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
  }
  
  throw lastError!;
};
