import asyncio
import gc
import hashlib
import json
import logging
import os
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union
from collections import defaultdict
from functools import wraps
import traceback

logger = logging.getLogger("erp03.async.tasks")


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    DEAD_LETTER = "dead_letter"


class PriorityLevel(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class TaskContext:
    task_id: str
    prefix: str
    domain: str
    action: str
    payload: Dict[str, Any]
    priority: PriorityLevel = PriorityLevel.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "prefix": self.prefix,
            "domain": self.domain,
            "action": self.action,
            "priority": self.priority.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "result": self.result,
            "metadata": self.metadata
        }


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    
    def get_delay(self, retry_count: int) -> float:
        delay = min(
            self.base_delay * (self.exponential_base ** retry_count),
            self.max_delay
        )
        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)
        return max(0.1, delay)


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3


class CircuitBreaker:
    
    def __init__(self, config: CircuitBreakerConfig = None):
        self.config = config or CircuitBreakerConfig()
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        async with self._lock:
            if self.state == "open":
                if self._should_attempt_reset():
                    self.state = "half-open"
                    logger.info("Circuit breaker entering half-open state")
                else:
                    raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        if not self.last_failure_time:
            return True
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.recovery_timeout
    
    async def _on_success(self):
        async with self._lock:
            if self.state == "half-open":
                self.success_count += 1
                if self.success_count >= self.config.half_open_max_calls:
                    self.state = "closed"
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info("Circuit breaker closed after successful recovery")
            else:
                self.failure_count = 0
    
    async def _on_failure(self):
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.state == "half-open":
                self.state = "open"
                logger.warning("Circuit breaker opened from half-open state")
            elif self.failure_count >= self.config.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class RateLimiter:
    
    def __init__(self, rate: float = 10.0, capacity: float = 20.0):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: float = 1.0) -> bool:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    async def wait_for_token(self, tokens: float = 1.0, timeout: float = None):
        start_time = time.monotonic()
        
        while True:
            if await self.acquire(tokens):
                return
            
            if timeout and (time.monotonic() - start_time) >= timeout:
                raise TimeoutError(f"Rate limiter timeout after {timeout}s")
            
            await asyncio.sleep(0.1)


@dataclass
class TaskMetrics:
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    retried_tasks: int = 0
    dead_letter_tasks: int = 0
    total_execution_time: float = 0.0
    domain_stats: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: {"success": 0, "failed": 0}))
    
    def record_success(self, domain: str, execution_time: float):
        self.total_tasks += 1
        self.successful_tasks += 1
        self.total_execution_time += execution_time
        self.domain_stats[domain]["success"] += 1
    
    def record_failure(self, domain: str):
        self.total_tasks += 1
        self.failed_tasks += 1
        self.domain_stats[domain]["failed"] += 1
    
    def record_retry(self):
        self.retried_tasks += 1
    
    def record_dead_letter(self):
        self.dead_letter_tasks += 1
    
    def get_summary(self) -> Dict[str, Any]:
        avg_time = (
            self.total_execution_time / self.successful_tasks
            if self.successful_tasks > 0 else 0
        )
        return {
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "retried_tasks": self.retried_tasks,
            "dead_letter_tasks": self.dead_letter_tasks,
            "success_rate": self.successful_tasks / max(1, self.total_tasks),
            "average_execution_time": avg_time,
            "domain_stats": dict(self.domain_stats)
        }


class DeadLetterQueue:
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queue: List[TaskContext] = []
        self._lock = asyncio.Lock()
    
    async def add(self, context: TaskContext):
        async with self._lock:
            if len(self.queue) >= self.max_size:
                self.queue.pop(0)
            self.queue.append(context)
            logger.warning(f"Task {context.task_id} added to dead letter queue")
    
    async def get_all(self) -> List[TaskContext]:
        async with self._lock:
            return self.queue.copy()
    
    async def clear(self):
        async with self._lock:
            self.queue.clear()
    
    async def size(self) -> int:
        async with self._lock:
            return len(self.queue)


T = TypeVar('T')


