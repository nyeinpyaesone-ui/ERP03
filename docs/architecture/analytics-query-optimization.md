# Analytics Query Optimization

## Goal

Keep the ERP control-tower/dashboard read path simple, deterministic, and bounded while preserving the existing response contract.

## Current implementation

`AnalyticsQueryService.get_dashboard()` is the read-side aggregation boundary for the dashboard. The FastAPI router delegates to this service instead of owning SQL aggregation logic.

## Query strategy

Dashboard metrics are grouped into domain-local aggregate queries:

- Finance/invoices: revenue and outstanding balance in one query.
- CRM/contacts: contact count in one query.
- CRM/deals: deal count and pipeline value in one query.
- HR/employees: total and active employees in one query.
- Inventory/products: total and low-stock products in one query.
- Projects: total and active projects in one query.
- Tasks: total and completed tasks in one query.
- Activity: latest ten activity records in one bounded read.

This replaces the earlier pattern of issuing separate queries for each metric where those metrics can be safely aggregated together.

## Design constraints

- No client/API contract change.
- No asynchronous execution introduced for dashboard reads.
- No new database pool introduced.
- No caching introduced without measured need.
- No cross-domain join that could multiply rows and corrupt aggregate values.
- SQL remains explicit and domain-local.

## Validation

`ERP-BACKEND/tests/test_analytics_service.py` verifies the dashboard response contract and the intended bounded query count at the service boundary.

Performance improvement must still be measured against a representative PostgreSQL dataset before claiming a specific latency or throughput gain.
