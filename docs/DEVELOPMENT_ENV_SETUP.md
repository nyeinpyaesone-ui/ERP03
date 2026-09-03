# ERP erp03 - Development Environment Setup Guide

Complete guide for setting up and running the ERP erp03 development environment.

## Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd erp03

# 2. Copy environment files
cp .env.example .env.dev
cp .env.production.example .env.production

# 3. Generate secure secrets (for production)
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env.production
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))" >> .env.production

# 4. Create secret files
mkdir -p secrets
echo "erp_user" > secrets/db_user.txt
echo "secure_password_here" > secrets/db_password.txt
echo "jwt_secret_key_here" > secrets/jwt_secret.txt

# 5. Start development environment
docker-compose -f docker-compose.dev.yml up -d

# 6. Verify services
docker-compose -f docker-compose.dev.yml ps
```

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Database server |
| Redis | 6379 | Cache & message broker |
| Backend API | 8000 | FastAPI application |
| Celery Worker | - | Background task processor |
| Flower | 5555 | Celery monitoring dashboard |
| Frontend | 5173 | Vite + React development server |
| pgAdmin | 5050 | Database management UI |

## Access URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Flower Dashboard**: http://localhost:5555 (admin/dev_flower_password)
- **pgAdmin**: http://localhost:5050 (admin@erp03.dev/admin)

## Configuration Files

### Environment Variables

#### `.env.dev` (Development)
Contains all configuration for local development with sensible defaults.

**Key variables to customize:**
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` - Database credentials
- `SECRET_KEY`, `JWT_SECRET` - Security keys (generate unique values)
- `CORS_ORIGINS` - Allowed origins for frontend
- `CELERY_CONCURRENCY` - Number of worker processes

#### `.env.production` (Production)
Secure configuration for production deployment.

**Critical settings:**
- Change all default passwords
- Use strong, randomly generated secrets
- Set `ENVIRONMENT=production`
- Set `DEBUG=false`

### Docker Compose Files

#### `docker-compose.dev.yml`
Optimized for development with:
- Hot-reload enabled
- Debug logging
- Volume mounts for code changes
- Developer tools (pgAdmin, Flower)

#### `docker-compose.yml`
Production-ready configuration with:
- Resource limits
- Health checks
- Internal networking
- Secret management

#### `docker-compose.prod.yml`
Additional production overrides for scaling and optimization.

## Building Docker Images

### Local Build (Development)

```bash
# Build all services
docker-compose -f docker-compose.dev.yml build

# Build specific service
docker-compose -f docker-compose.dev.yml build api
```

### Production Build & Push to GHCR

```bash
# Using automated script
chmod +x scripts/build-push-ghcr.sh
./scripts/build-push-ghcr.sh v1.0.0

# Manual build
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/YOUR_USERNAME/erp03-backend:latest \
  --push ./ERP-BACKEND
```

See [GHCR_SETUP_GUIDE.md](docs/GHCR_SETUP_GUIDE.md) for detailed instructions.

## Common Operations

### Start Services

```bash
# All services
docker-compose -f docker-compose.dev.yml up -d

# Specific services only
docker-compose -f docker-compose.dev.yml up -d api redis db

# With logs visible
docker-compose -f docker-compose.dev.yml up
```

### Stop Services

```bash
# Stop all
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (⚠️ deletes data)
docker-compose -f docker-compose.dev.yml down -v
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f api

# Last 100 lines
docker-compose -f docker-compose.dev.yml logs --tail=100 api
```

### Execute Commands in Containers

```bash
# Backend shell
docker-compose -f docker-compose.dev.yml exec api bash

# Database shell
docker-compose -f docker-compose.dev.yml exec db psql -U erp_dev -d erp03_dev

# Run migrations manually
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head

# Run tests
docker-compose -f docker-compose.dev.yml exec api pytest tests/ -v
```

### Database Management

```bash
# Backup database
docker-compose -f docker-compose.dev.yml exec db pg_dump -U erp_dev erp03_dev > backup.sql

# Restore database
docker-compose -f docker-compose.dev.yml exec -T db psql -U erp_dev -d erp03_dev < backup.sql

# Reset database (⚠️ deletes all data)
docker-compose -f docker-compose.dev.yml down -v
docker volume rm erp03_postgres_dev_data
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.dev.yml
```

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.dev.yml logs <service-name>

# Inspect container
docker inspect <container-id>

# Remove and recreate
docker-compose -f docker-compose.dev.yml rm -f <service-name>
docker-compose -f docker-compose.dev.yml up -d <service-name>
```

### Database Connection Issues

```bash
# Verify database is healthy
docker-compose -f docker-compose.dev.yml ps db

# Test connection
docker-compose -f docker-compose.dev.yml exec db pg_isready -U erp_dev

# Check credentials match in .env.dev
```

### Frontend Not Loading

```bash
# Rebuild frontend
docker-compose -f docker-compose.dev.yml build frontend

# Clear browser cache
# Hard refresh: Ctrl+Shift+R (Chrome) or Cmd+Shift+R (Mac)

# Check API URL in vite.config.ts matches backend
```

### Celery Worker Not Processing Tasks

```bash
# Check worker logs
docker-compose -f docker-compose.dev.yml logs -f worker

# Verify Redis connection
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping

# Restart worker
docker-compose -f docker-compose.dev.yml restart worker
```

## Performance Optimization

### Increase Resource Limits

Edit `docker-compose.dev.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 4G
```

### Enable Caching

```bash
# Redis is already configured as cache
# Verify it's working:
docker-compose -f docker-compose.dev.yml exec redis redis-cli INFO memory
```

### Database Indexing

Run migration to add indexes:
```bash
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head
```

## Security Checklist

Before deploying to production:

- [ ] Change all default passwords
- [ ] Generate unique SECRET_KEY and JWT_SECRET
- [ ] Set `DEBUG=false`
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure HTTPS/TLS
- [ ] Enable firewall rules
- [ ] Review CORS settings
- [ ] Set up proper backup strategy
- [ ] Configure log rotation
- [ ] Enable monitoring and alerting

## Additional Resources

- [GHCR Setup Guide](docs/GHCR_SETUP_GUIDE.md) - Container registry configuration
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Support

For issues or questions:
- Check existing GitHub issues
- Review logs carefully
- Open a new issue with detailed information
