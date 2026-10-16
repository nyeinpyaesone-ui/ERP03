# ERP03 Incident Response Runbook

Alerts from `infra/monitoring/alerts.yml` open incidents. Critical pages the
on-call; warnings are worked in business hours.

1. **Detect** — capture the alert, timestamp, `X-Request-ID`, commit and image
   digest from the current deployment summary.
2. **Triage** — classify availability, data-integrity, security or dependency
   impact. Data-integrity concerns escalate immediately.
3. **Contain** — stop promotion (`deploy-production` / `deploy-staging` have
   single-run concurrency, so a new promotion can be withheld), and isolate the
   affected component with a NetworkPolicy or by scaling it down.
4. **Recover** — use `Rollback` for application faults
   (`docs/ROLLBACK_RUNBOOK.md`) or the restore procedure for data faults
   (`docs/BACKUP_RESTORE_RUNBOOK.md`). Never downgrade schema automatically.
5. **Validate** — run `scripts/smoke.sh`, check `/api/v1/readyz`, and verify
   transaction integrity (`docs/TRANSACTION_INTEGRITY.md`).
6. **Close** — document root cause, corrective action and evidence. File the
   follow-up as a `fix/` branch per `docs/RELEASE_PROCESS.md`.

## Using request IDs

Every response carries `X-Request-ID`, and the same value appears in the
structured log line. Search the log index for `request_id=<value>` to find the
handling pod, duration and status, then correlate with the Grafana dashboard
window (`infra/monitoring/README.md`).

Never delete or rewrite transaction or audit evidence during incident
handling.
