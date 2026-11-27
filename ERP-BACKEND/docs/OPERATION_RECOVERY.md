# ERP03 Durable Operation Recovery Runbook

## Safety invariants

- PostgreSQL is authoritative for operation state and ERP business records.
- An operation is `committed` only when its domain transaction commits.
- POS invoice, payment, stock-balance, stock-movement and operation-result writes must commit or roll back together.
- The SQLite transaction journal is not proof that a sale or other business mutation succeeded.
- Reuse the original idempotency key for a retry. Never invent a new key to force a retry.

## Operation lifecycle

| State | Meaning | Operator action |
|---|---|---|
| `pending` | Durable command is waiting to be claimed | Allow the worker to claim it |
| `processing` | A worker owns a time-limited lease | Check owner and last heartbeat before recovery |
| `committed` | Domain mutation and operation result committed atomically | Treat as complete; replay only with the same idempotency key |
| `failed` | Attempt failed and bounded backoff is scheduled | Inspect stable error code and retry count |
| `reconciliation_required` | Retry limit reached; automatic retry stops | Manual review; do not blindly retry |
| `cancelled` | Operation was manually stopped | Terminal; preserve audit record |

Legal transitions are enforced by `OperationState.can_transition_to` and `OperationService`. Retry backoff is exponential and capped at one hour; `max_retries` bounds automatic attempts.

## Read-only triage

Run against the intended environment using a read-only database role:

```sql
SELECT
    operation_id,
    operation_type,
    business_id,
    branch_id,
    state,
    retry_count,
    max_retries,
    backoff_until,
    claimed_by,
    claimed_at,
    committed_at,
    updated_at,
    error_code
FROM operations
WHERE state IN (
    'pending',
    'processing',
    'failed',
    'reconciliation_required'
)
ORDER BY updated_at ASC;
```

Do not select or print `payload_json` or `error_message` into shared logs or tickets; they may contain sensitive business context. Use `operation_id` as the primary correlation key. When a trusted request ID is present in the operation payload, transition logs include it without logging the payload.

## Recovery procedure

1. Confirm the environment, database identity and current application revision.
2. Inspect the operation row and its timestamps, retry count, error code and worker owner.
3. For `processing`, confirm the worker is stopped or its lease has expired. A live worker should renew the lease with `OperationService.heartbeat(operation_id)`. 
4. For `failed`, wait until `backoff_until` and let the worker claim it through `claim_next()`.
5. For `reconciliation_required`, stop automatic retries. Verify the invoice, payment records, stock balance and stock movements before any manual action.
6. For `committed`, use the stored result and original idempotency key. Do not create a compensating sale merely because the client timed out.
7. Record the operator, operation ID, evidence, decision and approval in the incident/change record.

Never update operation states directly with SQL, delete journal rows, or manually decrement/increment stock to make a dashboard appear consistent. Use the domain service and its idempotency contract.

## Current implementation boundary

The POS sale path now writes its operation identity and committed result in the same PostgreSQL transaction as the invoice, payments and stock mutations. The operation service provides database row-lock claims, retry backoff, lease heartbeat, stale-operation reconciliation and stale-worker fencing.

**An always-running asynchronous worker/handler registry is not yet deployed by this change.** Do not assume queued operations will process automatically until that worker and its deployment have been implemented and qualified. The synchronous POS sale path remains available through its existing API transaction.

## Validation

From `ERP-BACKEND` in the matching checkout:

```bash
pytest -q tests/test_orchestration_service.py tests/test_erp_integration.py
ruff check app tests alembic
ruff format --check app tests alembic
```

PostgreSQL is required for the independent-session claim and concurrent idempotency tests. SQLite-only results do not qualify multi-replica concurrency.
