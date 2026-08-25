/**
 * Enterprise Validators
 * Standardized validation utilities for forms and data
 * 
 * @module core/utils/validators
 */

/**
 * Validation rule configuration
 */
export interface ValidationRule {
  /** Rule type */
  type: 'required' | 'email' | 'phone' | 'minLength' | 'maxLength' | 'pattern' | 'custom';
  /** Error message */
  message: string;
  /** Rule value (for minLength, maxLength, pattern) */
  value?: any;
  /** Custom validator function */
  validator?: (value: any) => boolean;
}

/**
 * Validator function type
 */
export type ValidatorFn = (value: any) => string | null;

/**
 * Validate required field
 * 
 * @example
 * ```typescript
 * validateRequired('');
 * // "This field is required"
 * 
 * validateRequired('value');
 * // null
 * ```
 */
export function validateRequired(value: any, message = 'This field is required'): string | null {
  if (value === null || value === undefined || value === '') {
    return message;
  }
  
  if (Array.isArray(value) && value.length === 0) {
    return message;
  }
  
  return null;
}

/**
 * Validate email format
 * 
 * @example
 * ```typescript
 * validateEmail('invalid');
 * // "Invalid email address"
 * 
 * validateEmail('user@example.com');
 * // null
 * ```
 */
export function validateEmail(value: string, message = 'Invalid email address'): string | null {
  if (!value) return null; // Skip if empty (use required validator)
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(value) ? null : message;
}

/**
 * Validate phone number (international format)
 * 
 * @example
 * ```typescript
 * validatePhone('123');
 * // "Invalid phone number"
 * 
 * validatePhone('+1-555-123-4567');
 * // null
 * ```
 */
export function validatePhone(value: string, message = 'Invalid phone number'): string | null {
  if (!value) return null; // Skip if empty (use required validator)
  
  // International phone number regex (flexible)
  const phoneRegex = /^[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}$/;
  return phoneRegex.test(value.replace(/\s/g, '')) ? null : message;
}

/**
 * Validate minimum length
 * 
 * @example
 * ```typescript
 * validateMinLength('ab', 3);
 * // "Must be at least 3 characters"
 * ```
 */
export function validateMinLength(
  value: string | any[],
  minLength: number,
  message?: string
): string | null {
  if (!value) return null;
  
  const actualMessage = message || `Must be at least ${minLength} characters`;
  return value.length >= minLength ? null : actualMessage;
}

/**
 * Validate maximum length
 * 
 * @example
 * ```typescript
 * validateMaxLength('verylongtext', 10);
 * // "Must be no more than 10 characters"
 * ```
 */
export function validateMaxLength(
  value: string | any[],
  maxLength: number,
  message?: string
): string | null {
  if (!value) return null;
  
  const actualMessage = message || `Must be no more than ${maxLength} characters`;
  return value.length <= maxLength ? null : actualMessage;
}

/**
 * Validate against a regex pattern
 * 
 * @example
 * ```typescript
 * validatePattern('abc123', /^[A-Z]+$/);
 * // "Invalid format"
 * ```
 */
export function validatePattern(
  value: string,
  pattern: RegExp,
  message = 'Invalid format'
): string | null {
  if (!value) return null;
  return pattern.test(value) ? null : message;
}

/**
 * Validate number range
 * 
 * @example
 * ```typescript
 * validateRange(5, { min: 1, max: 10 });
 * // null
 * 
 * validateRange(15, { min: 1, max: 10 });
 * // "Must be between 1 and 10"
 * ```
 */
export function validateRange(
  value: number,
  options: { min?: number; max?: number },
  message?: string
): string | null {
  if (value === null || value === undefined) return null;
  
  const { min, max } = options;
  const actualMessage = message || `Must be between ${min ?? '-∞'} and ${max ?? '∞'}`;
  
  if (min !== undefined && value < min) return actualMessage;
  if (max !== undefined && value > max) return actualMessage;
  
  return null;
}

/**
 * Create a composite validator from multiple rules
 * 
 * @example
 * ```typescript
 * const validateUserEmail = createValidator([
 *   { type: 'required', message: 'Email is required' },
 *   { type: 'email', message: 'Invalid email format' },
 * ]);
 * 
 * validateUserEmail('');
 * // "Email is required"
 * 
 * validateUserEmail('invalid');
 * // "Invalid email format"
 * 
 * validateUserEmail('valid@example.com');
 * // null
 * ```
 */
export function createValidator(rules: ValidationRule[]): ValidatorFn {
  return (value: any): string | null => {
    for (const rule of rules) {
      let isValid = true;
      
      switch (rule.type) {
        case 'required':
          isValid = validateRequired(value) === null;
          break;
        case 'email':
          isValid = validateEmail(value) === null;
          break;
        case 'phone':
          isValid = validatePhone(value) === null;
          break;
        case 'minLength':
          isValid = rule.value !== undefined && validateMinLength(value, rule.value) === null;
          break;
        case 'maxLength':
          isValid = rule.value !== undefined && validateMaxLength(value, rule.value) === null;
          break;
        case 'pattern':
          isValid = rule.value instanceof RegExp && validatePattern(value, rule.value) === null;
          break;
        case 'custom':
          isValid = rule.validator?.(value) ?? true;
          break;
      }
      
      if (!isValid) {
        return rule.message;
      }
    }
    
    return null;
  };
}

/**
 * Validate all fields in an object
 * 
 * @example
 * ```typescript
 * const errors = validateForm(
 *   { email: '', password: '123' },
 *   {
 *     email: [
 *       { type: 'required', message: 'Email required' },
 *       { type: 'email', message: 'Invalid email' },
 *     ],
 *     password: [
 *       { type: 'required', message: 'Password required' },
 *       { type: 'minLength', value: 8, message: 'Too short' },
 *     ],
 *   }
 * );
 * 
 * // { email: 'Email required', password: 'Too short' }
 * ```
 */
export function validateForm<T extends Record<string, any>>(
  values: T,
  rules: Record<keyof T, ValidationRule[]>
): Partial<Record<keyof T, string>> {
  const errors: Partial<Record<keyof T, string>> = {};
  
  for (const [field, fieldRules] of Object.entries(rules)) {
    const validator = createValidator(fieldRules);
    const error = validator(values[field as keyof T]);
    
    if (error) {
      errors[field as keyof T] = error;
    }
  }
  
  return errors;
}
