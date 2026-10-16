# ERP03 Release Process

## Versioning

Semantic Versioning: `MAJOR.MINOR.PATCH`, prefixed with `v`.

- **MAJOR** — breaking API or data-model change, or a migration that cannot be
  rolled back without data loss.
- **MINOR** — backwards-compatible capability (new endpoint, new field, new
  migration that is additive).
- **PATCH** — backwards-compatible fix (bug, security, performance).

Release candidates append `-rc.N` (`v1.4.0-rc.1`). The `Release` workflow
rejects any tag that does not match `vMAJOR.MINOR.PATCH(-rc.N)?`.

## What may be released

Only a commit whose gates have already run and passed:

1. CI (backend tests + coverage gate, frontend build)
2. Quality (ruff lint/format, eslint, prettier, shellcheck)
3. Security (secret scan, dependency audit, CodeQL)
4. Container (build + Trivy image scan, push to GHCR on `main`)
5. Infrastructure Validation (terraform fmt/validate/plan, kustomize builds)
6. ERP03 Qualification (`scripts/qualify.sh`)

The `Release` workflow re-checks the most recent completed run for the commit
and refuses to tag anything that did not conclude `success`.

## Cutting a candidate

```bash
# 1. Pick the commit that is green on main.
gh run list --branch main --limit 5

# 2. Dispatch the release workflow with an rc version.
gh workflow run release.yml -f version=v1.4.0-rc.1
```

Candidates are published as GitHub pre-releases. They are deployable to
staging via `Deploy Staging` by passing the commit SHA.

## Promoting to production

Promotion re-tags the *same* image digests that staging validated — the
production workflow never rebuilds.

1. Deploy and smoke-test the candidate in staging (`Deploy Staging`).
2. Complete staging sign-off: smoke results, transaction integrity, and any
   migration verification.
3. Dispatch `Deploy Production` with the staging-validated SHA and a migration
   note. The protected `production` environment requires reviewer approval.
4. The workflow verifies the candidate's gates, runs Alembic migrations,
   applies the production overlay with pinned digests, and smoke-tests.

Record the digests from the workflow summary in the release notes built from
`RELEASE_NOTES_TEMPLATE.md`.

## Hotfix path for production issues

1. Branch `fix/<short-description>` from the commit currently running in
   production (not from `main`) — see `CONTRIBUTING.md` for branch naming.
2. Make the smallest change that resolves the incident. No refactors.
3. Open a pull request. CI, Quality, Security, Container and Qualification
   must all pass — a hotfix has no exemption from the gates.
4. Deploy the branch build to staging, verify the incident scenario is fixed.
5. Run `Rollback` first if production is actively failing; a hotfix is not a
   substitute for rollback.
6. Merge to `main`, tag a `PATCH` release, promote, and close the incident
   with evidence in the incident record.

## Rollback

Rollback is a workflow, not an improvisation: `Rollback` pins the last known
good digest (preferred) or performs `kubectl rollout undo`. Database schema is
never downgraded automatically — see `ROLLBACK_RUNBOOK.md`.
