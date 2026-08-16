# Issue #56: Transaction/Rollback Tests

**Status:** 🚧 Ready for Implementation
**Priority:** 🔴 High (M1 Blocking)
**Milestone:** M1 - ERP Core Stabilization
**Module:** ERP-BACKEND
**Owner:** Backend Team

## Overview

Implement comprehensive transaction and rollback tests to ensure database integrity when operations fail, preventing partial state corruption in the ERP system.

## Business Value

- Guarantees data consistency across all ERP modules
- Prevents orphaned records and referential integrity violations
- Ensures failed operations leave no trace in the database
- Critical for financial and inventory accuracy
- Required for M1 exit gate qualification

## Requirements

### Transaction Scenarios to Test

1. **Multi-Entity Transactions**
   - Company + Contact creation (both succeed or both fail)
   - Deal + Contact association
   - Invoice + Invoice Items creation
   - Order + Order Items + Stock Movement
   - Project + Task creation

2. **Failure Injection Tests**
   - Database constraint violations (unique, foreign key, check)
   - Application-level validation failures mid-transaction
   - External service timeouts during transaction
   - Deadlock scenarios
   - Connection loss during commit

3. **Rollback Verification**
   - Verify no partial writes on exception
   - Verify sequence counters are not leaked
   - Verify triggers fire correctly on rollback
   - Verify audit logs record rollback events

4. **Isolation Level Tests**
   - Read committed behavior verification
   - Dirty read prevention
   - Non-repeatable read handling
   - Phantom read scenarios

### Modules Requiring Transaction Tests

- **CRM**: Company/Contact/Deal relationships
- **Finance**: Invoice/Payment/Account transactions
- **Inventory**: Product/StockMovement/Warehouse operations
- **HR**: Employee/Department/Payroll operations
- **Projects**: Project/Task/Assignment operations
- **Workflows**: WorkflowExecution/WorkflowStep transitions

## Technical Constraints

- Must use PostgreSQL transaction semantics
- Tests must be independent and idempotent
- No test may leave database in modified state
- Must work with Alembic migrations

## Acceptance Criteria

- [ ] All critical multi-entity operations have transaction tests
- [ ] Rollback behavior verified for all failure modes
- [ ] No orphaned records after failed transactions
- [ ] Audit trail correctly records rollback events
- [ ] Tests pass consistently (zero flakiness)
- [ ] Documentation of transaction boundaries in code

## Implementation Plan

### Phase 1: Test Infrastructure (Day 1)
1. Create transaction test fixtures
2. Implement rollback verification helpers
3. Set up database state inspection utilities

### Phase 2: CRM & Finance Transactions (Day 2-3)
1. Company+Contact atomic creation tests
2. Deal lifecycle transaction tests
3. Invoice+Items atomic creation tests
4. Payment recording transaction tests

### Phase 3: Inventory & HR Transactions (Day 4-5)
1. Product creation with stock initialisation
2. Stock movement atomic operations
3. Employee creation with department assignment
4. Payroll processing transactions

### Phase 4: Projects & Workflows (Day 6-7)
1. Project+Task atomic creation
2. Workflow execution state transitions
3. Multi-step workflow rollback scenarios

### Phase 5: Failure Injection (Day 8-9)
1. Constraint violation tests
2. Timeout/deadlock simulation
3. Connection failure scenarios

### Phase 6: Documentation & Cleanup (Day 10)
1. Document transaction boundaries
2. Add code comments for complex transactions
3. Update operational runbooks

## Dependencies

- Issue #55: API Contract Tests (for request-level testing)

## Related Issues

- #55: API Contract Tests for Critical Write Paths
- #57: Database Readiness Checks
- #58: API Error Handling Standardization
- #59: Audit Log Completeness Verification

## Definition of Done

- [x] Code is in the correct ownership boundary (ERP-BACKEND/tests/)
- [ ] Tests cover changed behavior
- [ ] No secret or production data is committed
- [ ] Migrations are reproducible
- [ ] Transaction boundaries are documented
- [ ] Rollback behavior is defined and tested
- [ ] CI/security checks pass
- [ ] Operational documentation is updated
- [ ] Acceptance evidence exists

---
*Created: 2026-08-16 | Last Updated: 2026-08-16*
