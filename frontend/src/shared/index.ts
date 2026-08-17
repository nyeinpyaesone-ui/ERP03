/**
 * Shared Module Index
 * Central export point for all shared utilities, hooks, and services
 */

// Auth utilities
export {
  getAuthToken,
  setAuthToken,
  setRefreshToken,
  getRefreshToken,
  clearAuthToken,
  isAuthenticated,
  getAuthHeaders,
  mergeHeaders,
} from './utils/auth';

// Helper utilities
export {
  formatCurrency,
  formatNumber,
  formatPercentage,
  formatCompactNumber,
  formatDate,
  formatRelativeTime,
  getTrendColor,
  getTrendIcon,
  calculateGrowthRate,
  calculatePercentageChange,
  calculateTotal,
  calculateWithTax,
  calculateDiscount,
  applyDiscount,
  debounce,
  throttle,
  clamp,
  roundTo,
  isEmpty,
  generateId,
} from './utils/helpers';

// Store helpers
export {
  createCommonSlice,
  updateArrayItem,
  addToArray,
  removeFromArray,
  findInArray,
  upsertInArray,
  calculateCartTotals,
  createSelector,
  shallowEqual,
  createStorageKey,
  type CommonStoreState,
  type CommonStoreActions,
} from './utils/storeHelpers';

// Performance utilities
export {
  createMemoizedCalculation,
  fastArrayOps,
  fastShallowEqual,
  createStableCallback,
  batchUpdates,
  debounceWithImmediate,
  throttleWithTrailing,
  createVirtualListCalculator,
  binarySearch,
  quickSelect,
  findMedian,
  createMemoizedSelector,
  deepClone,
  deepMerge,
  WorkerPool,
  performanceMonitor,
} from './utils/performance';

// Hooks
export {
  useApi,
  usePagination,
  useSearch,
  useModal,
} from './hooks/useCommon';

// API Client
export {
  createApiClient,
  getErrorMessage,
  handleApiResponse,
  retryWithBackoff,
  type ApiConfig,
} from './services/apiClient';
