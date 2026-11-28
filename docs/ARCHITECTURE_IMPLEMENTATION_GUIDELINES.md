# ERP03 Architecture Implementation Guidelines

**Repository:** `nyeinpyaesone-ui/ERP03`  
**Target:** `main` modular-monolith architecture  
**Document status:** implementation standard; verify every repository fact against the target commit before acting  
**Last reviewed:** 2026-11-29

This document is the implementation companion to [Architecture Blueprint — November 2026](ARCHITECTURE_BLUEPRINT_2026-11.md). It defines module boundaries, integration rules, engineering workflows, platform responsibilities, and acceptance evidence. It is not a production-readiness certificate.

## 1. Architectural direction

ERP03 is a multi-tenant business ERP delivered as a **modular monolith**:

- React/Vite frontend.
- FastAPI application on Python 3.12.
- PostgreSQL as the authoritative ERP data store.
- SQLAlchemy async persistence and Alembic migrations.
- Redis for bounded operational capabilities such as distributed rate limiting.
- Optional AI integrations, isolated from authoritative business decisions.
- Docker/Compose and Kubernetes deployment assets, with Terraform for infrastructure where applicable.

**Design objective:** correctness first; then efficiency, operability, and evolvability. Keep one deployable backend until measured scale, independent release needs, or clear ownership boundaries justify extraction.

Do not introduce a service mesh, message broker, Celery worker fleet, extra database, or new framework without a documented requirement, operational owner, measurable benefit, and rollback plan.

## 2. Logical module map

Keep the current repository layout and enforce responsibilities within it:

| Area | Owns | Must not own |
|---|---|---|
| `ERP-BACKEND/app/api/` | HTTP routing, auth dependencies, status codes, request/response mapping | Business policy, direct SQL orchestration |
| `ERP-BACKEND/app/schemas/` | Input validation and stable API contracts | Database sessions or side effects |
| `ERP-BACKEND/app/services/` | Domain use cases, invariants, transaction orchestration | HTTP request objects or frontend concerns |
| `ERP-BACKEND/app/models/` | Persistence mappings and relational constraints | HTTP serialization policy |
| `ERP-BACKEND/app/db/` | Engine, session lifecycle, persistence primitives | Domain-specific workflow decisions |
| `ERP-BACKEND/app/core/` | Cross-cutting config, security, errors, audit, metrics, adapters | A dumping ground for domain services |
| `frontend/src/` | UI composition, client-side state, typed API access | Authorization decisions or authoritative business calculations |
| `infra/` | Reproducible infrastructure and deployment configuration | Application business rules |
| `.github/workflows/` | CI, security, artifact publishing, release and approved deployment automation | Hidden production credentials or unreviewed deployment policy |

### Dependency direction

```text
HTTP route -> schema + application service -> domain rules
                                      |       |
                                      v       v
                                repository / DB session
                                      |
                                      v
                                  PostgreSQL

Frontend -> versioned API contract -> FastAPI
AI / Redis / external providers -> explicit adapters -> application services
```

Rules:

1. Routes stay thin and call services.
2. Services accept typed inputs and explicit dependencies; they do not import FastAPI request state.
3. Persistence access is explicit and transaction-scoped.
4. Cross-module calls use public service functions or stable contracts, not imports of another module's private internals.
5. Avoid circular imports and global mutable business state.
6. Keep adapters replaceable and external SDKs out of core domain logic.

## 3. Domain and data ownership

### PostgreSQL — source of truth

PostgreSQL owns tenant, user, branch, catalog, sales, purchasing, inventory, payment, accounting and audit-related business records. Use database constraints as the final guard for uniqueness, referential integrity and invariant enforcement.

- Every tenant-owned query and mutation must be scoped by the authenticated tenant/business identity.
- Never accept tenant identity from an untrusted request body as authorization.
- Use explicit transaction boundaries around each business command.
- Use row locks or atomic conditional updates for contested stock, invoice numbering, balances and workflow claims.
- Keep migrations backward-compatible during rolling deployment: expand, deploy compatible code, backfill, then contract in a later release.
- Test migrations against PostgreSQL; SQLite-only tests do not prove PostgreSQL locking, isolation or constraint behavior.

