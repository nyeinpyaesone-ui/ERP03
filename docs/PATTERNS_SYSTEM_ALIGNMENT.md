# Design Patterns & System Alignment Guide

Architectural patterns, design principles, and system alignment strategies used throughout the ERP platform.

## Table of Contents

1. [Architectural Patterns](#architectural-patterns)
2. [Design Patterns](#design-patterns)
3. [Frontend Patterns](#frontend-patterns)
4. [Backend Patterns](#backend-patterns)
5. [System Alignment](#system-alignment)
6. [Code Organization](#code-organization)

---

## Architectural Patterns

### 1.1 Multi-Module Architecture

**Pattern:** Modular Monolith with Clear Boundaries

The ERP system uses a multi-module architecture where each business domain operates as an independent module while sharing common infrastructure.

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Shell                        │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│E-commerce│   MRP    │   POS    │    BI    │   Shared    │
│  Module  │  Module  │  Module  │ Dashboard│  Components │
└──────────┴──────────┴──────────┴──────────┴─────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   API Gateway Layer                      │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  Backend Services                        │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│   User   │   CRM    │Inventory │ Finance  │    HR       │
│ Service  │ Service  │ Service  │ Service  │   Service   │
└──────────┴──────────┴──────────┴──────────┴─────────────┘
```

**Benefits:**
- Independent deployment of modules
- Clear ownership boundaries
- Shared infrastructure reduces duplication
- Easier testing and maintenance

**Implementation:**
- Frontend: Module-based routing (`/workspace/frontend/src/modules/`)
- Backend: Domain-specific models (`/workspace/ERP-BACKEND/app/models/`)

### 1.2 Repository Pattern

**Purpose:** Abstract data access logic from business logic

**Structure:**
```typescript
interface IRepository<T> {
  findById(id: string): Promise<T | null>;
  findAll(): Promise<T[]>;
  create(data: CreateDto): Promise<T>;
  update(id: string, data: UpdateDto): Promise<T>;
  delete(id: string): Promise<void>;
}
```

**Benefits:**
- Decouples business logic from data access
- Easy to swap implementations (e.g., SQL → NoSQL)
- Simplifies testing with mock repositories

### 1.3 Service Layer Pattern

**Purpose:** Encapsulate business logic

**Structure:**
```python
# Backend example
class OrderService:
    def __init__(self, order_repo: OrderRepository, inventory_repo: InventoryRepository):
        self.order_repo = order_repo
        self.inventory_repo = inventory_repo
    
    def create_order(self, user_id: str, items: List[OrderItem]) -> Order:
        # Business logic here
        pass
```

**Benefits:**
- Centralizes business rules
- Transaction management
- Cross-cutting concerns (logging, validation)

---

## Design Patterns

### 2.1 Factory Pattern

**Usage:** API Client Creation

**Implementation:**
```typescript
// frontend/src/shared/services/apiClient.ts
export const createApiClient = (baseURL: string, getAuthToken: () => string | null) => {
  // Configuration and interceptor setup
  return apiInstance;
};

// Usage in modules
export const ecommerceApi = createApiClient(
  '/api/ecommerce',
  () => localStorage.getItem('token')
);
```

**Benefits:**
- Consistent API client configuration
- Centralized error handling
- Easy to modify interceptors globally

### 2.2 Singleton Pattern

**Usage:** Store instances, configuration objects

**Implementation:**
```typescript
// Zustand stores are singletons by default
export const useEcommerceStore = create<EcommerceState>()(
  persist(
    (...args) => ({
      ...commonSlice(...args),
      // module-specific state
    }),
    { name: 'ecommerce-storage' }
  )
);
```

### 2.3 Observer Pattern

**Usage:** State management with Zustand, event emitters

**Implementation:**
```typescript
// Automatic re-render on state change
const cartItems = useEcommerceStore(state => state.cartItems);
const addItem = useEcommerceStore(state => state.addItem);

// Component automatically updates when cartItems changes
```

### 2.4 Strategy Pattern

**Usage:** Different calculation strategies, payment methods

**Implementation:**
```typescript
interface DiscountStrategy {
  calculate(originalPrice: number): number;
}

class PercentageDiscount implements DiscountStrategy {
  constructor(private percentage: number) {}
  calculate(price: number) { return price * (this.percentage / 100); }
}

class FixedDiscount implements DiscountStrategy {
  constructor(private amount: number) {}
  calculate(price: number) { return this.amount; }
}
```

### 2.5 Decorator Pattern

**Usage:** Adding behavior to functions (debounce, throttle, logging)

**Implementation:**
```typescript
// frontend/src/shared/utils/helpers.ts
const debouncedSearch = debounce(searchFunction, 300);
const throttledScroll = throttle(handleScroll, 100);
```

### 2.6 Composite Pattern

**Usage:** Tree structures (org charts, product categories)

**Implementation:**
```typescript
interface TreeNode {
  id: string;
  name: string;
  children?: TreeNode[];
}

// Treat individual nodes and compositions uniformly
```

### 2.7 Command Pattern

**Usage:** Undo/redo operations, action queues

**Implementation:**
```typescript
interface Command {
  execute(): void;
  undo(): void;
}

class AddToCartCommand implements Command {
  constructor(private item: CartItem, private cart: Cart) {}
  execute() { this.cart.add(this.item); }
  undo() { this.cart.remove(this.item.id); }
}
```

---

## Frontend Patterns

### 3.1 Container/Presentational Pattern

**Purpose:** Separate logic from UI

**Structure:**
```typescript
// Container (logic)
const ProductListContainer = () => {
  const products = useProducts();
  const loading = useLoading();
  
  return <ProductList products={products} loading={loading} />;
};

// Presentational (UI only)
const ProductList = ({ products, loading }) => {
  if (loading) return <Spinner />;
  return <div>{products.map(p => <ProductCard key={p.id} {...p} />)}</div>;
};
```

### 3.2 Custom Hooks Pattern

**Purpose:** Reusable stateful logic

**Implementation:**
```typescript
// frontend/src/shared/hooks/useCommon.ts
export const useApi = <T>(fetcher: () => Promise<T>) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  useEffect(() => {
    fetcher()
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);
  
  return { data, loading, error };
};
```

**Benefits:**
- Logic reuse across components
- Easier testing
- Cleaner component code

### 3.3 Selector Pattern

**Purpose:** Optimized state selection

**Implementation:**
```typescript
// frontend/src/shared/utils/storeHelpers.ts
export const createSelector = <T, U>(
  selector: (state: T) => U,
  equalityFn: (a: U, b: U) => boolean = shallowEqual
): ((state: T) => U) => {
  return selector;
};

// Usage with shallow comparison to prevent unnecessary re-renders
const cartTotal = useEcommerceStore(
  createSelector(state => state.cartTotal, shallowEqual)
);
```

### 3.4 Higher-Order Component (HOC)

**Purpose:** Add functionality to components

**Implementation:**
```typescript
const withAuth = (WrappedComponent) => {
  return function AuthenticatedComponent(props) {
    const isAuthenticated = useAuth();
    
    if (!isAuthenticated) return <LoginRedirect />;
    return <WrappedComponent {...props} />;
  };
};
```

### 3.5 Render Props Pattern

**Purpose:** Share code between components using props

**Implementation:**
```typescript
<DataFetcher url="/api/products">
  {(data, loading, error) => {
    if (loading) return <Spinner />;
    if (error) return <Error message={error} />;
    return <ProductList products={data} />;
  }}
</DataFetcher>
```

---

## Backend Patterns

### 4.1 Mixin Pattern

**Purpose:** Reusable model attributes

**Implementation:**
```python
# ERP-BACKEND/app/models/base.py
class TimestampMixin:
    """Adds created_at and updated_at fields"""
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SoftDeleteMixin:
    """Adds is_deleted flag for soft deletes"""
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

# Usage in models
class Product(BaseModel, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"
    # Additional fields...
```

**Benefits:**
- DRY principle for common fields
- Consistent audit trails
- Easy to add/remove features

### 4.2 Dependency Injection

**Purpose:** Manage service dependencies

**Implementation:**
```python
# FastAPI dependency injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return auth.get_user(token, db)

@app.get("/orders")
def list_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # current_user and db are injected
    pass
```

### 4.3 Middleware Pattern

**Purpose:** Cross-cutting concerns (logging, auth, CORS)

**Implementation:**
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url} - {process_time}s")
    return response
```

### 4.4 Event-Driven Architecture

**Purpose:** Decoupled communication between services

**Implementation:**
```python
# Event publisher
class EventPublisher:
    def publish(self, event_type: str, payload: dict):
        # Publish to message queue
        pass

# Event consumer
@event_handler("order.created")
def send_confirmation_email(payload: dict):
    # Send email
    pass
```

### 4.5 CQRS (Command Query Responsibility Segregation)

**Purpose:** Separate read and write operations

**Structure:**
```
Commands (Write)          Queries (Read)
     ↓                         ↓
  Command Handler         Query Handler
     ↓                         ↓
  Write Database          Read Database (Replica)
```

**Benefits:**
- Optimized read/write performance
- Independent scaling
- Clear separation of concerns

---

## System Alignment

### 5.1 Naming Conventions

#### TypeScript/Frontend
```typescript
// Files: camelCase.ts
helpers.ts, storeHelpers.ts, apiClient.ts

// Classes: PascalCase
class ShoppingCart { }

// Functions/Variables: camelCase
const calculateTotal = () => { }
let itemCount = 0

// Constants: UPPER_SNAKE_CASE
const MAX_RETRY_COUNT = 3

// Types/Interfaces: PascalCase
interface UserProfile { }
type OrderStatus = 'pending' | 'completed'

// React Components: PascalCase
const ProductCard = () => { }
```

#### Python/Backend
```python
# Files: snake_case.py
models.py, services.py, utils.py

# Classes: PascalCase
class OrderService:

# Functions/Variables: snake_case
def calculate_total():
    item_count = 0

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3

# Private members: _prefix
_internal_cache = {}
```

### 5.2 Error Handling Strategy

#### Frontend
```typescript
// Standardized error structure
interface ApiError {
  status: number;
  message: string;
  code: string;
  details?: any;
}

// Consistent handling
try {
  const result = await api.post('/orders', data);
} catch (error) {
  if (error.status === 401) {
    // Redirect to login
  } else if (error.status === 400) {
    // Show validation errors
  } else {
    // Show generic error
  }
}
```

#### Backend
```python
# Custom exception hierarchy
class AppException(Exception):
    def __init__(self, message: str, code: str, status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code

class ValidationException(AppException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", 400)
        self.details = details

# Exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": exc.message}
    )
```

### 5.3 Logging Strategy

#### Levels
- **ERROR**: System failures, exceptions
- **WARN**: Recoverable issues, deprecated usage
- **INFO**: Business events (user actions, transactions)
- **DEBUG**: Detailed technical information

#### Format
```json
{
  "timestamp": "2026-08-17T15:30:00Z",
  "level": "INFO",
  "service": "order-service",
  "traceId": "abc123",
  "userId": "user_456",
  "action": "order.created",
  "data": { "orderId": "ord_789" }
}
```

### 5.4 Configuration Management

#### Environment Variables
```bash
# .env.example
NODE_ENV=development
API_BASE_URL=http://localhost:8000
LOG_LEVEL=debug

# Backend
DATABASE_URL=postgresql://user:pass@localhost/db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
```

#### Runtime Configuration
```typescript
// config.ts
const config = {
  development: {
    apiUrl: 'http://localhost:8000',
    logLevel: 'debug',
  },
  production: {
    apiUrl: process.env.API_BASE_URL,
    logLevel: 'warn',
  },
};

export default config[process.env.NODE_ENV];
```

---

## Code Organization

### 6.1 Frontend Structure

```
frontend/src/
├── modules/
│   ├── ecommerce/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── store.ts
│   │   └── api.ts
│   ├── mrp/
│   ├── pos/
│   └── bi-dashboard/
├── shared/
│   ├── components/      # Reusable UI components
│   ├── hooks/           # Custom hooks
│   ├── services/        # API clients
│   ├── utils/           # Utility functions
│   └── index.ts         # Exports
├── types/               # Global type definitions
└── App.tsx
```

### 6.2 Backend Structure

```
ERP-BACKEND/app/
├── models/
│   ├── base.py          # Mixins
│   ├── user.py          # User model
│   ├── crm.py           # CRM models
│   ├── hr.py            # HR models
│   ├── inventory.py     # Inventory models
│   ├── finance.py       # Finance models
│   ├── projects.py      # Project models
│   └── __init__.py      # Exports
├── routers/
│   ├── users.py
│   ├── orders.py
│   └── ...
├── services/
│   ├── auth.py
│   └── ...
├── core/
│   ├── config.py
│   └── security.py
└── main.py
```

### 6.3 Documentation Structure

```
docs/
├── ARCHITECTURE_DECISIONS.md
├── FORMULAS_ALGORITHMS.md      # Mathematical formulas
├── PATTERNS_SYSTEM_ALIGNMENT.md # This file
├── API_SUMMARY.md
├── TESTING.md
└── architecture/
    └── BOUNDARIES.md
```

---

## Best Practices Checklist

### Code Quality
- [ ] Follow established naming conventions
- [ ] Use TypeScript strict mode
- [ ] Implement proper error handling
- [ ] Add unit tests for critical logic
- [ ] Document public APIs

### Performance
- [ ] Memoize expensive calculations
- [ ] Implement pagination for large datasets
- [ ] Use lazy loading for heavy components
- [ ] Optimize database queries (N+1 prevention)
- [ ] Cache frequently accessed data

### Security
- [ ] Validate all user inputs
- [ ] Use parameterized queries
- [ ] Implement rate limiting
- [ ] Sanitize outputs (XSS prevention)
- [ ] Use HTTPS in production

### Maintainability
- [ ] Keep functions small (<50 lines)
- [ ] Single responsibility principle
- [ ] DRY (Don't Repeat Yourself)
- [ ] Meaningful variable/function names
- [ ] Regular refactoring

---

## Related Documentation

- [Formulas & Algorithms](./FORMULAS_ALGORITHMS.md)
- [Architecture Decisions](./ARCHITECTURE_DECISIONS.md)
- [API Summary](./API_SUMMARY.md)
- [Testing Strategy](./TESTING.md)

---

**Last Updated:** 2026-08-17  
**Version:** 1.0  
**Maintained By:** Development Team
