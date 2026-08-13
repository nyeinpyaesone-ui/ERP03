# Runtime secrets

Production secret files are intentionally not committed. Create these files on the deployment host or provide equivalent CI/CD secret injection:

- `postgres_password.txt`
- `database_url.txt`
- `secret_key.txt`

Never commit real credentials. Keep `secrets/*` ignored by Git.
