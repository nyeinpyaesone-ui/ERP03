"""
Queue Service - Redis Job Dispatch Layer
Dispatches heavy/AI tasks to Celery workers via Redis.
"""
import uuid
from typing import Any, Dict, Optional
from celery import Celery
from pydantic import BaseModel, Field


class JobRequest(BaseModel):
    task_name: str
    payload: Dict[str, Any]
    priority: int = Field(default=5, ge=1, le=10)


class JobStatus(BaseModel):
    job_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None


class QueueService:
    """
    Service for dispatching jobs to Celery workers.
    Ensures ERP API never runs heavy workloads in-process.
    """
    
    def __init__(self, celery_app: Celery):
        """Initialize the queue service with a Celery application.
        
        Parameters:
        	celery_app (Celery): Celery application used to dispatch and manage jobs.
        """
        self.celery_app = celery_app
    
    def submit_job(self, request: JobRequest) -> str:
        """
        Submit a job to the Celery queue for asynchronous processing.
        
        Args:
            request (JobRequest): Task name, payload, and queue priority for the job.
        
        Returns:
            str: The generated job ID used to track the submitted job.
        
        Raises:
            ValueError: If the requested task is not registered with Celery.
        """
        task = self.celery_app.tasks.get(request.task_name)
        if not task:
            raise ValueError(f"Task '{request.task_name}' not found")
        
        job_id = str(uuid.uuid4())
        
        # Apply priority via queue routing (optional enhancement)
        task.apply_async(
            args=[request.payload],
            task_id=job_id,
            priority=request.priority
        )
        
        return job_id
    
    def get_status(self, job_id: str) -> JobStatus:
        """
        Retrieve the current status and outcome information for a queued job.
        
        Parameters:
        	job_id (str): Identifier of the job to inspect.
        
        Returns:
        	JobStatus: The normalized job status, including its result for completed jobs or error information for failed jobs.
        """
        result = self.celery_app.AsyncResult(job_id)
        
        status_map = {
            'PENDING': 'queued',
            'STARTED': 'processing',
            'SUCCESS': 'completed',
            'FAILURE': 'failed',
            'RETRY': 'retrying',
            'REVOKED': 'cancelled'
        }
        
        status = status_map.get(result.status, 'unknown')
        
        return JobStatus(
            job_id=job_id,
            status=status,
            result=result.result if result.successful() else None,
            error=str(result.info) if result.failed() else None
        )
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a queued or running job.
        
        Parameters:
            job_id (str): Identifier of the job to cancel.
        
        Returns:
            bool: `True` after the cancellation request is issued.
        """
        self.celery_app.control.revoke(job_id, terminate=True)
        return True
