# -*- coding: utf-8 -*-
"""
Testes unitários para o sistema de processamento de jobs.
"""

import asyncio
import pytest
from unittest.mock import patch
from datetime import datetime

from api.processing import JobManager, Worker, JobQueue, Job, JobStatus, JobPriority, TaskType


class TestJob:
    """Testes para a classe Job."""

    def test_job_creation(self):
        """Testa criação de job."""
        job = Job(
            id="test-job-1",
            task_name="test_task",
            task_type=TaskType.ASYNC,
            kwargs={"input": "test"},
            priority=JobPriority.HIGH
        )
        
        assert job.id == "test-job-1"
        assert job.task_name == "test_task"
        assert job.task_type == TaskType.ASYNC
        assert job.kwargs == {"input": "test"}
        assert job.priority == JobPriority.HIGH
        assert job.status == JobStatus.PENDING
        assert job.result is None
        assert job.error is None
        assert job.created_at is not None

    def test_job_default_values(self):
        """Testa valores padrão do job."""
        job = Job(
            id="test-job",
            task_name="test_task",
            task_type=TaskType.SYNC
        )
        
        assert job.priority == JobPriority.NORMAL
        assert job.status == JobStatus.PENDING
        assert job.retry_count == 0
        assert job.max_retries == 3
        assert job.progress == 0.0
        assert job.args == tuple()
        assert job.kwargs == {}

    def test_job_status_updates(self):
        """Testa atualizações de status do job."""
        job = Job(
            id="test-job",
            task_name="test_task",
            task_type=TaskType.SYNC
        )
        
        # Testa diferentes status
        job.status = JobStatus.RUNNING
        assert job.status == JobStatus.RUNNING
        
        job.status = JobStatus.COMPLETED
        assert job.status == JobStatus.COMPLETED
        
        job.status = JobStatus.FAILED
        assert job.status == JobStatus.FAILED

    def test_job_progress_updates(self):
        """Testa atualizações de progresso."""
        job = Job(
            id="test-job",
            task_name="test_task",
            task_type=TaskType.SYNC
        )
        
        job.progress = 0.5
        job.progress_message = "50% complete"
        
        assert job.progress == 0.5
        assert job.progress_message == "50% complete"

    def test_job_retry_logic(self):
        """Testa lógica de retry."""
        job = Job(
            id="test-job",
            task_name="test_task",
            task_type=TaskType.SYNC,
            max_retries=5
        )
        
        assert job.max_retries == 5
        assert job.retry_count == 0
        
        job.retry_count += 1
        assert job.retry_count == 1

    def test_job_metadata(self):
        """Testa metadados do job."""
        metadata = {"user": "test", "source": "api"}
        tags = ["urgent", "test"]
        
        job = Job(
            id="test-job",
            task_name="test_task",
            task_type=TaskType.SYNC,
            metadata=metadata,
            tags=tags
        )
        
        assert job.metadata == metadata
        assert job.tags == tags


class TestJobQueue:
    """Testes para a fila de jobs."""

    def test_queue_initialization(self):
        """Testa inicialização da fila."""
        queue = JobQueue()
        assert queue.size() == 0
        assert queue.is_empty() is True

    def test_queue_put_get(self):
        """Testa inserção e remoção de jobs."""
        queue = JobQueue()
        job = Job(id="test-job", task_type="test", parameters={})
        
        queue.put(job)
        assert queue.size() == 1
        assert queue.is_empty() is False
        
        retrieved_job = queue.get()
        assert retrieved_job == job
        assert queue.size() == 0
        assert queue.is_empty() is True

    def test_queue_priority_ordering(self):
        """Testa ordenação por prioridade."""
        queue = JobQueue()
        
        job1 = Job(id="job1", task_type="test", parameters={}, priority=1)
        job2 = Job(id="job2", task_type="test", parameters={}, priority=3)
        job3 = Job(id="job3", task_type="test", parameters={}, priority=2)
        
        queue.put(job1)
        queue.put(job2)
        queue.put(job3)
        
        # Deve retornar na ordem de prioridade (maior primeiro)
        assert queue.get().id == "job2"  # prioridade 3
        assert queue.get().id == "job3"  # prioridade 2
        assert queue.get().id == "job1"  # prioridade 1

    def test_queue_get_empty(self):
        """Testa get em fila vazia."""
        queue = JobQueue()
        
        with pytest.raises(Exception):  # Deve lançar exceção
            queue.get()

    def test_queue_clear(self):
        """Testa limpeza da fila."""
        queue = JobQueue()
        
        job1 = Job(id="job1", task_type="test", parameters={})
        job2 = Job(id="job2", task_type="test", parameters={})
        
        queue.put(job1)
        queue.put(job2)
        assert queue.size() == 2
        
        queue.clear()
        assert queue.size() == 0
        assert queue.is_empty() is True


