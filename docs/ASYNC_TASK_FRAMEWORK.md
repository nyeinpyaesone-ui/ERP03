# ERP erpo3 Asynchronous Task Framework Guide

## Overview

The ERP erpo3 Asynchronous Task Framework provides professional-grade async task execution with prefix-wired routing, exponential backoff retries, circuit breakers, and comprehensive error handling for real-world production scenarios.

## Key Features

### 1. Prefix-Wired Task Routing
- **Format**: `erpo3:{domain}:{action}`
- **Examples**: 
  - `erpo3:inventory:sync`
  - `erpo3:payments:process`
  - `erpo3:reports:generate`

### 2. Exponential Backoff with Jitter
- Configurable retry attempts (default: 3)
- Base delay: 1 second
- Maximum delay: 60 seconds
- Exponential base: 2x
- Optional jitter to prevent thundering herd

### 3. Circuit Breaker Pattern
- Failure threshold: 5 consecutive failures
- Recovery timeout: 30 seconds
- Half-open state testing with limited calls
- Automatic state transitions (closed → open → half-open → closed)

### 4. Rate Limiting
- Token bucket algorithm per domain
- Configurable rate (default: 10 requests/second)
- Configurable capacity (default: 20 tokens)
- Prevents resource exhaustion

### 5. Dead Letter Queue
- Captures tasks that exceed retry limits
- Configurable max size (default: 1000 tasks)
- Enables manual inspection and reprocessing
- Comprehensive error context preservation

### 6. Concurrency Control
- Semaphore-based parallelism control
- Configurable max concurrent tasks (default: 100)
- Prevents system overload
- Graceful task queuing

### 7. Comprehensive Metrics
- Total/successful/failed task counts
- Retry statistics
- Dead letter queue size
- Per-domain success/failure rates
- Average execution time

## Installation & Setup

### Basic Usage

```python
from app.async_tasks import create_default_executor, PriorityLevel

# Create executor with default configuration
executor = create_default_executor()

# Execute a single task
result = await executor.execute(
    domain="inventory",
    action="sync",
    payload={"warehouse_ids": ["WH001", "WH002"]},
    priority=PriorityLevel.HIGH,
    timeout=30.0
)
```

### Custom Configuration

```python
config = {
    "default_max_retries": 5,
    "rate_limit_per_domain": 20.0,
    "enable_circuit_breaker": True,
    "dead_letter_queue_size": 2000,
    "max_concurrent_tasks": 200
}

executor = create_default_executor(config)
```

## Task Execution Patterns

### Single Task Execution

```python
try:
    result = await executor.execute(
        domain="payments",
        action="process",
        payload={
            "amount": 100.00,
            "currency": "USD",
            "customer_id": "CUST-123"
        },
        priority=PriorityLevel.CRITICAL,
        max_retries=5,
        timeout=60.0
    )
    print(f"Payment processed: {result}")
except TimeoutError as e:
    print(f"Task timed out: {e}")
except Exception as e:
    print(f"Task failed after all retries: {e}")
    # Check dead letter queue for details
    dlq_tasks = await executor.get_dead_letter_tasks()
```

### Batch Task Execution

```python
batch_tasks = [
    {
        "domain": "inventory",
        "action": "sync",
        "payload": {"warehouse_ids": ["WH001"]},
        "priority": "HIGH",
        "timeout": 30.0
    },
    {
        "domain": "reports",
        "action": "generate",
        "payload": {"type": "sales", "date_range": "2024-01"},
        "priority": "NORMAL",
        "timeout": 120.0
    },
    {
        "domain": "notifications",
        "action": "send",
        "payload": {"type": "email", "recipients": ["user@example.com"]},
        "priority": "LOW",
        "timeout": 10.0
    }
]

results = await executor.execute_batch(batch_tasks, max_concurrency=5)

for result in results:
    if result["status"] == "success":
        print(f"Task {result['task_id']} succeeded: {result['result']}")
    else:
        print(f"Task {result['task_id']} failed: {result['error']}")
```

### Custom Task Handlers

```python
from app.async_tasks import AsyncTaskExecutor

executor = AsyncTaskExecutor()

async def custom_inventory_handler(payload):
    """Custom inventory synchronization logic."""
    warehouse_ids = payload.get("warehouse_ids", [])
    
    # Your business logic here
    for wh_id in warehouse_ids:
        await sync_warehouse(wh_id)
    
    return {"synced_count": len(warehouse_ids)}

# Register handler
executor.register_handler("inventory", "sync", custom_inventory_handler)

# Use the handler
result = await executor.execute(
    domain="inventory",
    action="sync",
    payload={"warehouse_ids": ["WH001", "WH002"]}
)
```

