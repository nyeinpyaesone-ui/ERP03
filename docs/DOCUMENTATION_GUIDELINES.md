# ERP03 Documentation Guidelines

**Last reviewed:** 2026-11-20  
**Purpose:** keep engineering, deployment and performance documents consistent with the repository rather than assumed or historical state.

## 1. Source-of-truth hierarchy

Use these documents for these concerns:

| Concern | Source of truth |
|---|---|
| Current priority, phases and sequencing | [Engineering Roadmap](ROADMAP.md) |
| Performance measurements and PR acceptance | [Performance Optimisation Checklist](PERFORMANCE_OPTIMIZATION_CHECKLIST.md) |
| Current implementation versus qualification evidence | [Production Readiness Matrix](PRODUCTION_READINESS_MATRIX.md) |
| Historical completed work and commit evidence | [Remediation Tracker](TODO.md) |
| Module boundaries and state ownership | [Architecture Blueprint](ARCHITECTURE_BLUEPRINT_2026-11.md) |
| Deployment, rollback and environment gates | [Deployment Runbook](DEPLOY_RUNBOOK.md) and [Zero-Downtime Deployment](ZERO_DOWNTIME_DEPLOYMENT_2026-11.md) |
| Credentials and environment variable names | [Configuration & Credentials Setup](../CONFIGURATION_SETUP.md) |

Do not maintain competing copies of the same task list. Put new priorities in the roadmap, implementation/verification evidence in the tracker, and current release state in the matrix. Historical documents may remain for traceability but must be visibly marked as historical.

## 2. Required metadata and evidence

Every operational or architecture document must identify:

- Repository and affected component.
- Last reviewed date.
- Exact source commit or branch inspected. Distinguish default-branch state from a feature-branch snapshot.
- Environment scope: local, CI, preview, staging or production.
- Evidence type: source inspected, test passed, workflow passed, artifact published, runtime smoke test, restore drill or operator sign-off.
- Known limitations, assumptions and next owner/action where relevant.

A successful build does not prove image publication, runtime connectivity, database recovery, multi-replica safety or production readiness. State exactly what the evidence proves.

## 3. Status vocabulary

Use these labels consistently:

- **Implemented:** source/configuration exists; runtime qualification may still be pending.
- **Partial:** only part of the requirement is implemented or some environments remain unverified.
- **Evidence pending:** configuration exists but the required workflow/runtime proof has not completed.
- **Blocked:** a known dependency, security issue or missing external input prevents safe progression.
- **Unmeasured:** no repeatable baseline or runtime measurements exist.
- **Qualified:** every stated acceptance gate has passed for the named environment and exact commit.

Never mark a row PASS/Qualified solely because files, workflows, manifests or scripts exist. Avoid “production-ready” or “zero-downtime” unless the runtime evidence, stateful dependency behaviour and rollback/restore drills support the claim.

## 4. Roadmap and checklist maintenance

- Every work item gets a priority, scope, dependency, owner (when known) and testable definition of done.
- Order work by correctness/security and operability before optimisation and scale.
- Performance tasks require an observed bottleneck, reproducible baseline, hypothesis, before/after evidence and correctness regression tests.
- Do not treat speculative architecture, arbitrary latency targets or theoretical load assumptions as completed work.
- Do not duplicate tasks already implemented; link to the commit/evidence and reopen only when the current baseline proves a regression.
- When a task changes status, update the roadmap/checklist and readiness matrix in the same documentation change where practical.
- If current code conflicts with a document, inspect the code and update the document with a commit reference; do not silently follow stale prose.

## 5. Safe command and deployment documentation

- Commands must match the checked-in scripts, paths and workflow inputs.
- Mark destructive commands and production-impacting actions explicitly; require a separate approval gate.
- Never document real secrets, access tokens, private keys, customer data or generated credentials. Use variable names and safe placeholders only.
- Never instruct operators to bypass failed required checks, TLS/host verification, security scanning or migration validation.
- Include preflight, expected result, failure handling and rollback guidance for operational procedures.
- Keep local-development instructions separate from staging and production.

## 6. Performance claims and measurement

- Label bundle sizes, benchmark values and deployment logs with their commit, environment and measurement type.
- Distinguish build-time artifact size from browser performance and service-side response time.
- Use p50/p95/p99, throughput, error rate and saturation together; an average alone is not sufficient.
- For database claims, include query plans, data scale, indexes, lock behaviour and the database engine used.
- For pool sizing, state pods × workers × per-process cap and reserve capacity for migrations/operations.
- Preserve financial correctness, tenant isolation, idempotency, stock integrity and audit semantics in every performance change.

## 7. Review checklist for documentation PRs

- [ ] Links and paths resolve in the target branch.
- [ ] Version, branch, commit and date are accurate.
- [ ] No stale command sequence remains presented as current.
- [ ] Implemented work is separated from unverified work.
- [ ] Current limitations and blocked dependencies are explicit.
- [ ] No secret or personal data is present.
- [ ] Roadmap, tracker and readiness matrix do not contradict each other.
- [ ] Exact-commit CI and any required review gates are recorded after the documentation change.
