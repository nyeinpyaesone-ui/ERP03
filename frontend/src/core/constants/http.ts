/**
 * HTTP Status Codes and Error Codes
 * Standardized constants for API communication
 * 
 * @module core/constants/http
 */

/**
 * HTTP Status Codes
 */
export const HTTP_STATUS = {
  // Success
  OK: 200,
  CREATED: 201,
  ACCEPTED: 202,
  NO_CONTENT: 204,
  
  // Redirection
  MOVED_PERMANENTLY: 301,
  FOUND: 302,
  NOT_MODIFIED: 304,
  
  // Client Errors
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  METHOD_NOT_ALLOWED: 405,
  CONFLICT: 409,
  GONE: 410,
  PRECONDITION_FAILED: 412,
  PAYLOAD_TOO_LARGE: 413,
  UNSUPPORTED_MEDIA_TYPE: 415,
  TOO_MANY_REQUESTS: 429,
  
  // Server Errors
  INTERNAL_SERVER_ERROR: 500,
  NOT_IMPLEMENTED: 501,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
  GATEWAY_TIMEOUT: 504,
} as const;

/**
 * Application Error Codes
 */
export const ERROR_CODES = {
  // Authentication & Authorization
  AUTH_REQUIRED: 'AUTH_REQUIRED',
  AUTH_INVALID_TOKEN: 'AUTH_INVALID_TOKEN',
  AUTH_TOKEN_EXPIRED: 'AUTH_TOKEN_EXPIRED',
  AUTH_ACCESS_DENIED: 'AUTH_ACCESS_DENIED',
  AUTH_INVALID_CREDENTIALS: 'AUTH_INVALID_CREDENTIALS',
  AUTH_ACCOUNT_LOCKED: 'AUTH_ACCOUNT_LOCKED',
  AUTH_ACCOUNT_DISABLED: 'AUTH_ACCOUNT_DISABLED',
  
  // Validation
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  VALIDATION_REQUIRED: 'VALIDATION_REQUIRED',
  VALIDATION_INVALID_FORMAT: 'VALIDATION_INVALID_FORMAT',
  VALIDATION_TOO_SHORT: 'VALIDATION_TOO_SHORT',
  VALIDATION_TOO_LONG: 'VALIDATION_TOO_LONG',
  VALIDATION_OUT_OF_RANGE: 'VALIDATION_OUT_OF_RANGE',
  
  // Resource Errors
  RESOURCE_NOT_FOUND: 'RESOURCE_NOT_FOUND',
  RESOURCE_CONFLICT: 'RESOURCE_CONFLICT',
  RESOURCE_ALREADY_EXISTS: 'RESOURCE_ALREADY_EXISTS',
  RESOURCE_DELETED: 'RESOURCE_DELETED',
  
  // Business Logic
  BUSINESS_RULE_VIOLATION: 'BUSINESS_RULE_VIOLATION',
  INSUFFICIENT_PERMISSIONS: 'INSUFFICIENT_PERMISSIONS',
  INVALID_STATE_TRANSITION: 'INVALID_STATE_TRANSITION',
  DEPENDENCY_MISSING: 'DEPENDENCY_MISSING',
  
  // System Errors
  SYSTEM_ERROR: 'SYSTEM_ERROR',
  DATABASE_ERROR: 'DATABASE_ERROR',
  EXTERNAL_SERVICE_ERROR: 'EXTERNAL_SERVICE_ERROR',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
  TIMEOUT: 'TIMEOUT',
  
  // Network Errors
  NETWORK_ERROR: 'NETWORK_ERROR',
  CONNECTION_LOST: 'CONNECTION_LOST',
  OFFLINE: 'OFFLINE',
} as const;

/**
 * Map error codes to user-friendly messages
 */
