# Issue #58: API Error Handling Standardization

**Status:** 🚧 Ready for Implementation
**Priority:** 🔴 High (M1 Blocking)
**Milestone:** M1 - ERP Core Stabilization
**Module:** ERP-BACKEND
**Owner:** Backend Team

## Overview

Standardize error handling across all ERP API endpoints to ensure consistent error responses, proper HTTP status codes, and actionable error messages for clients.

## Business Value

- Improves client integration experience
- Enables automated error handling in frontend/AI systems
- Reduces debugging time with structured error information
- Provides clear audit trail for failures
- Required for M1 exit gate qualification

## Requirements

### Error Response Schema

All API errors must follow this standard format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {},
    "correlation_id": "req_abc123",
    "timestamp": "2026-08-16T10:30:00Z",
    "path": "/api/v1/companies"
  }
}
```

### Error Code Taxonomy

| Category | Codes | HTTP Status |
|----------|-------|-------------|
| Authentication | `AUTH_REQUIRED`, `AUTH_INVALID`, `AUTH_EXPIRED` | 401 |
| Authorization | `FORBIDDEN`, `ROLE_INSUFFICIENT` | 403 |
| Validation | `VALIDATION_ERROR`, `REQUIRED_FIELD`, `INVALID_FORMAT` | 400 |
| Not Found | `NOT_FOUND`, `RESOURCE_MISSING` | 404 |
| Conflict | `CONFLICT`, `DUPLICATE_KEY`, `CONSTRAINT_VIOLATION` | 409 |
| Rate Limit | `RATE_LIMITED`, `QUOTA_EXCEEDED` | 429 |
| Server Error | `INTERNAL_ERROR`, `SERVICE_UNAVAILABLE`, `TIMEOUT` | 500, 503 |

### Error Handling Patterns

1. **Validation Errors**
   - Return field-level error details
   - Include expected format/constraints
   - Example: `{"field": "email", "error": "invalid_format", "expected": "RFC 5322"}`

2. **Database Errors**
   - Never expose raw SQL errors
   - Map to appropriate business error codes
   - Log full details server-side

3. **External Service Errors**
   - Include service name in error
   - Distinguish timeout vs. failure
   - Provide retry guidance

4. **Transaction Errors**
   - Indicate rollback occurred
   - Preserve original request data for retry

### Middleware Requirements

1. **Exception Handler Middleware**
   - Catch all unhandled exceptions
   - Log with correlation ID
   - Return standardized error response
   - Mask sensitive information

2. **Request Logging Middleware**
   - Generate correlation ID per request
   - Log request/response metadata
   - Track response times

3. **Validation Error Formatter**
   - Convert Pydantic validation errors
   - Format as field-level errors
   - Include constraint information

## Technical Constraints

- Must be backward compatible where possible
- Error responses must not leak sensitive data
- Correlation IDs must propagate through all services
- Must integrate with existing logging infrastructure

## Acceptance Criteria

- [ ] All routers use standardized error handler
- [ ] Error response schema documented in OpenAPI
- [ ] Correlation IDs present in all responses
- [ ] No raw exceptions exposed to clients
- [ ] Error codes documented for all endpoints
- [ ] Frontend team validates error usability

## Implementation Plan

### Phase 1: Error Handler Framework (Day 1-2)
1. Create exception hierarchy
2. Implement error response schema
3. Create exception handler middleware
4. Add correlation ID generation

### Phase 2: Router Updates (Day 3-5)
1. Update CRM router error handling
2. Update Finance router error handling
3. Update Inventory router error handling
4. Update HR router error handling
5. Update Projects router error handling
6. Update Permissions router error handling

### Phase 3: Validation Integration (Day 6-7)
1. Integrate Pydantic error formatting
2. Add field-level error details
3. Create validation error helpers

### Phase 4: Documentation (Day 8-9)
1. Document error code taxonomy
2. Update OpenAPI specifications
3. Create client integration guide
4. Add error handling examples

### Phase 5: Testing & Verification (Day 10)
1. Test all error scenarios
2. Verify no sensitive data leakage
3. Validate correlation ID propagation
4. Load test error handling path

## Dependencies

- None (foundational for M1)

## Related Issues

- #55: API Contract Tests for Critical Write Paths
- #56: Transaction/Rollback Tests
- #57: Database Readiness Checks
- #59: Audit Log Completeness Verification

## Definition of Done

- [x] Code is in the correct ownership boundary (ERP-BACKEND/app/)
- [ ] Tests cover changed behavior
- [ ] No secret or production data is committed
- [ ] Error handling is consistent across all routers
- [ ] API error contracts are documented
- [ ] CI/security checks pass
- [ ] Operational documentation is updated
- [ ] Acceptance evidence exists

---
*Created: 2026-08-16 | Last Updated: 2026-08-16*
