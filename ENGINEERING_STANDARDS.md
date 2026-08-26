# 🏗️ ERP03 Engineering Standards & Technical Stack

## **Executive Summary**
This document defines the professional engineering standards, approved technical stacks, tooling policies, and design patterns for ERP03 - an enterprise-grade, production-ready ERP system. All development must align with these standards to ensure maintainability, scalability, security, and operational excellence.

---

## **1. Approved Technical Stack**

### **1.1 Backend Services**

#### **ERP-BACKEND (Transactional Core)**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Runtime** | Python | 3.11+ | Core language |
| **Web Framework** | FastAPI | 0.104+ | High-performance async API |
| **ORM** | SQLAlchemy 2.0 | 2.0+ | Type-safe database access |
| **Migrations** | Alembic | 1.12+ | Schema version control |
| **Validation** | Pydantic v2 | 2.5+ | Data validation & serialization |
| **Auth** | PyJWT + passlib | Latest | JWT tokens, bcrypt hashing |
| **Task Queue** | Celery + Redis | 5.3+ | Background job processing |
| **Testing** | pytest + httpx | 7.4+ | Unit & integration tests |
| **Linting** | ruff + mypy | Latest | Code quality & type checking |

#### **AI-BACKEND (Intelligence Layer)**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Runtime** | Python | 3.11+ | Core language |
| **Framework** | FastAPI | 0.104+ | Agent API endpoints |
| **ML Orchestration** | LangChain | 0.1+ | LLM agent workflows |
| **Vector DB** | pgvector | 0.5+ | Semantic search (PostgreSQL extension) |
| **Embeddings** | sentence-transformers | 2.2+ | Text vectorization |
| **Isolation** | Separate DB | N/A | No direct ERP DB access |

### **1.2 Frontend Applications**

#### **Core Platform (React Native Web/Mobile)**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Runtime** | TypeScript | 5.3+ | Type-safe JavaScript |
| **Framework** | React Native | 0.73+ | Cross-platform UI |
| **State Management** | Zustand | 4.4+ | Lightweight store factory |
| **Data Fetching** | TanStack Query v5 | 5.17+ | Server state caching |
| **HTTP Client** | Axios | 1.6+ | API communication |
| **Navigation** | React Navigation | 6.5+ | Screen routing |
| **Forms** | React Hook Form | 7.49+ | Performant form handling |
| **Validation** | Zod | 3.22+ | Runtime type validation |
| **Styling** | Tailwind RN | 0.4+ | Utility-first styling |
| **Testing** | Jest + RTL | 29.7+ | Unit & component tests |
| **E2E Testing** | Detox | 20.16+ | End-to-end mobile tests |
| **Linting** | ESLint + Prettier | 8.56+ | Code quality & formatting |

### **1.3 Infrastructure & DevOps**

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Containerization** | Docker | 24.0+ | Application packaging |
| **Orchestration** | Docker Compose | 2.23+ | Multi-service deployment |
| **Database** | PostgreSQL | 16.1+ | Primary data store |
| **Cache** | Redis | 7.2+ | Session/cache layer |
| **Reverse Proxy** | Traefik | 2.10+ | Load balancing & SSL |
| **CI/CD** | GitHub Actions | Latest | Automated pipelines |
| **Monitoring** | Prometheus + Grafana | 2.48+/10.2+ | Metrics & dashboards |
| **Logging** | Loki + Promtail | 2.9+ | Log aggregation |
| **Tracing** | Jaeger | 1.51+ | Distributed tracing |
| **Secrets** | Doppler / Vault | Latest | Secret management |

---

## **2. Architectural Principles**

