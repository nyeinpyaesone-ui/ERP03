# Architecture Decision Records (ADR)

## ADR-001: FastAPI for Backend API
**Status:** Accepted
**Date:** 2026-06-19

### Context
Need a high-performance, modern Python API framework with automatic OpenAPI documentation.

### Decision
Use FastAPI with SQLAlchemy and Pydantic.

### Consequences
- ✅ Automatic API docs (Swagger/ReDoc)
- ✅ Type validation with Pydantic
- ✅ Async support for high performance
- ⚠️ Learning curve for team members

## ADR-002: React + TypeScript for Frontend
**Status:** Accepted
**Date:** 2026-06-19

### Context
Need a modern, type-safe frontend with component reusability.

### Decision
Use React 18 with TypeScript, Vite, and Tailwind CSS.

### Consequences
- ✅ Type safety reduces runtime errors
- ✅ Component reusability across modules
- ✅ Fast development with Vite HMR
- ⚠️ Build complexity for mobile webview

## ADR-003: React Native + Expo for Mobile
**Status:** Accepted
**Date:** 2026-06-19

### Context
Need cross-platform mobile app with rapid development.

### Decision
Use React Native with Expo for iOS and Android.

### Consequences
- ✅ Single codebase for both platforms
- ✅ Over-the-air updates with Expo
- ✅ Easy testing with Expo Go app
- ⚠️ Performance vs native development

## ADR-004: PostgreSQL + Redis
**Status:** Accepted
**Date:** 2026-06-19

### Context
Need reliable relational database with caching layer.

### Decision
Use PostgreSQL 15 for primary data, Redis 7 for caching and sessions.

### Consequences
- ✅ ACID compliance for financial data
- ✅ JSON support for flexible schemas
- ✅ Fast caching with Redis
- ⚠️ Operational complexity of two databases

## ADR-005: Kubernetes for Orchestration
**Status:** Accepted
**Date:** 2026-06-19

### Context
Need scalable, production-grade container orchestration.

### Decision
Use Kubernetes with Helm charts for deployment.

### Consequences
- ✅ Auto-scaling and self-healing
- ✅ Rolling updates with zero downtime
- ✅ Resource optimization
- ⚠️ Steep learning curve
