# ERP SOLUTION Kubernetes Deployment (v3.1)

## Overview
Production-ready Kubernetes deployment for ERP SOLUTION with auto-scaling, rolling updates, monitoring, and disaster recovery.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Ingress (NGINX)                       │
│  api.erp-domain.com | admin.erp-domain.com | store.erp     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │ API Pods │          │ Web Pods │          │Worker Pods│
   │  (3-20)  │          │  (2-10)  │          │  (2-10)   │
   └────┬────┘          └────┬────┘          └────┬────┘
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │ PostgreSQL│         │  Redis   │          │  S3/EFS  │
   │  (HA)    │          │  (Cache) │          │ (Storage)│
   └─────────┘          └─────────┘          └─────────┘
```

## Prerequisites

- Kubernetes 1.28+
- kubectl configured
- kustomize 5.0+
- Docker with buildx
- Access to container registry (GHCR)
- cert-manager for TLS
- NGINX Ingress Controller
- Prometheus + Grafana (optional)

## Directory Structure

```
k8s/
├── base/                          # Base Kubernetes manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml              # Template - fill in values
│   ├── rbac.yaml
│   ├── network-policy.yaml
│   ├── pvc.yaml
│   ├── postgres.yaml             # PostgreSQL StatefulSet
│   ├── redis.yaml                # Redis StatefulSet
│   ├── api-deployment.yaml       # API server
│   ├── web-deployment.yaml       # Web frontend
│   ├── worker-deployment.yaml    # Background workers
│   ├── ingress.yaml              # Ingress rules
│   └── cronjob.yaml              # Backup jobs
│
├── overlays/
│   ├── development/              # Dev environment
│   ├── staging/                  # Staging environment
│   └── production/               # Production environment
│
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.web
│   ├── Dockerfile.worker
│   └── docker-compose.yml        # Local development
│
├── scripts/
│   ├── deploy.sh                 # Deployment script
│   └── rollback.sh               # Rollback script
│
└── monitoring/
    ├── prometheus.yaml           # ServiceMonitor & Alerts
    └── grafana-dashboard.json    # Grafana dashboard
```

## Quick Start

### 1. Local Development (Docker Compose)

```bash
cd k8s/docker
docker-compose up -d

# Access:
# API: http://localhost:3000
# Web: http://localhost:3001
# PGAdmin: http://localhost:5050
# RedisInsight: http://localhost:5540
```

### 2. Development Environment (Kubernetes)

```bash
# Create namespace and apply manifests
kubectl apply -k overlays/development/

# Verify deployment
kubectl get pods -n erp_solution-dev
kubectl get svc -n erp_solution-dev
kubectl get ingress -n erp_solution-dev

# View logs
kubectl logs -f deployment/dev-erp_solution-api -n erp_solution-dev
```

### 3. Staging Environment

```bash
# Deploy to staging
./scripts/deploy.sh staging v3.0.0-rc1

# Verify
kubectl get pods -n erp_solution-staging
```

### 4. Production Environment

```bash
# Deploy to production (requires confirmation)
./scripts/deploy.sh production v3.0.0

# Monitor rollout
kubectl rollout status deployment/erp_solution-api -n erp_solution
kubectl rollout status deployment/erp_solution-web -n erp_solution
kubectl rollout status deployment/erp_solution-worker -n erp_solution
```

## Configuration

### Secrets

Before deploying, fill in the secrets:

```bash
# Edit secrets template
vim base/secrets.yaml

# Or use kubectl to create secrets
kubectl create secret generic erp_solution-secrets   --from-literal=DB_PASSWORD=$(openssl rand -base64 32)   --from-literal=JWT_SECRET=$(openssl rand -base64 64)   --from-literal=REDIS_PASSWORD=$(openssl rand -base64 32)   --from-literal=AWS_ACCESS_KEY_ID=YOUR_KEY   --from-literal=AWS_SECRET_ACCESS_KEY=YOUR_SECRET   -n erp_solution
```

### TLS Certificates

Using cert-manager:

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@erp-domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Scaling

### Horizontal Pod Autoscaling

```bash
# View current HPA status
kubectl get hpa -n erp_solution

# Manually scale API pods
kubectl scale deployment erp_solution-api --replicas=10 -n erp_solution

# View metrics
kubectl top pods -n erp_solution
```

### Database Scaling

```bash
# Create read replica
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: erp_solution-postgres-replica
  namespace: erp_solution