class TestWorker:
    """Testes para workers."""

    @pytest.mark.asyncio
    async def test_worker_initialization(self):
        """Testa inicialização do worker."""
        worker = Worker(worker_id="worker-1")
        
        assert worker.worker_id == "worker-1"
        assert worker.is_running is False
        assert worker.current_job is None

    @pytest.mark.asyncio
    async def test_worker_process_job_success(self):
        """Testa processamento bem-sucedido de job."""
        worker = Worker(worker_id="worker-1")
        job = Job(id="test-job", task_type="test_task", parameters={"input": "test"})
        
        # Mock da função de processamento
        async def mock_process(job_data):
            return {"output": "processed"}
        
        with patch.object(worker, '_process_task', side_effect=mock_process):
            await worker.process_job(job)
        
        assert job.status == JobStatus.COMPLETED
        assert job.result == {"output": "processed"}

    @pytest.mark.asyncio
    async def test_worker_process_job_failure(self):
        """Testa processamento com falha de job."""
        worker = Worker(worker_id="worker-1")
        job = Job(id="test-job", task_type="test_task", parameters={"input": "test"})
        
        # Mock da função de processamento que falha
        async def mock_process(job_data):
            raise Exception("Processing failed")
        
        with patch.object(worker, '_process_task', side_effect=mock_process):
            await worker.process_job(job)
        
        assert job.status == JobStatus.FAILED
        assert "Processing failed" in job.error

    @pytest.mark.asyncio
    async def test_worker_start_stop(self):
        """Testa início e parada do worker."""
        worker = Worker(worker_id="worker-1")
        queue = JobQueue()
        
        # Start worker
        task = worker.start(queue)
        assert worker.is_running is True
        
        # Stop worker
        await worker.stop()
        assert worker.is_running is False
        
        # Aguarda task finalizar
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


class TestJobManager:
    """Testes para o gerenciador de jobs."""

    @pytest.mark.asyncio
    async def test_job_manager_initialization(self):
        """Testa inicialização do JobManager."""
        manager = JobManager(max_workers=2)
        
        assert manager.max_workers == 2
        assert len(manager.workers) == 0
        assert manager.queue.is_empty() is True

    @pytest.mark.asyncio
    async def test_job_manager_submit_job(self):
        """Testa submissão de job."""
        manager = JobManager(max_workers=1)
        
        job_id = await manager.submit_job(
            task_type="test_task",
            parameters={"input": "test"},
            priority=1
        )
        
        assert job_id is not None
        assert len(job_id) > 0
        
        # Verifica se job foi adicionado à fila
        assert manager.queue.size() == 1

    @pytest.mark.asyncio
    async def test_job_manager_get_job_status(self):
        """Testa obtenção de status do job."""
        manager = JobManager(max_workers=1)
        
        job_id = await manager.submit_job(
            task_type="test_task",
            parameters={"input": "test"}
        )
        
        status = await manager.get_job_status(job_id)
        
        assert status is not None
        assert status["id"] == job_id
        assert status["status"] in ["pending", "running", "completed", "failed"]

    @pytest.mark.asyncio
    async def test_job_manager_get_job_status_nonexistent(self):
        """Testa obtenção de status de job inexistente."""
        manager = JobManager(max_workers=1)
        
        status = await manager.get_job_status("nonexistent-job")
        
        assert status is None

    @pytest.mark.asyncio
    async def test_job_manager_cancel_job(self):
        """Testa cancelamento de job."""
        manager = JobManager(max_workers=1)
        
        job_id = await manager.submit_job(
            task_type="test_task",
            parameters={"input": "test"}
        )
        
        success = await manager.cancel_job(job_id)
        assert success is True
        
        status = await manager.get_job_status(job_id)
        assert status["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_job_manager_get_statistics(self):
        """Testa obtenção de estatísticas."""
        manager = JobManager(max_workers=2)
        
        stats = await manager.get_statistics()
        
        assert "total_jobs" in stats
        assert "completed_jobs" in stats
        assert "failed_jobs" in stats
        assert "pending_jobs" in stats
        assert "active_workers" in stats
        assert isinstance(stats["total_jobs"], int)
        assert isinstance(stats["active_workers"], int)

    @pytest.mark.asyncio
    async def test_job_manager_get_queue_status(self):
        """Testa obtenção de status da fila."""
        manager = JobManager(max_workers=1)
        
        # Adiciona alguns jobs
        await manager.submit_job("test_task", {"input": "test1"})
        await manager.submit_job("test_task", {"input": "test2"})
        
        queue_status = await manager.get_queue_status()
        
        assert "queue_size" in queue_status
        assert "processing" in queue_status
        assert queue_status["queue_size"] >= 0
        assert queue_status["processing"] >= 0

    @pytest.mark.asyncio
    async def test_job_manager_start_stop(self):
        """Testa inicialização e parada do JobManager."""
        manager = JobManager(max_workers=2)
        
        await manager.start()
        assert len(manager.workers) == 2
        
        await manager.stop()
        assert all(not worker.is_running for worker in manager.workers)

    @pytest.mark.asyncio
    async def test_job_manager_concurrent_jobs(self):
        """Testa processamento concorrente de jobs."""
        manager = JobManager(max_workers=2)
        await manager.start()
        
        # Submete múltiplos jobs
        job_ids = []
        for i in range(5):
            job_id = await manager.submit_job(
                task_type="test_task",
                parameters={"input": f"test{i}"},
                priority=i
            )
            job_ids.append(job_id)
        
        # Aguarda um pouco para processamento
        await asyncio.sleep(0.1)
        
        # Verifica que jobs foram criados
        assert len(job_ids) == 5
        
        # Verifica estatísticas
        stats = await manager.get_statistics()
        assert stats["total_jobs"] >= 5
        
        await manager.stop()