def erp03_task(
    domain: str,
    action: str,
    priority: PriorityLevel = PriorityLevel.NORMAL,
    max_retries: int = 3,
    retry_config: RetryConfig = None,
    rate_limit: Optional[float] = None,
    circuit_breaker: bool = True
):
    prefix = f"erp03:{domain}:{action}"
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            task_id = str(uuid.uuid4())
            payload = {"args": args, "kwargs": kwargs}
            
            context = TaskContext(
                task_id=task_id,
                prefix=prefix,
                domain=domain,
                action=action,
                payload=payload,
                priority=priority,
                max_retries=max_retries
            )
            
            logger.info(f"[{task_id}] Starting task {prefix}")
            
            retry_cfg = retry_config or RetryConfig(max_retries=max_retries)
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    context.started_at = datetime.utcnow()
                    context.status = TaskStatus.RUNNING
                    
                    result = await func(*args, **kwargs)
                    
                    context.completed_at = datetime.utcnow()
                    context.status = TaskStatus.SUCCESS
                    context.result = result
                    
                    execution_time = (context.completed_at - context.started_at).total_seconds()
                    logger.info(f"[{task_id}] Task {prefix} completed successfully in {execution_time:.2f}s")
                    
                    return result
                    
                except Exception as e:
                    last_error = e
                    context.retry_count = attempt
                    context.error_message = str(e)
                    
                    if attempt < max_retries:
                        context.status = TaskStatus.RETRYING
                        delay = retry_cfg.get_delay(attempt)
                        
                        logger.warning(
                            f"[{task_id}] Task {prefix} failed (attempt {attempt + 1}/{max_retries + 1}). "
                            f"Retrying in {delay:.2f}s: {e}"
                        )
                        
                        await asyncio.sleep(delay)
                    else:
                        context.status = TaskStatus.FAILED
                        context.completed_at = datetime.utcnow()
                        logger.error(f"[{task_id}] Task {prefix} failed after {max_retries + 1} attempts: {e}")
                        break
            
            context.status = TaskStatus.DEAD_LETTER
            raise last_error
        
        return wrapper
    return decorator


