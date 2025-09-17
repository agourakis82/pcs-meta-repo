"""
Sistema H4 - Pipeline Templates

Templates de pipelines pré-configurados para casos de uso comuns.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import (
    DataFormat,
    DataSinkConfig,
    DataSourceConfig,
    DistributionStrategy,
    PipelineConfig,
    ProcessingConfig,
    ProcessingMode,
    QualityConfig,
    create_file_sink,
    create_file_source,
)
from ..engine import get_pipeline_executor
from ..processors.data_processors import create_processor

logger = logging.getLogger(__name__)


class PipelineTemplate:
    """Classe base para templates de pipeline."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"h4.template.{name}")
    
    def create_config(self, **kwargs) -> PipelineConfig:
        """Cria configuração do pipeline."""
        raise NotImplementedError
    
    def validate_params(self, **kwargs) -> bool:
        """Valida parâmetros do template."""
        return True


class SimpleETLTemplate(PipelineTemplate):
    """Template para ETL simples de arquivo para arquivo."""
    
    def __init__(self):
        super().__init__("simple_etl", "ETL simples de arquivo para arquivo")
    
    def create_config(self, **kwargs) -> PipelineConfig:
        """Cria configuração de ETL simples."""
        # Parâmetros obrigatórios
        input_file = kwargs.get("input_file")
        output_file = kwargs.get("output_file")
        
        if not input_file or not output_file:
            raise ValueError("input_file and output_file are required")
        
        # Parâmetros opcionais
        input_format = kwargs.get("input_format", DataFormat.JSON)
        output_format = kwargs.get("output_format", DataFormat.JSON)
        chunk_size = kwargs.get("chunk_size", 1000)
        enable_validation = kwargs.get("enable_validation", True)
        enable_cleaning = kwargs.get("enable_cleaning", False)
        
        # Cria fontes e destinos
        source = create_file_source(
            "input",
            input_file,
            format=input_format,
            chunk_size=chunk_size
        )
        
        sink = create_file_sink(
            "output",
            output_file,
            format=output_format,
            overwrite=kwargs.get("overwrite", True)
        )
        
        # Configuração de processamento
        processing = ProcessingConfig(
            mode=ProcessingMode.BATCH,
            distribution=DistributionStrategy.SINGLE_NODE,
            enable_caching=True
        )
        
        # Configuração de qualidade
        quality = QualityConfig(
            enable_validation=enable_validation,
            enable_profiling=True
        )
        
        return PipelineConfig(
            name=f"simple_etl_{Path(input_file).stem}",
            description="Simple ETL pipeline",
            sources=[source],
            sinks=[sink],
            processing=processing,
            quality=quality,
            metadata=kwargs
        )
    
    def validate_params(self, **kwargs) -> bool:
        """Valida parâmetros do template."""
        input_file = kwargs.get("input_file")
        output_file = kwargs.get("output_file")
        
        if not input_file or not output_file:
            return False
        
        # Verifica se arquivo de entrada existe
        return Path(input_file).exists()


class DataValidationTemplate(PipelineTemplate):
    """Template para validação de dados."""
    
    def __init__(self):
        super().__init__("data_validation", "Pipeline de validação de dados")
    
    def create_config(self, **kwargs) -> PipelineConfig:
        """Cria configuração de validação."""
        input_file = kwargs.get("input_file")
        validation_rules = kwargs.get("validation_rules", [])
        output_file = kwargs.get("output_file")
        
        if not input_file:
            raise ValueError("input_file is required")
        
        # Fonte de dados
        source = create_file_source(
            "input",
            input_file,
            format=kwargs.get("input_format", DataFormat.JSON)
        )
        
        # Destinos
        sinks = []
        if output_file:
            sink = create_file_sink(
                "output",
                output_file,
                format=kwargs.get("output_format", DataFormat.JSON)
            )
            sinks.append(sink)
        
        # Relatório de validação
        if kwargs.get("generate_report", True):
            report_file = kwargs.get("report_file", 
                                   str(Path(input_file).with_suffix('.validation_report.json')))
            report_sink = create_file_sink(
                "validation_report",
                report_file,
                format=DataFormat.JSON
            )
            sinks.append(report_sink)
        
        # Configuração de qualidade com regras customizadas
        quality = QualityConfig(
            enable_validation=True,
            enable_profiling=True,
            validation_rules=validation_rules,
            audit_trail=True
        )
        
        return PipelineConfig(
            name=f"validation_{Path(input_file).stem}",
            description="Data validation pipeline",
            sources=[source],
            sinks=sinks,
            quality=quality,
            metadata=kwargs
        )


