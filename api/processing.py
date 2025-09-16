"""
Sistema de Processamento Assíncrono - E1.
Implementação completa de job queues, workers e gerenciamento de tarefas.
"""

import asyncio
import os
import pickle
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .logging import get_logger

logger = get_logger("processing")


class JobStatus(str, Enum):
    """Status de execução de jobs."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(str, Enum):
    """Prioridades de jobs."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskType(str, Enum):
    """Tipos de tasks."""

    SYNC = "sync"
    ASYNC = "async"


@dataclass
class Job:
    """Definição de um job."""

    id: str
    task_name: str
    task_type: TaskType
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0
    progress_message: str = ""
    error: Optional[str] = None
    worker_id: Optional[str] = None


@dataclass
class TaskDefinition:
    """Definição de uma task."""

    name: str
    function: Callable
    task_type: TaskType = TaskType.SYNC
    default_priority: JobPriority = JobPriority.NORMAL
    default_max_retries: int = 3
    default_timeout: Optional[float] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)


class JobQueue:
    """Fila de jobs com prioridade."""

    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self._queues = {
            JobPriority.CRITICAL: deque(),
            JobPriority.HIGH: deque(),
            JobPriority.NORMAL: deque(),
            JobPriority.LOW: deque(),
        }
        self._size = 0

    def put(self, job: Job):
        """Adiciona job à fila."""
        if self._size >= self.maxsize:
            raise Exception("Queue cheia")
        self._queues[job.priority].append(job)
        self._size += 1

    def get(self) -> Optional[Job]:
        """Obtém próximo job da fila."""
        for priority in [
            JobPriority.CRITICAL,
            JobPriority.HIGH,
            JobPriority.NORMAL,
            JobPriority.LOW,
        ]:
            if self._queues[priority]:
                job = self._queues[priority].popleft()
                self._size -= 1
                return job
        return None

    def qsize(self) -> int:
        """Retorna tamanho da fila."""
        return self._size


class Worker:
    """Worker para processar jobs."""

    def __init__(self, worker_id: str, job_manager: "JobManager"):
        self.worker_id = worker_id
        self.job_manager = job_manager
        self.current_job: Optional[Job] = None
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.jobs_processed = 0
        self.jobs_succeeded = 0
        self.jobs_failed = 0
        self.created_at = datetime.now(timezone.utc)

    async def start(self):
        """Inicia o worker."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._work_loop())

    async def stop(self):
        """Para o worker."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _work_loop(self):
        """Loop principal do worker."""
        while self.is_running:
            try:
                job = self.job_manager.get_next_job()
                if job:
                    await self._process_job(job)
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Erro no worker {self.worker_id}: {e}")

    async def _process_job(self, job: Job):
        """Processa um job."""
        self.current_job = job
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        job.worker_id = self.worker_id

        try:
            task_def = self.job_manager.task_definitions.get(job.task_name)
            if not task_def:
                raise ValueError(f"Task {job.task_name} não encontrada")

            # Executar task
            if task_def.task_type == TaskType.ASYNC:
                result = await task_def.function(*job.args, **job.kwargs)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: task_def.function(*job.args, **job.kwargs)
                )

            job.result = result
            job.status = JobStatus.COMPLETED
            job.progress = 1.0
            self.jobs_succeeded += 1

        except Exception as e:
            job.error = str(e)
            job.status = JobStatus.FAILED
            self.jobs_failed += 1
            logger.error(f"Erro processando job {job.id}: {e}")

        finally:
            job.completed_at = datetime.now(timezone.utc)
            self.current_job = None
            self.jobs_processed += 1


