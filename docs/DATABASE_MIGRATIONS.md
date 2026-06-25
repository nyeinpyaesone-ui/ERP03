# Database Migration Guide

## Using Alembic

### Create a new migration
```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "add inventory forecasting table"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback one migration
```bash
alembic downgrade -1
```

### View migration history
```bash
alembic history --verbose
```

## Migration Best Practices
1. Always test migrations on a copy of production data
2. Never modify existing migrations after they've been applied
3. Include both `upgrade()` and `downgrade()` functions
4. Add data migrations separately from schema migrations

## Docker Migration
```bash
docker-compose exec backend alembic upgrade head
```
