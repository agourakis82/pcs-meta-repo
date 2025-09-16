"""
Sistema H4 - Data Processing Engine

Engine principal para processamento de dados com suporte a:
- Pipelines ETL configuráveis
- Processamento batch e streaming
- Distribuição multi-thread/multi-process
- Integração com sistemas H1, H2, H3
"""

import asyncio
import json
import logging
import pickle
import time
import uuid
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, Iterator, List, Optional

from .config import (
    DataSinkConfig,
    DataSourceConfig,
    DistributionStrategy,
    H4Config,
    PipelineConfig,
    ProcessingMode,
    get_h4_config,
)

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """Status de processamento."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class DataType(Enum):
    """Tipos de dados processados."""

    RECORD = "record"
    BATCH = "batch"
    STREAM = "stream"
    FILE = "file"


@dataclass
class ProcessingMetrics:
    """Métricas de processamento."""

    pipeline_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    records_processed: int = 0
    records_failed: int = 0
    bytes_processed: int = 0
    processing_time_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    error_count: int = 0
    warning_count: int = 0
    checkpoint_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converte métricas para dicionário."""
        return {
            "pipeline_id": self.pipeline_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status.value,
            "records_processed": self.records_processed,
            "records_failed": self.records_failed,
            "bytes_processed": self.bytes_processed,
            "processing_time_seconds": self.processing_time_seconds,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "checkpoint_count": self.checkpoint_count,
            "metadata": self.metadata,
        }


@dataclass
class ProcessingContext:
    """Contexto de processamento."""

    pipeline_id: str
    execution_id: str
    config: PipelineConfig
    metrics: ProcessingMetrics
    cache: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    logger: Optional[logging.Logger] = None

    def __post_init__(self):
        if self.logger is None:
            self.logger = logging.getLogger(f"h4.pipeline.{self.pipeline_id}")


class DataProcessor(ABC):
    """Classe base para processadores de dados."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"h4.processor.{name}")

    @abstractmethod
    async def process(self, data: Any, context: ProcessingContext) -> Any:
        """Processa dados."""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configuração do processador."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Retorna schema de entrada/saída do processador."""
        return {"input": {"type": "any"}, "output": {"type": "any"}, "config": {}}


class DataSource(ABC):
    """Classe base para fontes de dados."""

    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.logger = logging.getLogger(f"h4.source.{config.name}")

    @abstractmethod
    async def read(self, context: ProcessingContext) -> AsyncIterator[Any]:
        """Lê dados da fonte."""
        pass

    @abstractmethod
    async def validate(self) -> bool:
        """Valida se a fonte está acessível."""
        pass

    async def estimate_size(self) -> Optional[int]:
        """Estima tamanho dos dados (número de registros)."""
        return None


class DataSink(ABC):
    """Classe base para destinos de dados."""

    def __init__(self, config: DataSinkConfig):
        self.config = config
        self.logger = logging.getLogger(f"h4.sink.{config.name}")

    @abstractmethod
    async def write(self, data: Any, context: ProcessingContext) -> bool:
        """Escreve dados no destino."""
        pass

    @abstractmethod
    async def validate(self) -> bool:
        """Valida se o destino está acessível."""
        pass

    async def initialize(self) -> bool:
        """Inicializa o destino (cria tabelas, diretórios, etc.)."""
        return True

    async def finalize(self) -> bool:
        """Finaliza escrita (commit, close, etc.)."""
        return True


