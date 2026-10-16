# ERP03 Observability

## Metrics

The API exposes Prometheus metrics at `GET /metrics`:

| Metric | Type | Labels | Meaning |
|---|---|---|---|
| `erp03_http_requests_total` | counter | method, route, status | Requests handled, by matched route |
| `erp03_http_request_duration_seconds` | histogram | method, route | Request latency |

Scrape targets are defined in `prometheus.yml` and discover pods in
`erp03-dev`, `erp03-staging` and `erp03-production`. The NetworkPolicies in
`../kubernetes/base/networkpolicy.yaml` already permit the `monitoring`
namespace to reach the backend on port 8000; no policy change is needed to
start scraping.

Import `grafana/erp03-service-health.json` for the baseline dashboard: request
rate by status, p50/p95/p99 latency, 5xx ratio, target availability, CPU and
memory saturation, and database connections.

## Alerts

`alerts.yml` defines eight rules across availability, error rate, latency,
saturation and database pressure. Production thresholds come from
`infra/terraform/modules/monitoring` (`error_rate_threshold_percent`,
`latency_p95_threshold_ms`) and must be tightened, not loosened, over time.

Every alert links to `docs/INCIDENT_RESPONSE_RUNBOOK.md`. Page only on
`severity: critical`; `severity: warning` belongs in business hours.

## Logs and correlation

The HTTP middleware assigns every request an `X-Request-ID` (accepting an
inbound one) and returns it in the response header. The same value appears in
the structured access log line:

```
request method=POST path=/api/v1/sales status=201 duration_ms=42.10 request_id=9f1c...
```

To investigate an incident:

1. Take the `request_id` from the client error or support ticket.
2. Search the log index for `request_id=<value>` to find the handling pod,
   status and duration.
3. Use the pod name and timestamp to pull the matching metric window in
   Grafana.

Unhandled exceptions are logged with `logger.exception` and include the same
`request_id`, so a client-visible 500 is always traceable server-side. The
response body for those errors carries `request_id` too, so users can report a
value that is safe to share.

Retention: keep metrics for at least 15 days and searchable logs for at least
30 days (`infra/terraform/modules/monitoring`).
