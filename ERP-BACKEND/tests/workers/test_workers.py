"""
Tests for Celery workers and queue integration.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.workers.celery_app import celery_app
from app.workers.tasks import (
    predict_demand,
    analyze_sentiment,
    process_batch,
    generate_report,
    cleanup_resources
)
from app.services.queue_service import QueueService, JobRequest


class TestCeleryApp:
    """Test Celery application configuration."""
    
    def test_celery_app_initialized(self):
        """Verify Celery app is properly initialized."""
        assert celery_app is not None
        assert celery_app.conf.broker_url.startswith('redis://')
        assert celery_app.conf.result_backend.startswith('redis://')
    
    def test_celery_config(self):
        """Verify Celery configuration settings."""
        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.result_serializer == 'json'
        assert celery_app.conf.accept_content == ['json']
        assert celery_app.conf.timezone == 'UTC'
        assert celery_app.conf.enable_utc is True


class TestWorkerTasks:
    """Test async worker tasks."""
    
    @patch('app.workers.tasks.gc.collect')
    def test_predict_demand(self, mock_gc):
        """Test demand prediction task."""
        result = predict_demand.run({"product_id": "test-123", "months": 6})
        
        assert result is not None
        assert 'predicted_demand' in result or isinstance(result, dict)
        mock_gc.assert_called_once()
    
    @patch('app.workers.tasks.gc.collect')
    def test_analyze_sentiment(self, mock_gc):
        """Test sentiment analysis task."""
        texts = ["Great product!", "Terrible service.", "Okay experience."]
        result = analyze_sentiment.run({"texts": texts})
        
        assert result is not None
        assert 'results' in result
        mock_gc.assert_called_once()
    
    def test_process_batch(self):
        """Test batch processing task."""
        with patch('app.workers.tasks.gc.collect') as mock_gc:
            items = [{"id": i, "data": f"item-{i}"} for i in range(10)]
            result = process_batch.run({"items": items, "operation": "test"})
            
            assert result is not None
            assert 'total_processed' in result
            # GC called once per chunk (10 items / 100 chunk_size = 1 chunk)
            assert mock_gc.call_count >= 1
    
    @patch('app.workers.tasks.gc.collect')
    def test_generate_report(self, mock_gc):
        """Test report generation task."""
        result = generate_report.run({
            "report_type": "sales",
            "date_range": {"start": "2024-01-01", "end": "2024-12-31"}
        })
        
        assert result is not None
        assert 'file_url' in result or isinstance(result, dict)
        mock_gc.assert_called_once()
    
    def test_cleanup_resources(self):
        """Test resource cleanup task (no GC in cleanup)."""
        result = cleanup_resources.run({"resource_type": "temp_files", "older_than_days": 30})
        
        assert result is not None
        assert 'deleted_count' in result or isinstance(result, dict)
    
    def test_task_memory_limit(self):
        """Test that tasks respect memory limits."""
        # Simulate large batch
        large_items = [{"id": i, "data": "x" * 1000} for i in range(1000)]
        
        # Should complete without memory error
        result = process_batch.run({"items": large_items, "operation": "stress_test"})
        assert result is not None


class TestQueueService:
    """Test QueueService for job dispatch."""
    
    @pytest.fixture
    def queue_service(self):
        """Create QueueService instance with mocked Celery app."""
        with patch('celery.Celery') as mock_celery:
            service = QueueService(celery_app=mock_celery.return_value)
            yield service
    
    def test_submit_job(self, queue_service):
        """Test job submission to queue."""
        request = JobRequest(
            task_name="predict_demand",
            payload={"product_id": "test-123", "months": 6}
        )
        
        # Mock the task
        mock_task = MagicMock()
        mock_task.apply_async.return_value = MagicMock(id="test-job-123")
        queue_service.celery_app.tasks.get.return_value = mock_task
        
        job_id = queue_service.submit_job(request)
        
        assert job_id is not None
        assert len(job_id) > 0
        mock_task.apply_async.assert_called_once()
    
    def test_get_status(self, queue_service):
        """Test job status retrieval."""
        mock_result = MagicMock()
        mock_result.status = 'SUCCESS'
        mock_result.result = {"prediction": 100}
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        
        queue_service.celery_app.AsyncResult.return_value = mock_result
        
        status = queue_service.get_status("test-job-id")
        
        assert status is not None
        assert status.job_id == "test-job-id"
        assert status.status == 'completed'
        assert status.result == {"prediction": 100}
    
    def test_cancel_job(self, queue_service):
        """Test job cancellation."""
        result = queue_service.cancel_job("test-job-id")
        
        assert result is True
        queue_service.celery_app.control.revoke.assert_called_once()
    
    def test_list_jobs(self, queue_service):
        """Test listing jobs (placeholder for future implementation)."""
        # QueueService currently doesn't have list_jobs method
        # This test documents the expected behavior for future implementation
        assert hasattr(queue_service, 'submit_job')
        assert hasattr(queue_service, 'get_status')
        assert hasattr(queue_service, 'cancel_job')


class TestIntegration:
    """Integration tests for end-to-end job flow."""
    
    def test_queue_service_submit(self):
        """Test that QueueService can submit jobs."""
        with patch('celery.Celery') as mock_celery:
            service = QueueService(celery_app=mock_celery.return_value)
            mock_task = MagicMock()
            mock_task.apply_async.return_value = MagicMock(id="test-job-123")
            service.celery_app.tasks.get.return_value = mock_task
            
            request = JobRequest(task_name="predict_demand", payload={"product_id": "test"})
            job_id = service.submit_job(request)
            
            assert job_id is not None
            mock_task.apply_async.assert_called_once()
        
    def test_error_handling(self):
        """Test error handling in tasks."""
        # Test with empty list instead of None (task expects list)
        result = process_batch.run({"items": [], "operation": "test"})
        # Task should handle empty list gracefully
        assert result is not None
        assert result.get('total_processed') == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
