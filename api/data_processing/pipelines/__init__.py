"""
Sistema H4 - Pipeline Templates

Templates e exemplos para pipelines de processamento de dados.
"""

from .templates import (
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

__all__ = [
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
