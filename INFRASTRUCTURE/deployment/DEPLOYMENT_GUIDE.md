# ERP03 Enterprise Deployment Guide

**Version**: 1.0.0  
**Last Updated**: 2024  
**Target Platform**: Kubernetes v1.28+  

---

## Overview

This guide provides step-by-step instructions for deploying the ERP03 platform to Kubernetes environments using Kustomize for configuration management. The deployment structure follows GitOps best practices with environment-specific overlays for staging and production.

---

## Repository Structure

```
/workspace/INFRASTRUCTURE/deployment/
├── base/                      # Base manifests (shared across environments)
│   ├── backend-deployment.yaml
│   └── kustomization.yaml
├── staging/                   # Staging environment overrides
│   └── kustomization.yaml
└── production/                # Production environment overrides
    ├── kustomization.yaml
    ├── hpa.yaml              # Horizontal Pod Autoscaler
    └── pdb.yaml              # Pod Disruption Budget
```

---

## Prerequisites

### Required Tools
- `kubectl` v1.28+ configured with cluster access
- `kustomize` v5.0+ (bundled with kubectl v1.14+)
- Access to GHCR (GitHub Container Registry)
- Kubernetes cluster with:
  - Minimum 3 nodes (production)
  - 8 vCPU, 16GB RAM per node (recommended)
  - Storage class provisioned for persistent volumes

### Required Secrets

Create secrets in each namespace before deployment:

```bash
# Staging secrets
kubectl create secret generic erp03-secrets \
  --from-literal=database-url="postgresql://user:pass@postgres:5432/erp_staging" \
  --from-literal=redis-url="redis://redis:6379/0" \
  --from-literal=jwt-secret="$(openssl rand -hex 32)" \
  -n erp03-staging

# Production secrets
kubectl create secret generic erp03-secrets \
  --from-literal=database-url="postgresql://user:pass@postgres:5432/erp_production" \
  --from-literal=redis-url="redis://redis:6379/0" \
  --from-literal=jwt-secret="$(openssl rand -hex 32)" \
  -n erp03-production
```

### Required Namespaces

```bash
kubectl create namespace erp03-staging
kubectl create namespace erp03-production
```

---

## Deployment Procedures

### 1. Staging Environment Deployment

Staging is automatically deployed via CI/CD when merging to `develop` branch. Manual deployment:

```bash
# Preview manifests
kubectl kustomize INFRASTRUCTURE/deployment/staging/

# Apply to cluster
kubectl apply -k INFRASTRUCTURE/deployment/staging/

# Verify deployment
kubectl get all -n erp03-staging

# Check rollout status
kubectl rollout status deployment/erp-backend -n erp03-staging
kubectl rollout status deployment/erp-frontend -n erp03-staging
kubectl rollout status deployment/erp-worker -n erp03-staging

# View logs
kubectl logs -f deployment/erp-backend -n erp03-staging
```

**Expected Resources:**
- 2 replicas of backend
- 2 replicas of frontend
- 1 replica of worker
- Debug logging enabled

### 2. Production Environment Deployment

Production requires manual approval after staging validation.

```bash
# Preview manifests
kubectl kustomize INFRASTRUCTURE/deployment/production/

# Apply to cluster (after approval)
kubectl apply -k INFRASTRUCTURE/deployment/production/

# Verify deployment
kubectl get all -n erp03-production

# Check HPA status
kubectl get hpa -n erp03-production

# Check PDB status
kubectl get pdb -n erp03-production

# Monitor rollout
kubectl rollout status deployment/erp-backend -n erp03-production
```

**Expected Resources:**
- 4-12 replicas of backend (auto-scaled)
- 4-16 replicas of frontend (auto-scaled)
- 3 replicas of worker minimum
- Warning-level logging

---

## Post-Deployment Verification

### Health Checks

```bash
# Backend health
kubectl exec -it deployment/erp-backend -n erp03-staging -- \
  curl -s http://localhost:8000/api/v1/health | jq

# Frontend health
kubectl exec -it deployment/erp-frontend -n erp03-staging -- \
  curl -s http://localhost:3000/ | head -20
```

### Connectivity Tests

```bash
# Test internal service discovery
kubectl run test-pod --rm -it --image=curlimages/curl -n erp03-staging -- \
  curl http://erp-backend-service:8000/api/v1/health
```