### **2.1 Module Boundaries (M0 Compliance)**
```
┌─────────────────────────────────────────────────────────────┐
│                     ERP03 Architecture                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   MRP        │    │  E-commerce  │    │     POS      │  │
│  │   Module     │    │    Module    │    │    Module    │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │          │
│         └───────────────────┼───────────────────┘          │
│                             │                              │
│                  ┌──────────▼──────────┐                   │
│                  │   Core Module       │                   │
│                  │  (Shared Services)  │                   │
│                  └──────────┬──────────┘                   │
│                             │                              │
│  ┌──────────────┐    ┌──────▼───────┐    ┌──────────────┐  │
│  │   BI         │    │  API Client  │    │   Auth       │  │
│  │   Dashboard  │    │   Factory    │    │   Service    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │              INTEGRATION LAYER (Contracts)            │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐                      ┌──────────────┐    │
│  │  ERP-BACKEND │                      │  AI-BACKEND  │    │
│  │  (FastAPI)   │                      │  (Agents)    │    │
│  │  ┌────────┐  │                      │  ┌────────┐  │    │
│  │  │Postgres│  │◄──── NO DIRECT ────►│  │Postgres│  │    │
│  │  │  DB    │  │     ACCESS           │  │  DB    │  │    │
│  │  └────────┘  │                      │  └────────┘  │    │
│  └──────────────┘                      └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Rules:**
- ✅ AI-BACKEND communicates with ERP-BACKEND ONLY via INTEGRATION layer contracts
- ✅ Frontend modules access backend ONLY through Core API Client
- ✅ No cross-module imports between MRP, E-commerce, POS, BI
- ✅ Shared logic MUST reside in `/core/` module

### **2.2 Backend Design Patterns**

#### **Repository Pattern**
```python
# ✅ CORRECT: Repository abstraction
class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def get_by_id(self, id: UUID) -> T | None:
        result = await self.session.get(self.model, id)
        return result

class WorkOrderRepository(BaseRepository[WorkOrder]):
    async def get_active_orders(self, facility_id: UUID) -> list[WorkOrder]:
        stmt = select(WorkOrder).where(
            WorkOrder.facility_id == facility_id,
            WorkOrder.status == "active"
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
```

#### **Service Layer Pattern**
```python
# ✅ CORRECT: Business logic in service layer
class WorkOrderService:
    def __init__(self, repo: WorkOrderRepository, event_bus: EventBus):
        self.repo = repo
        self.event_bus = event_bus
    
    async def create_order(self, data: WorkOrderCreateDTO) -> WorkOrder:
        # Validation
        await self._validate_materials(data.materials)
        
        # Transaction
        async with self.repo.session.begin():
            order = await self.repo.create(data)
            await self.event_bus.publish("work_order.created", order)
        
        return order
```

#### **Dependency Injection**
```python
# ✅ CORRECT: Explicit dependencies
def get_work_order_service() -> WorkOrderService:
    repo = WorkOrderRepository(WorkOrder, get_db_session())
    event_bus = get_event_bus()
    return WorkOrderService(repo, event_bus)

# Router usage
@router.post("/work-orders")
async def create_work_order(
    data: WorkOrderCreateDTO,
    service: WorkOrderService = Depends(get_work_order_service)
):
    order = await service.create_order(data)
    return order
```

### **2.3 Frontend Design Patterns**

#### **Hook Factory Pattern**
```typescript
// ✅ CORRECT: Reusable hook factory
export function createQueryHooks<
  TEntity extends { id: string },
  TListParams extends Record<string, unknown>,
  TCreateDTO extends Record<string, unknown>,
  TUpdateDTO extends Record<string, unknown>
>(
  entityName: string,
  apiService: ApiService<TEntity, TListParams, TCreateDTO, TUpdateDTO>
) {
  const queryKeys = {
    all: [entityName] as const,
    lists: () => [...queryKeys.all, 'list'] as const,
    list: (params: TListParams) => [...queryKeys.lists(), params] as const,
    detail: (id: string) => [...queryKeys.all, 'detail', id] as const,
  };

  return {
    useList: (params: TListParams) => 
      useQuery({
        queryKey: queryKeys.list(params),
        queryFn: () => apiService.getList(params),
        staleTime: 5 * 60 * 1000, // 5 minutes
        retry: 2,
      }),
    
    useDetail: (id: string) => 
      useQuery({
        queryKey: queryKeys.detail(id),
        queryFn: () => apiService.getById(id),
        staleTime: 2 * 60 * 1000,
        retry: 1,
      }),
    
    useCreate: () => 
      useMutation({
        mutationFn: (data: TCreateDTO) => apiService.create(data),
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: queryKeys.all });
        },
      }),
  };
}
```

#### **Store Factory Pattern**
```typescript
// ✅ CORRECT: Modular store with async tracking
type ActionStatus = 'idle' | 'loading' | 'success' | 'error';

