import { lightTheme, darkTheme, spacing, borderRadius } from '../theme';

describe('Theme', () => {
  describe('lightTheme', () => {
    it('should have correct primary colors', () => {
      expect(lightTheme.colors.primary).toBe('#3B82F6');
      expect(lightTheme.colors.primaryContainer).toBe('#DBEAFE');
    });

    it('should have correct secondary colors', () => {
      expect(lightTheme.colors.secondary).toBe('#8B5CF6');
      expect(lightTheme.colors.secondaryContainer).toBe('#EDE9FE');
    });

    it('should have correct surface colors', () => {
      expect(lightTheme.colors.surface).toBe('#FFFFFF');
      expect(lightTheme.colors.surfaceVariant).toBe('#F1F5F9');
      expect(lightTheme.colors.background).toBe('#F8FAFC');
    });

    it('should have correct semantic colors', () => {
      expect(lightTheme.colors.error).toBe('#EF4444');
      expect(lightTheme.colors.success).toBe('#10B981');
      expect(lightTheme.colors.warning).toBe('#F59E0B');
      expect(lightTheme.colors.info).toBe('#06B6D4');
    });

    it('should have elevation levels', () => {
      expect(lightTheme.colors.elevation).toBeDefined();
      expect(lightTheme.colors.elevation?.level0).toBe('transparent');
      expect(lightTheme.colors.elevation?.level1).toBe('#FFFFFF');
    });

    it('should have Inter font family', () => {
      expect(lightTheme.fonts.bodyLarge.fontFamily).toBe('Inter');
      expect(lightTheme.fonts.bodyMedium.fontFamily).toBe('Inter');
      expect(lightTheme.fonts.titleLarge.fontFamily).toBe('Inter');
      expect(lightTheme.fonts.titleLarge.fontWeight).toBe('700');
      expect(lightTheme.fonts.titleMedium.fontWeight).toBe('600');
    });
  });

  describe('darkTheme', () => {
    it('should have correct primary colors', () => {
      expect(darkTheme.colors.primary).toBe('#60A5FA');
      expect(darkTheme.colors.primaryContainer).toBe('#1E3A8A');
    });

    it('should have correct secondary colors', () => {
      expect(darkTheme.colors.secondary).toBe('#A78BFA');
      expect(darkTheme.colors.secondaryContainer).toBe('#4C1D95');
    });

    it('should have correct surface colors', () => {
      expect(darkTheme.colors.surface).toBe('#1E293B');
      expect(darkTheme.colors.surfaceVariant).toBe('#334155');
      expect(darkTheme.colors.background).toBe('#0F172A');
    });

    it('should have correct semantic colors', () => {
      expect(darkTheme.colors.error).toBe('#F87171');
      expect(darkTheme.colors.success).toBe('#34D399');
      expect(darkTheme.colors.warning).toBe('#FBBF24');
      expect(darkTheme.colors.info).toBe('#22D3EE');
    });
  });

  describe('spacing', () => {
    it('should have correct spacing values', () => {
      expect(spacing.xs).toBe(4);
      expect(spacing.sm).toBe(8);
      expect(spacing.md).toBe(16);
      expect(spacing.lg).toBe(24);
      expect(spacing.xl).toBe(32);
      expect(spacing.xxl).toBe(48);
    });

    it('should follow consistent scale', () => {
      expect(spacing.sm).toBe(spacing.xs * 2);
      expect(spacing.md).toBe(spacing.sm * 2);
      expect(spacing.lg).toBe(spacing.md * 1.5);
    });
  });

  describe('borderRadius', () => {
    it('should have correct border radius values', () => {
      expect(borderRadius.sm).toBe(6);
      expect(borderRadius.md).toBe(10);
      expect(borderRadius.lg).toBe(16);
      expect(borderRadius.xl).toBe(24);
      expect(borderRadius.full).toBe(9999);
    });

    it('should increase in size order', () => {
      expect(borderRadius.sm).toBeLessThan(borderRadius.md);
      expect(borderRadius.md).toBeLessThan(borderRadius.lg);
      expect(borderRadius.lg).toBeLessThan(borderRadius.xl);
      expect(borderRadius.xl).toBeLessThan(borderRadius.full);
    });
  });
});
