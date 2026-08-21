# ERP03 Production Deployment Guide

## Enterprise Production Operations

This document defines production-grade deployment and operations for ERP03.

## Quick Start

```bash
# Development environment
make dev

# Run all tests
make test

# Production deployment
make prod

# Check health
make health
```

## Available Commands

| Command | Description |
|---------|-------------|
| `make help` | Show available targets |
| `make dev` | Start development environment (PostgreSQL, Redis, Ollama) |
| `make prod` | Start production stack |
| `make test` | Run all 204 tests with coverage |
| `make migrate` | Run database migrations |
| `make backup` | Create database backup |
| `make health` | Verify system health |
| `make stop` | Stop all services |
| `make clean` | Remove build artifacts |

## Database Operations

### Run Migrations
```bash
make migrate
```

### Create Backup
```bash
make backup
# Creates: ./backups/erpdb-YYYYMMDD-HHMMSS.sql
```

### Restore from Backup
```bash
docker exec erp03-postgres psql -U erpuser -d erpdb < ./backups/erpdb-20250101-120000.sql
```

## Production Checklist

- [ ] Set strong SECRET_KEY and JWT_SECRET_KEY in .env
- [ ] Configure DATABASE_URL for production PostgreSQL
- [ ] Enable SSL/TLS termination (nginx or load balancer)
- [ ] Configure firewall (ports 22, 80, 443 only)
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Test backup/restore procedure
- [ ] Document rollback procedure

## Environment Variables (Production)

```bash
# Security
SECRET_KEY=<64-char-random>
JWT_SECRET_KEY=<64-char-random>

# Database
DATABASE_URL=postgresql://user:pass@host:5432/erpprod

# Redis
REDIS_URL=redis://host:6379/0

# CORS
ALLOWED_ORIGINS=https://your-domain.com
```

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
# Returns: {"status": "healthy"}
```

### View Logs
```bash
docker compose logs -f
docker compose logs -f erp-backend
docker compose logs -f postgres
```

## Security Hardening

1. **Never commit .env files**
2. **Use strong random keys** (openssl rand -hex 32)
3. **Enable firewall**: ufw default deny && ufw allow 22,80,443/tcp
4. **SSL/TLS required** for all external traffic
5. **Regular backups** with off-site storage
6. **Monitor failed login attempts**

## Compliance

ERP03 supports:
- FDA 21 CFR Part 11 (electronic records/signatures)
- SOC 2 Type II controls
- GDPR data protection requirements
- Audit trail for all regulated operations

## Troubleshooting

**Tests failing**: `make clean && make test`

**Database connection error**: Check DATABASE_URL format

**Migration errors**: `docker compose down -v && make dev`

**High memory usage**: `docker stats`

---

For detailed documentation see /docs directory.
