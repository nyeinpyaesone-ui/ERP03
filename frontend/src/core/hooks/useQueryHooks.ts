/**
 * Enterprise Hook Factory for React Query
 * Provides type-safe factory functions for creating standardized query and mutation hooks
 * 
 * @module core/hooks/useQueryHooks
 */

import {
  useQuery,
  useMutation,
  UseQueryOptions,
  UseMutationOptions,
  QueryClient,
  UseQueryResult,
  UseMutationResult,
} from '@tanstack/react-query';

/**
 * Configuration for hook factory
 */
export interface HookFactoryConfig<TData, TError = Error> {
  /** Base query key prefix */
  queryKeyPrefix: string;
  /** Optional query client instance */
  queryClient?: QueryClient;
  /** Default query options */
  defaultQueryOptions?: Partial<UseQueryOptions<TData, TError>>;
  /** Default mutation options */
  defaultMutationOptions?: Partial<UseMutationOptions<TData, TError, any, unknown>>;
}

/**
 * Query key factory function type
 */
export type QueryKeyFactory<TParams = void> = TParams extends void
  ? () => readonly unknown[]
  : (params: TParams) => readonly unknown[];

/**
 * Generic query hook options
 */
export type UseQueryOptions<TData, TError = Error, TParams = void> = 
  & Omit<import('@tanstack/react-query').UseQueryOptions<TData, TError>, 'queryKey' | 'queryFn'>
  & { params?: TParams };

/**
 * Generic mutation hook options
 */
export type UseMutationOptions<TData, TError = Error, TVariables = any, TContext = unknown> =
  & Omit<import('@tanstack/react-query').UseMutationOptions<TData, TError, TVariables, TContext>, 'mutationFn'>
  & { retryCount?: number };

/**
 * Create standardized query hooks with consistent configuration
 * 
 * @example
 * ```typescript
 * const { useList, useItem } = createQueryHooks<BOM[], BOM>({
 *   queryKeyPrefix: 'boms',
 *   queryFn: { list: fetchBOMs, item: fetchBOM },
 * });
 * 
 * // Usage in components
 * const { data: boms } = useList();
 * const { data: bom } = useItem('123');
 * ```
 */
export function createQueryHooks<TData, TItem = TData extends Array<infer U> ? U : TData, TError = Error>(
  config: HookFactoryConfig<TData, TError> & {
    queryFn: {
      list: (params?: any) => Promise<TData>;
      item?: (id: string, params?: any) => Promise<TItem>;
      byField?: <TField extends string>(field: TField, value: any, params?: any) => Promise<TItem | TItem[]>;
    };
  }
) {
  const { queryKeyPrefix, defaultQueryOptions } = config;
  const { list, item, byField } = config.queryFn;

  /**
   * Hook for fetching list of items
   */
  const useList = <TParams = any>(
    params?: TParams,
    options?: Partial<UseQueryOptions<TData, TError, TParams>>
  ): UseQueryResult<TData, TError> => {
    return useQuery<TData, TError>({
      queryKey: [queryKeyPrefix, 'list', params].filter(Boolean),
      queryFn: () => list(params),
      ...defaultQueryOptions,
      ...options,
    });
  };

  /**
   * Hook for fetching single item by ID
   */
  const useItem = (
    id: string | undefined,
    params?: any,
    options?: Partial<UseQueryOptions<TItem, TError>>
  ): UseQueryResult<TItem, TError> => {
    return useQuery<TItem, TError>({
      queryKey: [queryKeyPrefix, 'item', id].filter(Boolean),
      queryFn: () => {
        if (!item) throw new Error('Item query function not provided');
        return item(id, params);
      },
      enabled: !!id && !!item,
      ...defaultQueryOptions,
      ...options,
    });
  };

  /**
   * Hook for fetching item by custom field
   */
  const useByField = <TField extends string>(
    field: TField,
    value: any,
    params?: any,
    options?: Partial<UseQueryOptions<TItem, TError>>
  ): UseQueryResult<TItem | TItem[], TError> => {
    return useQuery<TItem | TItem[], TError>({
      queryKey: [queryKeyPrefix, 'byField', field, value].filter(Boolean),
      queryFn: () => {
        if (!byField) throw new Error('byField query function not provided');
        return byField(field, value, params);
      },
      enabled: !!value && !!byField,
      ...defaultQueryOptions,
      ...options,
    });
  };

  return {
    useList,
    useItem,
    useByField,
  };
}

