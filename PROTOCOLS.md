# ERP03 Required Protocols — Branch Protection & Status Checks

Configure these settings in GitHub: Settings → Branches → Add branch protection rule.

## Branch Protection Rule — `main`

| Setting | Value |
|---------|-------|
| Branch name pattern | `main` |
| Require a pull request before merging | **Enabled** |
| Required approving reviews | 1 |
| Dismiss stale pull request approvals when new commits are pushed | **Enabled** |
| Require review from Code Owners | **Enabled** |
| Require status checks to pass before merging | **Enabled** |
| Require branches to be up to date before merging | **Enabled** |
| Restrict pushes to creating matching branches | **Disabled** |
| Do not allow bypassing the above settings | **Enabled** |
| Restrict who can push to matching branches | **Not selected** (all with write access) |
| Allow force pushes | **Disabled** |
| Allow deletions | **Disabled** |

## Required Status Checks

All of the following must pass before a PR can be merged:

| Check | Workflow | Purpose |
|-------|----------|---------|
| CI / backend | `ci.yml` | Backend tests, migrations, compile |
| CI / frontend | `ci.yml` | Frontend build |
| Quality / lint | `quality.yml` | Ruff check + format |
| Quality / frontend | `quality.yml` | Frontend build |
| Security / dependency-audit | `security.yml` | pip-audit vulnerability scan |
| Security / codeql | `security.yml` | CodeQL static analysis |
| Container / build-backend | `container.yml` | Docker image build (backend) |
| Container / build-frontend | `container.yml` | Docker image build (frontend) |

## Required Protocols — API Level

| Protocol | Requirement | Enforced By |
|----------|-------------|-------------|
| Authentication | All mutating endpoints (`POST`, `PUT`, `PATCH`, `DELETE`) require a valid Bearer JWT | `current_claims` dependency |
| Tenant isolation | Cross-tenant reads return 404, never leak foreign business data | `_business_id()` + store scoping |
| Idempotency | Write endpoints accept `X-Idempotency-Key` header; same key + different payload → HTTP 409 | `validate_idempotency_key` + fingerprint check |
| Request ID | Every response includes `X-Request-ID` header | Middleware in `app/main.py` |
| Security headers | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` | Middleware in `app/main.py` |
| CORS | Only configured origins allowed | `CORSMiddleware` with `settings.cors_origin_list` |
| HTTPS in production | Production CORS origins must use HTTPS; localhost origins rejected | `Settings.validate_production_security` |
| Secret key | Production requires SECRET_KEY ≥ 32 chars, not default value | `Settings.validate_production_security` |

## Environment Configuration

Copy `ERP-BACKEND/.env.example` to `ERP-BACKEND/.env` and adjust:

```
ENVIRONMENT=development
SECRET_KEY=<random 32+ byte secret>
DATABASE_URL=postgresql+asyncpg://erp03:erp03@127.0.0.1:5432/erp03
DATABASE_PATH=./.local/erp03.sqlite3
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

Never commit `.env` — it is gitignored.
