# Runtime secrets

This directory is intentionally **not** a source of truth for credentials.

Create these files locally or provision them through your deployment secret manager:

- `db_user.txt` — PostgreSQL username
- `db_password.txt` — PostgreSQL password
- `jwt_secret.txt` — random application signing secret, minimum 32 characters

The files are ignored by Git. Never commit real values.

For production Kubernetes deployments, use a native `Secret`, External Secrets Operator, or a managed secret store instead of mounting files from the repository.
