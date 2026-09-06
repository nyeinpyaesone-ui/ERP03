/**
 * Shared utility hooks for common patterns across modules
 */

import { useState, useCallback, useEffect } from 'react';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiReturn<T> extends UseApiState<T> {
  fetchData: (promise: Promise<T>) => Promise<void>;
  reset: () => void;
}

/**
 * Hook for handling API call state management
 * @param initialState - Optional initial data
 * @returns State and handlers for API operations
 */
export function useApi<T>(initialState?: T | null): UseApiReturn<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: initialState ?? null,
    loading: false,
    error: null,
  });

  const fetchData = useCallback(async (promise: Promise<T>) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const data = await promise;
      setState({ data, loading: false, error: null });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred';
      setState(prev => ({ ...prev, loading: false, error: errorMessage, data: null }));
      throw error;
    }
  }, []);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    fetchData,
    reset,
  };
}

interface PaginationState {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

interface UsePaginationReturn extends PaginationState {
  setPage: (page: number) => void;
  setLimit: (limit: number) => void;
  setTotal: (total: number) => void;
  nextPage: () => void;
  prevPage: () => void;
  goToPage: (page: number) => void;
  hasNextPage: boolean;
  hasPrevPage: boolean;
  reset: () => void;
}

/**
 * Hook for managing pagination state
 * @param initialLimit - Initial items per page
 * @returns Pagination state and handlers
 */
export function usePagination(initialLimit: number = 10): UsePaginationReturn {
  const [state, setState] = useState<PaginationState>({
    page: 1,
    limit: initialLimit,
    total: 0,
    totalPages: 0,
  });

  const setPage = useCallback((page: number) => {
    setState(prev => ({ ...prev, page: Math.max(1, page) }));
  }, []);

  const setLimit = useCallback((limit: number) => {
    setState(prev => ({ 
      ...prev, 
      limit: Math.max(1, limit),
      page: 1, // Reset to first page when limit changes
    }));
  }, []);

  const setTotal = useCallback((total: number) => {
    setState(prev => ({
      ...prev,
      total,
      totalPages: Math.ceil(total / prev.limit),
    }));
  }, []);

  const nextPage = useCallback(() => {
    setState(prev => ({
      ...prev,
      page: Math.min(prev.page + 1, prev.totalPages || prev.page),
    }));
  }, []);

  const prevPage = useCallback(() => {
    setState(prev => ({
      ...prev,
      page: Math.max(1, prev.page - 1),
    }));
  }, []);

  const goToPage = useCallback((page: number) => {
    setState(prev => ({
      ...prev,
      page: Math.max(1, Math.min(page, prev.totalPages)),
    }));
  }, []);

  const reset = useCallback(() => {
    setState({
      page: 1,
      limit: initialLimit,
      total: 0,
      totalPages: 0,
    });
  }, [initialLimit]);

  return {
    ...state,
    setPage,
    setLimit,
    setTotal,
    nextPage,
    prevPage,
    goToPage,
    hasNextPage: state.page < state.totalPages,
    hasPrevPage: state.page > 1,
    reset,
  };
}

interface UseSearchOptions {
  debounceMs?: number;
  minLength?: number;
}

interface UseSearchReturn {
  query: string;
  isSearching: boolean;
  setQuery: (query: string) => void;
  clearQuery: () => void;
}

/**
 * Hook for managing search input with debouncing
 * @param options - Search configuration options
 * @returns Search state and handlers
 */
export function useSearch(options: UseSearchOptions = {}): UseSearchReturn {
  const { debounceMs = 300, minLength = 1 } = options;
  const [query, setQueryState] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [debouncedQuery, setDebouncedQuery] = useState('');

  useEffect(() => {
    if (query.length < minLength) {
      setDebouncedQuery('');
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
      setIsSearching(false);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [query, debounceMs, minLength]);

  const setQuery = useCallback((newQuery: string) => {
    setQueryState(newQuery);
  }, []);

  const clearQuery = useCallback(() => {
    setQueryState('');
    setDebouncedQuery('');
    setIsSearching(false);
  }, []);

  return {
    query,
    isSearching,
    setQuery,
    clearQuery,
  };
}

interface UseModalReturn {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
}

/**
 * Hook for managing modal visibility state
 * @param initialOpen - Initial modal state
 * @returns Modal state and handlers
 */
export function useModal(initialOpen: boolean = false): UseModalReturn {
  const [isOpen, setIsOpen] = useState(initialOpen);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const toggle = useCallback(() => setIsOpen(prev => !prev), []);

  return {
    isOpen,
    open,
    close,
    toggle,
  };
}