class PipelineExecutor:
    """Executor de pipelines de processamento."""

    def __init__(self, config: H4Config = None):
        self.config = config or get_h4_config()
        self.logger = logging.getLogger("h4.executor")
        self.processors: Dict[str, DataProcessor] = {}
        self.sources: Dict[str, DataSource] = {}
        self.sinks: Dict[str, DataSink] = {}
        self.running_pipelines: Dict[str, ProcessingContext] = {}
        self.metrics_store: Dict[str, ProcessingMetrics] = {}

        # Integration with other systems
        self.h1_integration = None
        self.h2_integration = None
        self.h3_integration = None

        self._initialize_integrations()

    def _initialize_integrations(self):
        """Inicializa integrações com outros sistemas."""
        try:
            if self.config.h1_monitoring_enabled:
                from ..monitoring import metrics_collector

                self.h1_integration = metrics_collector
                self.logger.info("H1 monitoring integration enabled")
        except ImportError:
            self.logger.warning("H1 monitoring not available")

        try:
            if self.config.h2_cache_enabled:
                from ..cache import cache_manager

                self.h2_integration = cache_manager
                self.logger.info("H2 cache integration enabled")
        except ImportError:
            self.logger.warning("H2 cache not available")

        try:
            if self.config.h3_api_enabled:
                self.logger.info("H3 API integration available")
        except ImportError:
            self.logger.warning("H3 API not available")

    def register_processor(self, processor: DataProcessor):
        """Registra um processador."""
        self.processors[processor.name] = processor
        self.logger.info(f"Registered processor: {processor.name}")

    def register_source(self, source: DataSource):
        """Registra uma fonte de dados."""
        self.sources[source.config.name] = source
        self.logger.info(f"Registered source: {source.config.name}")

    def register_sink(self, sink: DataSink):
        """Registra um destino de dados."""
        self.sinks[sink.config.name] = sink
        self.logger.info(f"Registered sink: {sink.config.name}")

    async def execute_pipeline(self, config: PipelineConfig) -> ProcessingMetrics:
        """Executa um pipeline completo."""
        execution_id = str(uuid.uuid4())
        pipeline_id = config.name

        # Cria contexto de processamento
        metrics = ProcessingMetrics(pipeline_id=pipeline_id, start_time=datetime.now())

        context = ProcessingContext(
            pipeline_id=pipeline_id,
            execution_id=execution_id,
            config=config,
            metrics=metrics,
        )

        # Registra pipeline em execução
        self.running_pipelines[execution_id] = context

        try:
            context.logger.info(f"Starting pipeline execution: {pipeline_id}")

            # Valida configuração
            await self._validate_pipeline_config(config)

            # Inicializa destinos
            for sink_config in config.sinks:
                if sink_config.name in self.sinks:
                    await self.sinks[sink_config.name].initialize()

            # Executa pipeline baseado no modo
            if config.processing.mode == ProcessingMode.BATCH:
                await self._execute_batch_pipeline(context)
            elif config.processing.mode == ProcessingMode.STREAMING:
                await self._execute_streaming_pipeline(context)
            elif config.processing.mode == ProcessingMode.REAL_TIME:
                await self._execute_realtime_pipeline(context)
            else:
                await self._execute_hybrid_pipeline(context)

            # Finaliza destinos
            for sink_config in config.sinks:
                if sink_config.name in self.sinks:
                    await self.sinks[sink_config.name].finalize()

            # Marca como completado
            metrics.status = ProcessingStatus.COMPLETED
            metrics.end_time = datetime.now()
            metrics.processing_time_seconds = (
                metrics.end_time - metrics.start_time
            ).total_seconds()

            context.logger.info(f"Pipeline completed: {pipeline_id}")

        except Exception as e:
            context.logger.error(f"Pipeline failed: {pipeline_id}", exc_info=True)
            metrics.status = ProcessingStatus.FAILED
            metrics.end_time = datetime.now()
            metrics.error_count += 1
            metrics.metadata["error"] = str(e)

        finally:
            # Remove de pipelines em execução
            self.running_pipelines.pop(execution_id, None)

            # Armazena métricas
            self.metrics_store[execution_id] = metrics

            # Reporta métricas para H1
            await self._report_metrics(metrics)

        return metrics

    async def _validate_pipeline_config(self, config: PipelineConfig):
        """Valida configuração do pipeline."""
        # Valida fontes
        for source_config in config.sources:
            if source_config.name not in self.sources:
                raise ValueError(f"Source not registered: {source_config.name}")

            source = self.sources[source_config.name]
            if not await source.validate():
                raise ValueError(f"Source validation failed: {source_config.name}")

        # Valida destinos
        for sink_config in config.sinks:
            if sink_config.name not in self.sinks:
                raise ValueError(f"Sink not registered: {sink_config.name}")

            sink = self.sinks[sink_config.name]
            if not await sink.validate():
                raise ValueError(f"Sink validation failed: {sink_config.name}")

    async def _execute_batch_pipeline(self, context: ProcessingContext):
        """Executa pipeline em modo batch."""
        config = context.config

        if config.processing.distribution == DistributionStrategy.SINGLE_NODE:
            await self._execute_single_node(context)
        elif config.processing.distribution == DistributionStrategy.MULTI_THREAD:
            await self._execute_multi_thread(context)
        elif config.processing.distribution == DistributionStrategy.MULTI_PROCESS:
            await self._execute_multi_process(context)
        else:
            await self._execute_distributed(context)

    async def _execute_streaming_pipeline(self, context: ProcessingContext):
        """Executa pipeline em modo streaming."""
        context.logger.info("Executing streaming pipeline")

        # Para streaming, processa dados conforme chegam
        for source_config in context.config.sources:
            source = self.sources[source_config.name]

            async for data_batch in source.read(context):
                # Processa batch
                await self._process_data_batch(data_batch, context)

                # Checkpoint periódico
                context.metrics.checkpoint_count += 1

                # Verifica se deve parar
                if context.metrics.status == ProcessingStatus.CANCELLED:
                    break

    async def _execute_realtime_pipeline(self, context: ProcessingContext):
        """Executa pipeline em modo tempo real."""
        context.logger.info("Executing real-time pipeline")

        # Similar ao streaming, mas com latência mínima
        await self._execute_streaming_pipeline(context)

    async def _execute_hybrid_pipeline(self, context: ProcessingContext):
        """Executa pipeline em modo híbrido."""
        context.logger.info("Executing hybrid pipeline")

        # Combina batch e streaming
        await self._execute_batch_pipeline(context)

    async def _execute_single_node(self, context: ProcessingContext):
        """Executa em nó único."""
        for source_config in context.config.sources:
            source = self.sources[source_config.name]

            async for data_batch in source.read(context):
                await self._process_data_batch(data_batch, context)

    async def _execute_multi_thread(self, context: ProcessingContext):
        """Executa com múltiplas threads."""
        max_workers = context.config.processing.max_workers

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            tasks = []

            for source_config in context.config.sources:
                source = self.sources[source_config.name]

                async for data_batch in source.read(context):
                    # Submete para thread pool
                    future = executor.submit(
                        self._process_data_batch_sync, data_batch, context
                    )
                    tasks.append(future)

            # Aguarda conclusão
            for future in tasks:
                future.result()

    async def _execute_multi_process(self, context: ProcessingContext):
        """Executa com múltiplos processos."""
        max_workers = context.config.processing.max_workers

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            tasks = []

            for source_config in context.config.sources:
                source = self.sources[source_config.name]

                async for data_batch in source.read(context):
                    # Submete para process pool
                    future = executor.submit(
                        self._process_data_batch_sync, data_batch, context
                    )
                    tasks.append(future)

            # Aguarda conclusão
            for future in tasks:
                future.result()

    async def _execute_distributed(self, context: ProcessingContext):
        """Executa de forma distribuída."""
        context.logger.warning("Distributed execution not implemented yet")
        # TODO: Implementar com Celery, Dask ou similar
        await self._execute_single_node(context)

    async def _process_data_batch(self, data_batch: Any, context: ProcessingContext):
        """Processa um batch de dados."""
        try:
            # Aplica processadores (se houver)
            processed_data = data_batch

            # TODO: Aplicar processadores configurados
            # for processor_name in context.config.processors:
            #     processor = self.processors[processor_name]
            #     processed_data = await processor.process(processed_data, context)

            # Escreve nos destinos
            for sink_config in context.config.sinks:
                sink = self.sinks[sink_config.name]
                await sink.write(processed_data, context)

            # Atualiza métricas
            if isinstance(data_batch, list):
                context.metrics.records_processed += len(data_batch)
            else:
                context.metrics.records_processed += 1

            # Calcula tamanho aproximado
            try:
                size = len(str(data_batch).encode("utf-8"))
                context.metrics.bytes_processed += size
            except:
                pass

        except Exception as e:
            context.logger.error(f"Error processing batch: {e}")
            context.metrics.records_failed += 1
            context.metrics.error_count += 1

            if context.config.processing.error_handling == "abort":
                raise

    def _process_data_batch_sync(self, data_batch: Any, context: ProcessingContext):
        """Versão síncrona para thread/process pools."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._process_data_batch(data_batch, context)
            )
        finally:
            loop.close()

    async def _report_metrics(self, metrics: ProcessingMetrics):
        """Reporta métricas para sistema de monitoramento."""
        if self.h1_integration:
            try:
                # Reporta métricas para H1
                metrics_dict = metrics.to_dict()
                # TODO: Implementar interface específica para H1
                self.logger.debug(f"Reported metrics to H1: {metrics.pipeline_id}")
            except Exception as e:
                self.logger.warning(f"Failed to report metrics to H1: {e}")

    def get_pipeline_status(self, execution_id: str) -> Optional[ProcessingMetrics]:
        """Obtém status de pipeline."""
        # Verifica pipelines em execução
        if execution_id in self.running_pipelines:
            return self.running_pipelines[execution_id].metrics

        # Verifica histórico
        return self.metrics_store.get(execution_id)

    def list_running_pipelines(self) -> List[ProcessingContext]:
        """Lista pipelines em execução."""
        return list(self.running_pipelines.values())

    def cancel_pipeline(self, execution_id: str) -> bool:
        """Cancela execução de pipeline."""
        if execution_id in self.running_pipelines:
            context = self.running_pipelines[execution_id]
            context.metrics.status = ProcessingStatus.CANCELLED
            self.logger.info(f"Pipeline cancelled: {execution_id}")
            return True
        return False

    async def cleanup(self):
        """Limpa recursos do executor."""
        # Cancela pipelines em execução
        for execution_id in list(self.running_pipelines.keys()):
            self.cancel_pipeline(execution_id)

        # Aguarda finalização
        await asyncio.sleep(1)

        self.logger.info("Pipeline executor cleaned up")


# Instância global do executor
_pipeline_executor: Optional[PipelineExecutor] = None


def get_pipeline_executor() -> PipelineExecutor:
    """Obtém instância global do executor de pipelines."""
    global _pipeline_executor
    if _pipeline_executor is None:
        _pipeline_executor = PipelineExecutor()
    return _pipeline_executor


async def execute_pipeline_async(config: PipelineConfig) -> ProcessingMetrics:
    """Executa pipeline de forma assíncrona."""
    executor = get_pipeline_executor()
    return await executor.execute_pipeline(config)


def execute_pipeline_sync(config: PipelineConfig) -> ProcessingMetrics:
    """Executa pipeline de forma síncrona."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(execute_pipeline_async(config))


def execute_pipeline_sync(config: PipelineConfig) -> ProcessingMetrics:
    """Executa pipeline de forma síncrona."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(execute_pipeline_async(config))