interface EntityState<T> {
  items: T[];
  selectedId: string | null;
  status: ActionStatus;
  error: string | null;
}

export function createStore<T extends { id: string }>(
  name: string,
  initialState: EntityState<T>
) {
  return create<EntityState<T>>((set, get) => ({
    ...initialState,
    
    // Actions with status tracking
    fetchAll: async () => {
      set({ status: 'loading', error: null });
      try {
        const items = await api.getAll();
        set({ items, status: 'success' });
      } catch (error) {
        set({ status: 'error', error: error.message });
      }
    },
    
    // Typed selectors
    getSelected: () => {
      const { items, selectedId } = get();
      return items.find(item => item.id === selectedId) ?? null;
    },
  }));
}
```

---

## **3. Tooling & Development Workflow**

### **3.1 Allowed Tools by Category**

| Category | Approved Tools | Banned Tools | Notes |
|----------|---------------|--------------|-------|
| **Package Managers** | `pnpm`, `npm`, `pip`, `poetry` | `yarn` (v1) | pnpm preferred for monorepo |
| **Linters** | `ruff`, `ESLint`, `mypy`, `tsc --noEmit` | `tslint`, `flake8` | Modern, fast linters only |
| **Formatters** | `Prettier`, `ruff format`, `black` | `prettier-eslint` | Single formatter per language |
| **Testing** | `pytest`, `Jest`, `RTL`, `Detox` | `mocha`, `chai` | Unified testing stack |
| **Bundlers** | `Vite`, `Metro`, `esbuild` | `webpack` (legacy config) | Modern bundlers only |
| **DB Tools** | `alembic`, `psql`, `pgAdmin` | `sequelize-cli` | PostgreSQL-native tools |
| **Container Tools** | `docker`, `docker-compose`, `nerdctl` | `vagrant` | Container-first approach |
| **CI/CD** | `GitHub Actions`, `ArgoCD` | `Jenkins`, `Travis CI` | Cloud-native pipelines |
| **Monitoring** | `Prometheus`, `Grafana`, `Loki` | `Nagios`, `Zabbix` | Modern observability stack |
| **Secrets** | `Doppler`, `HashiCorp Vault` | `.env` files in prod | Never commit secrets |

### **3.2 Development Commands**

```bash
# Backend Development
cd ERP-BACKEND
poetry install                    # Install dependencies
poetry run ruff check .           # Lint
poetry run mypy .                 # Type check
poetry run pytest --cov=src       # Test with coverage
poetry run alembic upgrade head   # Apply migrations

# Frontend Development
cd frontend
pnpm install                      # Install dependencies
pnpm lint                         # ESLint + type check
pnpm test                         # Jest tests
pnpm build                        # Production build

# Infrastructure
docker-compose up -d              # Start all services
docker-compose logs -f backend    # Follow logs
docker-compose exec db psql -U erpuser -d erpdb  # DB access
```

### **3.3 Git Workflow**

```bash
# Branch naming
feature/<jira-id>-<description>    # e.g., feature/ERP-123-work-order-api
bugfix/<jira-id>-<description>     # e.g., bugfix/ERP-124-auth-token-refresh
hotfix/<critical-issue>            # e.g., hotfix/security-patch-jwt

