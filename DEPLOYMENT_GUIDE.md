# ERP03 Deployment Guide

## Overview
This guide covers the complete deployment process for ERP03, including artifact validation, environment resolution, package structure repair, image building, infrastructure startup, migration application, seed data loading, health verification, and atomic rollback procedures.

## Prerequisites

### System Requirements
- Docker 24.0+
- Docker Compose 2.20+
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7.0+

### Required Secrets
Set up the following GitHub secrets or environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: Secret for JWT token generation
- `STRIPE_SECRET_KEY`: Stripe API key (for e-commerce)
- `OPENAI_API_KEY`: OpenAI API key (for AI backend)

See [GITHUB_SECRETS.md](./docs/GITHUB_SECRETS.md) for detailed setup.

## Deployment Steps

### 1. Artifact Validation

Verify all required artifacts exist and are valid:

```bash
./scripts/validate_artifacts.sh
```

This checks:
- ✅ Dockerfile existence and syntax
- ✅ requirements.txt / package.json validity
- ✅ Migration files presence
- ✅ Environment template files
- ✅ Health check scripts

### 2. Environment Resolution

Create environment configuration files:

```bash
# ERP Backend
cp ERP-BACKEND/.env.example ERP-BACKEND/.env

# AI Backend
cp AI-BACKEND/.env.example AI-BACKEND/.env

# Infrastructure
cp .env.example .env
```

Edit each `.env` file with production values or use secret management.

### 3. Package Structure Repair

Fix any structural issues before deployment:

```bash
./scripts/repair_structure.sh
```

This ensures:
- ✅ Correct directory structure
- ✅ Missing __init__.py files created
- ✅ Symlinks resolved
- ✅ File permissions set correctly

### 4. Image Building

Build Docker images for all services:

```bash
# Development build
docker-compose build

# Production build (optimized)
docker-compose -f docker-compose.prod.yml build

# Build specific service
docker-compose build erp-backend
```

### 5. Infrastructure Startup

Start all services:

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# Specific services only
docker-compose up -d postgres redis erp-backend
```

Verify services are running:
```bash
docker-compose ps
```

### 6. Migration Application

Apply database migrations:

```bash
# Check migration status
docker-compose exec erp-backend alembic current

# Apply all migrations
docker-compose exec erp-backend alembic upgrade head

# Migrate to specific version
docker-compose exec erp-backend alembic upgrade <revision_id>

# Rollback one migration
docker-compose exec erp-backend alembic downgrade -1
```

### 7. Seed Data Loading

Load initial data into the database:

```bash
# Load seed data
docker-compose exec erp-backend python scripts/seed_data.py

# Load specific dataset
docker-compose exec erp-backend python scripts/seed_data.py --users
docker-compose exec erp-backend python scripts/seed_data.py --products
```

Default admin credentials (change immediately):
- **Email**: admin@erp03.com
- **Password**: Admin123!

### 8. Health Verification

Run comprehensive health checks:

```bash
./scripts/health_check.sh
```

Manual checks:
```bash
# ERP Backend
curl http://localhost:8000/api/v1/health

# AI Backend
curl http://localhost:8001/api/v1/health

# Frontend (if deployed)
curl http://localhost:3000

# Database
docker-compose exec postgres psql -U erpuser -d erpdb -c "SELECT 1"

# Redis
docker-compose exec redis redis-cli ping
```

Expected responses:
- Backend: `{"status": "healthy", "database": "connected", "redis": "connected"}`
- Redis: `PONG`
- Database: `?column? = 1`

### 9. Atomic Rollback on Failure

If deployment fails, execute atomic rollback:

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Rollback database to previous migration
docker-compose exec erp-backend alembic downgrade <previous_revision>

# Restore from backup (if needed)
./scripts/restore_backup.sh <backup_timestamp>

# Restart with previous image version
docker-compose -f docker-compose.prod.yml up -d
```

#### Rollback Procedures

**Database Rollback:**
```bash
# View migration history
docker-compose exec erp-backend alembic history

# Rollback to specific version
docker-compose exec erp-backend alembic downgrade <revision_id>

# Rollback all migrations
docker-compose exec erp-backend alembic downgrade base
```

**Service Rollback:**
```bash
# Rebuild with previous tag
docker-compose -f docker-compose.prod.yml build --no-cache

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

**Full System Rollback:**
```bash
./scripts/rollback.sh <deployment_id>
```

## Monitoring & Maintenance

### Log Access
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f erp-backend

# Last 100 lines
docker-compose logs --tail=100 erp-backend
```

### Database Backup
```bash
./scripts/backup_database.sh
```

### Service Restart
```bash
# Single service
docker-compose restart erp-backend

# All services
docker-compose restart
```

### Resource Monitoring
```bash
docker stats
docker-compose top
```

## Troubleshooting

### Common Issues

**Migration Failures:**
```bash
# Check current version
docker-compose exec erp-backend alembic current

# Stamp to specific version (if inconsistent)
docker-compose exec erp-backend alembic stamp <revision_id>

# Retry migration
docker-compose exec erp-backend alembic upgrade head
```

**Connection Issues:**
```bash
# Check network
docker-compose network ls

# Inspect container
docker-compose exec erp-backend env

# Test database connection
docker-compose exec erp-backend python -c "from app.core.database import SessionLocal; SessionLocal().close(); print('OK')"
```

**Port Conflicts:**
```bash
# Check port usage
netstat -tlnp | grep :8000

# Change port in docker-compose.yml
# Then restart
docker-compose down && docker-compose up -d
```

## Security Considerations

1. **Never commit `.env` files** - Always use `.env.example` as template
2. **Rotate secrets regularly** - Especially JWT_SECRET_KEY
3. **Use HTTPS in production** - Configure reverse proxy (nginx/traefik)
4. **Enable firewall** - Restrict access to necessary ports only
5. **Regular backups** - Automated daily database backups
6. **Monitor logs** - Set up alerting for errors and anomalies

## Next Steps

After successful deployment:
1. Change default admin password
2. Configure SSL/TLS certificates
3. Set up monitoring and alerting
4. Configure automated backups
5. Document custom configurations
6. Train operations team

## Support

For issues and questions:
- Check [FAQ.md](./docs/FAQ.md)
- Review [API_SUMMARY.md](./docs/API_SUMMARY.md)
- See [ARCHITECTURE_DECISIONS.md](./docs/ARCHITECTURE_DECISIONS.md)
- Contact: support@erp03.com
