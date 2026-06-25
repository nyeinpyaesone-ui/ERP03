# Production Deployment Guide

## Architecture Overview

```
┌─────────────────────────────────────────┐
│              Load Balancer              │
│         (NGINX / AWS ALB / Cloudflare)   │
└─────────────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───┴───┐   ┌──────┴──────┐  ┌───┴───┐
│ Web   │   │  API        │  │ Web   │
│ (CDN) │   │  (FastAPI)  │  │ (CDN) │
└───┬───┘   └──────┬──────┘  └───┬───┘
    │              │              │
    └──────────────┼──────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───┴───┐   ┌──────┴──────┐  ┌───┴───┐
│Postgre│   │   Redis     │  │Ollama │
│SQL 15 │   │   Cache     │  │ AI    │
└───────┘   └─────────────┘  └───────┘
```

## Deployment Options

### Option 1: Docker Compose (Single Server)

```bash
# 1. Clone repository
git clone https://github.com/nyeinpyaesone-ui/ERP.git
cd ERP

# 2. Create production .env
cp backend/.env.example backend/.env
# Edit: DATABASE_URL, REDIS_URL, SECRET_KEY

# 3. Start production stack
docker-compose -f docker-compose.yml up -d

# 4. Run migrations
docker-compose exec backend alembic upgrade head

# 5. Verify
curl http://localhost:8000/health
```

### Option 2: Kubernetes (Production Scale)

```bash
# 1. Apply manifests
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml
kubectl apply -f infra/k8s/secrets.yaml
kubectl apply -f infra/k8s/postgres.yaml
kubectl apply -f infra/k8s/redis.yaml
kubectl apply -f infra/k8s/backend.yaml
kubectl apply -f infra/k8s/frontend.yaml
kubectl apply -f infra/k8s/ingress.yaml

# 2. Verify
kubectl get pods -n erp_solution
kubectl get svc -n erp_solution
```

### Option 3: GitHub Actions Auto-Deploy

The `.github/workflows/release.yml` automatically:
1. Builds Docker images on version tags (`v*`)
2. Pushes to Docker Hub
3. Can trigger deployment to your server

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://erp:password@postgres:5432/erp_solution
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-256-bit-secret-key
ENVIRONMENT=production
OLLAMA_URL=http://ollama:11434
CORS_ORIGINS=https://yourdomain.com
JWT_EXPIRE_MINUTES=60
```

### Frontend (.env)
```env
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_WS_URL=wss://api.yourdomain.com
REACT_APP_SENTRY_DSN=https://xxx@yyy.ingest.sentry.io/zzz
```

## SSL/TLS Setup

### Let's Encrypt (Free)
```bash
# Using certbot with nginx
certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

### Cloudflare (Recommended)
1. Point DNS to Cloudflare
2. Enable "Full (Strict)" SSL mode
3. Enable Auto Minify, Brotli, HTTP/2

## Monitoring

### Health Checks
- Backend: `GET /health`
- Database: `GET /health/db`
- Redis: `GET /health/redis`

### Prometheus Metrics
- Endpoint: `GET /metrics`
- Metrics: request_count, request_duration, db_connections

### Logging
```python
# Structured logging in production
import structlog
logger = structlog.get_logger()
logger.info("user_login", user_id=123, ip="192.168.1.1")
```

## Backup Strategy

### Database
```bash
# Automated daily backup
pg_dump -h postgres -U erp erp_solution > backup_$(date +%Y%m%d).sql

# Upload to S3
aws s3 cp backup_*.sql s3://your-bucket/backups/
```

### File Storage
- Use S3/MinIO for uploads
- Enable versioning
- Cross-region replication for disaster recovery

## Scaling

### Horizontal Scaling
```yaml
# backend.yaml — scale to 5 replicas
replicas: 5
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Database Scaling
- Read replicas for reporting
- Connection pooling (PgBouncer)
- Partitioning for large tables

## Security Checklist

- [ ] Change default passwords
- [ ] Enable 2FA for all admin accounts
- [ ] Set up WAF (Cloudflare/AWS WAF)
- [ ] Regular security audits
- [ ] Dependency scanning (Snyk/Dependabot)
- [ ] Secrets rotation (monthly)
- [ ] Network segmentation (VPC)
- [ ] Backup encryption
- [ ] DDoS protection
- [ ] Rate limiting enabled

## Troubleshooting

### Common Issues

**Database connection failed**
```bash
# Check PostgreSQL is running
docker-compose ps
# Check logs
docker-compose logs postgres
# Verify credentials
cat backend/.env | grep DATABASE_URL
```

**Frontend can't reach API**
```bash
# Check CORS settings
cat backend/.env | grep CORS
# Verify API is accessible
curl http://localhost:8000/docs
```

**Out of memory**
```bash
# Check memory usage
docker stats
# Increase Docker memory limit
# Or scale down replicas temporarily
```

## Support

- GitHub Issues: https://github.com/nyeinpyaesone-ui/ERP/issues
- Documentation: `/docs` in repository
- API Docs: `https://api.yourdomain.com/docs`
