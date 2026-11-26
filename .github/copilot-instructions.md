# ERP03 Copilot Instructions

AGENTS.md is authoritative. This file adds navigation and agent-specific reminders; it does not replace, restate, or create a second project contract. Read AGENTS.md before changing code.

## Required completion workflow

Run these commands, in order, from the repository root:

```bash
bash scripts/agent/bootstrap.sh
bash scripts/agent/verify.sh
```

The second command is the only completion gate. Do not substitute standalone pytest, Ruff, frontend-build, or hand-written command sequences for it. Those commands may be used only to diagnose a failure, not to declare completion.

A task is complete only when verification exits successfully and prints `RESULT PASS`. Report the exact `.agent/evidence/<stamp>.json` path and quote its `result`, `commit`, and `used_pg` values. A local SQLite fallback can still produce `RESULT PASS`; it does not prove PostgreSQL production-config qualification. CI's `agent-parity.yml` runs the same bootstrap and verify commands with PostgreSQL 15 and Redis 7.

## Repository invariants

- Before changing workflows, run `python scripts/pin-github-actions.py --check`. Every action reference must remain pinned to a full 40-character commit SHA.
- Keep exactly one Alembic head; the current documented head is `0009_invoice_numbering_index`. Review generated migrations before applying them.
- Preserve `Settings.extra == "forbid"`; do not add undeclared backend environment variables.
- Production configuration must reject SQLite.
- Keep `ERP-BACKEND/.env` separate from root `.env.compose`. Never stage or commit `.env*`, `secrets/`, or `.agent/`; these are local/runtime material.

## Navigation

- New API: add the schema under `ERP-BACKEND/app/schemas/`, business logic under `app/services/`, route under `app/api/`, register it in `app/main.py`, and add focused tests.
- New database column: update `app/models/`, generate an Alembic revision, review the migration in `ERP-BACKEND/alembic/versions/`, then validate through the canonical gate.
- Do not assume a `dev` branch exists; use the actual base and PR head refs.

## Version caution

The repository's README, AGENTS.md, and bootstrap script currently disagree about the Vite version. Do not assert or standardize a Vite version in agent guidance until those sources are reconciled in a reviewed change.
