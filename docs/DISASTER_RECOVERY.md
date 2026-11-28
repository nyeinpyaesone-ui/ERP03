# ERP03 Disaster Recovery Runbook

**RPO:** 24 hours (daily automated backups)
**RTO:** 4 hours (full service restoration)

## 1. Backup Strategy

- Database: Daily `scripts/backup.sh` using pg_dump, compressed with gzip, SHA-256 checksummed
- Redis: Point-in-time snapshots via BGSAVE, plus AOF persistence
- Configuration: `.env.compose` and secrets in GitHub Secrets
- Application code: Git repository (version-controlled)

Backups are scheduled via systemd timer (`erp03-backup.timer`) running daily at 02:00 UTC,
or via cron as an alternative.

## 2. Restore Procedures

### PostgreSQL

```bash
# List available backups
ls -la /data/backups/

# Verify a backup before restoring
./scripts/restore.sh /data/backups/erp03-20260101T020000Z.sql.gz --verify-only

# Restore from backup
./scripts/restore.sh /data/backups/erp03-20260101T020000Z.sql.gz
```

### Redis

```bash
# Copy the RDB snapshot to the Redis data directory
cp /tmp/restore/dump.rdb /var/lib/redis/data/

# Restart Redis to load the snapshot
docker compose restart redis
# or:
kubectl rollout restart deployment/erp03-redis -n erp03
```

### Full Environment Restoration

1. Provision infrastructure (`terraform apply`)
2. Apply Kubernetes manifests (`kubectl apply -k infra/kubernetes/overlays/production`)
3. Run migrations (`alembic upgrade head`)
4. Restore database (Section 2 - PostgreSQL)
5. Restore Redis (Section 2 - Redis)
6. Restart services (`docker compose up -d`)
7. Verify health (`./scripts/doctor.sh`)

## 3. Failover Steps

### Primary Region Failure

1. Point DNS to secondary region ingress
2. Scale backend/frontend HPA (`kubectl scale hpa erp03-backend-hpa -n erp03 --replicas=10`)
3. Verify `GET /api/v1/healthz` returns 200

### Database Failure

1. Promote read replica to primary
2. Update `DATABASE_URL` to point to the new primary
3. Restart backend pods (`kubectl rollout restart deployment/erp03-backend -n erp03`)

### Redis Failure

1. Fail over to Redis replica if configured
2. Restart Redis from latest RDB snapshot
3. Restart backend pods to re-establish connections

## 4. Testing Schedule

| Test | Frequency | Description |
|------|-----------|-------------|
| Health check verification | Weekly | Verify `GET /api/v1/healthz` returns 200 |
| Backup restoration test | Monthly | Restore latest backup to scratch database and verify |
| Full DR drill | Quarterly | Complete environment restoration and failover test |

## 5. Emergency Contacts

- On-call engineer: via PagerDuty / Slack #alerts
- Infrastructure: infrastructure@erp.example.com
- Database admin: dba@erp.example.com
