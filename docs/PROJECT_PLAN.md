# ERP03 Project Plan

> **Verified baseline:** 2026-08-16  
> **Branch:** `main`  
> **Purpose:** executable engineering plan for the ERP System of Record, integration boundary, external AI platform, and production qualification.

## 1. Verified repository baseline

The current repository contains these architectural roots:

```text
ERP03/
├── ERP-BACKEND/       # active ERP runtime
├── AI-BACKEND/        # AI ownership boundary; runtime not yet implemented
├── INTEGRATION/       # ERP ↔ AI contract boundary
├── INFRASTRUCTURE/    # runtime/platform dependencies
├── docs/              # architecture and operations
└── scripts/           # automation
```

`ERP-BACKEND` currently contains a FastAPI application, Alembic migrations, and the React frontend build. The ERP router layer includes authentication, finance, HR, inventory, CRM, analytics, payments, permissions, projects, documents, administration, and integration-related routes. The AI directories are currently architectural placeholders rather than a qualified running AI service.

There are currently **no Git tags** in the repository. Therefore the repository must not claim that v1.0.0 has been released or production-qualified.

## 2. Product goals

### Primary goal
Deliver a dependable ERP System of Record first, then add AI through explicit contracts.

### Non-negotiable boundaries

1. ERP owns transactional truth.
2. ERP owns authorization for ERP actions.
3. ERP owns persistence and audit records for ERP transactions.
4. AI receives only authorized/necessary ERP context.
5. AI never connects directly to the ERP database.
6. AI commands must enter through authenticated ERP contracts.
7. AI memory/model state is derived state, not ERP truth.
8. Production data never becomes development/test fixture data by copying the live database.
9. Every destructive migration has a recovery strategy.
10. Every release has reproducible build/test/deployment evidence.

## 3. Milestone and target matrix

| ID | Target | Status | Primary qualification |
|---|---|---|---|
| M0 | Architecture boundary | Complete | Active tree has clean ownership boundaries |
| M1 | ERP core stabilization | Next | ERP critical workflows pass independently |
| M2 | Integration contracts | Planned | Contract tests + service authentication pass |
| M3 | AI runtime MVP | Planned | One approved AI workflow works without DB access |
| M4 | E2E qualification | Planned | Critical ERP↔AI workflows reproducibly pass |
| M5 | Production qualification | Planned | Security, backup, migration, deployment, observability pass |
| M6 | v1.0 product release | Gated | All release gates + operational acceptance pass |

## 4. Step-by-step implementation procedure

### Step 1 — Baseline inventory

**Requirements**
- List every ERP route and identify its business capability.
- Map each route to models, services, repositories/data access, and migrations.
- Identify external integrations and infrastructure dependencies.
- Identify all remaining AI references.

**Code/service output**
- `docs/architecture/` ownership maps.
- Module inventory.
- Dependency map.
- AI-reference inventory.

**Qualification**
- No unknown production entry point remains.
- Every transactional route has an identified owner.

### Step 2 — ERP application boundary

**Requirements**
- Keep FastAPI/HTTP concerns at the API edge.
- Put business decisions in application/domain services where extraction is useful.
- Keep database access behind controlled data-access components.
- Do not place model/LLM calls inside ERP business transactions.

**Code/service output**
- `ERP-BACKEND/app/routers/`
- `ERP-BACKEND/app/services/`
- database/model layer
- Alembic migrations

**Qualification**
- Unit tests cover business rules.
- Integration tests cover persistence.
- API tests cover authorization and validation.

### Step 3 — Transaction safety

**Requirements**
- Define transaction boundaries for each critical command.
- Validate inputs before writes.
- Enforce authorization before state mutation.
- Ensure duplicate requests cannot create duplicate financial/inventory effects where idempotency is required.
- Roll back failed multi-write operations.

**Qualification**
- Duplicate-command tests pass.
- Rollback tests pass.
- Unauthorized mutation tests pass.

### Step 4 — Data lifecycle

**Requirements**
- Treat ERP database as system of record.
- Use versioned migrations.
- Record audit metadata for sensitive changes.
- Define retention/backup requirements.
- Separate development/test data from production data.

**Qualification**
- Empty database migration succeeds.
- Upgrade migration succeeds from supported baseline.
- Restore drill succeeds.
- No real production credentials/data are committed.

### Step 5 — Integration contracts

**Requirements**
- Define versioned API schemas.
- Define event envelope and event versioning.
- Define service authentication.
- Define timeout/retry/idempotency behavior.
- Define read vs command permissions.

**Code/service output**
```text
INTEGRATION/
├── contracts/api/
├── contracts/events/
├── contracts/schemas/
├── erp-client/
├── event-bus/
└── authentication/
```

**Qualification**
- Contract tests run independently.
- Invalid payloads are rejected deterministically.
- Service credentials cannot exceed intended permissions.

### Step 6 — AI service implementation

**Requirements**
- AI API must authenticate callers.
- Orchestrator must enforce policy before tool execution.
- Tools must be allow-listed.
- Model adapters must be replaceable.
- Memory must store derived AI state only.
- Sensitive ERP commands require explicit ERP authorization/approval.

