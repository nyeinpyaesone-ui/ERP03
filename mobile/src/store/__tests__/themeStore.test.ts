import { useThemeStore } from '../themeStore';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
}));

const AsyncStorage = require('@react-native-async-storage/async-storage');

describe('Theme Store', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset store state before each test
    useThemeStore.setState({
      isDarkMode: false,
      fontSize: 'medium',
    });
  });

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const state = useThemeStore.getState();
      
      expect(state.isDarkMode).toBe(false);
      expect(state.fontSize).toBe('medium');
    });
  });

  describe('toggleTheme', () => {
    it('should toggle from light to dark mode', async () => {
      (AsyncStorage.setItem as jest.Mock).mockResolvedValue(undefined);
      
      useThemeStore.setState({ isDarkMode: false });
      
      await useThemeStore.getState().toggleTheme();
      
      expect(useThemeStore.getState().isDarkMode).toBe(true);
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('dark_mode', 'true');
    });

    it('should toggle from dark to light mode', async () => {
      (AsyncStorage.setItem as jest.Mock).mockResolvedValue(undefined);
      
      useThemeStore.setState({ isDarkMode: true });
      
      await useThemeStore.getState().toggleTheme();
      
      expect(useThemeStore.getState().isDarkMode).toBe(false);
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('dark_mode', 'false');
    });

    it('should persist theme preference to AsyncStorage', async () => {
      (AsyncStorage.setItem as jest.Mock).mockResolvedValue(undefined);
      
      await useThemeStore.getState().toggleTheme();
      
      expect(AsyncStorage.setItem).toHaveBeenCalled();
    });
  });

  describe('setFontSize', () => {
    it('should set font size to small', async () => {
      (AsyncStorage.setItem as jest.Mock).mockResolvedValue(undefined);
      
      await useThemeStore.getState().setFontSize('small');
      
      expect(useThemeStore.getState().fontSize).toBe('small');
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('font_size', 'small');
    });

    it('should set font size to medium', async () => {
      (AsyncStorage.setItem as jest.Mock).mockResolvedValue(undefined);
      
      await useThemeStore.getState().setFontSize('medium');
      
      expect(useThemeStore.getState().fontSize).toBe('medium');
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('font_size', 'medium');
    });

    it('should set font size to large', async () => {
      (AsyncStorage.setItem as jest.Mock).mockResolvedValue(undefined);
      
      await useThemeStore.getState().setFontSize('large');
      
      expect(useThemeStore.getState().fontSize).toBe('large');
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('font_size', 'large');
    });
  });

  describe('loadPreferences', () => {
    it('should load dark mode preference from storage', async () => {
      (AsyncStorage.getItem as jest.Mock)
        .mockResolvedValueOnce('true')
        .mockResolvedValueOnce(null);
      
      await useThemeStore.getState().loadPreferences();
      
      expect(useThemeStore.getState().isDarkMode).toBe(true);
    });

    it('should load font size preference from storage', async () => {
      (AsyncStorage.getItem as jest.Mock)
        .mockResolvedValueOnce(null)
        .mockResolvedValueOnce('large');
      
      await useThemeStore.getState().loadPreferences();
      
      expect(useThemeStore.getState().fontSize).toBe('large');
    });

    it('should load both preferences from storage', async () => {
      (AsyncStorage.getItem as jest.Mock)
        .mockResolvedValueOnce('true')
        .mockResolvedValueOnce('small');
      
      await useThemeStore.getState().loadPreferences();
      
      expect(useThemeStore.getState().isDarkMode).toBe(true);
      expect(useThemeStore.getState().fontSize).toBe('small');
    });

    it('should use default values when no preferences exist', async () => {
      (AsyncStorage.getItem as jest.Mock)
        .mockResolvedValueOnce(null)
        .mockResolvedValueOnce(null);
      
      await useThemeStore.getState().loadPreferences();
      
      expect(useThemeStore.getState().isDarkMode).toBe(false);
      expect(useThemeStore.getState().fontSize).toBe('medium');
    });

    it('should parse dark mode boolean correctly', async () => {
      (AsyncStorage.getItem as jest.Mock)
        .mockResolvedValueOnce('false')
        .mockResolvedValueOnce(null);
      
      await useThemeStore.getState().loadPreferences();
      
      expect(useThemeStore.getState().isDarkMode).toBe(false);
    });
  });

  describe('state persistence', () => {
    it('should call AsyncStorage.setItem when toggling theme', async () => {
      (AsyncStorage.setItem as jest.Mock).mockResolvedValue(undefined);
      
      await useThemeStore.getState().toggleTheme();
      
      expect(AsyncStorage.setItem).toHaveBeenCalledTimes(1);
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('dark_mode', expect.any(String));
    });

    it('should call AsyncStorage.setItem when setting font size', async () => {
      (AsyncStorage.setItem as jest.Mock).mockResolvedValue(undefined);
      
      await useThemeStore.getState().setFontSize('large');
      
      expect(AsyncStorage.setItem).toHaveBeenCalledTimes(1);
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('font_size', 'large');
    });
  });

  describe('state selectors', () => {
    it('should provide access to all state properties and actions', () => {
      const state = useThemeStore.getState();
      
      expect(typeof state.isDarkMode).toBe('boolean');
      expect(typeof state.fontSize).toBe('string');
      expect(typeof state.toggleTheme).toBe('function');
      expect(typeof state.setFontSize).toBe('function');
      expect(typeof state.loadPreferences).toBe('function');
    });
  });
});
