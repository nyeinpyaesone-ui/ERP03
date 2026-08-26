/**
 * Object Utilities
 * Deep clone, merge, pick, omit, and other object helpers
 * 
 * @module core/utils/objects
 */

/**
 * Create a deep clone of an object
 * 
 * @example
 * ```typescript
 * const original = { a: 1, b: { c: 2 } };
 * const cloned = deepClone(original);
 * cloned.b.c = 3;
 * console.log(original.b.c); // 2 (unchanged)
 * ```
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime()) as any;
  }

  if (obj instanceof Array) {
    return obj.map(item => deepClone(item)) as any;
  }

  if (obj instanceof Object) {
    const clonedObj = {} as T;
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }

  return obj;
}

/**
 * Deep merge multiple objects
 * 
 * @example
 * ```typescript
 * const base = { a: 1, b: { c: 2, d: 3 } };
 * const override = { b: { c: 4 }, e: 5 };
 * const merged = deepMerge(base, override);
 * // { a: 1, b: { c: 4, d: 3 }, e: 5 }
 * ```
 */
export function deepMerge<T extends Record<string, any>>(...objects: Array<Partial<T>>): T {
  return objects.reduce((result, source) => {
    if (!source) return result;

    const output = { ...result };

    for (const key in source) {
      if (!Object.prototype.hasOwnProperty.call(source, key)) continue;

      const sourceValue = source[key];
      const targetValue = output[key];

      if (isPlainObject(sourceValue) && isPlainObject(targetValue)) {
        output[key] = deepMerge(targetValue, sourceValue);
      } else if (Array.isArray(sourceValue) && Array.isArray(targetValue)) {
        output[key] = [...targetValue, ...sourceValue] as any;
      } else {
        output[key] = sourceValue as any;
      }
    }

    return output;
  }, {} as T);
}

/**
 * Pick specific keys from an object
 * 
 * @example
 * ```typescript
 * const user = { id: 1, name: 'John', email: 'john@example.com', role: 'admin' };
 * const safeUser = pick(user, ['id', 'name']);
 * // { id: 1, name: 'John' }
 * ```
 */
export function pick<T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> {
  return keys.reduce((result, key) => {
    if (key in obj) {
      result[key] = obj[key];
    }
    return result;
  }, {} as Pick<T, K>);
}

/**
 * Omit specific keys from an object
 * 
 * @example
 * ```typescript
 * const user = { id: 1, name: 'John', email: 'john@example.com', role: 'admin' };
 * const safeUser = omit(user, ['email', 'role']);
 * // { id: 1, name: 'John' }
 * ```
 */
export function omit<T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> {
  const result = { ...obj };
  for (const key of keys) {
    delete result[key];
  }
  return result as Omit<T, K>;
}

/**
 * Flatten a nested object with dot notation keys
 * 
 * @example
 * ```typescript
 * const nested = { a: 1, b: { c: 2, d: { e: 3 } } };
 * const flat = flatten(nested);
 * // { a: 1, 'b.c': 2, 'b.d.e': 3 }
 * ```
 */
export function flatten(obj: Record<string, any>, prefix = ''): Record<string, any> {
  return Object.keys(obj).reduce((result, key) => {
    const value = obj[key];
    const newKey = prefix ? `${prefix}.${key}` : key;

    if (isPlainObject(value) && !isEmpty(value)) {
      Object.assign(result, flatten(value, newKey));
    } else {
      result[newKey] = value;
    }

    return result;
  }, {} as Record<string, any>);
}

/**
 * Group array items by a key or function
 * 
 * @example
 * ```typescript
 * const users = [
 *   { name: 'John', role: 'admin' },
 *   { name: 'Jane', role: 'user' },
 *   { name: 'Bob', role: 'admin' },
 * ];
 * 
 * const grouped = groupBy(users, 'role');
 * // { admin: [{ name: 'John' }, { name: 'Bob' }], user: [{ name: 'Jane' }] }
 * 
 * const groupedByFirstLetter = groupBy(users, u => u.name[0]);
 * // { J: [...], B: [...] }
 * ```
 */
export function groupBy<T>(
  items: T[],
  keyOrFn: keyof T | ((item: T) => string)
): Record<string, T[]> {
  const getKey = typeof keyOrFn === 'function'
    ? keyOrFn
    : (item: T) => String(item[keyOrFn]);

  return items.reduce((result, item) => {
    const key = getKey(item);
    if (!result[key]) {
      result[key] = [];
    }
    result[key].push(item);
    return result;
  }, {} as Record<string, T[]>);
}

/**
 * Check if value is a plain object
 */
function isPlainObject(value: any): value is Record<string, any> {
  return value !== null &&
    typeof value === 'object' &&
    value.constructor === Object;
}

/**
 * Check if object is empty
 */
function isEmpty(obj: Record<string, any>): boolean {
  return Object.keys(obj).length === 0;
}

/**
 * Get a nested value from an object using dot notation
 * 
 * @example
 * ```typescript
 * const obj = { a: { b: { c: 3 } } };
 * getNested(obj, 'a.b.c'); // 3
 * getNested(obj, 'a.b.d', 'default'); // 'default'
 * ```
 */
export function getNested<T = any>(
  obj: Record<string, any>,
  path: string,
  defaultValue?: T
): T | undefined {
  const keys = path.split('.');
  let result: any = obj;

  for (const key of keys) {
    if (result === null || result === undefined || !(key in result)) {
      return defaultValue;
    }
    result = result[key];
  }

  return result as T;
}

/**
 * Set a nested value in an object using dot notation
 * 
 * @example
 * ```typescript
 * const obj = { a: { b: { c: 3 } } };
 * setNested(obj, 'a.b.d', 4);
 * // { a: { b: { c: 3, d: 4 } } }
 * ```
 */
export function setNested<T extends Record<string, any>>(
  obj: T,
  path: string,
  value: any
): T {
  const keys = path.split('.');
  const lastKey = keys.pop()!;
  
  let current: any = obj;
  for (const key of keys) {
    if (!(key in current) || !isPlainObject(current[key])) {
      current[key] = {};
    }
    current = current[key];
  }
  
  current[lastKey] = value;
  return obj;
}

/**
 * Transform keys of an object
 * 
 * @example
 * ```typescript
 * const obj = { first_name: 'John', last_name: 'Doe' };
 * const camelCase = transformKeys(obj, key => 
 *   key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
 * );
 * // { firstName: 'John', lastName: 'Doe' }
 * ```
 */
export function transformKeys<T extends Record<string, any>>(
  obj: T,
  transformFn: (key: string) => string
): Record<string, any> {
  return Object.keys(obj).reduce((result, key) => {
    const value = obj[key];
    const newKey = transformFn(key);
    
    result[newKey] = isPlainObject(value) 
      ? transformKeys(value, transformFn)
      : value;
    
    return result;
  }, {} as Record<string, any>);
}
