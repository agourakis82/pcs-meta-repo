"""
Sistema H4 - Data Processors

Processadores especializados para transformação de dados.
"""

from .data_processors import (
    AggregationProcessor,
    CleaningProcessor,
    FilterProcessor,
    TransformationProcessor,
    ValidationProcessor,
    create_processor,
)

__all__ = [
    "ValidationProcessor",
    "CleaningProcessor",
    "TransformationProcessor",
    "AggregationProcessor",
    "FilterProcessor",
    "create_processor",
]