### Performance Validation

```bash
# Check resource utilization
kubectl top pods -n erp03-production

# Verify HPA is working
kubectl get hpa -n erp03-production -w
```

---

## Rollback Procedures

### Quick Rollback (Last Known Good)

```bash
# Rollback to previous revision
kubectl rollout undo deployment/erp-backend -n erp03-production
kubectl rollout undo deployment/erp-frontend -n erp03-production

# Rollback to specific revision
kubectl rollout undo deployment/erp-backend -n erp03-production --to-revision=3

# Monitor rollback status
kubectl rollout status deployment/erp-backend -n erp03-production
```

### Full Rollback (Revert Kustomize)

```bash
# Revert to previous commit in git
git checkout <previous-commit-hash> -- INFRASTRUCTURE/deployment/

# Apply previous version
kubectl apply -k INFRASTRUCTURE/deployment/production/
```

---

## Scaling Operations

### Manual Scaling

```bash
# Scale backend manually
kubectl scale deployment/erp-backend --replicas=6 -n erp03-production

# Scale frontend
kubectl scale deployment/erp-frontend --replicas=8 -n erp03-production
```

### Autoscaling Configuration

HPA is pre-configured in production with:
- **CPU Target**: 70% utilization
- **Memory Target**: 80% utilization
- **Scale Up**: Max 100% increase per minute
- **Scale Down**: Max 25% decrease per 5 minutes

Adjust thresholds:

```bash
kubectl edit hpa erp-backend-hpa -n erp03-production
```

---

## Monitoring & Observability

### Prometheus Metrics Endpoints

- Backend: `http://erp-backend-service:8000/metrics`
- Worker: `http://erp-worker-service:8001/metrics`

### Key Dashboards

1. **Application Health**: Request rate, error rate, latency percentiles
2. **Resource Utilization**: CPU, memory, network I/O
3. **WebSocket Connections**: Active connections, message throughput
4. **Database Performance**: Query latency, connection pool usage

### Alert Rules

Configure alerts for:
- Pod restart count > 3 in 5 minutes
- Error rate > 1% over 5 minutes
- Latency p95 > 500ms over 10 minutes
- HPA at max replicas for 15 minutes

---

## Security Hardening

### Network Policies (Recommended)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: erp-backend-policy
  namespace: erp03-production
spec:
  podSelector:
    matchLabels:
      app: erp-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: erp-frontend
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### Pod Security Standards

All deployments enforce:
- `runAsNonRoot: true`
- Non-root user (UID 1000)
- Read-only root filesystem (where possible)
- No privilege escalation

---

## Troubleshooting

### Common Issues

**ImagePullBackOff:**
```bash
# Check image pull secrets
kubectl get secrets -n erp03-production | grep ghcr

# Verify GHCR credentials
kubectl describe pod <pod-name> -n erp03-production
```

**CrashLoopBackOff:**
```bash
# Check logs
kubectl logs <pod-name> -n erp03-production --previous

# Check environment variables
kubectl describe pod <pod-name> -n erp03-production

# Verify secrets exist
kubectl get secrets erp03-secrets -n erp03-production
```

**High Latency:**
```bash
# Check resource constraints
kubectl top pods -n erp03-production

# Review HPA events
kubectl describe hpa erp-backend-hpa -n erp03-production

# Check node pressure
kubectl describe node <node-name>
```

---

## Maintenance Windows

### Scheduled Updates

1. **Database Migrations**: Run during low-traffic periods (2 AM - 4 AM local time)
2. **Certificate Rotation**: 30 days before expiry
3. **Kubernetes Version Upgrade**: Quarterly, with staging validation first
4. **Dependency Updates**: Monthly security patches

### Pre-Maintenance Checklist

- [ ] Notify stakeholders 48 hours in advance
- [ ] Create backup of database
- [ ] Document rollback procedure
- [ ] Test in staging environment
- [ ] Prepare communication templates
- [ ] Schedule on-call engineer

---

## Contact & Support

**DevOps Team**: `#erp03-devops` (Slack)  
**On-Call**: PagerDuty `erp03-production`  
**Documentation**: https://docs.erp03.example.com  

---

*This document should be reviewed and updated after each major deployment or infrastructure change.*