export const ERROR_MESSAGES: Record<string, string> = {
  [ERROR_CODES.AUTH_REQUIRED]: 'Please log in to continue',
  [ERROR_CODES.AUTH_INVALID_TOKEN]: 'Your session has expired. Please log in again.',
  [ERROR_CODES.AUTH_TOKEN_EXPIRED]: 'Your session has expired. Please log in again.',
  [ERROR_CODES.AUTH_ACCESS_DENIED]: 'You do not have permission to perform this action.',
  [ERROR_CODES.AUTH_INVALID_CREDENTIALS]: 'Invalid email or password.',
  [ERROR_CODES.AUTH_ACCOUNT_LOCKED]: 'Your account has been locked. Please contact support.',
  [ERROR_CODES.AUTH_ACCOUNT_DISABLED]: 'Your account has been disabled. Please contact support.',
  
  [ERROR_CODES.VALIDATION_ERROR]: 'Please check your input and try again.',
  [ERROR_CODES.VALIDATION_REQUIRED]: 'This field is required.',
  [ERROR_CODES.VALIDATION_INVALID_FORMAT]: 'Please enter a valid format.',
  [ERROR_CODES.VALIDATION_TOO_SHORT]: 'The value is too short.',
  [ERROR_CODES.VALIDATION_TOO_LONG]: 'The value is too long.',
  [ERROR_CODES.VALIDATION_OUT_OF_RANGE]: 'The value is out of range.',
  
  [ERROR_CODES.RESOURCE_NOT_FOUND]: 'The requested resource was not found.',
  [ERROR_CODES.RESOURCE_CONFLICT]: 'There is a conflict with the current state.',
  [ERROR_CODES.RESOURCE_ALREADY_EXISTS]: 'This resource already exists.',
  [ERROR_CODES.RESOURCE_DELETED]: 'This resource has been deleted.',
  
  [ERROR_CODES.BUSINESS_RULE_VIOLATION]: 'This action violates a business rule.',
  [ERROR_CODES.INSUFFICIENT_PERMISSIONS]: 'You do not have sufficient permissions.',
  [ERROR_CODES.INVALID_STATE_TRANSITION]: 'This action cannot be performed in the current state.',
  [ERROR_CODES.DEPENDENCY_MISSING]: 'A required dependency is missing.',
  
  [ERROR_CODES.SYSTEM_ERROR]: 'An unexpected error occurred. Please try again later.',
  [ERROR_CODES.DATABASE_ERROR]: 'A database error occurred. Please try again later.',
  [ERROR_CODES.EXTERNAL_SERVICE_ERROR]: 'An external service is unavailable.',
  [ERROR_CODES.RATE_LIMIT_EXCEEDED]: 'Too many requests. Please wait a moment.',
  [ERROR_CODES.SERVICE_UNAVAILABLE]: 'The service is temporarily unavailable.',
  [ERROR_CODES.TIMEOUT]: 'The request timed out. Please try again.',
  
  [ERROR_CODES.NETWORK_ERROR]: 'A network error occurred. Please check your connection.',
  [ERROR_CODES.CONNECTION_LOST]: 'Connection lost. Please check your network.',
  [ERROR_CODES.OFFLINE]: 'You are offline. Some features may not be available.',
};

/**
 * Get user-friendly error message
 */
export function getErrorMessage(code: string, fallback = 'An unexpected error occurred'): string {
  return ERROR_MESSAGES[code] || fallback;
}

/**
 * Check if status code indicates success
 */
export function isSuccessStatus(status: number): boolean {
  return status >= 200 && status < 300;
}

/**
 * Check if status code indicates client error
 */
export function isClientErrorStatus(status: number): boolean {
  return status >= 400 && status < 500;
}

/**
 * Check if status code indicates server error
 */
export function isServerErrorStatus(status: number): boolean {
  return status >= 500 && status < 600;
}

/**
 * Check if status code is retryable
 */
export function isRetryableStatus(status: number): boolean {
  return status === 408 || // Request Timeout
         status === 429 || // Too Many Requests
         status === 500 || // Internal Server Error
         status === 502 || // Bad Gateway
         status === 503 || // Service Unavailable
         status === 504;   // Gateway Timeout
}
