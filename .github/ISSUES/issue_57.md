# Issue #57: Database Readiness Checks

**Status:** 🚧 Ready for Implementation
**Priority:** 🔴 High (M1 Blocking)
**Milestone:** M1 - ERP Core Stabilization
**Module:** ERP-BACKEND / INFRASTRUCTURE
**Owner:** Backend Team

## Overview

Implement comprehensive database readiness checks to verify migration reproducibility, connection health, and schema integrity before the ERP system accepts traffic.

## Business Value

- Prevents deployment of broken database schemas
- Ensures clean install and upgrade paths
- Reduces downtime during migrations
- Provides early warning of database issues
- Required for M1 exit gate qualification

## Requirements

### Health Check Endpoints

1. **Basic Connectivity Check** (`GET /health/db`)
   - Verify database connection pool is available
   - Response time < 100ms
   - Return connection pool statistics

2. **Migration Status Check** (`GET /health/migrations`)
   - Verify all migrations are applied
   - Detect pending migrations
   - Detect migration conflicts
   - Return current revision and head revision

3. **Schema Integrity Check** (`GET /health/schema`)
   - Verify all expected tables exist
   - Verify critical indexes exist
   - Check for orphaned records
   - Validate foreign key constraints

4. **Deep Health Check** (`GET /health/db/deep`)
   - Execute test query on each major table
   - Verify read/write permissions
   - Check disk space availability
   - Validate sequence counters

### Migration Reproducibility

1. **Clean Install Test**
   - Drop all tables
   - Run all migrations from scratch
   - Verify final schema matches expected state
   - Seed initial data successfully

2. **Upgrade Path Test**
   - Start from previous release schema
   - Apply incremental migrations
   - Verify data preservation
   - Verify no data loss or corruption

3. **Rollback Test**
   - Apply migration
   - Rollback migration
   - Verify schema returns to previous state
   - Verify data integrity maintained

### Monitoring & Alerting

1. **Metrics to Expose**
   - Connection pool utilization
   - Query execution times (p50, p95, p99)
   - Transaction rate
   - Deadlock count
   - Lock wait times

2. **Alert Conditions**
   - Connection pool exhaustion
   - Migration failures
   - Schema drift detected
   - Long-running queries (> 30s)
   - Deadlock frequency spike

## Technical Constraints

- Must work with PostgreSQL 14+
- Must integrate with Alembic migration system
- Health checks must be lightweight (< 1s)
- Must not expose sensitive information
- Must work in Kubernetes environment

## Acceptance Criteria

- [ ] All health check endpoints implemented
- [ ] Clean install migration verified
- [ ] Upgrade path from v0.x to v1.0 verified
- [ ] Rollback procedure documented and tested
- [ ] Kubernetes readiness/liveness probes configured
- [ ] Monitoring metrics exposed via Prometheus
- [ ] Operational runbook updated

## Implementation Plan

### Phase 1: Health Check Endpoints (Day 1-2)
1. Implement `/health/db` endpoint
2. Implement `/health/migrations` endpoint
3. Implement `/health/schema` endpoint
4. Add authentication for deep health checks

### Phase 2: Migration Testing Framework (Day 3-5)
1. Create clean install test script
2. Create upgrade path test script
3. Create rollback test script
4. Integrate with CI pipeline

### Phase 3: Monitoring Integration (Day 6-7)
1. Add Prometheus metrics exporters
2. Configure Grafana dashboards
3. Set up alert rules
4. Test alert notifications

### Phase 4: Kubernetes Integration (Day 8)
1. Configure readiness probe
2. Configure liveness probe
3. Configure startup probe for migrations
4. Test pod lifecycle

### Phase 5: Documentation & Runbooks (Day 9-10)
1. Document health check endpoints
2. Create migration troubleshooting guide
3. Update deployment runbook
4. Train operations team

## Dependencies

- None (foundational for M1)

## Related Issues

- #55: API Contract Tests for Critical Write Paths
- #56: Transaction/Rollback Tests
- #58: API Error Handling Standardization
- #59: Audit Log Completeness Verification

## Definition of Done

- [x] Code is in the correct ownership boundary (ERP-BACKEND/app/routers/, infra/)
- [ ] Tests cover changed behavior
- [ ] No secret or production data is committed
- [ ] Migrations are reproducible
- [ ] Health check API contracts are documented
- [ ] Failure and rollback behavior are defined
- [ ] CI/security checks pass
- [ ] Operational documentation is updated
- [ ] Acceptance evidence exists

---
*Created: 2026-08-16 | Last Updated: 2026-08-16*
