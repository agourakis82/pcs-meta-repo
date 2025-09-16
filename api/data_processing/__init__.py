"""
Sistema H4 - Data Processing

Sistema avançado de processamento de dados com pipelines ETL,
análise em tempo real e processamento distribuído.
"""

from .config import (
    DataFormat,
    DataSinkConfig,
    DataSourceConfig,
    DistributionStrategy,
    H4Config,
    PipelineConfig,
    ProcessingConfig,
    ProcessingMode,
    QualityConfig,
    create_file_sink,
    create_file_source,
    get_h4_config,
)
from .engine import (
    DataProcessor,
    PipelineExecutor,
    ProcessingContext,
    ProcessingMetrics,
    get_pipeline_executor,
)
from .formats.file_handlers import (
    CSVHandler,
    ExcelHandler,
    FileDataSource,
    FileSink,
    FormatHandler,
    JSONHandler,
    XMLHandler,
    get_format_handler,
)
from .pipelines.templates import (
    AggregationTemplate,
    DataCleaningTemplate,
    DataValidationTemplate,
    FormatConversionTemplate,
    MultiFileETLTemplate,
    PipelineTemplate,
    SimpleETLTemplate,
    create_pipeline_from_template,
    execute_template_pipeline,
    get_template,
    list_templates,
)
from .processors.data_processors import (
    AggregationProcessor,
    CleaningProcessor,
    FilterProcessor,
    TransformationProcessor,
    ValidationProcessor,
    create_processor,
)

__version__ = "1.0.0"
__author__ = "PCS Meta Repository"
__description__ = "Sistema H4 de Processamento de Dados"

# Exportações principais
__all__ = [
    # Config
    "H4Config",
    "PipelineConfig",
    "DataSourceConfig",
    "DataSinkConfig",
    "ProcessingConfig",
    "QualityConfig",
    "DataFormat",
    "ProcessingMode",
    "DistributionStrategy",
    "create_file_source",
    "create_file_sink",
    "get_h4_config",
    # Engine
    "PipelineExecutor",
    "ProcessingContext",
    "ProcessingMetrics",
    "get_pipeline_executor",
    # Format Handlers
    "FormatHandler",
    "JSONHandler",
    "CSVHandler",
    "XMLHandler",
    "ExcelHandler",
    "FileDataSource",
    "FileSink",
    "get_format_handler",
    # Processors
    "DataProcessor",
    "ValidationProcessor",
    "CleaningProcessor",
    "TransformationProcessor",
    "AggregationProcessor",
    "FilterProcessor",
    "create_processor",
    # Templates
    "PipelineTemplate",
    "SimpleETLTemplate",
    "DataValidationTemplate",
    "DataCleaningTemplate",
    "AggregationTemplate",
    "FormatConversionTemplate",
    "MultiFileETLTemplate",
    "get_template",
    "list_templates",
    "create_pipeline_from_template",
    "execute_template_pipeline",
]

# Configuração padrão do logging
import logging


def setup_logging(level=logging.INFO):
    """Configura logging para o sistema H4."""
    logger = logging.getLogger("h4")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


# Inicializa logging por padrão
setup_logging()


# Funções de conveniência para uso rápido
async def quick_etl(input_file: str, output_file: str, **kwargs):
    """ETL rápido de arquivo para arquivo."""
    return await execute_template_pipeline(
        "simple_etl", input_file=input_file, output_file=output_file, **kwargs
    )


async def quick_validation(input_file: str, validation_rules: list, **kwargs):
    """Validação rápida de dados."""
    return await execute_template_pipeline(
        "data_validation",
        input_file=input_file,
        validation_rules=validation_rules,
        **kwargs,
    )


async def quick_format_conversion(
    input_file: str,
    output_file: str,
    input_format: DataFormat,
    output_format: DataFormat,
    **kwargs,
):
    """Conversão rápida de formato."""
    return await execute_template_pipeline(
        "format_conversion",
        input_file=input_file,
        output_file=output_file,
        input_format=input_format,
        output_format=output_format,
        **kwargs,
    )


# Sistema de saúde do H4
def health_check():
    """Verifica saúde do sistema H4."""
    try:
        config = get_h4_config()
        executor = get_pipeline_executor()

        return {
            "status": "healthy",
            "config_loaded": config is not None,
            "executor_ready": executor is not None,
            "version": __version__,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "version": __version__}


# Informações do sistema
def system_info():
    """Retorna informações do sistema H4."""
    return {
        "name": "Sistema H4 - Data Processing",
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "available_templates": list_templates(),
        "supported_formats": [format.value for format in DataFormat],
        "processing_modes": [mode.value for mode in ProcessingMode],
        "distribution_strategies": [
            strategy.value for strategy in DistributionStrategy
        ],
    }
