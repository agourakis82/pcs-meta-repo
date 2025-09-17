"""
Router para endpoints de processamento - Sistema E1.
Gerenciamento de jobs, workers e estatísticas do sistema de processamento assíncrono.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..auth import verify_token
from ..logging import get_logger
from ..processing import JobPriority, JobStatus, job_manager

router = APIRouter(prefix="/processing", tags=["processing"])
logger = get_logger(__name__)


# Modelos Pydantic
class JobSubmissionRequest(BaseModel):
    """Request para submissão de job."""
    task_name: str = Field(..., description="Nome da task registrada")
    args: List[Any] = Field(default=[], description="Argumentos posicionais")
    kwargs: Dict[str, Any] = Field(default={}, description="Argumentos nomeados")
    priority: JobPriority = Field(default=JobPriority.NORMAL, description="Prioridade do job")
    max_retries: Optional[int] = Field(default=None, description="Máximo de tentativas")
    timeout: Optional[float] = Field(default=None, description="Timeout em segundos")
    scheduled_at: Optional[datetime] = Field(default=None, description="Agendar para execução")
    tags: List[str] = Field(default=[], description="Tags para classificação")
    metadata: Dict[str, Any] = Field(default={}, description="Metadados adicionais")


class JobResponse(BaseModel):
    """Response com informações do job."""
    id: str
    task_name: str
    status: JobStatus
    priority: JobPriority
    created_at: datetime
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: float
    retry_count: int
    max_retries: int
    result: Optional[Any]
    error: Optional[str]
    tags: List[str]
    metadata: Dict[str, Any]


class JobStatsResponse(BaseModel):
    """Response com estatísticas dos jobs."""
    total_workers: int
    active_workers: int
    idle_workers: int
    jobs: Dict[str, int]
    queue_size: int
    uptime: float


class WorkerStatsResponse(BaseModel):
    """Response com estatísticas dos workers."""
    worker_id: str
    is_busy: bool
    current_job_id: Optional[str]
    jobs_processed: int
    jobs_succeeded: int
    jobs_failed: int
    created_at: datetime


class TaskListResponse(BaseModel):
    """Response com lista de tasks registradas."""
    name: str
    task_type: str
    default_priority: JobPriority
    default_max_retries: int
    default_timeout: Optional[float]
    description: str
    tags: List[str]


# Endpoints
@router.post("/jobs", response_model=Dict[str, str], status_code=status.HTTP_201_CREATED)
async def submit_job(
    job_request: JobSubmissionRequest,
    current_user: dict = Depends(verify_token)
):
    """
    Submete um novo job para processamento.
    
    - **task_name**: Nome da task registrada no sistema
    - **args**: Argumentos posicionais para a task
    - **kwargs**: Argumentos nomeados para a task
    - **priority**: Prioridade de execução (LOW, NORMAL, HIGH, CRITICAL)
    - **max_retries**: Número máximo de tentativas em caso de falha
    - **timeout**: Timeout em segundos para execução
    - **scheduled_at**: Data/hora para agendar execução
    - **tags**: Tags para classificação e filtros
    - **metadata**: Metadados adicionais
    """
    try:
        # Verificar se a task existe
        if job_request.task_name not in job_manager.task_definitions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task '{job_request.task_name}' não encontrada"
            )

        # Submeter job
        job_id = job_manager.submit_job(
            task_name=job_request.task_name,
            *job_request.args,
            priority=job_request.priority,
            max_retries=job_request.max_retries,
            timeout=job_request.timeout,
            scheduled_at=job_request.scheduled_at,
            tags=job_request.tags,
            metadata=job_request.metadata,
            **job_request.kwargs
        )

        logger.info(f"Job {job_id} submetido por usuário {current_user.get('username')}")
        
        return {
            "job_id": job_id,
            "message": "Job submetido com sucesso",
            "status": "submitted"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao submeter job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao submeter job"
        )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(verify_token)
):
    """
    Obtém status e informações detalhadas de um job específico.
    
    - **job_id**: ID único do job
    """
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} não encontrado"
            )

        return JobResponse(
            id=job.id,
            task_name=job.task_name,
            status=job.status,
            priority=job.priority,
            created_at=job.created_at,
            scheduled_at=job.scheduled_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            progress=job.progress,
            retry_count=job.retry_count,
            max_retries=job.max_retries,
            result=job.result,
            error=job.error,
            tags=job.tags,
            metadata=job.metadata
        )

    except Exception as e:
        logger.error(f"Erro ao buscar job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar job"
        )


@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    status_filter: Optional[JobStatus] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(verify_token)
):
    """
    Lista jobs com filtros opcionais.
    
    - **status_filter**: Filtrar por status específico
    - **limit**: Máximo de jobs retornados (padrão: 100)
    - **offset**: Número de jobs para pular (padrão: 0)
    """
    try:
        jobs = list(job_manager.jobs.values())
        
        # Aplicar filtro de status
        if status_filter:
            jobs = [job for job in jobs if job.status == status_filter]
        
        # Ordenar por data de criação (mais recentes primeiro)
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        # Aplicar paginação
        jobs = jobs[offset:offset + limit]
        
        return [
            JobResponse(
                id=job.id,
                task_name=job.task_name,
                status=job.status,
                priority=job.priority,
                created_at=job.created_at,
                scheduled_at=job.scheduled_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                progress=job.progress,
                retry_count=job.retry_count,
                max_retries=job.max_retries,
                result=job.result,
                error=job.error,
                tags=job.tags,
                metadata=job.metadata
            )
            for job in jobs
        ]

    except Exception as e:
        logger.error(f"Erro ao listar jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar jobs"
        )


@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: dict = Depends(verify_token)
):
    """
    Cancela um job pendente ou em execução.
    
    - **job_id**: ID único do job a ser cancelado
    """
    try:
        success = job_manager.cancel_job(job_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} não encontrado ou não pode ser cancelado"
            )

        logger.info(f"Job {job_id} cancelado por usuário {current_user.get('username')}")
        
        return {
            "message": f"Job {job_id} cancelado com sucesso",
            "status": "cancelled"
        }

    except Exception as e:
        logger.error(f"Erro ao cancelar job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao cancelar job"
        )


@router.get("/stats", response_model=JobStatsResponse)
async def get_processing_stats(current_user: dict = Depends(verify_token)):
    """
    Obtém estatísticas gerais do sistema de processamento.
    
    Inclui informações sobre workers, jobs e performance do sistema.
    """
    try:
        stats = job_manager.get_stats()
        
        return JobStatsResponse(
            total_workers=stats["workers"]["total"],
            active_workers=stats["workers"]["active"],
            idle_workers=stats["workers"]["idle"],
            jobs=stats["jobs"],
            queue_size=stats.get("queue_size", 0),
            uptime=stats.get("uptime", 0.0)
        )

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao obter estatísticas"
        )


@router.get("/workers", response_model=List[WorkerStatsResponse])
async def get_worker_stats(current_user: dict = Depends(verify_token)):
    """
    Obtém estatísticas detalhadas de todos os workers.
    
    Inclui informações sobre estado atual, jobs processados e performance.
    """
    try:
        worker_stats = job_manager.get_worker_stats()
        
        return [
            WorkerStatsResponse(
                worker_id=worker_id,
                is_busy=stats["is_busy"],
                current_job_id=stats.get("current_job_id"),
                jobs_processed=stats["jobs_processed"],
                jobs_succeeded=stats["jobs_succeeded"],
                jobs_failed=stats["jobs_failed"],
                created_at=stats["created_at"]
            )
            for worker_id, stats in worker_stats.items()
        ]

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas dos workers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao obter estatísticas dos workers"
        )


@router.get("/tasks", response_model=List[TaskListResponse])
async def list_tasks(current_user: dict = Depends(verify_token)):
    """
    Lista todas as tasks registradas no sistema.
    
    Útil para verificar quais tasks estão disponíveis para submissão de jobs.
    """
    try:
        tasks = []
        for name, task_def in job_manager.task_definitions.items():
            tasks.append(TaskListResponse(
                name=name,
                task_type=task_def.task_type.value,
                default_priority=task_def.default_priority,
                default_max_retries=task_def.default_max_retries,
                default_timeout=task_def.default_timeout,
                description=task_def.description,
                tags=task_def.tags
            ))
        
        # Ordenar por nome
        tasks.sort(key=lambda x: x.name)
        
        return tasks

    except Exception as e:
        logger.error(f"Erro ao listar tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar tasks"
        )


@router.post("/workers/{action}")
async def manage_workers(
    action: str,
    count: int = 1,
    current_user: dict = Depends(verify_token)
):
    """
    Gerencia workers do sistema de processamento.
    
    - **action**: Ação a ser executada ('add' ou 'remove')
    - **count**: Número de workers a adicionar ou remover (padrão: 1)
    """
    try:
        if action not in ["add", "remove"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ação deve ser 'add' ou 'remove'"
            )

        if count < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Count deve ser maior que zero"
            )

        if action == "add":
            added = job_manager.add_workers(count)
            logger.info(f"{added} workers adicionados por usuário {current_user.get('username')}")
            return {
                "message": f"{added} workers adicionados com sucesso",
                "action": "add",
                "count": added
            }
        else:  # remove
            removed = job_manager.remove_workers(count)
            logger.info(f"{removed} workers removidos por usuário {current_user.get('username')}")
            return {
                "message": f"{removed} workers removidos com sucesso",
                "action": "remove",
                "count": removed
            }

    except Exception as e:
        logger.error(f"Erro ao gerenciar workers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao gerenciar workers"
        )


@router.get("/health")
async def processing_health_check():
    """
    Verificação de saúde do sistema de processamento.
    
    Endpoint público para monitoramento de infraestrutura.
    """
    try:
        stats = job_manager.get_stats()
        
        is_healthy = (
            stats["workers"]["total"] > 0 and
            job_manager.is_running
        )
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "workers_active": stats["workers"]["active"],
            "workers_total": stats["workers"]["total"],
            "jobs_pending": stats["jobs"].get("pending", 0),
            "system_running": job_manager.is_running
        }

    except Exception as e:
        logger.error(f"Erro na verificação de saúde: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }