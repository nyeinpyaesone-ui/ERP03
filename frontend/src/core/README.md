# ERP03 Frontend Core Module

Enterprise-grade shared utilities, hooks, store patterns, and constants for all frontend modules.

## Overview

The `core` module provides standardized, production-ready functionality that can be reused across all frontend modules (MRP, E-commerce, POS, BI Dashboard). This ensures consistency, reduces code duplication, and maintains enterprise-level quality standards.

## Module Structure

```
src/core/
├── api/              # API client and HTTP utilities
│   ├── apiClient.ts  # Axios-based API client with auth & retry
│   └── index.ts      # Public exports
├── hooks/            # Reusable React hooks
│   ├── useQueryHooks.ts    # Query/mutation hook factories
│   ├── useAsyncAction.ts   # Async action state management
│   ├── useDebounce.ts      # Debounce utilities
│   ├── useLocalStorage.ts  # Persistent storage hooks
│   └── index.ts
├── store/            # State management utilities
│   ├── createStore.ts      # Zustand-based store factory
│   ├── useStore.ts         # Typed store access hook
│   └── index.ts
├── utils/            # Utility functions
│   ├── formatters.ts       # Date, number, currency formatters
│   ├── validators.ts       # Form and data validators
│   ├── async.ts            # Async utilities (retry, debounce, throttle)
│   ├── objects.ts          # Object manipulation utilities
│   └── index.ts
├── constants/        # Application-wide constants
│   ├── http.ts             # HTTP status codes and error codes
│   ├── dates.ts            # Date formats and timezones
│   ├── pagination.ts       # Pagination defaults
│   ├── permissions.ts      # RBAC permissions and roles
│   └── index.ts
├── types/            # Shared TypeScript types
└── index.ts          # Main entry point
```

## Installation

Ensure required dependencies are installed:

```bash
npm install axios @tanstack/react-query zustand @react-native-async-storage/async-storage
```

## Usage

### API Client

```typescript
import { createAPIClient, setAuthToken, handleError } from '@/core/api';

// Create API client for your module
const api = createAPIClient('https://api.erp03.com/manufacturing', 30000);

// Set auth token after login
await setAuthToken('jwt_token_here');

// Use in your API service
export const bomAPI = {
  getAll: () => api.get<BOM[]>('/boms').then(r => r.data),
  getById: (id: string) => api.get<BOM>(`/boms/${id}`).then(r => r.data),
  create: (data: CreateBOMDTO) => api.post<BOM>('/boms', data).then(r => r.data),
};
```

### Hook Factories

```typescript
import { createQueryHooks, createMutationHooks } from '@/core/hooks';
import { bomAPI } from './services/api/mrpApi';

// Create standardized hooks for BOM entity
const { useList, useItem } = createQueryHooks<BOM[], BOM>({
  queryKeyPrefix: 'boms',
  queryFn: {
    list: bomAPI.getAll,
    item: bomAPI.getById,
  },
});

const { useCreate, useUpdate, useDelete } = createMutationHooks<BOM, CreateBOMDTO>({
  queryKeyPrefix: 'boms',
  mutationFn: {
    create: bomAPI.create,
    update: bomAPI.update,
    delete: bomAPI.delete,
  },
  invalidateOnSuccess: ['list'],
});

// Use in components
function BOMList() {
  const { data: boms, isLoading } = useList();
  const createMutation = useCreate();
  
  return (/* ... */);
}
```

### Async Actions

```typescript
import { useAsyncAction } from '@/core/hooks';

function LoginScreen() {
  const { execute, isLoading, result } = useAsyncAction<User>({
    onSuccess: (user) => {
      console.log('Logged in:', user.name);
    },
    onError: (error) => {
      console.error('Login failed:', error.message);
    },
  });
  
  const handleLogin = async () => {
    await execute(() => authAPI.login(credentials));
  };
  
  return (/* ... */);
}
```

### Store

```typescript
import { createStore, createSlice } from '@/core/store';

// Create a slice
const userSlice = createSlice({
  name: 'user',
  initialState: { user: null, preferences: {} },
  actions: (set, get) => ({
    setUser: (user) => set({ user }),
    updatePreferences: (prefs) => 
      set({ preferences: { ...get().preferences, ...prefs } }),
  }),
});

// Create store
const useAppStore = createStore({
  name: 'app',
  initialState: {
    ...userSlice.initialState,
    _actions: {},
    _errors: {},
  },
  actions: (set, get) => ({
    ...userSlice.actions(set, get),
  }),
});

// Use in components
const { user, setUser } = useAppStore();
```

### Utilities

```typescript
import { 
  formatDate, 
  formatCurrency, 
  validateEmail, 
  deepClone,
  retry 
} from '@/core/utils';

// Formatters
formatDate(new Date(), { dateStyle: 'long' }); // "January 15, 2024"
formatCurrency(1234.56, { currency: 'USD' });  // "$1,234.56"

// Validators
validateEmail('user@example.com'); // null
validateEmail('invalid');          // "Invalid email address"

// Object utilities
const cloned = deepClone(original);
const picked = pick(obj, ['id', 'name']);

// Async utilities
const result = await retry(() => api.fetchData(), {
  maxRetries: 3,
  initialDelay: 1000,
});
```

### Constants

```typescript
import { 
  HTTP_STATUS, 
  ERROR_CODES, 
  DATE_FORMATS,
  PERMISSIONS,
  ROLES,
  PAGINATION_DEFAULTS 
} from '@/core/constants';

// Check permissions
import { hasPermission } from '@/core/constants/permissions';
if (hasPermission(userRole, PERMISSIONS.ORDERS_APPROVE)) {
  // Show approve button
}

// Use pagination defaults
const { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS } = PAGINATION_DEFAULTS;
```

## Features

### API Client
- ✅ Automatic JWT token refresh on 401 responses
- ✅ Unified error handling with 15+ error codes
- ✅ Exponential backoff retry logic (configurable)
- ✅ Token storage via AsyncStorage
- ✅ Request/response interceptors
- ✅ Type-safe response handlers

### Hook Factories
- ✅ Type-safe query hook generation
- ✅ Standardized mutation hooks with invalidation
- ✅ Consistent loading/error states
- ✅ Reduced boilerplate by ~70%

### Store
- ✅ Zustand-based state management
- ✅ Async action tracking (idle/loading/success/error)
- ✅ Modular slice pattern
- ✅ Typed selectors with shallow equality

### Utilities
- ✅ Intl-based formatters (dates, numbers, currencies)
- ✅ Comprehensive validation rules
- ✅ Retry with exponential backoff
- ✅ Debounce/throttle functions
- ✅ Deep clone/merge utilities
- ✅ Object manipulation (pick, omit, flatten, groupBy)

### Constants
- ✅ HTTP status codes
- ✅ Standardized error codes and messages
- ✅ Date/time formats and timezones
- ✅ Pagination defaults
- ✅ RBAC permissions and roles

## Best Practices

1. **Import from core**: Always use core utilities instead of creating module-specific implementations
2. **Type safety**: Leverage TypeScript types from core modules
3. **Error handling**: Use standardized error codes and messages
4. **Consistency**: Follow established patterns for hooks, stores, and API services
5. **Documentation**: Add JSDoc comments to custom extensions

## Migration Guide

To migrate existing module code to use core utilities:

1. Replace custom API clients with `createAPIClient`
2. Refactor hooks to use `createQueryHooks` and `createMutationHooks`
3. Consolidate stores using `createStore` and `createSlice`
4. Replace utility functions with core equivalents
5. Use constants instead of hardcoded values

## Testing

All core utilities are designed to be testable:

```typescript
import { renderHook } from '@testing-library/react-hooks';
import { useAsyncAction } from '@/core/hooks';

test('useAsyncAction handles success', async () => {
  const { result } = renderHook(() => useAsyncAction());
  
  await result.current.execute(async () => 'success');
  
  expect(result.current.isSuccess).toBe(true);
  expect(result.current.data).toBe('success');
});
```

## Contributing

When adding new utilities to core:

1. Ensure broad applicability across modules
2. Include comprehensive JSDoc documentation
3. Add usage examples
4. Maintain type safety
5. Follow existing code style
6. Update this README

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Maintainer**: ERP03 Frontend Team