class DataCleaningTemplate(PipelineTemplate):
    """Template para limpeza de dados."""
    
    def __init__(self):
        super().__init__("data_cleaning", "Pipeline de limpeza de dados")
    
    def create_config(self, **kwargs) -> PipelineConfig:
        """Cria configuração de limpeza."""
        input_file = kwargs.get("input_file")
        output_file = kwargs.get("output_file")
        cleaning_rules = kwargs.get("cleaning_rules", [])
        
        if not input_file or not output_file:
            raise ValueError("input_file and output_file are required")
        
        # Fonte e destino
        source = create_file_source(
            "input",
            input_file,
            format=kwargs.get("input_format", DataFormat.JSON)
        )
        
        sink = create_file_sink(
            "output",
            output_file,
            format=kwargs.get("output_format", DataFormat.JSON)
        )
        
        # Configurações
        processing = ProcessingConfig(
            mode=ProcessingMode.BATCH,
            distribution=kwargs.get("distribution", DistributionStrategy.SINGLE_NODE)
        )
        
        quality = QualityConfig(
            enable_validation=True,
            enable_profiling=True
        )
        
        return PipelineConfig(
            name=f"cleaning_{Path(input_file).stem}",
            description="Data cleaning pipeline",
            sources=[source],
            sinks=[sink],
            processing=processing,
            quality=quality,
            metadata={
                **kwargs,
                "cleaning_rules": cleaning_rules
            }
        )


class AggregationTemplate(PipelineTemplate):
    """Template para agregação de dados."""
    
    def __init__(self):
        super().__init__("aggregation", "Pipeline de agregação de dados")
    
    def create_config(self, **kwargs) -> PipelineConfig:
        """Cria configuração de agregação."""
        input_file = kwargs.get("input_file")
        output_file = kwargs.get("output_file")
        group_by_fields = kwargs.get("group_by_fields", [])
        aggregations = kwargs.get("aggregations", [])
        
        if not input_file or not output_file:
            raise ValueError("input_file and output_file are required")
        
        if not aggregations:
            raise ValueError("aggregations are required")
        
        # Fonte e destino
        source = create_file_source(
            "input",
            input_file,
            format=kwargs.get("input_format", DataFormat.JSON)
        )
        
        sink = create_file_sink(
            "output",
            output_file,
            format=kwargs.get("output_format", DataFormat.JSON)
        )
        
        return PipelineConfig(
            name=f"aggregation_{Path(input_file).stem}",
            description="Data aggregation pipeline",
            sources=[source],
            sinks=[sink],
            metadata={
                **kwargs,
                "group_by_fields": group_by_fields,
                "aggregations": aggregations
            }
        )


class FormatConversionTemplate(PipelineTemplate):
    """Template para conversão de formato."""
    
    def __init__(self):
        super().__init__("format_conversion", "Conversão entre formatos de dados")
    
    def create_config(self, **kwargs) -> PipelineConfig:
        """Cria configuração de conversão de formato."""
        input_file = kwargs.get("input_file")
        output_file = kwargs.get("output_file")
        input_format = kwargs.get("input_format")
        output_format = kwargs.get("output_format")
        
        if not all([input_file, output_file, input_format, output_format]):
            raise ValueError("input_file, output_file, input_format, and output_format are required")
        
        # Fonte e destino
        source = create_file_source(
            "input",
            input_file,
            format=input_format
        )
        
        sink = create_file_sink(
            "output",
            output_file,
            format=output_format
        )
        
        return PipelineConfig(
            name=f"conversion_{Path(input_file).stem}_to_{output_format.value}",
            description=f"Convert {input_format.value} to {output_format.value}",
            sources=[source],
            sinks=[sink],
            metadata=kwargs
        )


class MultiFileETLTemplate(PipelineTemplate):
    """Template para ETL de múltiplos arquivos."""
    
    def __init__(self):
        super().__init__("multi_file_etl", "ETL de múltiplos arquivos")
    
    def create_config(self, **kwargs) -> PipelineConfig:
        """Cria configuração de ETL multi-arquivo."""
        input_pattern = kwargs.get("input_pattern")  # glob pattern
        output_file = kwargs.get("output_file")
        
        if not input_pattern or not output_file:
            raise ValueError("input_pattern and output_file are required")
        
        # Encontra arquivos que correspondem ao padrão
        from glob import glob
        input_files = glob(input_pattern)
        
        if not input_files:
            raise ValueError(f"No files found matching pattern: {input_pattern}")
        
        # Cria fontes para cada arquivo
        sources = []
        for i, file_path in enumerate(input_files):
            source = create_file_source(
                f"input_{i}",
                file_path,
                format=kwargs.get("input_format", DataFormat.JSON)
            )
            sources.append(source)
        
        # Destino único
        sink = create_file_sink(
            "output",
            output_file,
            format=kwargs.get("output_format", DataFormat.JSON)
        )
        
        # Processamento paralelo para múltiplos arquivos
        processing = ProcessingConfig(
            mode=ProcessingMode.BATCH,
            distribution=DistributionStrategy.MULTI_THREAD,
            max_workers=min(len(input_files), 4)
        )
        
        return PipelineConfig(
            name=f"multi_etl_{len(input_files)}_files",
            description=f"ETL of {len(input_files)} files",
            sources=sources,
            sinks=[sink],
            processing=processing,
            metadata={
                **kwargs,
                "input_files": input_files
            }
        )


