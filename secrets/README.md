# Runtime secrets

Production secret files are intentionally not committed.

Create on the deployment host:

- `secrets/postgres_password.txt` — PostgreSQL password only.
- `secrets/database_url.txt` — complete SQLAlchemy PostgreSQL URL using the same database credentials.
- `secrets/secret_key.txt` — application signing key, minimum 32 characters; generate with `openssl rand -hex 32` or stronger.

Production startup:

```bash
docker compose -f docker-compose.yml -f compose.production.yml up -d --build
```

The production overlay removes development bind mounts/reload mode, does not publish PostgreSQL directly, and injects `DATABASE_URL` and `SECRET_KEY` through Docker secrets.

Never commit real credentials, `.env`, or files under `secrets/`.
