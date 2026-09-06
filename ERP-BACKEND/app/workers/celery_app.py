"""
Celery Application Configuration
Initializes Celery app with Redis broker and result backend.
Includes memory control hooks and task routing.
"""
import os
import gc
from celery import Celery
from celery.signals import task_postrun


# Redis configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery app
celery_app = Celery(
    'erp_workers',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.workers.tasks']
)

# Configuration
celery_app.conf.update(
    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=100,  # Recycle worker after 100 tasks (memory control)
    worker_concurrency=int(os.getenv("CELERY_CONCURRENCY", "4")),
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_transport_options={'visibility_timeout': 3600},
    
    # Result backend settings
    result_expires=3600,
    result_persistent=True,
)


@task_postrun.connect
def cleanup_after_task(**kwargs):
    """Trigger garbage collection after a task completes."""
    gc.collect()


def get_celery_app():
    """Return the Celery application instance."""
    return celery_app
