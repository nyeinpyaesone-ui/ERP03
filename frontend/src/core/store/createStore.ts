/**
 * Enterprise Store Factory
 * Creates type-safe Zustand-style stores with Redux-like slices
 * 
 * @module core/store/createStore
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

/**
 * Async operation status
 */
export type AsyncStatus = 'idle' | 'loading' | 'success' | 'error';

/**
 * Result of an async action
 */
export interface ActionResult<T = any> {
  status: AsyncStatus;
  data: T | null;
  error: string | null;
}

/**
 * Base state with async action tracking
 */
export interface BaseState {
  _actions: Record<string, AsyncStatus>;
  _errors: Record<string, string | null>;
}

/**
 * Store configuration
 */
export interface StoreConfig<TState extends BaseState, TActions = {}> {
  /** Unique store name */
  name: string;
  /** Initial state */
  initialState: TState;
  /** Actions that modify state */
  actions: (set: any, get: any) => TActions;
  /** Persist configuration */
  persist?: {
    enabled: boolean;
    key?: string;
    partialize?: (state: TState) => Partial<TState>;
  };
}

/**
 * Enhanced state with action status helpers
 */
export type StoreState<T extends BaseState> = T & {
  /** Get status of a specific action */
  getActionStatus: (actionName: string) => AsyncStatus;
  /** Get error of a specific action */
  getActionError: (actionName: string) => string | null;
  /** Check if any action is loading */
  isLoading: boolean;
  /** Check if any action has error */
  hasError: boolean;
};

/**
 * Enhanced actions with async helpers
 */
export type StoreActions<TActions> = TActions & {
  /** Set action status */
  _setActionStatus: (actionName: string, status: AsyncStatus) => void;
  /** Set action error */
  _setActionError: (actionName: string, error: string | null) => void;
};

/**
 * Create a standardized store with async action tracking
 * 
 * @example
 * ```typescript
 * const useUserStore = createStore({
 *   name: 'user',
 *   initialState: {
 *     user: null,
 *     _actions: {},
 *     _errors: {},
 *   },
 *   actions: (set, get) => ({
 *     fetchUser: async (id: string) => {
 *       get()._setActionStatus('fetchUser', 'loading');
 *       try {
 *         const user = await api.getUser(id);
 *         set({ user });
 *         get()._setActionStatus('fetchUser', 'success');
 *       } catch (error) {
 *         get()._setActionError('fetchUser', error.message);
 *       }
 *     },
 *   }),
 * });
 * ```
 */
export function createStore<TState extends BaseState, TActions = {}>(
  config: StoreConfig<TState, TActions>
) {
  const { name, initialState, actions } = config;

  const useStore = create<StoreState<TState> & StoreActions<TActions>>()(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      // Action status helpers
      getActionStatus: (actionName: string) => {
        const state = get() as StoreState<TState>;
        return state._actions[actionName] || 'idle';
      },

      getActionError: (actionName: string) => {
        const state = get() as StoreState<TState>;
        return state._errors[actionName] || null;
      },

      get isLoading() {
        const state = get() as StoreState<TState>;
        return Object.values(state._actions).some(status => status === 'loading');
      },

      get hasError() {
        const state = get() as StoreState<TState>;
        return Object.values(state._errors).some(error => error !== null);
      },

      _setActionStatus: (actionName: string, status: AsyncStatus) => {
        set((state: any) => ({
          _actions: { ...state._actions, [actionName]: status },
        }));
      },

      _setActionError: (actionName: string, error: string | null) => {
        set((state: any) => ({
          _errors: { ...state._errors, [actionName]: error },
        }));
      },

      // User-defined actions
      ...actions(set, get),
    }))
  );

  // Add store name for debugging
  useStore.setState = ((partial: any, replace?: boolean) => {
    console.debug(`[Store:${name}] State update`, { partial, replace });
    return useStore.setState(partial, replace);
  }) as any;

  return useStore;
}

/**
 * Create a slice of state and actions for modular stores
 * 
 * @example
 * ```typescript
 * const userSlice = createSlice({
 *   name: 'user',
 *   initialState: { user: null },
 *   actions: (set, get) => ({
 *     setUser: (user) => set({ user }),
 *   }),
 * });
 * 
 * const useStore = createStore({
 *   name: 'app',
 *   initialState: { ...userSlice.initialState },
 *   actions: (set, get) => ({
 *     ...userSlice.actions(set, get),
 *   }),
 * });
 * ```
 */
export function createSlice<TState, TActions = {}>(config: {
  name: string;
  initialState: TState;
  actions: (set: any, get: any) => TActions;
}) {
  return {
    name: config.name,
    initialState: config.initialState,
    actions: config.actions,
  };
}
