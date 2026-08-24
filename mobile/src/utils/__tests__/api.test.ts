import { apiClient, setAuthToken, removeAuthToken } from '../api';

// Mock expo-secure-store
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

const SecureStore = require('expo-secure-store');

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('apiClient configuration', () => {
    it('should be created with correct base URL', () => {
      expect(apiClient.defaults.baseURL).toBe('https://your-api-domain.com/api/v1');
    });

    it('should have correct timeout', () => {
      expect(apiClient.defaults.timeout).toBe(30000);
    });

    it('should have correct default headers', () => {
      expect(apiClient.defaults.headers.common['Content-Type']).toBe('application/json');
      expect(apiClient.defaults.headers.common['Accept']).toBe('application/json');
    });
  });

  describe('Request Interceptor', () => {
    it('should add auth token to request headers when token exists', async () => {
      const mockToken = 'mock-auth-token';
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(mockToken);

      const config = {
        headers: {},
        url: '/test',
        method: 'get',
      };

      const interceptors = apiClient.interceptors.request.handlers[0];
      const result = await interceptors.fulfilled(config);

      expect(SecureStore.getItemAsync).toHaveBeenCalledWith('auth_token');
      expect(result.headers.Authorization).toBe(`Bearer ${mockToken}`);
    });

    it('should not add Authorization header when no token exists', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(null);

      const config = {
        headers: {},
        url: '/test',
        method: 'get',
      };

      const interceptors = apiClient.interceptors.request.handlers[0];
      const result = await interceptors.fulfilled(config);

      expect(SecureStore.getItemAsync).toHaveBeenCalledWith('auth_token');
      expect(result.headers.Authorization).toBeUndefined();
    });

    it('should reject on error', async () => {
      const mockError = new Error('Network error');
      (SecureStore.getItemAsync as jest.Mock).mockRejectedValue(mockError);

      const interceptors = apiClient.interceptors.request.handlers[0];

      await expect(interceptors.rejected(mockError)).rejects.toBe(mockError);
    });
  });

  describe('Response Interceptor', () => {
    it('should pass through successful responses', async () => {
      const mockResponse = { data: { success: true }, status: 200 };

      const interceptors = apiClient.interceptors.response.handlers[0];
      const result = await interceptors.fulfilled(mockResponse);

      expect(result).toEqual(mockResponse);
    });

    it('should remove auth token and reject on 401 response', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { message: 'Unauthorized' },
        },
      };

      (SecureStore.deleteItemAsync as jest.Mock).mockResolvedValue(undefined);

      const interceptors = apiClient.interceptors.response.handlers[0];

      await expect(interceptors.rejected(mockError)).rejects.toEqual(mockError);
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('auth_token');
    });

    it('should reject non-401 errors without removing token', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { message: 'Server error' },
        },
      };

      const interceptors = apiClient.interceptors.response.handlers[0];

      await expect(interceptors.rejected(mockError)).rejects.toEqual(mockError);
      expect(SecureStore.deleteItemAsync).not.toHaveBeenCalled();
    });
  });

  describe('setAuthToken', () => {
    it('should store token in secure store', async () => {
      const mockToken = 'test-token-123';
      (SecureStore.setItemAsync as jest.Mock).mockResolvedValue(undefined);

      await setAuthToken(mockToken);

      expect(SecureStore.setItemAsync).toHaveBeenCalledWith('auth_token', mockToken);
    });
  });

  describe('removeAuthToken', () => {
    it('should remove token from secure store', async () => {
      (SecureStore.deleteItemAsync as jest.Mock).mockResolvedValue(undefined);

      await removeAuthToken();

      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('auth_token');
    });
  });
});
