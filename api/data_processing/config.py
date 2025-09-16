"""
Sistema H4 - Data Processing Configuration

Configuração centralizada para o sistema de processamento de dados.
Inclui configurações para pipelines de ETL, processamento distribuído e análise em tempo real.
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """Modos de processamento de dados."""

    BATCH = "batch"
    STREAMING = "streaming"
    REAL_TIME = "real_time"
    HYBRID = "hybrid"


class DataFormat(Enum):
    """Formatos de dados suportados."""

    JSON = "json"
    CSV = "csv"
    PARQUET = "parquet"
    AVRO = "avro"
    XML = "xml"
    YAML = "yaml"
    EXCEL = "excel"
    HDF5 = "hdf5"
    NETCDF = "netcdf"
    CUSTOM = "custom"


class CompressionType(Enum):
    """Tipos de compressão suportados."""

    NONE = "none"
    GZIP = "gzip"
    BZIP2 = "bzip2"
    LZMA = "lzma"
    ZSTD = "zstd"
    SNAPPY = "snappy"


class DistributionStrategy(Enum):
    """Estratégias de distribuição de processamento."""

    SINGLE_NODE = "single_node"
    MULTI_THREAD = "multi_thread"
    MULTI_PROCESS = "multi_process"
    DISTRIBUTED = "distributed"
    SPARK = "spark"
    DASK = "dask"


@dataclass
class DataSourceConfig:
    """Configuração de fonte de dados."""

    name: str
    type: str  # file, database, api, stream, etc.
    location: str
    format: DataFormat = DataFormat.JSON
    compression: CompressionType = CompressionType.NONE
    credentials: Optional[Dict[str, str]] = None
    options: Dict[str, Any] = field(default_factory=dict)
    schema_validation: bool = True
    chunk_size: Optional[int] = None
    rate_limit: Optional[int] = None  # records per second


@dataclass
class DataSinkConfig:
    """Configuração de destino de dados."""

    name: str
    type: str  # file, database, api, stream, etc.
    location: str
    format: DataFormat = DataFormat.JSON
    compression: CompressionType = CompressionType.NONE
    credentials: Optional[Dict[str, str]] = None
    options: Dict[str, Any] = field(default_factory=dict)
    overwrite: bool = False
    partition_by: Optional[List[str]] = None
    batch_size: int = 1000


@dataclass
class ProcessingConfig:
    """Configuração de processamento."""

    mode: ProcessingMode = ProcessingMode.BATCH
    distribution: DistributionStrategy = DistributionStrategy.SINGLE_NODE
    max_workers: int = 4
    max_memory_mb: int = 1024
    max_retries: int = 3
    timeout_seconds: int = 3600
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    enable_monitoring: bool = True
    checkpoint_interval: int = 1000
    error_handling: str = "continue"  # continue, abort, retry


@dataclass
class QualityConfig:
    """Configuração de qualidade de dados."""

    enable_validation: bool = True
    enable_profiling: bool = True
    enable_anomaly_detection: bool = False
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    quality_thresholds: Dict[str, float] = field(default_factory=dict)
    data_lineage: bool = True
    audit_trail: bool = True


@dataclass
class PipelineConfig:
    """Configuração completa de pipeline."""

    name: str
    description: str = ""
    version: str = "1.0.0"
    sources: List[DataSourceConfig] = field(default_factory=list)
    sinks: List[DataSinkConfig] = field(default_factory=list)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    schedule: Optional[str] = None  # cron expression
    dependencies: List[str] = field(default_factory=list)
    notifications: Dict[str, Any] = field(default_factory=dict)


class H4Config:
    """Configuração principal do sistema H4."""

    def __init__(self):
        self.base_path = Path(os.getenv("H4_BASE_PATH", "/tmp/h4_data"))
        self.temp_path = Path(os.getenv("H4_TEMP_PATH", "/tmp/h4_temp"))
        self.log_level = os.getenv("H4_LOG_LEVEL", "INFO")
        self.enable_metrics = os.getenv("H4_ENABLE_METRICS", "true").lower() == "true"
        self.enable_distributed = (
            os.getenv("H4_ENABLE_DISTRIBUTED", "false").lower() == "true"
        )

        # Database connections
        self.databases = {
            "postgres": os.getenv("POSTGRES_URL"),
            "redis": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "mongodb": os.getenv("MONGODB_URL"),
            "elasticsearch": os.getenv("ELASTICSEARCH_URL"),
        }

        # Message queues
        self.message_queues = {
            "kafka": os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
            "rabbitmq": os.getenv("RABBITMQ_URL"),
            "redis_stream": os.getenv("REDIS_URL", "redis://localhost:6379"),
        }

        # Storage systems
        self.storage = {
            "s3_bucket": os.getenv("S3_BUCKET"),
            "gcs_bucket": os.getenv("GCS_BUCKET"),
            "azure_container": os.getenv("AZURE_CONTAINER"),
            "local_path": str(self.base_path),
        }

        # Processing limits
        self.limits = {
            "max_file_size_mb": int(os.getenv("H4_MAX_FILE_SIZE_MB", "1024")),
            "max_memory_usage_mb": int(os.getenv("H4_MAX_MEMORY_MB", "2048")),
            "max_processing_time_seconds": int(
                os.getenv("H4_MAX_TIME_SECONDS", "7200")
            ),
            "max_concurrent_pipelines": int(os.getenv("H4_MAX_PIPELINES", "10")),
            "max_workers_per_pipeline": int(os.getenv("H4_MAX_WORKERS", "8")),
        }

        # Integration with other systems
        self.h1_monitoring_enabled = (
            os.getenv("H4_H1_INTEGRATION", "true").lower() == "true"
        )
        self.h2_cache_enabled = os.getenv("H4_H2_INTEGRATION", "true").lower() == "true"
        self.h3_api_enabled = os.getenv("H4_H3_INTEGRATION", "true").lower() == "true"

        # Feature flags
        self.features = {
            "real_time_processing": os.getenv("H4_REAL_TIME", "true").lower() == "true",
            "distributed_processing": os.getenv("H4_DISTRIBUTED", "false").lower()
            == "true",
            "ml_integration": os.getenv("H4_ML_ENABLED", "false").lower() == "true",
            "auto_scaling": os.getenv("H4_AUTO_SCALE", "false").lower() == "true",
            "data_lineage": os.getenv("H4_DATA_LINEAGE", "true").lower() == "true",
            "quality_monitoring": os.getenv("H4_QUALITY_MONITORING", "true").lower()
            == "true",
        }

        # Ensure directories exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)

        logger.info("H4 Data Processing configuration initialized")
        logger.info(f"Base path: {self.base_path}")
        logger.info(f"Temp path: {self.temp_path}")
        logger.info(f"Features enabled: {[k for k, v in self.features.items() if v]}")

    def get_database_url(self, db_type: str) -> Optional[str]:
        """Obtém URL de conexão de banco de dados."""
        return self.databases.get(db_type)

    def get_message_queue_url(self, mq_type: str) -> Optional[str]:
        """Obtém URL de fila de mensagens."""
        return self.message_queues.get(mq_type)

    def get_storage_config(self, storage_type: str) -> Optional[str]:
        """Obtém configuração de armazenamento."""
        return self.storage.get(storage_type)

    def is_feature_enabled(self, feature: str) -> bool:
        """Verifica se uma feature está habilitada."""
        return self.features.get(feature, False)

    def get_limit(self, limit_type: str) -> Optional[int]:
        """Obtém limite de configuração."""
        return self.limits.get(limit_type)

    def to_dict(self) -> Dict[str, Any]:
        """Converte configuração para dicionário."""
        return {
            "base_path": str(self.base_path),
            "temp_path": str(self.temp_path),
            "log_level": self.log_level,
            "enable_metrics": self.enable_metrics,
            "enable_distributed": self.enable_distributed,
            "databases": {k: v for k, v in self.databases.items() if v},
            "message_queues": {k: v for k, v in self.message_queues.items() if v},
            "storage": self.storage,
            "limits": self.limits,
            "integrations": {
                "h1_monitoring": self.h1_monitoring_enabled,
                "h2_cache": self.h2_cache_enabled,
                "h3_api": self.h3_api_enabled,
            },
            "features": self.features,
        }


# Instância global da configuração
_h4_config: Optional[H4Config] = None


def get_h4_config() -> H4Config:
    """Obtém instância global da configuração H4."""
    global _h4_config
    if _h4_config is None:
        _h4_config = H4Config()
    return _h4_config


def create_pipeline_config(
    name: str,
    sources: List[DataSourceConfig],
    sinks: List[DataSinkConfig],
    processing_mode: ProcessingMode = ProcessingMode.BATCH,
    **kwargs,
) -> PipelineConfig:
    """Cria configuração de pipeline com valores padrão."""
    processing_config = ProcessingConfig(mode=processing_mode)
    quality_config = QualityConfig()

    return PipelineConfig(
        name=name,
        sources=sources,
        sinks=sinks,
        processing=processing_config,
        quality=quality_config,
        **kwargs,
    )


def create_file_source(
    name: str, file_path: str, format: DataFormat = DataFormat.JSON, **kwargs
) -> DataSourceConfig:
    """Cria configuração de fonte de arquivo."""
    return DataSourceConfig(
        name=name, type="file", location=file_path, format=format, **kwargs
    )


def create_file_sink(
    name: str, file_path: str, format: DataFormat = DataFormat.JSON, **kwargs
) -> DataSinkConfig:
    """Cria configuração de destino de arquivo."""
    return DataSinkConfig(
        name=name, type="file", location=file_path, format=format, **kwargs
    )


def create_database_source(
    name: str, connection_url: str, query: str, **kwargs
) -> DataSourceConfig:
    """Cria configuração de fonte de banco de dados."""
    return DataSourceConfig(
        name=name,
        type="database",
        location=connection_url,
        options={"query": query},
        **kwargs,
    )


def create_api_source(
    name: str, endpoint_url: str, method: str = "GET", **kwargs
) -> DataSourceConfig:
    """Cria configuração de fonte de API."""
    return DataSourceConfig(
        name=name,
        type="api",
        location=endpoint_url,
        options={"method": method},
        **kwargs,
    )


# Template configurations
TEMPLATE_CONFIGS = {
    "simple_etl": {
        "description": "Pipeline ETL simples para arquivos",
        "processing": {
            "mode": ProcessingMode.BATCH,
            "distribution": DistributionStrategy.SINGLE_NODE,
        },
    },
    "real_time_streaming": {
        "description": "Pipeline de streaming em tempo real",
        "processing": {
            "mode": ProcessingMode.STREAMING,
            "distribution": DistributionStrategy.MULTI_THREAD,
        },
    },
    "distributed_batch": {
        "description": "Processamento batch distribuído",
        "processing": {
            "mode": ProcessingMode.BATCH,
            "distribution": DistributionStrategy.DISTRIBUTED,
        },
    },
    "ml_preprocessing": {
        "description": "Pré-processamento para ML",
        "processing": {
            "mode": ProcessingMode.BATCH,
            "distribution": DistributionStrategy.MULTI_PROCESS,
        },
        "quality": {
            "enable_validation": True,
            "enable_profiling": True,
            "enable_anomaly_detection": True,
        },
    },
}


def get_template_config(template_name: str) -> Dict[str, Any]:
    """Obtém configuração de template."""
    return TEMPLATE_CONFIGS.get(template_name, {})


def list_template_configs() -> List[str]:
    """Lista templates de configuração disponíveis."""
    return list(TEMPLATE_CONFIGS.keys())
