# Agent Workflow

## Loop

1. **Detect** — `source scripts/agent/env.sh && agent_detect; echo "$AGENT_ENV_NAME"`
2. **Bootstrap** — `bash scripts/agent/bootstrap.sh` (idempotent; safe to re-run)
3. **Work** — small, reversible edits
4. **Verify** — `bash scripts/agent/verify.sh`
5. **Evidence** — quote `.agent/evidence/<stamp>.json` and the `RESULT` line
6. **Commit** — conventional commit, one logical change, clean `git status`

## Completion contract

A task is not complete without:

```text
[PASS] ruff
[PASS] compile
[PASS] migrate
[PASS] tests
[PASS] frontend
EVIDENCE .agent/evidence/<stamp>.json
RESULT PASS
```

`[SKIP] <step> reason=<why>` is allowed and must be quoted verbatim.
Never write "should work", "probably", or "tests likely pass".

## Commands

| Purpose | Command |
|---|---|
| everything | `bash scripts/agent/verify.sh` |
| one test | `cd ERP-BACKEND && ../.venv/bin/pytest tests/test_api.py -k name -q` |
| migrations | `cd ERP-BACKEND && ../.venv/bin/alembic heads` |
| frontend build | `./scripts/build-frontend.sh` (from repo root) |

## Boundaries

- Do not edit `.env`, `secrets/`, or `.agent/`.
- Do not add dependencies to make a gate pass.
- Do not disable a gate (`|| true`, `continue-on-error`, `# noqa`) to go green.
- Do not run two verification gates; `scripts/verify.sh` delegates to `verify.sh`.