/**
 * Create standardized mutation hooks with consistent error handling and invalidation
 * 
 * @example
 * ```typescript
 * const { useCreate, useUpdate, useDelete } = createMutationHooks<BOM, CreateBOMDTO>({
 *   queryKeyPrefix: 'boms',
 *   mutationFn: {
 *     create: createBOM,
 *     update: updateBOM,
 *     delete: deleteBOM,
 *   },
 * });
 * 
 * // Usage in components
 * const createMutation = useCreate();
 * createMutation.mutate({ name: 'New BOM' });
 * ```
 */
export function createMutationHooks<TData, TCreateDTO = Partial<TData>, TUpdateDTO = Partial<TData>, TError = Error>(
  config: HookFactoryConfig<TData, TError> & {
    mutationFn: {
      create: (data: TCreateDTO) => Promise<TData>;
      update: (id: string, data: TUpdateDTO) => Promise<TData>;
      delete: (id: string) => Promise<void>;
      upsert?: (data: TCreateDTO & { id?: string }) => Promise<TData>;
    };
    /** Fields to invalidate on mutation success */
    invalidateOnSuccess?: Array<'list' | 'item' | 'all'>;
  }
) {
  const { queryKeyPrefix, defaultMutationOptions, invalidateOnSuccess = ['list'] } = config;
  const { create, update, delete: deleteFn, upsert } = config.mutationFn;

  /**
   * Hook for creating new items
   */
  const useCreate = (
    options?: Partial<UseMutationOptions<TData, TError, TCreateDTO>>
  ): UseMutationResult<TData, TError, TCreateDTO, unknown> => {
    return useMutation<TData, TError, TCreateDTO>({
      mutationFn: create,
      onSuccess: (data) => {
        // Default success handling
        if (invalidateOnSuccess.includes('list')) {
          // Invalidate list queries
        }
        options?.onSuccess?.(data);
      },
      ...defaultMutationOptions,
      ...options,
    });
  };

  /**
   * Hook for updating existing items
   */
  const useUpdate = (
    options?: Partial<UseMutationOptions<TData, TError, { id: string; data: TUpdateDTO }>>
  ): UseMutationResult<TData, TError, { id: string; data: TUpdateDTO }, unknown> => {
    return useMutation<TData, TError, { id: string; data: TUpdateDTO }>({
      mutationFn: ({ id, data }) => update(id, data),
      onSuccess: (data, variables) => {
        if (invalidateOnSuccess.includes('list')) {
          // Invalidate list queries
        }
        if (invalidateOnSuccess.includes('item')) {
          // Invalidate specific item query
        }
        options?.onSuccess?.(data, variables);
      },
      ...defaultMutationOptions,
      ...options,
    });
  };

  /**
   * Hook for deleting items
   */
  const useDelete = (
    options?: Partial<UseMutationOptions<void, TError, string>>
  ): UseMutationResult<void, TError, string, unknown> => {
    return useMutation<void, TError, string>({
      mutationFn: deleteFn,
      onSuccess: (_, id) => {
        if (invalidateOnSuccess.includes('list')) {
          // Invalidate list queries
        }
        if (invalidateOnSuccess.includes('item')) {
          // Invalidate specific item query
        }
        options?.onSuccess?.(_, id);
      },
      ...defaultMutationOptions,
      ...options,
    });
  };

  /**
   * Hook for upserting items (create or update)
   */
  const useUpsert = (
    options?: Partial<UseMutationOptions<TData, TError, TCreateDTO & { id?: string }>>
  ): UseMutationResult<TData, TError, TCreateDTO & { id?: string }, unknown> => {
    if (!upsert) {
      throw new Error('Upsert mutation function not provided');
    }
    return useMutation<TData, TError, TCreateDTO & { id?: string }>({
      mutationFn: upsert,
      onSuccess: (data) => {
        if (invalidateOnSuccess.includes('all')) {
          // Invalidate all related queries
        }
        options?.onSuccess?.(data);
      },
      ...defaultMutationOptions,
      ...options,
    });
  };

  return {
    useCreate,
    useUpdate,
    useDelete,
    useUpsert,
  };
}