# Commit message convention (Conventional Commits)
feat(api): add work order batch endpoint
fix(auth): resolve token refresh race condition
docs(readme): update installation instructions
test(e2e): add login flow test coverage
refactor(core): extract API client factory
chore(deps): upgrade React Native to 0.73

# PR Requirements
- [ ] All tests passing (CI green)
- [ ] Code coverage >80%
- [ ] Type checking passes (no errors)
- [ ] Linting passes (no warnings)
- [ ] Documentation updated
- [ ] Migration scripts included (if schema changed)
- [ ] Reviewed by 2 senior engineers
```

---

## **4. Quality Gates & Acceptance Criteria**

### **4.1 Code Quality Metrics**

| Metric | Threshold | Tool | Enforcement |
|--------|-----------|------|-------------|
| **Test Coverage** | >80% | pytest-cov, Jest | CI block if <75% |
| **Type Safety** | 0 errors | mypy, tsc | CI block on any error |
| **Lint Violations** | 0 errors | ruff, ESLint | CI block on any error |
| **Code Duplication** | <5% | radon, duplicator | Warning if >10% |
| **Cyclomatic Complexity** | <10 avg | xenon, complexity | Warning if >15 |
| **Bundle Size** | <500KB initial | webpack-bundle-analyzer | Warning if >1MB |
| **API Response Time** | <200ms p95 | k6, locust | Alert if >500ms |
| **Frontend Load Time** | <3s FCP | Lighthouse | Warning if >5s |

### **4.2 Security Requirements**

| Requirement | Implementation | Verification |
|-------------|----------------|--------------|
| **Authentication** | JWT with RS256, 15min expiry | Penetration test |
| **Authorization** | RBAC with policy enforcement | Audit log review |
| **Input Validation** | Pydantic/Zod schemas | Fuzz testing |
| **SQL Injection** | Parameterized queries (SQLAlchemy) | SAST scan |
| **XSS Prevention** | React escaping, CSP headers | DAST scan |
| **CSRF Protection** | SameSite cookies, CSRF tokens | OWASP ZAP scan |
| **Rate Limiting** | Redis-based sliding window | Load test |
| **Secrets Management** | Vault/Doppler, no .env in code | Secret scan (gitleaks) |
| **Dependency Scanning** | Dependabot, safety, npm audit | Weekly automated scan |

### **4.3 Performance Benchmarks**

| Scenario | Target | Measurement |
|----------|--------|-------------|
| **API Latency (p95)** | <200ms | k6 load test, 1000 RPS |
| **Database Query Time** | <50ms | pg_stat_statements |
| **Frontend FCP** | <1.5s | Lighthouse, throttled 4G |
| **Frontend TTI** | <3.5s | Lighthouse, mid-tier device |
| **WebSocket Latency** | <50ms | Custom benchmark |
| **Cache Hit Ratio** | >90% | Redis INFO stats |
| **Concurrent Users** | 10,000+ | Stress test |

---

## **5. Deployment & Operations Standards**

### **5.1 Environment Strategy**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Development│───►│     Staging │───►│  Production │    │   Disaster  │
│   (Local)   │    │   (QA/UAT)  │    │   (Live)    │    │  Recovery   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                  │                  │                  │
  docker-compose    docker-compose     Kubernetes/ECS       Separate
  Local DB          Replica DB         Primary DB           Region
  Mock services     Full staging       Production configs   Cold standby
```

### **5.2 Release Process**

```mermaid
graph LR
    A[Feature Complete] --> B[Code Review]
    B --> C[Merge to develop]
    C --> D[Deploy to Staging]
    D --> E[QA Testing]
    E --> F[UAT Sign-off]
    F --> G[Create Release Branch]
    G --> H[Security Scan]
    H --> I[Performance Test]
    I --> J[Deploy to Production]
    J --> K[Smoke Tests]
    K --> L[Monitor 24h]
    L --> M[Tag Release]
```

