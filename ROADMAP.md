# ERP03 Roadmap

> **Planning baseline:** 2026-08-16  
> **Repository:** `nyeinpyaesone-ui/ERP03`  
> **Current stage:** Architecture Boundary / ERP Runtime Stabilization  
> **Release status:** No release tag exists yet; `main` is not a production v1.0 release.

## Product direction

ERP03 is an ERP **System of Record** with a separately owned AI/agent platform.

```text
ERP-BACKEND  <── authenticated contracts/events ──>  AI-BACKEND
     │                                                   │
     ▼                                                   ▼
ERP database                                      AI state/models
(transactional truth)                              (derived state)
```

ERP remains authoritative for transactions, permissions, workflow state, auditability, and persistence. AI must never become a second ERP database or bypass ERP authorization.

## M0 — Architecture Baseline
**COMPLETE**

- ERP runtime moved to `ERP-BACKEND/`.
- `AI-BACKEND/`, `INTEGRATION/`, and `INFRASTRUCTURE/` boundaries established.
- In-process AI runtime removed from ERP runtime.
- Superseded backend generations removed from active `main`; Git history remains the recovery source.
- Compose, Docker build, release, and Nginx references updated to the active ERP service root.
- Architecture and data-ownership rules documented.

**Exit qualification:** no active legacy backend runtime; ERP startup has no former AI dependency; no AI-to-ERP-database path.

## M1 — ERP Core Stabilization
**NEXT / BLOCKING**

**Goal:** make the ERP System of Record independently testable and deployable before AI is reintroduced.

### Required implementation
1. Inventory routes, services, models, migrations, and external integrations.
2. Separate business rules from HTTP routing where practical.
3. Establish deterministic service/use-case boundaries for transactional writes.
4. Verify authentication, authorization, validation, idempotency, and audit behavior.
5. Verify Alembic migration reproducibility from an empty database.
6. Add API contract tests for critical write paths.
7. Add transaction/rollback tests.
8. Add database/infrastructure readiness checks.

### Product qualification
- Critical ERP transactions work end-to-end.
- ERP owns the single authoritative transactional write path.
- Authenticated and authorized writes are enforced.
- Failed transactions roll back without partial state.
- Clean install and upgrade migrations succeed.
- Critical paths expose request/correlation IDs and structured errors.

**Exit gate:** `ERP-BACKEND` passes its critical suite without `AI-BACKEND`.

## M2 — Integration Contract Layer
**PLANNED**

**Goal:** create the only supported ERP ↔ AI communication boundary.

### Required code/services
- `INTEGRATION/contracts/api/` — versioned request/response schemas.
- `INTEGRATION/contracts/events/` — versioned event envelopes.
- `INTEGRATION/contracts/schemas/` — shared validation models.
- `INTEGRATION/erp-client/` — authenticated ERP client used by AI.
- `INTEGRATION/authentication/` — service-to-service authentication policy.
- `INTEGRATION/event-bus/` — transport abstraction where required.

### Required controls
- API/event versioning.
- Correlation/request ID propagation.
- Timeout, retry, and idempotency policy.
- Least-privilege service credentials.
- Read/query and command permissions separated.
- No ORM/model sharing across service boundaries.

**Exit gate:** contract tests prove AI can read approved ERP data and submit an approved command only through the integration boundary.

## M3 — AI Runtime MVP
**PLANNED**

**Goal:** implement AI as an external consumer/orchestrator, not ERP business logic.

### Required code/services
- `AI-BACKEND/api/` — AI API.
- `AI-BACKEND/orchestrator/` — task routing/execution policy.
- `AI-BACKEND/agents/` — bounded specialist agents.
- `AI-BACKEND/tools/` — allow-listed tools.
- `AI-BACKEND/models/` — model adapters/configuration.
- `AI-BACKEND/memory/` — derived conversation/task state only.
- `AI-BACKEND/policies/` — safety/permission/approval rules.
- `AI-BACKEND/events/` — AI event consumers/publishers.

### MVP capabilities
1. Authenticated AI request.
2. Deterministic ERP context retrieval through integration.
3. Model invocation.
4. Allow-listed tool execution.
5. Human/ERP authorization for sensitive commands.
6. Structured result with audit/correlation metadata.
7. Failure/timeout handling.

**Exit gate:** one approved workflow works end-to-end without direct ERP DB access or authorization bypass.

## M4 — End-to-End Qualification
**PLANNED**

```text
request
  → authentication
  → AI policy
  → ERP read contract
  → model/tool decision
  → ERP command contract (if permitted)
  → ERP transaction
  → audit/event
  → response
```

### Required tests
- Contract compatibility.
- Authentication/authorization.
- Prompt/tool abuse boundaries.
- Duplicate command/idempotency.
- Timeout/retry behavior.
- ERP rollback behavior.
- Audit completeness.
- Event delivery/replay where enabled.
- Data-leakage/authorization-context tests.

**Exit gate:** critical workflows pass reproducibly with no direct AI-to-database path.

## M5 — Production Qualification
**PLANNED**

- Production deployment configuration verified.
- Immutable image references/digests.
- Secrets only through deployment secret stores.
- Database backup + restore drill completed.
- Migration forward/rollback strategy documented.
- Health/readiness checks verified.
- Logs, metrics, and traces available for critical services.
- Resource limits/restart behavior tested.
- Staging deployment verified before production promotion.

**Release gate:** code, tests, containers, migrations, security, deployment, rollback, and recovery evidence all pass.

## M6 — Product Release v1.0
**FUTURE / GATED**

Target product:
- transactional integrity;
- role/permission enforcement;
- auditability;
- reproducible deployment;
- backup/recovery;
- versioned integration contracts;
- independently deployable AI service;
- operational runbook.

**Do not create the v1.0 release tag until M1–M5 exit gates are satisfied.**

## Deferred / potential features

Lower priority than ERP correctness and service boundaries:

- Advanced forecasting / anomaly detection.
- Natural-language ERP query.
- Automated report generation.
- Mobile offline workflows.
- Barcode/QR workflows.
- Advanced RBAC/custom roles.
- Multi-currency.
- Advanced BI.
- Plugin/extension system.
- GraphQL.
- IoT/voice/AR/VR/blockchain.

## Standard implementation routine

Every milestone follows:

1. **Requirement** — business outcome + constraints.
2. **Contract** — inputs, outputs, ownership, permissions, errors, versioning.
3. **Design** — service/module/database boundaries.
4. **Implementation** — smallest production-capable slice.
5. **Unit tests** — business rules.
6. **Integration tests** — DB/APIs/queues/external boundaries.
7. **Security tests** — auth, authorization, secrets, data exposure.
8. **Operational tests** — health, restart, migration, backup/restore, observability.
9. **Staging qualification** — exact release candidate.
10. **Evidence** — record build/test/deployment results.
11. **Acceptance** — satisfy milestone exit gate.
12. **Release** — tag only after required gates pass.

## Definition of Done

A task is Done only when:

- code is in the correct ownership boundary;
- tests cover changed behavior;
- no secret or production data is committed;
- migrations are reproducible;
- API/event contracts are documented/versioned when applicable;
- failure and rollback behavior are defined;
- CI/security checks pass;
- operational documentation is updated;
- acceptance evidence exists.

See `docs/PROJECT_PLAN.md` for the executable implementation plan and qualification matrix.