### Using the Decorator

```python
from app.async_tasks import erpo3_task, PriorityLevel, RetryConfig

@erpo3_task(
    domain="finance",
    action="reconcile",
    priority=PriorityLevel.HIGH,
    max_retries=5,
    retry_config=RetryConfig(
        max_retries=5,
        base_delay=2.0,
        max_delay=120.0,
        exponential_base=2.5,
        jitter=True
    ),
    rate_limit=5.0,
    circuit_breaker=True
)
async def reconcile_accounts(account_ids: list):
    """Reconcile financial accounts."""
    # Your reconciliation logic
    for account_id in account_ids:
        await process_account(account_id)
    
    return {"reconciled": len(account_ids)}

# Usage
result = await reconcile_accounts(["ACC001", "ACC002", "ACC003"])
```

## Error Handling & Recovery

### Retry Behavior

The framework implements exponential backoff with optional jitter:

```
Attempt 1: Immediate execution
Attempt 2: Wait 1-2 seconds (base_delay * 2^1 ± jitter)
Attempt 3: Wait 2-4 seconds (base_delay * 2^2 ± jitter)
Attempt 4: Wait 4-8 seconds (base_delay * 2^3 ± jitter)
...
Max delay capped at max_delay (default: 60 seconds)
```

### Circuit Breaker States

1. **Closed**: Normal operation, requests flow through
2. **Open**: Failures exceeded threshold, requests blocked immediately
3. **Half-Open**: Testing recovery with limited requests

```python
# Circuit breaker automatically opens after 5 consecutive failures
# After 30 seconds (recovery_timeout), it enters half-open state
# If 3 consecutive successes occur, it closes again
```

### Dead Letter Queue Management

```python
# Retrieve failed tasks
dlq_tasks = await executor.get_dead_letter_tasks()

for task in dlq_tasks:
    print(f"Task ID: {task['task_id']}")
    print(f"Domain: {task['domain']}")
    print(f"Action: {task['action']}")
    print(f"Error: {task['error_message']}")
    print(f"Retry Count: {task['retry_count']}")
    
# Manual reprocessing
for task in dlq_tasks:
    try:
        await executor.execute(
            domain=task['domain'],
            action=task['action'],
            payload=task['payload']
        )
    except Exception as e:
        logger.error(f"Reprocessing failed: {e}")

# Clear DLQ after processing
await executor.dead_letter_queue.clear()
```

## Monitoring & Metrics

### Real-time Metrics

```python
metrics = executor.get_metrics()

print(f"Total Tasks: {metrics['total_tasks']}")
print(f"Success Rate: {metrics['success_rate']:.2%}")
print(f"Average Execution Time: {metrics['average_execution_time']:.2f}s")
print(f"Retried Tasks: {metrics['retried_tasks']}")
print(f"Dead Letter Tasks: {metrics['dead_letter_tasks']}")

# Per-domain breakdown
for domain, stats in metrics['domain_stats'].items():
    print(f"\n{domain}:")
    print(f"  Successful: {stats['success']}")
    print(f"  Failed: {stats['failed']}")
```

### Integration with FastAPI

```python
from fastapi import FastAPI
from app.async_tasks import create_default_executor

app = FastAPI()
executor = create_default_executor()

@app.post("/api/v1/tasks/inventory/sync")
async def sync_inventory(warehouse_ids: list):
    result = await executor.execute(
        domain="inventory",
        action="sync",
        payload={"warehouse_ids": warehouse_ids}
    )
    return result

@app.get("/api/v1/tasks/metrics")
async def get_task_metrics():
    return executor.get_metrics()

@app.get("/api/v1/tasks/dead-letter")
async def get_dead_letter_tasks():
    return await executor.get_dead_letter_tasks()

@app.post("/api/v1/tasks/dead-letter/reprocess")
async def reprocess_dead_letter():
    dlq_tasks = await executor.get_dead_letter_tasks()
    results = []
    
    for task in dlq_tasks:
        try:
            result = await executor.execute(
                domain=task['domain'],
                action=task['action'],
                payload=task['payload']
            )
            results.append({"task_id": task['task_id'], "status": "reprocessed"})
        except Exception as e:
            results.append({"task_id": task['task_id'], "status": "failed", "error": str(e)})
    
    await executor.dead_letter_queue.clear()
    return results
```