### **5.3 Rollback Procedures**

```bash
# Automatic rollback triggers
- Health check failure (3 consecutive)
- Error rate >5% for 5 minutes
- Latency p95 >1s for 10 minutes
- Database migration failure

# Manual rollback command
./scripts/rollback.sh --target <previous-version> --force

# Post-rollback checklist
- [ ] Verify database consistency
- [ ] Check error rates normalized
- [ ] Notify stakeholders
- [ ] Document incident
- [ ] Root cause analysis scheduled
```

---

## **6. Documentation Standards**

### **6.1 Required Documentation**

| Document | Owner | Update Frequency | Location |
|----------|-------|------------------|----------|
| **Architecture Decision Records (ADR)** | Tech Lead | Per major decision | `/docs/adr/` |
| **API Documentation** | Backend Team | Per release | OpenAPI (auto-generated) |
| **Runbooks** | DevOps | Quarterly | `/docs/runbooks/` |
| **Onboarding Guide** | Engineering Manager | Monthly | `/docs/onboarding.md` |
| **Incident Reports** | On-call Engineer | Per incident | `/docs/incidents/` |
| **Performance Benchmarks** | QA Team | Per release | `/docs/performance/` |

### **6.2 Code Documentation**

```python
# ✅ CORRECT: Docstring format (Google Style)
class WorkOrderService:
    """Service layer for work order business logic.
    
    Handles creation, updates, status transitions, and material
    allocation for manufacturing work orders.
    
    Attributes:
        repo: Repository for database operations
        event_bus: Event dispatcher for domain events
    
    Example:
        >>> service = WorkOrderService(repo, event_bus)
        >>> order = await service.create_order(data)
        >>> await service.allocate_materials(order.id, materials)
    """
    
    async def create_order(self, data: WorkOrderCreateDTO) -> WorkOrder:
        """Create a new work order with validation.
        
        Args:
            data: DTO containing work order details
            
        Returns:
            Created work order entity
            
        Raises:
            ValidationError: If materials are insufficient
            DuplicateError: If order number already exists
            
        Side Effects:
            - Publishes 'work_order.created' event
            - Reserves allocated materials
        """
```

```typescript
// ✅ CORRECT: TSDoc format
/**
 * Factory function to create standardized React Query hooks.
 * 
 * Generates type-safe query and mutation hooks for CRUD operations
 * with consistent caching strategies and error handling.
 * 
 * @template TEntity - Entity type with id property
 * @template TListParams - Parameters for list queries
 * @template TCreateDTO - Data transfer object for creation
 * @template TUpdateDTO - Data transfer object for updates
 * 
 * @param entityName - Entity name for query keys (e.g., 'work-orders')
 * @param apiService - API service instance with CRUD methods
 * 
 * @returns Object containing useList, useDetail, useCreate, useUpdate, useDelete hooks
 * 
 * @example
 * ```typescript
 * const workOrderHooks = createQueryHooks(
 *   'work-orders',
 *   workOrderApiService
 * );
 * 
 * const { useList, useCreate } = workOrderHooks;
 * const { data: orders } = useList({ status: 'active' });
 * const createMutation = useCreate();
 * ```
 */
export function createQueryHooks<...>() { ... }
```

---

## **7. Monitoring & Observability**

### **7.1 Required Metrics**

| Category | Metrics | Alert Threshold |
|----------|---------|-----------------|
| **Application** | Request rate, error rate, latency (p50/p95/p99) | Error rate >1%, latency p95 >500ms |
| **Database** | Connections, query time, lock waits, replication lag | Connections >80%, query time >100ms |
| **Cache** | Hit ratio, memory usage, evictions | Hit ratio <80%, memory >90% |
| **Queue** | Job count, processing time, failures | Failures >5%, queue depth >1000 |
| **Infrastructure** | CPU, memory, disk, network | CPU >80%, memory >85%, disk >90% |

### **7.2 Logging Standards**

