# ERP03 — Current Engineering Status

> **Verified:** 2026-08-16  
> **Branch:** `main`  
> **Release status:** NOT RELEASED / NOT PRODUCTION-QUALIFIED

This file replaces the obsolete v1.0.0 completion checklist. The previous checklist described a different repository layout, referenced a nonexistent CI workflow/tag, and claimed production readiness without current evidence.

## M0 — Architecture Boundary

- [x] `ERP-BACKEND/` is the active ERP runtime root.
- [x] `AI-BACKEND/` is the dedicated AI ownership boundary.
- [x] `INTEGRATION/` is the ERP ↔ AI contract boundary.
- [x] `INFRASTRUCTURE/` is the runtime/platform boundary.
- [x] Former in-process AI runtime removed from ERP startup.
- [x] Superseded backend generations removed from active `main`.
- [x] Historical source remains recoverable through Git history/archive.
- [x] Root Compose/build/release references use `ERP-BACKEND/`.

**M0 status: COMPLETE**

## M1 — ERP Core Stabilization

- [ ] Critical route/module inventory completed.
- [ ] Business/use-case boundaries reviewed.
- [ ] Critical transaction tests complete.
- [ ] Authorization tests complete.
- [ ] Idempotency/duplicate-command tests complete.
- [ ] Rollback/transaction tests complete.
- [ ] Alembic clean-install migration verified.
- [ ] Upgrade migration verified.
- [ ] Audit/correlation behavior verified.
- [ ] ERP can qualify independently of AI.

**M1 status: NEXT / BLOCKING**

## M2 — Integration Contract Layer

- [ ] Versioned ERP query contracts.
- [ ] Versioned ERP command contracts.
- [ ] Versioned event envelopes where required.
- [ ] Shared schema validation.
- [ ] Service-to-service authentication.
- [ ] Timeout/retry/idempotency policy.
- [ ] Contract test suite.
- [ ] No ORM/model sharing across boundaries.

**M2 status: PLANNED**

## M3 — AI Runtime MVP

- [ ] AI API implementation.
- [ ] Orchestrator implementation.
- [ ] Agent/tool allow-listing.
- [ ] Model adapter implementation.
- [ ] Derived memory implementation.
- [ ] AI policy/approval enforcement.
- [ ] AI event handling where required.
- [ ] AI has no ERP database access.

**M3 status: PLANNED**

## M4 — End-to-End Qualification

- [ ] ERP read → AI reasoning → authorized ERP command path tested.
- [ ] Unauthorized AI command rejected.
- [ ] Duplicate/retry behavior verified.
- [ ] Timeout/failure behavior verified.
- [ ] ERP rollback verified.
- [ ] Audit evidence verified.
- [ ] Data-exposure tests verified.
- [ ] Critical workflow smoke/E2E suite passes.

**M4 status: PLANNED**

## M5 — Production Qualification

- [ ] CI checks pass on release candidate.
- [ ] Security checks pass.
- [ ] Backend/frontend images build reproducibly.
- [ ] Immutable release image digests recorded.
- [ ] Secrets externalized.
- [ ] Production configuration validated.
- [ ] Staging deployment verified.
- [ ] Backup/restore drill completed.
- [ ] Migration recovery procedure tested.
- [ ] Logs/metrics/traces verified.
- [ ] Rollback procedure tested.

**M5 status: PLANNED**

## M6 — v1.0 Release

- [ ] M1 exit gate complete.
- [ ] M2 exit gate complete.
- [ ] M3 exit gate complete if AI is included in v1.0.
- [ ] M4 exit gate complete.
- [ ] M5 exit gate complete.
- [ ] Release notes reflect actual implementation.
- [ ] Release tag created.
- [ ] Approved deployment artifact/digest recorded.

**M6 status: GATED / FUTURE**

## Current repository evidence

- Default branch: `main`.
- Latest architecture documentation work is on `main`.
- GitHub currently reports **no status checks** for the latest architecture documentation commit; CI success must therefore not be claimed until an actual workflow run is observed.
- Repository currently has **no Git tags**.
- Active workflow files currently include `docker-image.yml`, `release.yml`, and `security.yml`; there is no current `.github/workflows/ci.yml` matching the old checklist.
- The release workflow builds the frontend from `ERP-BACKEND/frontend-react` and the backend from `ERP-BACKEND`, with staging and production environment gates.
- `AI-BACKEND/` currently contains architectural directories and documentation; it is not yet a qualified production AI service.

## Source of truth

- Architecture: `docs/architecture/BOUNDARIES.md`
- Roadmap: `ROADMAP.md`
- Executable project plan: `docs/PROJECT_PLAN.md`
- Repository overview: `README.md`

## Rule

**Do not mark a checkbox complete because the file or directory exists. Mark it complete only after its stated acceptance evidence exists.**