## Pre-configured Task Handlers

The framework includes pre-built handlers for common ERP operations:

### Inventory Operations
- `erpo3:inventory:sync` - Sync inventory across warehouses

### Payment Operations
- `erpo3:payments:process` - Process payment transactions

### Reporting Operations
- `erpo3:reports:generate` - Generate analytics reports

### Validation Operations
- `erpo3:validation:check` - Validate data integrity

### Notification Operations
- `erpo3:notifications:send` - Send notifications to users

## Best Practices

### 1. Choose Appropriate Priority Levels

```python
PriorityLevel.CRITICAL    # System-critical operations (immediate attention)
PriorityLevel.HIGH        # Important business operations
PriorityLevel.NORMAL      # Standard operations (default)
PriorityLevel.LOW         # Non-urgent background tasks
PriorityLevel.BACKGROUND  # Maintenance and cleanup tasks
```

### 2. Set Reasonable Timeouts

```python
# Quick operations (< 5 seconds)
timeout=5.0

# Standard operations (5-30 seconds)
timeout=30.0

# Long-running operations (30-120 seconds)
timeout=120.0

# Report generation, bulk imports (> 120 seconds)
timeout=300.0
```

### 3. Configure Retry Limits Appropriately

```python
# Idempotent operations (safe to retry)
max_retries=5

# Non-idempotent operations (limited retries)
max_retries=2

# External API calls (moderate retries)
max_retries=3

# One-way operations (no retries)
max_retries=0
```

### 4. Monitor Circuit Breakers

```python
# Log circuit breaker state changes
logger.info("Circuit breaker opened - external service degraded")

# Implement fallback mechanisms
if circuit_breaker.state == "open":
    # Use cached data or alternative service
    result = await fallback_operation()
```

### 5. Handle Dead Letter Queue Proactively

```python
# Schedule regular DLQ monitoring
async def monitor_dlq():
    dlq_size = await executor.dead_letter_queue.size()
    
    if dlq_size > 100:
        # Alert operations team
        await send_alert(f"DLQ size critical: {dlq_size}")
        
        # Auto-reprocess non-critical failures
        await auto_reprocess_non_critical()

# Run every 5 minutes
asyncio.create_task(periodic_dlq_monitoring())
```

## Performance Tuning

### Concurrency Settings

```python
# High-throughput system
config = {
    "max_concurrent_tasks": 500,
    "rate_limit_per_domain": 50.0
}

# Resource-constrained environment
config = {
    "max_concurrent_tasks": 50,
    "rate_limit_per_domain": 5.0
}
```

### Memory Management

```python
# Enable automatic garbage collection after tasks
import gc

@erpo3_task(domain="ml", action="predict")
async def ml_prediction(data):
    result = await run_model(data)
    gc.collect()  # Force garbage collection
    return result
```

## Troubleshooting

### Common Issues

**Issue**: Tasks consistently timing out
- **Solution**: Increase timeout value or optimize task logic
- **Check**: Network connectivity, database performance

**Issue**: Circuit breaker constantly opening
- **Solution**: Investigate root cause of failures, increase failure_threshold
- **Check**: External service health, resource availability

**Issue**: Dead letter queue growing rapidly
- **Solution**: Fix underlying errors, implement better error handling
- **Check**: Task payloads, external dependencies

**Issue**: Rate limiting too aggressive
- **Solution**: Increase rate_limit_per_domain based on capacity
- **Check**: System resource utilization

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("erp03.async.tasks")
logger.setLevel(logging.DEBUG)
```

## Migration from Celery

If migrating from Celery workers:

```python
# Old Celery task
@celery_app.task(bind=True, max_retries=3)
def old_sync_inventory(self, warehouse_ids):
    try:
        # Logic here
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

# New erpo3 async task
@erpo3_task(
    domain="inventory",
    action="sync",
    max_retries=3,
    retry_config=RetryConfig(base_delay=1.0, max_delay=60.0)
)
async def new_sync_inventory(warehouse_ids):
    # Logic here (async)
    pass
```

## Conclusion

The ERP erpo3 Asynchronous Task Framework provides enterprise-grade reliability for distributed task execution with built-in resilience patterns, comprehensive monitoring, and flexible configuration for diverse workload requirements.

For support and questions, refer to the main ERP erpo3 documentation or contact the development team.
