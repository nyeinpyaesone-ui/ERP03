# Agent Environments

Three targets, one contract. The agent runs two commands everywhere:

```bash
bash scripts/agent/bootstrap.sh
bash scripts/agent/verify.sh
```

Everything environment-specific lives in `scripts/agent/env.sh` and
`scripts/agent/bootstrap.sh`. Never hardcode `apt`, `sudo`, `docker` or `systemd`
in a task.

## Capability matrix

| Capability | Termux → proot Ubuntu arm64 | Codespaces | CI `ubuntu-latest` |
|---|---|---|---|
| `scripts/setup.sh` | yes (inside proot) | yes | yes |
| Python | 3.12 via apt (glibc) | 3.12 feature | 3.12 setup-python |
| aarch64 manylinux wheels | work (glibc, not bionic) | n/a | n/a |
| PostgreSQL | cannot run as root → SQLite | compose service | service container |
| Redis | runs as root | compose, password `erp03` | service, no password |
| Docker | **no** | yes | yes |
| Node 22 + `npm ci` | yes | yes | yes |
| Playwright | not used | not used | not used |

## Termux → proot Ubuntu arm64

```bash
# In Termux (host):
pkg install proot-distro
proot-distro install ubuntu
termux-wake-lock

# Enter the glibc environment as a non-root user:
proot-distro login ubuntu --user builder --shared-tmp
```

Inside proot:

```bash
git clone <repo> ~/ERP03 && cd ~/ERP03
bash scripts/agent/bootstrap.sh
bash scripts/agent/verify.sh
```

Hard rules:

- **Never install Python deps in native Termux.** bionic libc cannot use manylinux
  aarch64 wheels (`asyncpg`, `cryptography`, `argon2-cffi`). `bootstrap.sh` exits 3
  there on purpose.
- **Never run PostgreSQL as root.** Root is the proot default; use `--user`, or let
  the suite run on SQLite (it is fully green there).
- Keep the clone under `$HOME`. `/sdcard` is FUSE and breaks permissions/inotify.
- `termux-wake-lock` runs in the Termux session, **before** `proot-distro login`.
- Bind `127.0.0.1`, not `localhost`.
- Docker is unavailable: compose/image gates report `[SKIP] docker reason=no-daemon`.

## GitHub Codespaces

The existing devcontainer compose stack already provides PostgreSQL 15 and Redis.
`bootstrap.sh` must not start them again.

- `AGENT_ENV=codespace` is injected by `containerEnv`.
- Ports auto-forward: `3000, 5173, 8000, 5432, 6379`.
- If the org offers an arm64 machine type, the same scripts apply unchanged.

## GitHub Actions

- The only place with guaranteed Docker and multi-arch builds.
- `AGENT_ENV=ci` plus `DATABASE_URL` on `127.0.0.1` so `qualify.sh` finds PostgreSQL.
- Redis divergence is intentional: devcontainer uses `--requirepass erp03`; GitHub
  service containers cannot pass redis arguments, so CI uses no password. Do not
  "fix" it by adding a password to `REDIS_URL` alone.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `no matching distribution` for `asyncpg` | native Termux (bionic) | enter proot, rerun bootstrap |
| `Cannot find module @rollup/rollup-linux-arm64-gnu` | lockfile regenerated on another platform | `cd frontend && rm -rf node_modules && npm ci --include=optional` |
| Vite `Bus error` / OOM | low memory | `NODE_OPTIONS=--max-old-space-size=512` |
| `[SKIP] postgres reason=sqlite-fallback` | no reachable PG | expected in proot; run `--user` PG if needed |
| `postgres: cannot be run as root` | proot default user | `proot-distro login ubuntu --user builder` |
| verify exits 3 | native Termux guard | enter proot |