**Code/service output**
```text
AI-BACKEND/
├── api/
├── orchestrator/
├── agents/
├── models/
├── tools/
├── memory/
├── policies/
└── events/
```

**Qualification**
- AI has no ERP ORM/database dependency.
- Tool calls are auditable.
- Prompt/tool injection tests do not produce unauthorized ERP commands.
- Model failure does not corrupt ERP state.

### Step 7 — End-to-end workflow qualification

For every AI-enabled workflow:

```text
Caller
  ↓
Authentication
  ↓
AI policy
  ↓
ERP read contract
  ↓
Model / tool decision
  ↓
ERP command contract (only if authorized)
  ↓
ERP transaction
  ↓
Audit / event
  ↓
Result
```

**Required evidence**
- happy-path test;
- unauthorized-path test;
- malformed-input test;
- duplicate/retry test;
- timeout test;
- ERP rollback test;
- audit verification;
- data-exposure test.

### Step 8 — Service qualification

Each deployable service must satisfy:

**Build**
- deterministic dependency installation;
- reproducible Docker build;
- minimal runtime image where practical;
- no secrets in image/layers.

**Runtime**
- health endpoint/check;
- readiness check for required dependencies;
- controlled shutdown;
- restart-safe behavior;
- structured logs.

**Security**
- least privilege;
- authenticated service access;
- secret injection at runtime;
- dependency/security scanning;
- no direct database access from unauthorized service.

**Operations**
- metrics for critical operations;
- correlation/request IDs;
- backup/restore procedure;
- migration procedure;
- rollback procedure.

### Step 9 — Release candidate

A release candidate is created only after the changed code passes:

```text
lint/type checks
      ↓
unit tests
      ↓
integration tests
      ↓
security checks
      ↓
container build
      ↓
deployment configuration validation
      ↓
staging deployment
      ↓
smoke/E2E tests
      ↓
backup/restore evidence where applicable
      ↓
release approval
```

The repository's release workflow already builds ERP backend/frontend images from the active `ERP-BACKEND` paths and uses immutable image digests as the promotion boundary; staging and production remain approval gates. The workflow must be treated as a release mechanism, not proof that a release has already passed.

## 5. Product qualification gates

### Gate A — Architecture
- [ ] No ERP↔AI direct database dependency.
- [ ] Ownership boundaries documented.
- [ ] Legacy runtime absent from active tree.

### Gate B — ERP correctness
- [ ] Critical writes tested.
- [ ] Authorization tested.
- [ ] Transactions/rollback tested.
- [ ] Migrations tested.
- [ ] Audit behavior tested.

### Gate C — Integration
- [ ] API contracts versioned.
- [ ] Event contracts versioned where used.
- [ ] Service authentication implemented.
- [ ] Retry/idempotency policy tested.

### Gate D — AI safety/correctness
- [ ] AI has no direct ERP DB access.
- [ ] Tools allow-listed.
- [ ] Sensitive commands authorized.
- [ ] AI failures cannot corrupt ERP state.
- [ ] Audit/correlation metadata retained.

### Gate E — Production operations
- [ ] Build reproducible.
- [ ] Images immutable.
- [ ] Secrets externalized.
- [ ] Backup and restore verified.
- [ ] Deployment verified in staging.
- [ ] Rollback procedure tested.
- [ ] Monitoring/logging operational.

### Gate F — Release
- [ ] All previous gates complete.
- [ ] Release notes reflect actual state.
- [ ] Version/tag created only after acceptance.
- [ ] Deployment artifact/digest recorded.

## 6. Issue/commit routine

Use small atomic changes:

```text
architecture → contract → implementation → tests → security → operations → docs
```

Commit examples:

- `feat(erp): add inventory command boundary`
- `test(erp): cover inventory transaction rollback`
- `feat(integration): add v1 ERP query contract`
- `feat(ai): add authenticated task endpoint`
- `test(e2e): verify AI inventory query boundary`
- `docs(release): record staging qualification`

Do not mix unrelated migrations, AI features, infrastructure changes, and product features in one commit unless they form one inseparable deployment unit.

## 7. Data management rules

- Git stores source/configuration templates, not production data.
- Production secrets belong in deployment secret stores.
- Database backups are operational artifacts, not repository files.
- AI memory is not an authoritative copy of ERP transactions.
- Event payloads must avoid unnecessary sensitive data.
- Logs must not contain passwords, tokens, or unnecessary personal/financial data.
- Schema changes require migration files and rollback/recovery consideration.
- Destructive data changes require explicit backup/recovery evidence.

## 8. Current blockers

1. ERP runtime needs independent functional/test qualification.
2. Integration directories need real versioned contracts and authentication implementation.
3. AI-BACKEND is currently a structural boundary, not a qualified running service.
4. End-to-end ERP↔AI tests do not yet establish service parity.
5. GitHub currently reports no status checks for the latest architecture documentation commit; therefore CI health must not be described as verified until an actual workflow run is observed.
6. No repository release tag currently exists.

## 9. Release target

**v1.0 is a qualification target, not the current repository status.**

The first production release should be created only after the ERP core is independently reliable and the AI integration, if included in the release, passes the same security and operational qualification gates.