class JobManager:
    """Gerenciador principal de jobs."""

    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.job_queue = JobQueue()
        self.workers: Dict[str, Worker] = {}
        self.jobs: Dict[str, Job] = {}
        self.task_definitions: Dict[str, TaskDefinition] = {}
        self.scheduled_jobs: List[Job] = []
        self.is_running = False
        self._start_time = time.time()
        self._scheduler_task: Optional[asyncio.Task] = None

    async def start(self):
        """Inicia o job manager."""
        if self.is_running:
            return

        self.is_running = True
        self._start_time = time.time()

        # Criar workers
        for i in range(self.num_workers):
            worker_id = f"worker-{i+1}"
            worker = Worker(worker_id, self)
            self.workers[worker_id] = worker
            await worker.start()

        # Iniciar scheduler
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info(f"Job manager iniciado com {self.num_workers} workers")

    async def stop(self):
        """Para o job manager."""
        if not self.is_running:
            return

        self.is_running = False

        # Parar scheduler
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        # Parar workers
        for worker in self.workers.values():
            await worker.stop()

        logger.info("Job manager finalizado")

    def register_task(
        self,
        name: str,
        function: Callable,
        task_type: TaskType = TaskType.SYNC,
        default_priority: JobPriority = JobPriority.NORMAL,
        default_max_retries: int = 3,
        default_timeout: Optional[float] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
    ):
        """Registra uma task no sistema."""
        task_def = TaskDefinition(
            name=name,
            function=function,
            task_type=task_type,
            default_priority=default_priority,
            default_max_retries=default_max_retries,
            default_timeout=default_timeout,
            description=description,
            tags=tags or [],
        )
        self.task_definitions[name] = task_def
        logger.info(f"Task registrada: {name}")

    def submit_job(
        self,
        task_name: str,
        *args: Any,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: Optional[int] = None,
        timeout: Optional[float] = None,
        scheduled_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """Submete um novo job."""
        task_def = self.task_definitions.get(task_name)
        if not task_def:
            raise ValueError(f"Task {task_name} não encontrada")

        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            task_name=task_name,
            task_type=task_def.task_type,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries or task_def.default_max_retries,
            timeout=timeout or task_def.default_timeout,
            scheduled_at=scheduled_at,
            tags=tags or [],
            metadata=metadata or {},
        )

        self.jobs[job_id] = job

        if scheduled_at and scheduled_at > datetime.now(timezone.utc):
            self.scheduled_jobs.append(job)
        else:
            self.job_queue.put(job)

        logger.info(f"Job {job_id} submetido")
        return job_id

    def get_next_job(self) -> Optional[Job]:
        """Obtém próximo job da queue."""
        return self.job_queue.get()

    def get_job(self, job_id: str) -> Optional[Job]:
        """Obtém um job pelo ID."""
        return self.jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Cancela um job."""
        job = self.jobs.get(job_id)
        if not job:
            return False

        if job.status in [JobStatus.PENDING]:
            job.status = JobStatus.CANCELLED
            job.error = "Job cancelado pelo usuário"
            job.completed_at = datetime.now(timezone.utc)
            logger.info(f"Job {job_id} cancelado")
            return True

        return False

    def add_workers(self, count: int) -> int:
        """Adiciona workers."""
        added = 0
        for _ in range(count):
            worker_id = f"worker-{len(self.workers) + 1}"
            worker = Worker(worker_id, self)
            self.workers[worker_id] = worker
            if self.is_running:
                asyncio.create_task(worker.start())
            added += 1
        return added

    def remove_workers(self, count: int) -> int:
        """Remove workers."""
        worker_ids = list(self.workers.keys())
        removed = 0
        for worker_id in worker_ids[:count]:
            worker = self.workers.pop(worker_id, None)
            if worker and self.is_running:
                asyncio.create_task(worker.stop())
                removed += 1
        return removed

    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas."""
        uptime = time.time() - self._start_time if self.is_running else 0.0
        return {
            "workers": {
                "total": len(self.workers),
                "active": len([w for w in self.workers.values() if w.current_job]),
                "idle": len([w for w in self.workers.values() if not w.current_job]),
            },
            "jobs": {
                "total": len(self.jobs),
                "pending": len(
                    [j for j in self.jobs.values() if j.status == JobStatus.PENDING]
                ),
                "running": len(
                    [j for j in self.jobs.values() if j.status == JobStatus.RUNNING]
                ),
                "completed": len(
                    [j for j in self.jobs.values() if j.status == JobStatus.COMPLETED]
                ),
                "failed": len(
                    [j for j in self.jobs.values() if j.status == JobStatus.FAILED]
                ),
            },
            "queue_size": self.job_queue.qsize(),
            "uptime": uptime,
        }

    def get_worker_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas dos workers."""
        return {
            worker_id: {
                "is_busy": bool(worker.current_job),
                "current_job_id": worker.current_job.id if worker.current_job else None,
                "jobs_processed": worker.jobs_processed,
                "jobs_succeeded": worker.jobs_succeeded,
                "jobs_failed": worker.jobs_failed,
                "created_at": worker.created_at,
            }
            for worker_id, worker in self.workers.items()
        }

    async def _scheduler_loop(self):
        """Loop do scheduler para jobs agendados."""
        while self.is_running:
            try:
                now = datetime.now(timezone.utc)
                jobs_to_schedule = []

                for job in self.scheduled_jobs[:]:
                    if job.scheduled_at and job.scheduled_at <= now:
                        self.scheduled_jobs.remove(job)
                        jobs_to_schedule.append(job)

                for job in jobs_to_schedule:
                    self.job_queue.put(job)
                    logger.info(f"Job agendado {job.id} movido para queue")

                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Erro no scheduler: {e}")


# Instância global
job_manager = JobManager()


# Decorators
def task(
    name: Optional[str] = None,
    task_type: TaskType = TaskType.SYNC,
    priority: JobPriority = JobPriority.NORMAL,
    max_retries: int = 3,
    timeout: Optional[float] = None,
    description: str = "",
    tags: Optional[List[str]] = None,
):
    """Decorator para registrar tasks."""

    def decorator(func: Callable) -> Callable:
        task_name = name or func.__name__
        job_manager.register_task(
            name=task_name,
            function=func,
            task_type=task_type,
            default_priority=priority,
            default_max_retries=max_retries,
            default_timeout=timeout,
            description=description,
            tags=tags or [],
        )
        return func

    return decorator


def async_task(
    name: Optional[str] = None,
    priority: JobPriority = JobPriority.NORMAL,
    max_retries: int = 3,
    timeout: Optional[float] = None,
    description: str = "",
    tags: Optional[List[str]] = None,
):
    """Decorator para async tasks."""
    return task(name, TaskType.ASYNC, priority, max_retries, timeout, description, tags)


# Funções helper
async def start_processing():
    """Inicia o sistema de processamento."""
    try:
        await job_manager.start()
        logger.info("Sistema de processamento iniciado")
    except Exception as e:
        logger.error(f"Erro iniciando processamento: {e}")


async def stop_processing():
    """Para o sistema de processamento."""
    try:
        await job_manager.stop()
        logger.info("Sistema de processamento finalizado")
    except Exception as e:
        logger.error(f"Erro finalizando processamento: {e}")


def submit_job(task_name: str, *args: Any, **kwargs: Any) -> str:
    """Submete um job para execução."""
    return job_manager.submit_job(task_name, *args, **kwargs)


def get_job_status(job_id: str) -> Optional[Job]:
    """Obtém status de um job."""
    return job_manager.get_job(job_id)
