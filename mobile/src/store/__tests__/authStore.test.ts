import { useAuthStore } from '../authStore';

// Mock expo-secure-store
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

const SecureStore = require('expo-secure-store');

describe('Auth Store', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset store state before each test
    useAuthStore.setState({
      isAuthenticated: false,
      user: null,
      token: null,
      isLoading: false,
    });
  });

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const state = useAuthStore.getState();
      
      expect(state.isAuthenticated).toBe(false);
      expect(state.user).toBeNull();
      expect(state.token).toBeNull();
      expect(state.isLoading).toBe(false);
    });
  });

  describe('login', () => {
    it('should set loading to true when login starts', async () => {
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: false,
          status: 401,
        } as Response)
      );

      useAuthStore.getState().login('test@example.com', 'password');
      
      expect(useAuthStore.getState().isLoading).toBe(true);
    });

    it('should successfully login and store user data', async () => {
      const mockUser = {
        id: 'user-123',
        name: 'Test User',
        email: 'test@example.com',
        role: 'admin',
      };
      const mockToken = 'auth-token-xyz';

      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ user: mockUser, access_token: mockToken }),
        } as any)
      );

      (SecureStore.setItemAsync as jest.Mock).mockResolvedValue(undefined);

      const result = await useAuthStore.getState().login('test@example.com', 'password');

      expect(result).toBe(true);
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
      expect(useAuthStore.getState().user).toEqual(mockUser);
      expect(useAuthStore.getState().token).toBe(mockToken);
      expect(useAuthStore.getState().isLoading).toBe(false);
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith('auth_token', mockToken);
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith('user_data', JSON.stringify(mockUser));
    });

    it('should handle login failure', async () => {
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: false,
          status: 401,
        } as Response)
      );

      const result = await useAuthStore.getState().login('test@example.com', 'wrongpassword');

      expect(result).toBe(false);
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().isLoading).toBe(false);
    });

    it('should handle network errors', async () => {
      global.fetch = jest.fn(() => Promise.reject(new Error('Network error')));

      const result = await useAuthStore.getState().login('test@example.com', 'password');

      expect(result).toBe(false);
      expect(useAuthStore.getState().isLoading).toBe(false);
    });
  });

  describe('logout', () => {
    it('should clear auth data and logout', async () => {
      // First login
      useAuthStore.setState({
        isAuthenticated: true,
        user: { id: 'user-123', name: 'Test', email: 'test@example.com', role: 'user' },
        token: 'some-token',
      });

      (SecureStore.deleteItemAsync as jest.Mock).mockResolvedValue(undefined);

      await useAuthStore.getState().logout();

      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('auth_token');
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('user_data');
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().user).toBeNull();
      expect(useAuthStore.getState().token).toBeNull();
    });
  });

  describe('checkAuth', () => {
    it('should set authenticated state when valid token and user data exist', async () => {
      const mockUser = { id: 'user-123', name: 'Test', email: 'test@example.com', role: 'user' };
      const mockToken = 'valid-token';

      (SecureStore.getItemAsync as jest.Mock)
        .mockResolvedValueOnce(mockToken)
        .mockResolvedValueOnce(JSON.stringify(mockUser));

      await useAuthStore.getState().checkAuth();

      expect(useAuthStore.getState().isAuthenticated).toBe(true);
      expect(useAuthStore.getState().token).toBe(mockToken);
      expect(useAuthStore.getState().user).toEqual(mockUser);
    });

    it('should not set authenticated state when no token exists', async () => {
      (SecureStore.getItemAsync as jest.Mock)
        .mockResolvedValueOnce(null)
        .mockResolvedValueOnce(null);

      await useAuthStore.getState().checkAuth();

      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().user).toBeNull();
    });

    it('should not set authenticated state when only token exists', async () => {
      (SecureStore.getItemAsync as jest.Mock)
        .mockResolvedValueOnce('some-token')
        .mockResolvedValueOnce(null);

      await useAuthStore.getState().checkAuth();

      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });
  });

  describe('state selectors', () => {
    it('should provide access to current state', () => {
      const state = useAuthStore.getState();
      
      expect(typeof state.login).toBe('function');
      expect(typeof state.logout).toBe('function');
      expect(typeof state.checkAuth).toBe('function');
    });
  });
});
