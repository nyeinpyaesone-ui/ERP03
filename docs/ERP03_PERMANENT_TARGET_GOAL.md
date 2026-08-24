# ERP03 — Permanent Target Goal

## North-Star Objective

> **Make ERP03 more correct, efficient, scalable, observable, and independently evolvable.**

This objective is the governing target for ERP03 architecture, refactoring, optimization, and future service evolution.

---

## 1. Primary Success Dimensions

### Correct

- Preserve business-rule integrity.
- Keep critical transactions atomic and reliable.
- Protect concurrency-sensitive operations.
- Preserve idempotency where commands can be retried.
- Preserve auditability and traceability.
- Do not sacrifice correctness for performance.

### Efficient

- Optimize measured SQL/query hotspots.
- Eliminate N+1 and unnecessary repeated queries.
- Reduce unnecessary client/API round trips.
- Use aggregation/query paths for expensive cross-domain reads.
- Control database connection usage.
- Cache only where measured access patterns justify it.
- Optimize before adding concurrency.

### Scalable

- Maintain explicit domain boundaries.
- Keep transactional and long-running workloads appropriately separated.
- Use queues/workers for genuinely asynchronous workloads.
- Scale components independently only when evidence justifies it.
- Avoid premature microservice fragmentation.

### Observable

- Use structured logs.
- Propagate correlation identifiers.
- Measure request and query latency.
- Monitor database connection usage.
- Monitor Redis and worker/queue behavior where used.
- Expose health and failure conditions.
- Validate performance with measurements, not assumptions.

### Independently Evolvable

- Keep routers focused on transport concerns.
- Keep application and domain responsibilities explicit.
- Control persistence access behind appropriate boundaries.
- Maintain explicit contracts between major system boundaries.
- Keep ERP and AI concerns isolated.
- Preserve the option to extract a service later without requiring a full rewrite.

---

## 2. Confirmed Architectural Direction

ERP03 should evolve as a **modular ERP core first**, not as an immediate microservice system.

```text
Client
  ↓
FastAPI Transport
  ↓
Commands / Queries / Integration
  ↓
Application Services
  ↓
Domain Services
  ↓
Persistence Boundaries
  ↓
PostgreSQL
```

Long-running or non-blocking workloads may use:

```text
API → Queue/Redis → Worker → Application Service → PostgreSQL
```

High-value read workloads may use:

```text
Client → Query/Aggregation Service → Optimized Reads → Aggregated DTO → Client
```

---

## 3. Permanent Rules

1. ERP Core remains the system of record.
2. Keep the current modular-monolith direction until service extraction is justified by evidence.
3. Keep FastAPI routers thin and focused on HTTP/transport concerns.
4. Progressively move business behavior into explicit application/domain responsibilities.
5. Treat commands and queries differently where the distinction provides practical value.
6. Keep critical ERP transactions synchronous, atomic, and confirmation-based.
7. Use asynchronous processing selectively for long-running or non-blocking work.
8. Do not multiply database pools without measured operational justification.
9. Do not use async/concurrency blindly against database sessions.
10. Optimize SQL, query shape, indexes, batching, payloads, and access patterns before adding concurrency.
11. Use aggregation paths to optimize expensive dashboards and cross-domain reads.
12. Redis is not the ERP system of record.
13. AI must not directly access ERP PostgreSQL or ERP ORM models.
14. The ERP↔AI integration boundary remains contract-based, authenticated, authorized, idempotent, correlated, and auditable.
15. Every architectural change must be testable and reversible.
16. Existing working functionality and infrastructure must not be destabilized without a verified reason.
17. Performance improvements must be demonstrated by profiling or load testing.
18. Microservices are an evidence-based future extraction option, not the immediate architecture target.

---

## 4. Implementation Priority Order

```text
1. Correctness
       ↓
2. Clear Boundaries
       ↓
3. Query Efficiency
       ↓
4. Selective Async Workloads
       ↓
5. Measurement and Observability
       ↓
6. Production Hardening
       ↓
7. Evidence-Based Service Extraction
```

This order is mandatory in principle: ERP transaction integrity must not be traded away for architectural novelty or speculative performance gains.

---

## 5. Required Outcome Tests

A proposed ERP03 change should answer these questions:

- Does it improve or preserve correctness?
- Does it reduce a measured inefficiency or operational risk?
- Does it improve scalability without unnecessary complexity?
- Does it improve observability or diagnosability?
- Does it create a cleaner boundary for future independent evolution?
- Is the benefit measurable or operationally justified?
- Can the change be tested and rolled back?

If the answer is not meaningfully positive, the change should not be adopted merely for architectural fashion.

---

## 6. Explicit Non-Goals

This target does not require:

- an immediate full backend rewrite;
- immediate microservice conversion;
- converting every endpoint to `async`;
- a database pool per domain;
- direct AI-to-database access;
- replacing working infrastructure without evidence;
- claiming performance gains before measurement.

---

## Final Confirmation

> **ERP03's permanent target goal is to make the system more correct, efficient, scalable, observable, and independently evolvable.**

The architectural path is:

> **Modular ERP Core → Correct Boundaries → Optimized Query/Aggregation Paths → Selective Async Workloads → Measurement/Observability → Production Hardening → Evidence-Based Service Extraction.**

Any future ERP03 architectural proposal or implementation should be evaluated against this objective.
