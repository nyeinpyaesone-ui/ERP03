# ERP03 Maintenance Checklist

## Data protection
- [ ] Backups ran on schedule (`scripts/backup.sh` output and checksums).
- [ ] A restore was verified this period (`scripts/restore-test.sh`).
- [ ] Retention and recovery objectives still match the approved RPO/RTO.
- [ ] Backup encryption keys are reachable by the on-call rotation.

## Security hygiene
- [ ] Dependency audit results reviewed (pip-audit, npm audit).
- [ ] Container image scan (Trivy) results reviewed; base image digests
      refreshed via Dependabot.
- [ ] Secret scan (gitleaks) is green; no secret has been added to history.
- [ ] `erp03-secrets` values rotated (database password, `SECRET_KEY`) and the
      rollout restarted; note that rotating `SECRET_KEY` invalidates issued
      JWTs.
- [ ] TLS certificates and their expiry verified for every ingress host.
- [ ] Kubernetes service accounts and RBAC reviewed for least privilege.

## Capacity and health
- [ ] CPU, memory, database connections and latency reviewed in Grafana.
- [ ] Application error rates and sampled request IDs reviewed.
- [ ] Saturation alerts tuned against actual headroom.
- [ ] Failed jobs and scheduled operations inspected.

## Change and release
- [ ] Migration state matches the deployed revision (`alembic current`).
- [ ] All workflows are green on `main`; no workflow parked in a failing state.
- [ ] Pending pull requests reviewed for stale Dependabot or agent branches.
- [ ] Release notes published for anything promoted since the last cycle.

## Record
- [ ] Maintenance window, operator and evidence recorded in the change log.