### SQLite transaction journal — transitional constraint

The repository blueprint documents a SQLite WAL journal on a ReadWriteOnce volume while backend replicas can scale. This is **not a safe cross-node shared journal**.

- Do not treat the SQLite journal as the accounting ledger or as proof of multi-replica idempotency.
- Do not increase backend replicas/HPA and claim safe horizontal scaling while journal ownership remains unresolved.
- Preferred direction: move journal/idempotency records into PostgreSQL or another proven shared transactional store, with schema migration, backfill, dual-read/dual-write strategy where necessary, reconciliation, and rollback.
- Preserve idempotency keys and historical outcomes during migration; test replay and payload-mismatch behavior.

### Redis — operational dependency only

Redis may support distributed rate limiting and future cache/session use when explicitly designed. It is not the ledger, durable workflow store, or authority for financial state.

- Bound connection pools and set connect/operation timeouts.
- Define fail-open versus fail-closed per capability; document the security and availability trade-off.
- Emit metrics and alerts when the rate limiter degrades.
- Cache only data with a documented key, tenant scope, TTL, invalidation rule and stale-data tolerance.
- Never cache authorization outcomes or financial balances without a correctness design.
- Avoid adding Redis Streams, queues or Celery until a real asynchronous workload and delivery semantics are specified.

## 4. Critical correctness and security requirements

### Authentication and tenant isolation

- Verify JWT signature, allowed algorithm, issuer/audience when configured, expiry and relevant claims before trusting any claim.
- Middleware must not decode an unverified token and use `business_id` to form a tenant rate-limit key. The current checked `ERP-BACKEND/app/main.py` snapshot contains a decode call with signature and expiry verification disabled; treat this as a security defect until the current main/PR state proves it corrected.
- Resolve tenant identity from verified authentication context and enforce authorization again in the service/data-access path.
- Test expired, malformed, wrong-signature, wrong-algorithm, missing-tenant and cross-tenant requests.

### Idempotency and concurrency

- Scope idempotency keys by tenant and caller/client identity.
- Persist a canonical request fingerprint and the final result/outcome.
- Same key + same payload returns the original result; same key + different payload returns a stable conflict error.
- Make state transitions atomic; use conditional updates and PostgreSQL locking semantics where required.
- Treat retries as normal: external calls must use provider idempotency keys or an outbox/reconciliation design.
- Test duplicate concurrent requests, worker/process races, crash recovery and stale in-progress claims against PostgreSQL.

### Audit and financial operations

- Record actor, tenant, operation, target, timestamp, request/correlation ID and outcome for sensitive business actions.
- Do not log passwords, tokens, secret values, payment credentials or unnecessary personal data.
- Use append-oriented audit records with restricted mutation permissions.
- Reconcile sales, payments, stock movements and accounting postings; never infer a financial success from an HTTP response alone.
- Use decimal/numeric representations for money and explicit currency/rounding rules; never use binary floating point for ledger amounts.

## 5. API and frontend implementation contract

- Keep routes under the configured versioned prefix (`/api/v1`).
- Define request and response schemas before implementation.
- Return stable typed error codes and a consistent error envelope.
- Include request IDs in responses, logs and audit events.
- Document pagination, filtering, sorting, idempotency and retry behavior.
- Validate CORS origins and production HTTPS settings from environment configuration.
- Frontend API calls must use one shared client, typed response models, bounded timeouts and consistent error handling.
- Do not duplicate authoritative calculations (tax, totals, inventory availability, balances) in the browser.
- Treat UI permissions as presentation only; backend authorization remains mandatory.
- Keep design tokens, accessibility rules and reusable components centralized. A Themely-generated palette may seed tokens, but it must pass contrast checks and must not create a runtime dependency on the theme-generation service.

## 6. AI and NVIDIA integration policy

AI is an optional assistant capability, not an authority over ERP state.

- Keep AI providers behind an adapter interface with explicit timeout, retry, cancellation and circuit-breaker behavior.
- Pass the minimum tenant-scoped context needed; redact secrets and sensitive fields.
- Treat model output as untrusted suggestions. Validate it against typed schemas and deterministic business rules.
- Require explicit human approval for high-impact actions (payments, accounting adjustments, stock corrections, permission changes).
- Persist provenance: model/provider, model version, prompt/template version, request ID, confidence where meaningful, and approval/outcome.
- A model outage must not prevent ordinary ERP transactions.