```python
# ✅ CORRECT: Structured logging (JSON)
import structlog

logger = structlog.get_logger()

async def create_order(self, data: WorkOrderCreateDTO) -> WorkOrder:
    logger.info(
        "work_order_creation_started",
        user_id=data.user_id,
        facility_id=data.facility_id,
        order_type=data.order_type
    )
    
    try:
        order = await self._create_in_db(data)
        logger.info(
            "work_order_created",
            order_id=str(order.id),
            duration_ms=timer.elapsed_ms
        )
        return order
    except ValidationError as e:
        logger.warning(
            "work_order_validation_failed",
            error_code=e.code,
            field=e.field
        )
        raise
```

### **7.3 Tracing Requirements**

- All requests MUST include trace ID (W3C Trace Context)
- Span names MUST follow convention: `<operation>.<resource>` (e.g., `db.query.work_orders`)
- Spans MUST include: HTTP method, status code, user ID (sanitized), duration
- Critical paths MUST be traced: API → Service → Repository → DB

---

## **8. Compliance & Audit**

### **8.1 Data Retention**

| Data Type | Retention Period | Storage | Deletion Method |
|-----------|------------------|---------|-----------------|
| **Audit Logs** | 7 years | Encrypted S3 | Immutable bucket |
| **User Activity** | 2 years | PostgreSQL | Soft delete + archive |
| **Transaction Records** | 10 years | PostgreSQL + S3 | Legal hold capable |
| **Session Data** | 30 days | Redis | TTL expiration |
| **Debug Logs** | 7 days | Loki | Automatic rotation |

### **8.2 Access Control**

- **Principle of Least Privilege**: Minimum permissions required
- **Separation of Duties**: Developers cannot deploy to production alone
- **Audit Trail**: All privileged actions logged with user identity
- **Regular Reviews**: Access rights reviewed quarterly

---

## **9. Continuous Improvement**

### **9.1 Technical Debt Management**

- Track debt in Jira with `tech-debt` label
- Allocate 20% of sprint capacity to debt reduction
- Quarterly architecture review to identify systemic issues
- Maintain debt register with priority scores

### **9.2 Innovation Time**

- Engineers spend 10% time on exploration/improvement
- Monthly tech talks to share learnings
- Proof-of-concept projects encouraged
- Conference attendance budget per engineer

---

## **10. Contact & Governance**

### **10.1 Standards Committee**

- **Chair**: Chief Technology Officer
- **Members**: Tech Leads from Backend, Frontend, DevOps, Security
- **Meeting Cadence**: Bi-weekly
- **Responsibilities**:
  - Review and update standards quarterly
  - Approve exceptions to standards
  - Evaluate new tools/technologies
  - Resolve architectural disputes

### **10.2 Exception Process**

1. Submit exception request via RFC template
2. Present case to Standards Committee
3. Committee votes within 5 business days
4. Approved exceptions documented in ADR
5. Exceptions reviewed after 6 months

---

## **Appendix A: Quick Reference**

### **Do's**
✅ Use factory patterns for hooks and stores  
✅ Implement repository pattern for database access  
✅ Write comprehensive tests (>80% coverage)  
✅ Use structured logging with correlation IDs  
✅ Validate all inputs with Pydantic/Zod  
✅ Handle errors gracefully with proper status codes  
✅ Document public APIs with OpenAPI/TSDoc  
✅ Use dependency injection for testability  

### **Don'ts**
❌ Use `any` type in TypeScript  
❌ Hardcode credentials or secrets  
❌ Skip error handling in async operations  
❌ Write business logic in controllers/routers  
❌ Directly import between feature modules  
❌ Commit `.env` files or secrets to git  
❌ Ignore failing tests or lint errors  
❌ Deploy without health checks  

---

**Version**: 1.0  
**Last Updated**: 2024  
**Approved By**: ERP03 Standards Committee  
**Next Review**: Q2 2024
