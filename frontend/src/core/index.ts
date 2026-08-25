/**
 * ERP03 Frontend Core Module
 * Enterprise-grade shared utilities and services
 * 
 * @module core
 * @description Centralized core functionality for all frontend modules
 */

export * from './api';
export * from './hooks';
export * from './store';
export * from './utils';
export * from './constants';

// Re-export commonly used types
export type {
  APIResponse,
  PaginatedResponse,
  QueryConfig,
  MutationConfig,
} from './api';

export type {
  AsyncStatus,
  ActionResult,
} from './store';
