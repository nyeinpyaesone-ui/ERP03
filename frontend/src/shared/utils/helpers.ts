/**
 * Shared utilities for formatting and calculations
 * Used across all frontend modules
 */

/**
 * Format currency value
 * @param value - Numeric value to format
 * @param currency - Currency code (default: USD)
 * @param locale - Locale string (default: en-US)
 */
export const formatCurrency = (value: number, currency = 'USD', locale = 'en-US'): string => {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
};

/**
 * Format number with thousand separators
 * @param value - Numeric value to format
 * @param locale - Locale string (default: en-US)
 */
export const formatNumber = (value: number, locale = 'en-US'): string => {
  return new Intl.NumberFormat(locale).format(value);
};

/**
 * Format percentage value
 * @param value - Percentage value (e.g., 25.5 for 25.5%)
 * @param decimals - Number of decimal places
 */
export const formatPercentage = (value: number, decimals: number = 1): string => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
};

/**
 * Format large numbers using compact notation (K, M, B)
 * @param value - Numeric value to format
 * @param locale - Locale string (default: en-US)
 */
export const formatCompactNumber = (value: number, locale = 'en-US'): string => {
  return new Intl.NumberFormat(locale, {
    notation: 'compact',
    compactDisplay: 'short',
  }).format(value);
};

/**
 * Format date string
 * @param dateString - ISO date string
 * @param options - Intl.DateTimeFormatOptions
 */
export const formatDate = (
  dateString: string,
  options: Intl.DateTimeFormatOptions = {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }
): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', options);
};

/**
 * Format relative time (e.g., "2h ago", "3d ago")
 * @param dateString - ISO date string
 */
export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateString);
};

/**
 * Get trend color based on change value
 * @param change - Percentage change value
 */
export const getTrendColor = (change: number): string => {
  if (change > 0) return '#388E3C'; // Green
  if (change < 0) return '#D32F2F'; // Red
  return '#757575'; // Gray
};

/**
 * Get trend icon name based on change value
 * @param change - Percentage change value
 */
export const getTrendIcon = (change: number): string => {
  if (change > 0) return 'trending-up';
  if (change < 0) return 'trending-down';
  return 'trending-neutral';
};

/**
 * Calculate growth rate between two values
 * @param current - Current value
 * @param previous - Previous value
 */
export const calculateGrowthRate = (current: number, previous: number): number => {
  if (previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / previous) * 100;
};

/**
 * Calculate percentage change
 * @param newValue - New value
 * @param oldValue - Old value
 */
export const calculatePercentageChange = (newValue: number, oldValue: number): number => {
  if (oldValue === 0) return 0;
  return ((newValue - oldValue) / oldValue) * 100;
};

/**
 * Calculate total from line items
 * @param items - Array of items with quantity and price
 */
export const calculateTotal = <T extends { quantity: number; price: number }>(items: T[]): number => {
  return items.reduce((sum, item) => sum + item.quantity * item.price, 0);
};

/**
 * Calculate subtotal with tax
 * @param amount - Base amount
 * @param taxRate - Tax rate as percentage
 */
export const calculateWithTax = (amount: number, taxRate: number): number => {
  return amount * (1 + taxRate / 100);
};

/**
 * Calculate discount amount
 * @param originalPrice - Original price
 * @param discountRate - Discount rate as percentage
 */
export const calculateDiscount = (originalPrice: number, discountRate: number): number => {
  return originalPrice * (discountRate / 100);
};

/**
 * Apply discount to price
 * @param originalPrice - Original price
 * @param discountRate - Discount rate as percentage
 */
export const applyDiscount = (originalPrice: number, discountRate: number): number => {
  return originalPrice - calculateDiscount(originalPrice, discountRate);
};

/**
 * Debounce function execution
 * @param func - Function to debounce
 * @param wait - Wait time in milliseconds
 */
export const debounce = <T extends (...args: any[]) => void>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * Throttle function execution
 * @param func - Function to throttle
 * @param limit - Minimum time between executions in milliseconds
 */
export const throttle = <T extends (...args: any[]) => void>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean = false;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

/**
 * Clamp number between min and max
 * @param value - Value to clamp
 * @param min - Minimum value
 * @param max - Maximum value
 */
export const clamp = (value: number, min: number, max: number): number => {
  return Math.min(Math.max(value, min), max);
};

/**
 * Round number to specified decimal places
 * @param value - Value to round
 * @param decimals - Number of decimal places
 */
export const roundTo = (value: number, decimals: number = 2): number => {
  const factor = Math.pow(10, decimals);
  return Math.round(value * factor) / factor;
};

/**
 * Check if value is empty (null, undefined, empty string, empty array, empty object)
 * @param value - Value to check
 */
export const isEmpty = (value: any): boolean => {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim() === '';
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
};

/**
 * Generate unique ID
 * @param prefix - Optional prefix for the ID
 */
export const generateId = (prefix: string = ''): string => {
  const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  return prefix ? `${prefix}-${id}` : id;
};
