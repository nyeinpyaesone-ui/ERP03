# ERP03 Qualification Contract

This contract makes the database used by qualification explicit. A green result must not be interpreted as proof of PostgreSQL behavior unless the evidence records a successful PostgreSQL connection.

## Modes

| Mode | Selection | PostgreSQL unavailable | Intended use |
|---|---|---|---|
| `auto` (default) | Prefer PostgreSQL; otherwise use SQLite | Falls back to SQLite and records `used_pg=false` | Developer machines and Termux/PRoot |
| `required` | PostgreSQL only | Fails closed; no SQLite fallback | GitHub Actions, release qualification, production-like validation |
| `sqlite` | SQLite only | Not applicable | Fast local feedback; never PostgreSQL evidence |

Set the mode with `QUALIFY_DB_MODE`.

## Commands

Local environment with automatic detection:

```bash
bash scripts/agent/bootstrap.sh
QUALIFY_DB_MODE=auto bash scripts/agent/verify.sh
```

Explicit local SQLite run:

```bash
QUALIFY_DB_MODE=sqlite bash scripts/agent/verify.sh
```

Strict PostgreSQL qualification:

```bash
QUALIFY_DB_MODE=required \
DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@HOST:5432/erp03' \
bash scripts/agent/verify.sh
```

Do not place credentials in committed files or shell history. Supply CI credentials through the platform's protected environment/secrets when non-ephemeral credentials are required. The current GitHub Actions service database uses ephemeral job-local credentials.

## Evidence contract

`scripts/qualify.sh --json-out PATH` writes the selected `db_mode`, `used_pg`, completed steps, current step, and final result.

- `db_mode=required` and `used_pg=false` is a failure.
- `db_mode=auto` and `used_pg=false` means local SQLite fallback, not PostgreSQL qualification.
- A PostgreSQL pass requires a successful authenticated connection and `SELECT 1`.
- A skipped Docker daemon is an environment capability note; it is not a Docker build or release pass.
- The Agent Parity workflow sets `QUALIFY_DB_MODE=required`; it cannot silently qualify on SQLite.

## Release interpretation

A local `RESULT PASS` under `auto` or `sqlite` validates the checks that actually ran in that environment. It does not replace PostgreSQL integration, container, multi-architecture, signing, staging, rollback, or production runtime evidence. Release readiness must be based on those separate gates and their retained artifacts.
