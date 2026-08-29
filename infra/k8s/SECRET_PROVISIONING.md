# Kubernetes secret contract

Production manifests intentionally do **not** include credentials. Create a Secret named `erp_solution-secrets` in namespace `erp_solution` using a managed secret system (External Secrets Operator, AWS Secrets Manager, Vault, etc.).

Required keys:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `SECRET_KEY` (minimum 32 random characters)
- `REDIS_PASSWORD`
- `REDIS_URL` (for example `redis://:<password>@erp_solution-redis:6379/0`)

The same Secret is consumed by the API, worker, PostgreSQL, and Redis workloads.

Do not commit the resulting Secret manifest or generated values. The legacy `infra/k8s/base/secrets.yaml` is not referenced by the production Kustomization and must not be applied to a production cluster.
