/**
 * useStore Hook
 * Typed hook for accessing store state and actions
 * 
 * @module core/store/useStore
 */

import { useMemo } from 'react';
import { StoreApi, UseBoundStore } from 'zustand';

/**
 * Extract state type from store
 */
export type StoreState<T> = T extends UseBoundStore<infer S>
  ? S extends StoreApi<infer State>
    ? State
    : never
  : never;

/**
 * Extract actions type from store
 */
export type StoreActions<T> = {
  [K in keyof StoreState<T> as StoreState<T>[K] extends (...args: any[]) => any ? K : never]: StoreState<T>[K];
};

/**
 * Typed selector for store state
 */
export type Selector<T, U = T> = (state: StoreState<T>) => U;

/**
 * Equality function for selectors
 */
export type EqualityFn<T> = (a: T, b: T) => boolean;

/**
 * Shallow equality comparison for objects and arrays
 */
export function shallowEqual<T>(objA: T, objB: T): boolean {
  if (Object.is(objA, objB)) {
    return true;
  }

  if (
    typeof objA !== 'object' ||
    typeof objB !== 'object' ||
    objA === null ||
    objB === null
  ) {
    return false;
  }

  const keysA = Object.keys(objA);
  const keysB = Object.keys(objB);

  if (keysA.length !== keysB.length) {
    return false;
  }

  for (const key of keysA) {
    if (
      !Object.prototype.hasOwnProperty.call(objB, key) ||
      !Object.is((objA as any)[key], (objB as any)[key])
    ) {
      return false;
    }
  }

  return true;
}

/**
 * Enhanced useStore hook with typed selectors and actions
 * 
 * @example
 * ```typescript
 * // Full store access
 * const { user, fetchUser } = useStore(useUserStore);
 * 
 * // Select specific state
 * const user = useStore(useUserStore, state => state.user);
 * 
 * // Select with shallow equality
 * const { name, email } = useStore(
 *   useUserStore,
 *   state => ({ name: state.user.name, email: state.user.email }),
 *   shallowEqual
 * );
 * 
 * // Get only actions
 * const { fetchUser, updateUser } = useStore.actions(useUserStore);
 * ```
 */
export function useStore<T extends UseBoundStore<StoreApi<any>>>(
  store: T
): StoreState<T> & StoreActions<T>;

export function useStore<T extends UseBoundStore<StoreApi<any>>, U>(
  store: T,
  selector: Selector<T, U>,
  equalityFn?: EqualityFn<U>
): U;

export function useStore<T extends UseBoundStore<StoreApi<any>>, U>(
  store: T,
  selector?: Selector<T, U>,
  equalityFn?: EqualityFn<U>
): any {
  if (!selector) {
    // Return full store state and actions
    const state = store();
    const actions = useMemo(() => {
      const actionKeys = Object.keys(state).filter(
        key => typeof state[key as keyof typeof state] === 'function'
      );
      return actionKeys.reduce((acc, key) => {
        acc[key] = state[key as keyof typeof state];
        return acc;
      }, {} as Record<string, any>);
    }, [state]);

    return { ...state, ...actions };
  }

  // Use selector with optional equality function
  return store(selector as any, equalityFn);
}

/**
 * Get only actions from store (no state subscription)
 */
useStore.actions = <T extends UseBoundStore<StoreApi<any>>>(store: T): StoreActions<T> => {
  const state = store.getState();
  
  return useMemo(() => {
    const actionKeys = Object.keys(state).filter(
      key => typeof state[key as keyof typeof state] === 'function'
    );
    
    return actionKeys.reduce((acc, key) => {
      acc[key] = state[key as keyof typeof state];
      return acc;
    }, {} as StoreActions<T>);
  }, [state]);
};

/**
 * Get only state from store (no actions)
 */
useStore.state = <T extends UseBoundStore<StoreApi<any>>, U = StoreState<T>>(
  store: T,
  selector?: Selector<T, U>,
  equalityFn?: EqualityFn<U>
): U extends Selector<T, infer V> ? V : U => {
  if (!selector) {
    return store.getState() as any;
  }
  return store(selector as any, equalityFn);
};