# Registry de templates
TEMPLATE_REGISTRY = {
    "simple_etl": SimpleETLTemplate(),
    "data_validation": DataValidationTemplate(),
    "data_cleaning": DataCleaningTemplate(),
    "aggregation": AggregationTemplate(),
    "format_conversion": FormatConversionTemplate(),
    "multi_file_etl": MultiFileETLTemplate(),
}


def get_template(template_name: str) -> PipelineTemplate:
    """Obtém template pelo nome."""
    template = TEMPLATE_REGISTRY.get(template_name)
    if template is None:
        raise ValueError(f"Unknown template: {template_name}")
    return template


def list_templates() -> List[str]:
    """Lista templates disponíveis."""
    return list(TEMPLATE_REGISTRY.keys())


def create_pipeline_from_template(template_name: str, **kwargs) -> PipelineConfig:
    """Cria pipeline a partir de template."""
    template = get_template(template_name)
    
    # Valida parâmetros
    if not template.validate_params(**kwargs):
        raise ValueError(f"Invalid parameters for template {template_name}")
    
    # Cria configuração
    config = template.create_config(**kwargs)
    
    logger.info(f"Created pipeline from template {template_name}: {config.name}")
    return config


async def execute_template_pipeline(template_name: str, **kwargs):
    """Executa pipeline a partir de template."""
    config = create_pipeline_from_template(template_name, **kwargs)
    executor = get_pipeline_executor()
    
    # Registra processadores se necessário
    if template_name == "data_validation":
        validation_processor = create_processor("validation")
        # Configura regras de validação
        validation_rules = kwargs.get("validation_rules", [])
        for rule in validation_rules:
            validation_processor.add_rule(**rule)
        executor.register_processor(validation_processor)
    
    elif template_name == "data_cleaning":
        cleaning_processor = create_processor("cleaning")
        # Configura regras de limpeza
        cleaning_rules = kwargs.get("cleaning_rules", [])
        for rule in cleaning_rules:
            cleaning_processor.add_cleaning_rule(**rule)
        executor.register_processor(cleaning_processor)
    
    elif template_name == "aggregation":
        aggregation_processor = create_processor("aggregation")
        # Configura agregações
        group_by_fields = kwargs.get("group_by_fields", [])
        aggregations = kwargs.get("aggregations", [])
        
        aggregation_processor.set_group_by(group_by_fields)
        for agg in aggregations:
            aggregation_processor.add_aggregation(**agg)
        
        executor.register_processor(aggregation_processor)
    
    # Executa pipeline
    return await executor.execute_pipeline(config)


# Funções de conveniência para templates comuns
def simple_file_to_file_etl(input_file: str, output_file: str, **kwargs):
    """ETL simples de arquivo para arquivo."""
    return create_pipeline_from_template(
        "simple_etl",
        input_file=input_file,
        output_file=output_file,
        **kwargs
    )


def validate_data_file(input_file: str, validation_rules: List[Dict], **kwargs):
    """Valida arquivo de dados."""
    return create_pipeline_from_template(
        "data_validation",
        input_file=input_file,
        validation_rules=validation_rules,
        **kwargs
    )


def clean_data_file(input_file: str, output_file: str, cleaning_rules: List[Dict], **kwargs):
    """Limpa arquivo de dados."""
    return create_pipeline_from_template(
        "data_cleaning",
        input_file=input_file,
        output_file=output_file,
        cleaning_rules=cleaning_rules,
        **kwargs
    )


def convert_file_format(input_file: str, output_file: str, 
                       input_format: DataFormat, output_format: DataFormat, **kwargs):
    """Converte formato de arquivo."""
    return create_pipeline_from_template(
        "format_conversion",
        input_file=input_file,
        output_file=output_file,
        input_format=input_format,
        output_format=output_format,
        **kwargs
    )


def aggregate_data_file(input_file: str, output_file: str,
                       group_by_fields: List[str], aggregations: List[Dict], **kwargs):
    """Agrega dados de arquivo."""
    return create_pipeline_from_template(
        "aggregation",
        input_file=input_file,
        output_file=output_file,
        group_by_fields=group_by_fields,
        aggregations=aggregations,
        **kwargs
    )