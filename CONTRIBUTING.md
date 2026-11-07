# Contributing to ERP03

## Branches
- `feat/<short-description>` for features.
- `fix/<short-description>` for defects and hardening.
- `chore/<short-description>` for maintenance.
- `docs/<short-description>` for documentation-only changes.

## Commits
Use Conventional Commits: `type(scope): imperative summary`.
Examples: `fix(auth): reject weak production secrets`, `ci: add qualification gate`.

## Required before merge
- Relevant tests pass.
- Ruff quality gate passes for backend changes.
- Security/container/IaC gates pass when applicable.
- Database changes include an Alembic migration and rollback/recovery consideration.
- Production-impacting changes include operational evidence or a runbook update.
