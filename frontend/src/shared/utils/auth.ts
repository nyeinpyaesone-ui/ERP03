/**
 * Shared authentication utility for API calls
 * Centralized token management across all modules
 */

import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const TOKEN_EXPIRY_KEY = 'token_expiry';

/**
 * Get authentication token from secure storage
 * Works on both mobile (SecureStore) and web (AsyncStorage)
 */
export const getAuthToken = async (): Promise<string | null> => {
  try {
    // Check if token exists and is not expired
    const expiry = await SecureStore.getItemAsync(TOKEN_EXPIRY_KEY);
    if (expiry) {
      const expiryTime = parseInt(expiry, 10);
      const now = Date.now();
      
      // Refresh token if less than 5 minutes remaining
      if (now > expiryTime - 5 * 60 * 1000) {
        await clearAuthToken();
        return null;
      }
    }
    
    return await SecureStore.getItemAsync(TOKEN_KEY);
  } catch (error) {
    console.error('Error getting auth token:', error);
    return null;
  }
};

/**
 * Set authentication token with expiry
 * @param token - JWT access token
 * @param expiresIn - Token expiry time in seconds (default: 1 hour)
 */
export const setAuthToken = async (token: string, expiresIn: number = 3600): Promise<void> => {
  try {
    const now = Date.now();
    const expiryTime = now + expiresIn * 1000;
    
    await SecureStore.setItemAsync(TOKEN_KEY, token);
    await SecureStore.setItemAsync(TOKEN_EXPIRY_KEY, expiryTime.toString());
  } catch (error) {
    console.error('Error setting auth token:', error);
    throw error;
  }
};

/**
 * Set refresh token for token renewal
 */
export const setRefreshToken = async (token: string): Promise<void> => {
  try {
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, token);
  } catch (error) {
    console.error('Error setting refresh token:', error);
    throw error;
  }
};

/**
 * Get refresh token
 */
export const getRefreshToken = async (): Promise<string | null> => {
  try {
    return await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
  } catch (error) {
    console.error('Error getting refresh token:', error);
    return null;
  }
};

/**
 * Clear all authentication tokens
 */
export const clearAuthToken = async (): Promise<void> => {
  try {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
    await SecureStore.deleteItemAsync(TOKEN_EXPIRY_KEY);
  } catch (error) {
    console.error('Error clearing auth token:', error);
    throw error;
  }
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = async (): Promise<boolean> => {
  const token = await getAuthToken();
  return token !== null;
};

/**
 * Create authorization header for API requests
 */
export const getAuthHeaders = async (): Promise<Record<string, string>> => {
  const token = await getAuthToken();
  if (!token) {
    return {};
  }
  return {
    Authorization: `Bearer ${token}`,
  };
};

/**
 * Merge auth headers with custom headers
 */
export const mergeHeaders = (customHeaders?: Record<string, string>): Promise<Record<string, string>> => {
  return getAuthHeaders().then(authHeaders => ({
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...authHeaders,
    ...customHeaders,
  }));
};