Use NVIDIA GPU/CUDA/TensorRT/NeMo/RAPIDS or related tooling only when a measured AI/analytics workload benefits from it and compatible target hardware is available. Keep GPU-specific dependencies and services optional; CPU-only ERP operation must remain supported. Do not add GPU infrastructure merely because an NVIDIA integration exists.

## 7. External platform integration boundaries

These platforms are optional tooling or deployment targets, not additional sources of ERP truth. Select only what the team actually operates.

| Platform | Appropriate role | Integration rule |
|---|---|---|
| GitHub | Canonical source repository, code review, CI, releases and issues/PRs | GitHub `main` remains the source of truth unless an approved migration changes it |
| GitLab | Optional mirror or separately approved CI destination | Avoid two writable canonical remotes; define mirror direction, protected branches and token scopes |
| Linear | Engineering issue tracking and delivery planning | Link issues to PRs/commits; do not duplicate source code or secrets |
| Notion | Human-readable architecture decisions, runbooks and project knowledge | Link to versioned docs in Git; Git-tracked docs remain reviewable implementation authority |
| Redis | Cache/rate-limit infrastructure | Follow Section 3; never use as durable ERP ledger |
| Supabase | Optional managed PostgreSQL/Auth/Storage/Realtime evaluation | Do not introduce a second auth or database authority alongside ERP03 without a migration/ownership decision; validate RLS and tenant isolation before exposure |
| Vercel | Optional frontend preview/hosting | Backend API, secrets, database connectivity, CORS and deployment ownership must be explicit; do not move backend state implicitly |
| Floot | Optional prototype or separately hosted app workflow | Do not fork production business logic or create a competing ERP data store |
| Themely Design + Style Generator | Design-token exploration | Export reviewed tokens into the frontend; no production runtime dependency |
| NVIDIA ecosystem | Optional accelerated AI/analytics | Isolate GPU workloads behind adapters and preserve CPU fallback |

For every external integration, document: owner, purpose, data classification, system of record, authentication method, minimum permissions, network path, timeout/retry policy, failure mode, observability, cost owner and decommission procedure. Never copy credentials into source files, issues, Notion pages or logs.

## 8. Runtime and deployment rules

- Keep development, CI, staging and production configuration explicit and validated at startup.
- Production must reject development secrets, localhost CORS origins and SQLite database URLs.
- Store secrets in the deployment platform's secret manager; use least-privilege, environment-scoped credentials.
- Build immutable AMD64 and ARM64 artifacts where required; attach SBOM/provenance and verify signatures where configured.
- Deploy by immutable image digest, not mutable `latest` tags.
- Run migrations as a controlled release step, not concurrently from every application replica.
- Use readiness/liveness probes with distinct semantics; readiness should represent ability to serve safely.
- Use graceful shutdown, bounded requests, resource limits and rollback to a known compatible image.
- A rolling update is not zero downtime if database, journal, Redis, ingress or external dependencies are single points of failure.
- Do not apply production manifests until all image digest placeholders, runtime secrets, storage classes, ingress/TLS values and backup/restore procedures are verified.

The current architecture notes identify unresolved production risks: the SQLite journal with a single ReadWriteOnce volume, single-instance PostgreSQL/Redis manifests, image digest placeholders, and an unqualified production deployment script. These are release blockers until verified resolved on the target commit.

## 9. Observability and operational requirements

Every request and business command should be traceable across API, service, database and external adapter boundaries.

Required signals:

- Structured logs with timestamp, severity, service, environment, request ID, tenant-safe identifier and outcome.
- Metrics for request count/latency/errors, database pool saturation, transaction conflicts, idempotency replays, queue depth if a queue is later introduced, Redis degradation and migration/deployment status.
- Distributed traces when OpenTelemetry is enabled; do not attach secrets or sensitive payloads.
- Health endpoints with documented liveness/readiness semantics.
- Alerts tied to actionable runbooks and an accountable owner.

Do not expose Prometheus metrics, traces or internal diagnostics publicly without authentication/network restrictions.

