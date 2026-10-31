# PR Merge Order

## Priority 1 – Security & Infra hygiene
1. #170 – env credentials rotation / security hardening. Merge after verifying secrets are rotated.
2. #191-#196 – Dependabot patches for backend/frontend. Merge after CI green on ubuntu-latest.

## Priority 2 – CI/CD & Quality
3. #229, #228 – workflow reliability improvements. Merge after path filter changes land.
4. #220 – CI optimization.

## Priority 3 – Features
5. #196 – Inventory feature tests. Gate with qualification run.
6. #195, #194, #193, #192 – feature PRs. Merge only after code quality PASS in CI.

## Priority 4 – Documentation
7. #125 – inventory docs. Merge after feature is qualified.

## Notes
- Do not merge #219 as qualified until live qualification evidence exists.
- Close issues #224, #226 after CI runs succeed on ubuntu-latest.
- Issue #223 idempotency payload handling implemented in main.
