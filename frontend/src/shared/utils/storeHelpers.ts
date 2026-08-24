/**
 * Performance-Optimized Store Utilities
 * Advanced patterns for high-performance state management across modules
 */

import { StateCreator } from 'zustand';
import { shallowEqual as fastShallowEqual } from './performance';

/**
 * Interface for common store state properties
 */
export interface CommonStoreState {
  isLoading: boolean;
  error: string | null;
}

/**
 * Interface for common store actions
 */
export interface CommonStoreActions {
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

/**
 * Create a slice for common store functionality
 * Can be composed with other slices using Zustand's pattern
 */
export const createCommonSlice = <T extends Record<string, any> = {}>(): StateCreator<
  CommonStoreState & CommonStoreActions & T,
  [['zustand/persist', unknown]],
  [],
  CommonStoreState & CommonStoreActions
> => (set) => ({
  isLoading: false,
  error: null,
  setIsLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
});

/**
 * Helper to create update handlers for array items
 * @param array - Current array
 * @param itemId - ID of item to update
 * @param updates - Updates to apply
 * @param idField - Name of ID field (default: 'id')
 */
export const updateArrayItem = <T extends Record<string, any>>(
  array: T[],
  itemId: string | number,
  updates: Partial<T>,
  idField: keyof T = 'id' as keyof T
): T[] => {
  return array.map((item) =>
    item[idField] === itemId ? { ...item, ...updates } : item
  );
};

/**
 * Helper to add item to array
 * @param array - Current array
 * @param item - Item to add
 */
export const addToArray = <T>(array: T[], item: T): T[] => {
  return [...array, item];
};

/**
 * Helper to remove item from array by ID
 * @param array - Current array
 * @param itemId - ID of item to remove
 * @param idField - Name of ID field (default: 'id')
 */
export const removeFromArray = <T extends Record<string, any>>(
  array: T[],
  itemId: string | number,
  idField: keyof T = 'id' as keyof T
): T[] => {
  return array.filter((item) => item[idField] !== itemId);
};

/**
 * Helper to find item in array by ID
 * @param array - Array to search
 * @param itemId - ID to find
 * @param idField - Name of ID field (default: 'id')
 */
export const findInArray = <T extends Record<string, any>>(
  array: T[],
  itemId: string | number,
  idField: keyof T = 'id' as keyof T
): T | undefined => {
  return array.find((item) => item[idField] === itemId);
};

/**
 * Helper to upsert (update or insert) item in array
 * @param array - Current array
 * @param item - Item to upsert
 * @param idField - Name of ID field (default: 'id')
 */
export const upsertInArray = <T extends Record<string, any>>(
  array: T[],
  item: T,
  idField: keyof T = 'id' as keyof T
): T[] => {
  const existingIndex = array.findIndex((i) => i[idField] === item[idField]);
  
  if (existingIndex >= 0) {
    const newArray = [...array];
    newArray[existingIndex] = item;
    return newArray;
  }
  
  return [...array, item];
};

/**
 * Optimized cart totals calculation with single-pass algorithm
 * @param items - Array of items with quantity, price, tax, discount
 */
export const calculateCartTotals = <
  T extends {
    quantity: number;
    subtotal?: number;
    taxAmount?: number;
    discountAmount?: number;
  }
>(
  items: T[]
): {
  subtotal: number;
  totalTax: number;
  totalDiscount: number;
  totalQuantity: number;
  itemCount: number;
} => {
  let subtotal = 0;
  let totalTax = 0;
  let totalDiscount = 0;
  let totalQuantity = 0;
  
  // Single pass optimization instead of multiple reduces
  for (const item of items) {
    subtotal += item.subtotal || 0;
    totalTax += item.taxAmount || 0;
    totalDiscount += item.discountAmount || 0;
    totalQuantity += item.quantity;
  }
  
  return {
    subtotal,
    totalTax,
    totalDiscount,
    totalQuantity,
    itemCount: items.length,
  };
};

/**
 * Create selector with built-in memoization for Zustand stores
 * Prevents unnecessary re-renders by caching results
 * @param selector - Function to select data from store
 * @param equalityFn - Custom equality function (defaults to optimized shallow equal)
 */
export const createSelector = <T, U>(
  selector: (state: T) => U,
  equalityFn: (a: U, b: U) => boolean = fastShallowEqual
): ((state: T) => U) => {
  let lastState: T | null = null;
  let lastResult: U | null = null;
  
  return (state: T): U => {
    if (
      lastState !== null &&
      lastResult !== null &&
      equalityFn(state as any, lastState as any)
    ) {
      return lastResult;
    }
    
    lastState = state;
    lastResult = selector(state);
    return lastResult;
  };
};

/**
 * Shallow equality comparison for objects
 * Optimized version with early exit strategies
 * @param obj1 - First object
 * @param obj2 - Second object
 */
export const shallowEqual = <T extends Record<string, any>>(obj1: T, obj2: T): boolean => {
  // Reference equality check (fastest)
  if (obj1 === obj2) return true;
  
  // Null/undefined check
  if (!obj1 || !obj2) return false;
  
  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);
  
  // Length mismatch (early exit)
  if (keys1.length !== keys2.length) return false;
  
  // Property comparison
  for (const key of keys1) {
    if (obj1[key] !== obj2[key]) return false;
  }
  
  return true;
};

/**
 * Create a persisted storage key with module prefix
 * @param moduleName - Name of the module
 * @param suffix - Optional suffix
 */
export const createStorageKey = (moduleName: string, suffix?: string): string => {
  return `${moduleName}-storage${suffix ? `-${suffix}` : ''}`;
};

/**
 * Batch state updates for better performance
 * Combines multiple updates into a single setState call
 * @param set - Zustand set function
 * @param updates - Array of partial state updates
 */
export const batchSetState = <T extends Record<string, any>>(
  set: (partial: Partial<T>) => void,
  updates: Array<Partial<T>>
): void => {
  const combined = updates.reduce((acc, update) => ({ ...acc, ...update }), {} as Partial<T>);
  set(combined);
};

/**
 * Create an optimized computed property that only recalculates when dependencies change
 * @param compute - Computation function
 * @param getDependencies - Function to get dependency values
 */
export const createComputed = <T, D>(
  compute: (deps: D) => T,
  getDependencies: () => D
): (() => T) => {
  let lastDeps: D | null = null;
  let lastResult: T | null = null;
  
  return (): T => {
    const deps = getDependencies();
    
    if (lastDeps !== null && fastShallowEqual(deps as any, lastDeps as any)) {
      return lastResult!;
    }
    
    lastDeps = deps;
    lastResult = compute(deps);
    return lastResult;
  };
};
