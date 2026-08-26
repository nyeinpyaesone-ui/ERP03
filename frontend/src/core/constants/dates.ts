/**
 * Date and Time Constants
 * Standardized date formats and timezone definitions
 * 
 * @module core/constants/dates
 */

/**
 * Common date format patterns
 */
export const DATE_FORMATS = {
  // Display formats
  DATE_SHORT: 'MM/dd/yyyy',
  DATE_MEDIUM: 'MMM dd, yyyy',
  DATE_LONG: 'MMMM dd, yyyy',
  DATE_FULL: 'EEEE, MMMM dd, yyyy',
  
  // Time formats
  TIME_SHORT: 'h:mm a',
  TIME_MEDIUM: 'h:mm:ss a',
  TIME_24H: 'HH:mm',
  TIME_24H_FULL: 'HH:mm:ss',
  
  // Combined formats
  DATETIME_SHORT: 'MM/dd/yyyy h:mm a',
  DATETIME_MEDIUM: 'MMM dd, yyyy h:mm a',
  DATETIME_LONG: 'MMMM dd, yyyy h:mm:ss a',
  DATETIME_ISO: "yyyy-MM-dd'T'HH:mm:ss.SSSXXX",
  DATETIME_ISO_ZULU: "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'",
  
  // Specialized formats
  DATE_INPUT: 'yyyy-MM-dd',
  TIME_INPUT: 'HH:mm',
  DATETIME_INPUT: "yyyy-MM-dd'T'HH:mm",
  
  // Fiscal/Reporting
  FISCAL_MONTH: 'MMM yyyy',
  FISCAL_QUARTER: 'QQQ yyyy',
  FISCAL_YEAR: 'yyyy',
  WEEK_RANGE: 'MMM dd - MMM dd, yyyy',
} as const;

/**
 * Common timezones for enterprise applications
 */
export const TIME_ZONES = {
  // UTC
  UTC: 'UTC',
  
  // North America
  EASTERN: 'America/New_York',
  CENTRAL: 'America/Chicago',
  MOUNTAIN: 'America/Denver',
  PACIFIC: 'America/Los_Angeles',
  ALASKA: 'America/Anchorage',
  HAWAII: 'Pacific/Honolulu',
  
  // Europe
  LONDON: 'Europe/London',
  PARIS: 'Europe/Paris',
  BERLIN: 'Europe/Berlin',
  MOSCOW: 'Europe/Moscow',
  
  // Asia
  TOKYO: 'Asia/Tokyo',
  SHANGHAI: 'Asia/Shanghai',
  HONG_KONG: 'Asia/Hong_Kong',
  SINGAPORE: 'Asia/Singapore',
  DUBAI: 'Asia/Dubai',
  KOLKATA: 'Asia/Kolkata',
  
  // Oceania
  SYDNEY: 'Australia/Sydney',
  AUCKLAND: 'Pacific/Auckland',
  
  // South America
  SAO_PAULO: 'America/Sao_Paulo',
  BUENOS_AIRES: 'America/Argentina/Buenos_Aires',
  
  // Africa
  JOHANNESBURG: 'Africa/Johannesburg',
  CAIRO: 'Africa/Cairo',
  LAGOS: 'Africa/Lagos',
} as const;

/**
 * Days of week (0 = Sunday)
 */
export const DAYS_OF_WEEK = [
  'Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
] as const;

/**
 * Months of year (0-indexed)
 */
export const MONTHS_OF_YEAR = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
] as const;

/**
 * Quarter definitions
 */
export const QUARTERS = [
  { label: 'Q1', months: [0, 1, 2], startMonth: 0 },
  { label: 'Q2', months: [3, 4, 5], startMonth: 3 },
  { label: 'Q3', months: [6, 7, 8], startMonth: 6 },
  { label: 'Q4', months: [9, 10, 11], startMonth: 9 },
] as const;

/**
 * Get timezone offset in minutes from UTC
 */
export function getTimezoneOffset(timeZone: string, date: Date = new Date()): number {
  const tzString = date.toLocaleString('en-US', { timeZone });
  const utcString = date.toLocaleString('en-US', { timeZone: 'UTC' });
  const diff = new Date(tzString).getTime() - new Date(utcString).getTime();
  return Math.round(diff / (1000 * 60));
}

/**
 * Check if timezone observes DST
 */
export function observesDST(timeZone: string): boolean {
  const jan = new Date(new Date().getFullYear(), 0, 1);
  const jul = new Date(new Date().getFullYear(), 6, 1);
  const janOffset = getTimezoneOffset(timeZone, jan);
  const julOffset = getTimezoneOffset(timeZone, jul);
  return janOffset !== julOffset;
}