spec:
  serviceName: erp_solution-postgres-replica
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: erp_solution-postgres-replica
  template:
    metadata:
      labels:
        app.kubernetes.io/name: erp_solution-postgres-replica
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          valueFrom:
            configMapKeyRef:
              name: erp_solution-config
              key: DB_NAME
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: erp_solution-secrets
              key: DB_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: erp_solution-secrets
              key: DB_PASSWORD
        - name: PGDATA
          value: "/var/lib/postgresql/data/pgdata"
        command:
        - /bin/sh
        - -c
        - |
          rm -rf /var/lib/postgresql/data/pgdata/*
          pg_basebackup -h erp_solution-postgres -D /var/lib/postgresql/data/pgdata -U $(POSTGRES_USER) -v -P -W
          echo "standby_mode = 'on'" >> /var/lib/postgresql/data/pgdata/recovery.conf
          echo "primary_conninfo = 'host=erp_solution-postgres port=5432 user=$(POSTGRES_USER) password=$(POSTGRES_PASSWORD)'" >> /var/lib/postgresql/data/pgdata/recovery.conf
          postgres -D /var/lib/postgresql/data/pgdata
EOF
```

## Backup & Recovery

### Automated Backups

Backups run automatically via CronJob:
- Database: Daily at 2 AM (Myanmar time)
- Redis: Daily at 3 AM (Myanmar time)
- Retention: 30 days
- Storage: S3 Standard-IA

### Manual Backup

```bash
# Database backup
kubectl create job manual-db-backup --from=cronjob/erp_solution-db-backup -n erp_solution

# Redis backup
kubectl create job manual-redis-backup --from=cronjob/erp_solution-redis-backup -n erp_solution
```

### Restore from Backup

```bash
# Restore database
kubectl exec -it erp_solution-postgres-0 -n erp_solution -- bash
aws s3 cp s3://erp_solution-production/backups/database/erp_solution-20240101-020000.sql.gz /tmp/
gunzip /tmp/erp_solution-20240101-020000.sql.gz
psql -U erp_solution_user -d erp_solution_production < /tmp/erp_solution-20240101-020000.sql
```

## Monitoring

### Prometheus Metrics

```bash
# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack   --namespace erp_solution-monitoring   --create-namespace

# Apply ServiceMonitor
kubectl apply -f monitoring/prometheus.yaml
```

### Grafana Dashboard

```bash
# Import dashboard
kubectl create configmap erp_solution-dashboard   --from-file=monitoring/grafana-dashboard.json   -n erp_solution-monitoring   --dry-run=client -o yaml | kubectl apply -f -
```

### Alerts

Key alerts configured:
- API error rate > 5%
- API P95 latency > 2s
- Pod restarts > 0
- DB connections > 150
- DB replication lag > 5 min
- Worker queue depth > 1000
- PVC usage > 85%

## Security

### Network Policies

Default deny-all with explicit allow rules:
- API pods can communicate with DB, Redis, and external APIs
- Web pods can communicate with API
- Workers can communicate with DB, Redis, and S3
- Ingress only from NGINX ingress controller

### RBAC

Minimal permissions:
- ServiceAccount with read-only access to pods, services, endpoints
- No cluster-admin binding
- No privileged containers
- Non-root user execution

### Pod Security

- runAsNonRoot: true
- readOnlyRootFilesystem: true (where possible)
- drop all capabilities
- seccompProfile: RuntimeDefault

## Troubleshooting

### Common Issues

```bash
# Pod not starting
kubectl describe pod <pod-name> -n erp_solution
kubectl logs <pod-name> -n erp_solution --previous

# High memory usage
kubectl top pods -n erp_solution
kubectl exec -it <pod-name> -n erp_solution -- sh -c "ps aux --sort=-%mem | head"

# Database connection issues
kubectl exec -it erp_solution-postgres-0 -n erp_solution -- psql -U erp_solution_user -d erp_solution_production -c "SELECT count(*) FROM pg_stat_activity;"

# Redis issues
kubectl exec -it erp_solution-redis-0 -n erp_solution -- redis-cli info

# Ingress issues
kubectl get ingress -n erp_solution
kubectl describe ingress erp_solution-ingress -n erp_solution
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

### Rollback

```bash
# Quick rollback
./scripts/rollback.sh production

# Or manual rollback
kubectl rollout undo deployment/erp_solution-api -n erp_solution
kubectl rollout undo deployment/erp_solution-web -n erp_solution
kubectl rollout undo deployment/erp_solution-worker -n erp_solution
```

## Cost Optimization

### Resource Requests vs Limits

| Component | Request CPU | Request Memory | Limit CPU | Limit Memory |
|-----------|-------------|----------------|-----------|--------------|
| API | 250m | 512Mi | 1000m | 2Gi |
| Web | 100m | 128Mi | 500m | 512Mi |
| Worker | 100m | 256Mi | 500m | 1Gi |
| PostgreSQL | 500m | 1Gi | 2000m | 4Gi |
| Redis | 100m | 256Mi | 500m | 1Gi |

### Spot Instances (Production)

```yaml
# Add to pod spec for non-critical workloads
nodeSelector:
  karpenter.sh/capacity-type: spot
tolerations:
- key: "spot"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
```

## Multi-Region Deployment

For high availability across regions:

```bash
# Primary region (Singapore)
kubectl config use-context singapore
kubectl apply -k overlays/production/

# Secondary region (Tokyo)
kubectl config use-context tokyo
kubectl apply -k overlays/production/

# Configure global load balancer (Cloudflare/AWS Global Accelerator)
```

## Maintenance Windows

```bash
# Cordon node for maintenance
kubectl cordon <node-name>

# Drain node
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Uncordon after maintenance
kubectl uncordon <node-name>
```

## Next Steps

1. **Istio Service Mesh** - mTLS, traffic management, observability
2. **Vault Integration** - Dynamic secrets, encryption as a service
3. **GitOps (ArgoCD/Flux)** - Declarative continuous deployment
4. **Chaos Engineering** - Litmus/Gremlin for resilience testing
5. **Cost Monitoring** - Kubecost for resource optimization
6. **Multi-tenancy** - Namespace-as-a-service for client isolation

