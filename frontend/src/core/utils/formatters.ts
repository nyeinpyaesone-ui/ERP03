/**
 * Enterprise Formatters
 * Standardized formatting utilities for dates, numbers, currencies
 * 
 * @module core/utils/formatters
 */

/**
 * Date format options
 */
export interface DateFormatOptions {
  /** Locale string (default: 'en-US') */
  locale?: string;
  /** Date style: short, medium, long, full */
  dateStyle?: 'short' | 'medium' | 'long' | 'full';
  /** Time style: short, medium, long, full */
  timeStyle?: 'short' | 'medium' | 'long' | 'full';
  /** Custom format pattern */
  format?: string;
  /** Timezone (default: system timezone) */
  timeZone?: string;
}

/**
 * Currency format options
 */
export interface CurrencyFormatOptions {
  /** Currency code (default: 'USD') */
  currency?: string;
  /** Locale string (default: 'en-US') */
  locale?: string;
  /** Minimum fraction digits */
  minimumFractionDigits?: number;
  /** Maximum fraction digits */
  maximumFractionDigits?: number;
  /** Display style: symbol, code, name */
  currencyDisplay?: 'symbol' | 'code' | 'name';
  /** Use grouping separators */
  useGrouping?: boolean;
}

/**
 * Format a date with locale and options
 * 
 * @example
 * ```typescript
 * formatDate(new Date(), { dateStyle: 'long', locale: 'en-US' });
 * // "January 15, 2024"
 * 
 * formatDate('2024-01-15T10:30:00Z', { 
 *   dateStyle: 'medium', 
 *   timeStyle: 'short',
 *   timeZone: 'America/New_York'
 * });
 * // "Jan 15, 2024, 5:30 AM"
 * ```
 */
export function formatDate(value: Date | string | number, options: DateFormatOptions = {}): string {
  const {
    locale = 'en-US',
    dateStyle = 'medium',
    timeStyle,
    timeZone,
  } = options;

  const date = new Date(value);
  
  if (isNaN(date.getTime())) {
    console.warn('Invalid date value:', value);
    return 'Invalid Date';
  }

  const intlOptions: Intl.DateTimeFormatOptions = { dateStyle };
  
  if (timeStyle) {
    intlOptions.timeStyle = timeStyle;
  }
  
  if (timeZone) {
    intlOptions.timeZone = timeZone;
  }

  return new Intl.DateTimeFormat(locale, intlOptions).format(date);
}

/**
 * Format a number as currency
 * 
 * @example
 * ```typescript
 * formatCurrency(1234.56, { currency: 'USD' });
 * // "$1,234.56"
 * 
 * formatCurrency(1234.56, { currency: 'EUR', locale: 'de-DE' });
 * // "1.234,56 €"
 * 
 * formatCurrency(1234.567, { currency: 'JPY', minimumFractionDigits: 0 });
 * // "¥1,235"
 * ```
 */
export function formatCurrency(value: number, options: CurrencyFormatOptions = {}): string {
  const {
    currency = 'USD',
    locale = 'en-US',
    minimumFractionDigits,
    maximumFractionDigits,
    currencyDisplay = 'symbol',
    useGrouping = true,
  } = options;

  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits,
    maximumFractionDigits,
    currencyDisplay,
    useGrouping,
  }).format(value);
}

/**
 * Format a number with locale-specific grouping and decimals
 * 
 * @example
 * ```typescript
 * formatNumber(1234567.89, { locale: 'en-US' });
 * // "1,234,567.89"
 * 
 * formatNumber(1234567.89, { locale: 'de-DE' });
 * // "1.234.567,89"
 * 
 * formatNumber(0.123456, { maximumFractionDigits: 2 });
 * // "0.12"
 * ```
 */
export function formatNumber(value: number, options: {
  locale?: string;
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  useGrouping?: boolean;
  style?: 'decimal' | 'percent' | 'unit';
  unit?: string;
} = {}): string {
  const {
    locale = 'en-US',
    minimumFractionDigits,
    maximumFractionDigits,
    useGrouping = true,
    style = 'decimal',
    unit,
  } = options;

  const intlOptions: Intl.NumberFormatOptions = {
    style,
    minimumFractionDigits,
    maximumFractionDigits,
    useGrouping,
  };

  if (style === 'unit' && unit) {
    intlOptions.unit = unit;
    intlOptions.unitDisplay = 'short';
  }

  return new Intl.NumberFormat(locale, intlOptions).format(value);
}

/**
 * Format a number as percentage
 * 
 * @example
 * ```typescript
 * formatPercentage(0.1234);
 * // "12.34%"
 * 
 * formatPercentage(0.1234, { minimumFractionDigits: 1 });
 * // "12.3%"
 * 
 * formatPercentage(0.5, { locale: 'de-DE' });
 * // "50 %"
 * ```
 */
export function formatPercentage(
  value: number,
  options: {
    locale?: string;
    minimumFractionDigits?: number;
    maximumFractionDigits?: number;
  } = {}
): string {
  const {
    locale = 'en-US',
    minimumFractionDigits = 2,
    maximumFractionDigits = 2,
  } = options;

  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits,
    maximumFractionDigits,
  }).format(value);
}

/**
 * Format relative time (e.g., "2 hours ago", "in 3 days")
 * 
 * @example
 * ```typescript
 * formatRelativeTime(Date.now() - 3600000);
 * // "1 hour ago"
 * 
 * formatRelativeTime(Date.now() + 86400000);
 * // "in 1 day"
 * ```
 */
export function formatRelativeTime(
  value: Date | string | number,
  options: { locale?: string; numeric?: 'auto' | 'always' } = {}
): string {
  const { locale = 'en-US', numeric = 'auto' } = options;

  const date = new Date(value);
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffSecs = Math.round(diffMs / 1000);
  const diffMins = Math.round(diffSecs / 60);
  const diffHours = Math.round(diffMins / 60);
  const diffDays = Math.round(diffHours / 24);
  const diffWeeks = Math.round(diffDays / 7);
  const diffMonths = Math.round(diffDays / 30);
  const diffYears = Math.round(diffDays / 365);

  const rtf = new Intl.RelativeTimeFormat(locale, { numeric });

  if (Math.abs(diffYears) >= 1) {
    return rtf.format(Math.round(diffDays / 365), 'year');
  }
  if (Math.abs(diffMonths) >= 1) {
    return rtf.format(Math.round(diffDays / 30), 'month');
  }
  if (Math.abs(diffWeeks) >= 1) {
    return rtf.format(Math.round(diffDays / 7), 'week');
  }
  if (Math.abs(diffDays) >= 1) {
    return rtf.format(diffDays, 'day');
  }
  if (Math.abs(diffHours) >= 1) {
    return rtf.format(diffHours, 'hour');
  }
  if (Math.abs(diffMins) >= 1) {
    return rtf.format(diffMins, 'minute');
  }
  return rtf.format(diffSecs, 'second');
}