## 10. Engineering workflow and change discipline

Follow the repository's existing agent contract in `AGENTS.md` and `docs/agent/WORKFLOW.md`:

1. Inspect the target branch, working tree, related code, tests, workflows and open PRs.
2. Confirm the current implementation and avoid relying on stale documentation.
3. Write a small design note or ADR for cross-module, schema, security or deployment changes.
4. Implement one logical change on a topic branch; do not rewrite history or edit unrelated modules.
5. Add regression tests with the change.
6. Run the repository's single completion gate: `bash scripts/agent/bootstrap.sh`, then `bash scripts/agent/verify.sh`.
7. Preserve the exact PASS/SKIP evidence and the generated `.agent/evidence/*.json` locally; never commit `.agent/`.
8. Review the diff for secrets, generated files, dependency drift, workflow permission expansion and unrelated edits.
9. Open a PR with problem, scope, design, migration/rollback plan, tests, evidence and known limitations.
10. Merge only after required checks and review policies pass; verify the resulting main commit and post-merge workflows.

Never make a gate green by disabling it, using `|| true`, weakening tests, suppressing findings or inventing evidence. Do not change production secrets, branch protections, environments or live infrastructure as part of a documentation-only task.

### Documentation and decision records

- Keep this implementation guide and the architecture blueprint aligned.
- Record material decisions in `docs/adr/NNNN-short-title.md` with context, decision, alternatives, consequences and rollback implications.
- Update runbooks and readiness matrices only when implementation evidence changes.
- Notion may link to or summarize approved docs; avoid divergent copies that claim a different implementation state.
- Linear issues should identify acceptance criteria and link to the owning PR.

## 11. Required acceptance checklist

A module or integration is ready for review only when applicable items are satisfied:

- [ ] Clear owner, purpose, public contract and data ownership.
- [ ] Dependency direction follows the module map; no circular or private cross-module coupling.
- [ ] Tenant isolation and authorization are enforced server-side.
- [ ] Transaction, idempotency and concurrency behavior is defined and tested.
- [ ] Migrations are reviewed, reversible where feasible, and rolling-deployment compatible.
- [ ] Errors, logs, metrics and audit events are actionable and redact sensitive data.
- [ ] External dependencies have timeout, retry, outage and decommission behavior.
- [ ] Unit tests and PostgreSQL integration tests cover critical paths.
- [ ] Frontend build and API contract compatibility pass where applicable.
- [ ] Security, dependency, container and IaC checks pass where applicable.
- [ ] ARM64/AMD64 compatibility is verified for published images when both are supported.
- [ ] Deployment, rollback, backup and restore evidence exists before production claims.
- [ ] PR contains verification evidence and documents any skipped checks or unresolved risks.

## 12. Known documentation drift to reconcile

The checked repository files are not fully consistent. Before using any version or gate statement as authoritative, reconcile:

1. `README.md` reports FastAPI 0.162.0, Vite 8.3.6 and React 19.3.1, while `AGENTS.md` contains older Vite 5.4.11 guidance.
2. Alembic head references differ across `AGENTS.md` and older readiness/task documents.
3. `docs/PRODUCTION_READINESS_MATRIX.md` labels production readiness QUALIFIED, while the architecture blueprint and deployment notes identify unresolved journal, database HA, digest and production-script blockers. Use runtime evidence and the stricter blocker list; do not infer production approval from a matrix label.
4. Recheck open PR status and workflow conclusions on the current target commit; historical PR numbers and check results in dated documents are not current state.

Update the owning document from verified manifests, lockfiles, migration heads, workflow runs and runtime evidence. Do not resolve drift by changing source configuration merely to match stale documentation.

## 13. Non-goals

This guide does not authorize:
- a microservice rewrite or a second canonical repository;
- replacing PostgreSQL with Supabase or another provider;
- moving the backend to Vercel or Floot;
- adopting GitLab as a second writable source of truth;
- adding Celery, Kafka, RabbitMQ, Redis Streams or GPU infrastructure without a measured requirement;
- changing live deployments, secrets, branch protections or production data.

**Guiding rule:** preserve business correctness and source-of-truth clarity; add complexity only when evidence demonstrates that it is necessary.