class AsyncTaskExecutor:
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.default_max_retries = self.config.get("default_max_retries", 3)
        self.rate_limit_per_domain = self.config.get("rate_limit_per_domain", 10.0)
        self.enable_circuit_breakers = self.config.get("enable_circuit_breaker", True)
        self.max_concurrent_tasks = self.config.get("max_concurrent_tasks", 100)
        
        self._rate_limiters: Dict[str, RateLimiter] = defaultdict(
            lambda: RateLimiter(rate=self.rate_limit_per_domain)
        )
        
        self._circuit_breakers: Dict[str, CircuitBreaker] = defaultdict(
            lambda: CircuitBreaker()
        )
        
        self.dead_letter_queue = DeadLetterQueue(
            max_size=self.config.get("dead_letter_queue_size", 1000)
        )
        
        self.metrics = TaskMetrics()
        
        self._task_handlers: Dict[str, Callable] = {}
        
        self._semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        
        self._background_tasks: Set[asyncio.Task] = set()
        
        logger.info(f"AsyncTaskExecutor initialized with max_concurrency={self.max_concurrent_tasks}")
    
    def register_handler(self, domain: str, action: str, handler: Callable):
        key = f"erp03:{domain}:{action}"
        self._task_handlers[key] = handler
        logger.info(f"Registered handler for {key}")
    
    async def execute(
        self,
        domain: str,
        action: str,
        payload: Dict[str, Any],
        priority: PriorityLevel = PriorityLevel.NORMAL,
        max_retries: Optional[int] = None,
        timeout: Optional[float] = None
    ) -> Any:
        task_id = str(uuid.uuid4())
        prefix = f"erp03:{domain}:{action}"
        retries = max_retries or self.default_max_retries
        
        context = TaskContext(
            task_id=task_id,
            prefix=prefix,
            domain=domain,
            action=action,
            payload=payload,
            priority=priority,
            max_retries=retries
        )
        
        logger.info(f"[{task_id}] Executing task {prefix}")
        
        async with self._semaphore:
            rate_limiter = self._rate_limiters[domain]
            await rate_limiter.wait_for_token(timeout=30.0)
            
            circuit_breaker = self._circuit_breakers[domain] if self.enable_circuit_breakers else None
            
            retry_config = RetryConfig(max_retries=retries)
            last_error = None
            
            for attempt in range(retries + 1):
                try:
                    context.started_at = datetime.utcnow()
                    context.status = TaskStatus.RUNNING
                    context.retry_count = attempt
                    
                    if circuit_breaker:
                        result = await self._execute_with_circuit_breaker(
                            circuit_breaker, domain, action, payload, timeout
                        )
                    else:
                        result = await self._execute_task(domain, action, payload, timeout)
                    
                    context.completed_at = datetime.utcnow()
                    context.status = TaskStatus.SUCCESS
                    context.result = result
                    
                    execution_time = (context.completed_at - context.started_at).total_seconds()
                    self.metrics.record_success(domain, execution_time)
                    
                    logger.info(
                        f"[{task_id}] Task {prefix} completed successfully "
                        f"in {execution_time:.2f}s (attempt {attempt + 1})"
                    )
                    
                    return result
                    
                except asyncio.TimeoutError:
                    last_error = TimeoutError(f"Task {prefix} timed out after {timeout}s")
                    logger.error(f"[{task_id}] Task {prefix} timed out")
                    break
                    
                except Exception as e:
                    last_error = e
                    context.error_message = str(e)
                    
                    if attempt < retries:
                        context.status = TaskStatus.RETRYING
                        delay = retry_config.get_delay(attempt)
                        
                        self.metrics.record_retry()
                        
                        logger.warning(
                            f"[{task_id}] Task {prefix} failed (attempt {attempt + 1}/{retries + 1}). "
                            f"Retrying in {delay:.2f}s: {e}"
                        )
                        
                        await asyncio.sleep(delay)
                    else:
                        context.status = TaskStatus.FAILED
                        context.completed_at = datetime.utcnow()
                        self.metrics.record_failure(domain)
                        
                        logger.error(
                            f"[{task_id}] Task {prefix} failed after {retries + 1} attempts: {e}\n"
                            f"{traceback.format_exc()}"
                        )
                        break
            
            context.status = TaskStatus.DEAD_LETTER
            await self.dead_letter_queue.add(context)
            self.metrics.record_dead_letter()
            
            raise last_error
    
    async def _execute_with_circuit_breaker(
        self,
        circuit_breaker: CircuitBreaker,
        domain: str,
        action: str,
        payload: Dict[str, Any],
        timeout: Optional[float]
    ) -> Any:
        async def task_func():
            return await self._execute_task(domain, action, payload, timeout)
        
        return await circuit_breaker.call(task_func)
    
    async def _execute_task(
        self,
        domain: str,
        action: str,
        payload: Dict[str, Any],
        timeout: Optional[float]
    ) -> Any:
        key = f"erp03:{domain}:{action}"
        
        if key in self._task_handlers:
            handler = self._task_handlers[key]
            if timeout:
                return await asyncio.wait_for(handler(payload), timeout=timeout)
            return await handler(payload)
        
        logger.debug(f"No handler registered for {key}, using default execution")
        await asyncio.sleep(0.1)
        return {"status": "completed", "domain": domain, "action": action}
    
    async def execute_batch(
        self,
        tasks: List[Dict[str, Any]],
        max_concurrency: int = 10
    ) -> List[Dict[str, Any]]:
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def execute_single(task_def: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                try:
                    result = await self.execute(
                        domain=task_def["domain"],
                        action=task_def["action"],
                        payload=task_def.get("payload", {}),
                        priority=PriorityLevel(task_def.get("priority", "NORMAL")),
                        timeout=task_def.get("timeout")
                    )
                    return {
                        "task_id": task_def.get("task_id", str(uuid.uuid4())),
                        "status": "success",
                        "result": result
                    }
                except Exception as e:
                    return {
                        "task_id": task_def.get("task_id", str(uuid.uuid4())),
                        "status": "failed",
                        "error": str(e)
                    }
        
        coroutines = [execute_single(task) for task in tasks]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.get_summary()
    
    async def get_dead_letter_tasks(self) -> List[Dict[str, Any]]:
        tasks = await self.dead_letter_queue.get_all()
        return [task.to_dict() for task in tasks]
    
    async def shutdown(self):
        logger.info("Shutting down AsyncTaskExecutor...")
        
        for task in self._background_tasks:
            task.cancel()
        
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        logger.info("AsyncTaskExecutor shutdown complete")


class ERP03TaskHandlers:
    
    @staticmethod
    async def sync_inventory(payload: Dict[str, Any]) -> Dict[str, Any]:
        warehouse_ids = payload.get("warehouse_ids", [])
        logger.info(f"Syncing inventory for warehouses: {warehouse_ids}")
        await asyncio.sleep(0.5)
        return {"synced_warehouses": len(warehouse_ids), "status": "success"}
    
    @staticmethod
    async def process_payment(payload: Dict[str, Any]) -> Dict[str, Any]:
        amount = payload.get("amount", 0)
        currency = payload.get("currency", "USD")
        logger.info(f"Processing payment: {amount} {currency}")
        await asyncio.sleep(0.3)
        return {"transaction_id": str(uuid.uuid4()), "status": "completed"}
    
    @staticmethod
    async def generate_report(payload: Dict[str, Any]) -> Dict[str, Any]:
        report_type = payload.get("type", "summary")
        date_range = payload.get("date_range")
        logger.info(f"Generating {report_type} report for {date_range}")
        await asyncio.sleep(1.0)
        return {
            "report_type": report_type,
            "file_url": f"/reports/{report_type}_{uuid.uuid4()}.pdf",
            "generated_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def validate_data(payload: Dict[str, Any]) -> Dict[str, Any]:
        data_type = payload.get("data_type")
        records = payload.get("records", [])
        logger.info(f"Validating {len(records)} {data_type} records")
        await asyncio.sleep(0.2)
        return {
            "valid_count": len(records),
            "invalid_count": 0,
            "validation_errors": []
        }
    
    @staticmethod
    async def send_notification(payload: Dict[str, Any]) -> Dict[str, Any]:
        notification_type = payload.get("type")
        recipients = payload.get("recipients", [])
        logger.info(f"Sending {notification_type} to {len(recipients)} recipients")
        await asyncio.sleep(0.1)
        return {"sent_count": len(recipients), "failed_count": 0}


def create_default_executor(config: Optional[Dict[str, Any]] = None) -> AsyncTaskExecutor:
    executor = AsyncTaskExecutor(config)
    
    executor.register_handler("inventory", "sync", ERP03TaskHandlers.sync_inventory)
    executor.register_handler("payments", "process", ERP03TaskHandlers.process_payment)
    executor.register_handler("reports", "generate", ERP03TaskHandlers.generate_report)
    executor.register_handler("validation", "check", ERP03TaskHandlers.validate_data)
    executor.register_handler("notifications", "send", ERP03TaskHandlers.send_notification)
    
    return executor


async def main():
    config = {
        "default_max_retries": 3,
        "rate_limit_per_domain": 5.0,
        "enable_circuit_breaker": True,
        "dead_letter_queue_size": 500,
        "max_concurrent_tasks": 50
    }
    
    executor = create_default_executor(config)
    
    try:
        result = await executor.execute(
            domain="inventory",
            action="sync",
            payload={"warehouse_ids": ["WH001", "WH002", "WH003"]},
            priority=PriorityLevel.HIGH,
            timeout=30.0
        )
        print(f"Single task result: {result}")
        
        batch_tasks = [
            {"domain": "payments", "action": "process", "payload": {"amount": 100, "currency": "USD"}},
            {"domain": "reports", "action": "generate", "payload": {"type": "sales", "date_range": "2024-01"}},
            {"domain": "validation", "action": "check", "payload": {"data_type": "customers", "records": [1, 2, 3]}},
        ]
        
        batch_results = await executor.execute_batch(batch_tasks, max_concurrency=3)
        print(f"Batch results: {batch_results}")
        
        metrics = executor.get_metrics()
        print(f"Metrics: {json.dumps(metrics, indent=2)}")
        
    finally:
        await executor.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
