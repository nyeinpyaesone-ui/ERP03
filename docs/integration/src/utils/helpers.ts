import { format, parseISO } from 'date-fns';
import { enUS, my } from 'date-fns/locale';
import { useLanguage } from '../hooks/useLanguage';

// Date formatting utilities
export const formatDate = (date: string | Date, formatStr: string = 'PP'): string => {
  const { isMyanmar } = useLanguage();
  const d = typeof date === 'string' ? parseISO(date) : date;
  return format(d, formatStr, { locale: isMyanmar ? my : enUS });
};

export const formatDateTime = (date: string | Date): string => {
  const { isMyanmar } = useLanguage();
  const d = typeof date === 'string' ? parseISO(date) : date;
  return format(d, 'PPp', { locale: isMyanmar ? my : enUS });
};

export const formatRelativeTime = (date: string | Date): string => {
  const d = typeof date === 'string' ? parseISO(date) : date;
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - d.getTime()) / 1000);

  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
  return formatDate(date);
};

// Currency formatting
export const formatCurrency = (amount: number, currency: string = 'MMK'): string => {
  const { isMyanmar } = useLanguage();

  if (isMyanmar) {
    const formatted = new Intl.NumberFormat('my-MM').format(amount);
    return `${formatted} ${currency === 'MMK' ? 'ကျပ်' : currency}`;
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(amount);
};

// Number formatting
export const formatNumber = (num: number, decimals: number = 0): string => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
};

export const formatPercentage = (value: number, decimals: number = 1): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

// String utilities
export const truncate = (str: string, length: number = 50): string => {
  if (str.length <= length) return str;
  return str.substring(0, length) + '...';
};

export const slugify = (text: string): string => {
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^\w\-]+/g, '')
    .replace(/\-\-+/g, '-');
};

export const generateId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

export const initials = (name: string): string => {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .substring(0, 2);
};

// Color utilities
export const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    active: '#4caf50',
    inactive: '#9e9e9e',
    pending: '#ff9800',
    paid: '#4caf50',
    overdue: '#f44336',
    completed: '#4caf50',
    cancelled: '#f44336',
    draft: '#9e9e9e',
    in_progress: '#2196f3',
    approved: '#4caf50',
    rejected: '#f44336',
    present: '#4caf50',
    absent: '#f44336',
    late: '#ff9800',
    on_leave: '#9c27b0',
    in_stock: '#4caf50',
    low_stock: '#ff9800',
    out_of_stock: '#f44336',
    processing: '#2196f3',
    shipped: '#03a9f4',
    delivered: '#4caf50',
    refunded: '#9e9e9e',
  };
  return colors[status.toLowerCase()] || '#9e9e9e';
};

// Validation utilities
export const isValidEmail = (email: string): boolean => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
};

export const isValidPhone = (phone: string): boolean => {
  return /^[+]?[(]?[0-9]{1,4}[)]?[-\s.]?[0-9]{1,4}[-\s.]?[0-9]{1,9}$/.test(phone);
};

export const isValidMyanmarPhone = (phone: string): boolean => {
  return /^09[0-9]{7,9}$/.test(phone);
};

export const isValidURL = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

// Array utilities
export const groupBy = <T>(array: T[], key: keyof T): Record<string, T[]> => {
  return array.reduce((result, item) => {
    const groupKey = String(item[key]);
    result[groupKey] = result[groupKey] || [];
    result[groupKey].push(item);
    return result;
  }, {} as Record<string, T[]>);
};

export const sortBy = <T>(array: T[], key: keyof T, order: 'asc' | 'desc' = 'asc'): T[] => {
  return [...array].sort((a, b) => {
    if (a[key] < b[key]) return order === 'asc' ? -1 : 1;
    if (a[key] > b[key]) return order === 'asc' ? 1 : -1;
    return 0;
  });
};

export const uniqueBy = <T>(array: T[], key: keyof T): T[] => {
  const seen = new Set();
  return array.filter((item) => {
    const val = item[key];
    if (seen.has(val)) return false;
    seen.add(val);
    return true;
  });
};

// File utilities
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

export const getFileExtension = (filename: string): string => {
  return filename.slice(((filename.lastIndexOf('.') - 1) >>> 0) + 2);
};

export const isImageFile = (filename: string): boolean => {
  const ext = getFileExtension(filename).toLowerCase();
  return ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(ext);
};

// Deep clone utility
export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T;
  if (Array.isArray(obj)) return obj.map((item) => deepClone(item)) as unknown as T;
  const cloned = {} as T;
  Object.keys(obj).forEach((key) => {
    cloned[key as keyof T] = deepClone(obj[key as keyof T]);
  });
  return cloned;
};

// Debounce utility (for non-hook usage)
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

// Throttle utility
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

// Myanmar numerals conversion
export const toMyanmarNumerals = (num: number | string): string => {
  const myanmarDigits = ['၀', '၁', '၂', '၃', '၄', '၅', '၆', '၇', '၈', '၉'];
  return String(num)
    .split('')
    .map((char) => (char >= '0' && char <= '9' ? myanmarDigits[parseInt(char)] : char))
    .join('');
};

export const fromMyanmarNumerals = (str: string): number => {
  const myanmarDigits = ['၀', '၁', '၂', '၃', '၄', '၅', '၆', '၇', '၈', '၉'];
  const result = str
    .split('')
    .map((char) => {
      const index = myanmarDigits.indexOf(char);
      return index !== -1 ? String(index) : char;
    })
    .join('');
  return parseInt(result) || 0;
};

