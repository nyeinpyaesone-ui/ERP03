/**
 * ERP03 Frontend Core Hooks Module
 * Reusable React Query hooks and utilities for enterprise applications
 * 
 * @module core/hooks
 * @description Factory functions for creating type-safe query and mutation hooks
 */

export { createQueryHooks, createMutationHooks } from './useQueryHooks';
export { useAsyncAction } from './useAsyncAction';
export { useDebounce } from './useDebounce';
export { useLocalStorage } from './useLocalStorage';

export type {
  UseQueryOptions,
  UseMutationOptions,
  QueryKeyFactory,
  HookFactoryConfig,
} from './useQueryHooks';

export type {
  AsyncActionOptions,
  AsyncActionResult,
} from './useAsyncAction';
