"""
Sistema H4 - Data Processors

Processadores específicos para transformação e análise de dados.
Inclui validação, limpeza, agregação e transformações customizadas.
"""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Union

from ..engine import DataProcessor, ProcessingContext

logger = logging.getLogger(__name__)


class ValidationProcessor(DataProcessor):
    """Processador para validação de dados."""

    def __init__(self, name: str = "validation"):
        super().__init__(name)
        self.rules = []
        self.strict_mode = False

    def add_rule(self, field: str, rule_type: str, **kwargs):
        """Adiciona regra de validação."""
        rule = {"field": field, "type": rule_type, "params": kwargs}
        self.rules.append(rule)
        self.logger.info(f"Added validation rule: {field} -> {rule_type}")

    async def process(self, data: Any, context: ProcessingContext) -> Any:
        """Aplica validações aos dados."""
        if isinstance(data, list):
            return [await self._validate_record(record, context) for record in data]
        else:
            return await self._validate_record(data, context)

    async def _validate_record(
        self, record: Dict[str, Any], context: ProcessingContext
    ) -> Dict[str, Any]:
        """Valida um registro individual."""
        if not isinstance(record, dict):
            if self.strict_mode:
                raise ValueError(f"Expected dict, got {type(record)}")
            return record

        errors = []
        warnings = []

        for rule in self.rules:
            field = rule["field"]
            rule_type = rule["type"]
            params = rule["params"]

            value = record.get(field)

            try:
                if rule_type == "required":
                    if value is None or value == "":
                        errors.append(f"Field '{field}' is required")

                elif rule_type == "type":
                    expected_type = params.get("expected")
                    if value is not None and not isinstance(value, expected_type):
                        errors.append(
                            f"Field '{field}' must be {expected_type.__name__}"
                        )

                elif rule_type == "range":
                    min_val = params.get("min")
                    max_val = params.get("max")
                    if value is not None:
                        if min_val is not None and value < min_val:
                            errors.append(f"Field '{field}' must be >= {min_val}")
                        if max_val is not None and value > max_val:
                            errors.append(f"Field '{field}' must be <= {max_val}")

                elif rule_type == "length":
                    min_len = params.get("min")
                    max_len = params.get("max")
                    if value is not None and hasattr(value, "__len__"):
                        length = len(value)
                        if min_len is not None and length < min_len:
                            errors.append(
                                f"Field '{field}' length must be >= {min_len}"
                            )
                        if max_len is not None and length > max_len:
                            errors.append(
                                f"Field '{field}' length must be <= {max_len}"
                            )

                elif rule_type == "regex":
                    pattern = params.get("pattern")
                    if value is not None and isinstance(value, str):
                        if not re.match(pattern, value):
                            errors.append(f"Field '{field}' does not match pattern")

                elif rule_type == "enum":
                    allowed_values = params.get("values", [])
                    if value is not None and value not in allowed_values:
                        errors.append(
                            f"Field '{field}' must be one of {allowed_values}"
                        )

            except Exception as e:
                errors.append(f"Validation error for '{field}': {str(e)}")

        # Adiciona metadados de validação
        validation_meta = {
            "_validation": {
                "errors": errors,
                "warnings": warnings,
                "is_valid": len(errors) == 0,
                "validated_at": datetime.now().isoformat(),
            }
        }

        # Se tem erros e está em modo estrito, raise exception
        if errors and self.strict_mode:
            raise ValueError(f"Validation failed: {errors}")

        # Adiciona metadados ao registro
        if isinstance(record, dict):
            record.update(validation_meta)

        # Atualiza métricas
        if errors:
            context.metrics.error_count += len(errors)
        if warnings:
            context.metrics.warning_count += len(warnings)

        return record

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configuração do processador."""
        required_fields = ["rules"]
        return all(field in config for field in required_fields)


class CleaningProcessor(DataProcessor):
    """Processador para limpeza de dados."""

    def __init__(self, name: str = "cleaning"):
        super().__init__(name)
        self.cleaning_rules = []

    def add_cleaning_rule(self, field: str, rule_type: str, **kwargs):
        """Adiciona regra de limpeza."""
        rule = {"field": field, "type": rule_type, "params": kwargs}
        self.cleaning_rules.append(rule)
        self.logger.info(f"Added cleaning rule: {field} -> {rule_type}")

    async def process(self, data: Any, context: ProcessingContext) -> Any:
        """Aplica limpeza aos dados."""
        if isinstance(data, list):
            return [await self._clean_record(record, context) for record in data]
        else:
            return await self._clean_record(data, context)

    async def _clean_record(
        self, record: Dict[str, Any], context: ProcessingContext
    ) -> Dict[str, Any]:
        """Limpa um registro individual."""
        if not isinstance(record, dict):
            return record

        cleaned_record = record.copy()

        for rule in self.cleaning_rules:
            field = rule["field"]
            rule_type = rule["type"]
            params = rule["params"]

            if field not in cleaned_record:
                continue

            value = cleaned_record[field]

            try:
                if rule_type == "trim":
                    if isinstance(value, str):
                        cleaned_record[field] = value.strip()

                elif rule_type == "lowercase":
                    if isinstance(value, str):
                        cleaned_record[field] = value.lower()

                elif rule_type == "uppercase":
                    if isinstance(value, str):
                        cleaned_record[field] = value.upper()

                elif rule_type == "remove_special_chars":
                    if isinstance(value, str):
                        pattern = params.get("pattern", r"[^a-zA-Z0-9\s]")
                        cleaned_record[field] = re.sub(pattern, "", value)

                elif rule_type == "normalize_phone":
                    if isinstance(value, str):
                        # Remove caracteres não numéricos
                        phone = re.sub(r"[^\d]", "", value)
                        cleaned_record[field] = phone

                elif rule_type == "normalize_email":
                    if isinstance(value, str):
                        cleaned_record[field] = value.lower().strip()

                elif rule_type == "fill_na":
                    default_value = params.get("default")
                    if value is None or value == "":
                        cleaned_record[field] = default_value

                elif rule_type == "convert_type":
                    target_type = params.get("target_type")
                    if value is not None and target_type:
                        try:
                            if target_type == "int":
                                cleaned_record[field] = int(float(str(value)))
                            elif target_type == "float":
                                cleaned_record[field] = float(value)
                            elif target_type == "str":
                                cleaned_record[field] = str(value)
                            elif target_type == "bool":
                                if isinstance(value, str):
                                    cleaned_record[field] = value.lower() in [
                                        "true",
                                        "1",
                                        "yes",
                                        "on",
                                    ]
                                else:
                                    cleaned_record[field] = bool(value)
                        except (ValueError, TypeError):
                            self.logger.warning(
                                f"Could not convert {field} to {target_type}"
                            )

                elif rule_type == "remove_duplicates":
                    if isinstance(value, list):
                        cleaned_record[field] = list(dict.fromkeys(value))

            except Exception as e:
                self.logger.error(
                    f"Error applying cleaning rule {rule_type} to {field}: {e}"
                )

        return cleaned_record

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configuração do processador."""
        return "cleaning_rules" in config


class TransformationProcessor(DataProcessor):
    """Processador para transformações de dados."""

    def __init__(self, name: str = "transformation"):
        super().__init__(name)
        self.transformations = []

    def add_transformation(
        self, source_field: str, target_field: str, transform_func: Callable[[Any], Any]
    ):
        """Adiciona transformação."""
        transformation = {
            "source": source_field,
            "target": target_field,
            "function": transform_func,
        }
        self.transformations.append(transformation)
        self.logger.info(f"Added transformation: {source_field} -> {target_field}")

    def add_calculated_field(
        self, target_field: str, calculation: str, dependencies: List[str]
    ):
        """Adiciona campo calculado."""
        transformation = {
            "type": "calculated",
            "target": target_field,
            "calculation": calculation,
            "dependencies": dependencies,
        }
        self.transformations.append(transformation)
        self.logger.info(f"Added calculated field: {target_field}")

    async def process(self, data: Any, context: ProcessingContext) -> Any:
        """Aplica transformações aos dados."""
        if isinstance(data, list):
            return [await self._transform_record(record, context) for record in data]
        else:
            return await self._transform_record(data, context)

    async def _transform_record(
        self, record: Dict[str, Any], context: ProcessingContext
    ) -> Dict[str, Any]:
        """Transforma um registro individual."""
        if not isinstance(record, dict):
            return record

        transformed_record = record.copy()

        for transformation in self.transformations:
            try:
                if transformation.get("type") == "calculated":
                    # Campo calculado
                    target = transformation["target"]
                    calculation = transformation["calculation"]
                    dependencies = transformation["dependencies"]

                    # Verifica se todas as dependências existem
                    if all(dep in transformed_record for dep in dependencies):
                        # Cria contexto local para avaliação
                        local_context = {
                            dep: transformed_record[dep] for dep in dependencies
                        }

                        # Adiciona funções matemáticas comuns
                        import math

                        local_context.update(
                            {
                                "abs": abs,
                                "min": min,
                                "max": max,
                                "round": round,
                                "sum": sum,
                                "len": len,
                                "sqrt": math.sqrt,
                                "pow": pow,
                                "ceil": math.ceil,
                                "floor": math.floor,
                            }
                        )

                        # Avalia expressão
                        try:
                            result = eval(
                                calculation, {"__builtins__": {}}, local_context
                            )
                            transformed_record[target] = result
                        except Exception as e:
                            self.logger.error(
                                f"Error evaluating calculation {calculation}: {e}"
                            )

                else:
                    # Transformação com função
                    source = transformation["source"]
                    target = transformation["target"]
                    func = transformation["function"]

                    if source in transformed_record:
                        try:
                            result = func(transformed_record[source])
                            transformed_record[target] = result
                        except Exception as e:
                            self.logger.error(
                                f"Error applying transformation to {source}: {e}"
                            )

            except Exception as e:
                self.logger.error(f"Error in transformation: {e}")

        return transformed_record

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configuração do processador."""
        return "transformations" in config


class AggregationProcessor(DataProcessor):
    """Processador para agregação de dados."""

    def __init__(self, name: str = "aggregation"):
        super().__init__(name)
        self.group_by_fields = []
        self.aggregations = []

    def set_group_by(self, fields: List[str]):
        """Define campos para agrupamento."""
        self.group_by_fields = fields

    def add_aggregation(self, field: str, operation: str, alias: str = None):
        """Adiciona agregação."""
        aggregation = {
            "field": field,
            "operation": operation,
            "alias": alias or f"{field}_{operation}",
        }
        self.aggregations.append(aggregation)
        self.logger.info(
            f"Added aggregation: {operation}({field}) as {aggregation['alias']}"
        )

    async def process(self, data: Any, context: ProcessingContext) -> Any:
        """Aplica agregações aos dados."""
        if not isinstance(data, list):
            return data

        if not self.group_by_fields:
            # Agregação global
            return [await self._aggregate_all(data)]
        else:
            # Agregação por grupos
            return await self._aggregate_by_groups(data)

    async def _aggregate_all(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Agrega todos os registros."""
        result = {}

        for aggregation in self.aggregations:
            field = aggregation["field"]
            operation = aggregation["operation"]
            alias = aggregation["alias"]

            # Extrai valores do campo
            values = [r.get(field) for r in records if r.get(field) is not None]

            if not values:
                result[alias] = None
                continue

            try:
                if operation == "count":
                    result[alias] = len(values)
                elif operation == "sum":
                    result[alias] = sum(float(v) for v in values if v is not None)
                elif operation == "avg":
                    numeric_values = [float(v) for v in values if v is not None]
                    result[alias] = (
                        sum(numeric_values) / len(numeric_values)
                        if numeric_values
                        else None
                    )
                elif operation == "min":
                    result[alias] = min(values)
                elif operation == "max":
                    result[alias] = max(values)
                elif operation == "distinct_count":
                    result[alias] = len(set(values))
                elif operation == "concat":
                    separator = " "  # Configurável
                    result[alias] = separator.join(str(v) for v in values)
                else:
                    self.logger.warning(f"Unknown aggregation operation: {operation}")
                    result[alias] = None

            except Exception as e:
                self.logger.error(
                    f"Error in aggregation {operation} for field {field}: {e}"
                )
                result[alias] = None

        return result

    async def _aggregate_by_groups(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Agrega por grupos."""
        # Agrupa registros
        groups = {}

        for record in records:
            # Cria chave do grupo
            group_key = tuple(record.get(field) for field in self.group_by_fields)

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(record)

        # Agrega cada grupo
        results = []

        for group_key, group_records in groups.items():
            # Cria registro resultado com campos de agrupamento
            result = {
                field: value for field, value in zip(self.group_by_fields, group_key)
            }

            # Adiciona agregações
            aggregated = await self._aggregate_all(group_records)
            result.update(aggregated)

            results.append(result)

        return results

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configuração do processador."""
        return "aggregations" in config


class FilterProcessor(DataProcessor):
    """Processador para filtragem de dados."""

    def __init__(self, name: str = "filter"):
        super().__init__(name)
        self.filters = []

    def add_filter(
        self, field: str, operator: str, value: Any, logical_op: str = "and"
    ):
        """Adiciona filtro."""
        filter_rule = {
            "field": field,
            "operator": operator,
            "value": value,
            "logical_op": logical_op,
        }
        self.filters.append(filter_rule)
        self.logger.info(f"Added filter: {field} {operator} {value}")

    async def process(self, data: Any, context: ProcessingContext) -> Any:
        """Aplica filtros aos dados."""
        if isinstance(data, list):
            filtered_data = []
            for record in data:
                if await self._matches_filters(record):
                    filtered_data.append(record)
            return filtered_data
        else:
            if await self._matches_filters(data):
                return data
            else:
                return None

    async def _matches_filters(self, record: Dict[str, Any]) -> bool:
        """Verifica se registro atende aos filtros."""
        if not self.filters:
            return True

        if not isinstance(record, dict):
            return True

        results = []

        for filter_rule in self.filters:
            field = filter_rule["field"]
            operator = filter_rule["operator"]
            filter_value = filter_rule["value"]

            record_value = record.get(field)

            try:
                if operator == "eq":
                    match = record_value == filter_value
                elif operator == "ne":
                    match = record_value != filter_value
                elif operator == "gt":
                    match = record_value is not None and record_value > filter_value
                elif operator == "gte":
                    match = record_value is not None and record_value >= filter_value
                elif operator == "lt":
                    match = record_value is not None and record_value < filter_value
                elif operator == "lte":
                    match = record_value is not None and record_value <= filter_value
                elif operator == "in":
                    match = record_value in filter_value
                elif operator == "not_in":
                    match = record_value not in filter_value
                elif operator == "contains":
                    match = (
                        isinstance(record_value, str)
                        and isinstance(filter_value, str)
                        and filter_value in record_value
                    )
                elif operator == "starts_with":
                    match = (
                        isinstance(record_value, str)
                        and isinstance(filter_value, str)
                        and record_value.startswith(filter_value)
                    )
                elif operator == "ends_with":
                    match = (
                        isinstance(record_value, str)
                        and isinstance(filter_value, str)
                        and record_value.endswith(filter_value)
                    )
                elif operator == "regex":
                    match = (
                        isinstance(record_value, str)
                        and re.match(filter_value, record_value) is not None
                    )
                elif operator == "is_null":
                    match = record_value is None
                elif operator == "is_not_null":
                    match = record_value is not None
                else:
                    self.logger.warning(f"Unknown filter operator: {operator}")
                    match = True

                results.append(match)

            except Exception as e:
                self.logger.error(f"Error applying filter {operator} to {field}: {e}")
                results.append(False)

        # Combina resultados (por enquanto só AND)
        return all(results)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Valida configuração do processador."""
        return "filters" in config


# Registry de processadores
PROCESSOR_REGISTRY = {
    "validation": ValidationProcessor,
    "cleaning": CleaningProcessor,
    "transformation": TransformationProcessor,
    "aggregation": AggregationProcessor,
    "filter": FilterProcessor,
}


def create_processor(processor_type: str, name: str = None) -> DataProcessor:
    """Cria instância de processador."""
    processor_class = PROCESSOR_REGISTRY.get(processor_type)
    if processor_class is None:
        raise ValueError(f"Unknown processor type: {processor_type}")

    return processor_class(name or processor_type)


def list_available_processors() -> List[str]:
    """Lista processadores disponíveis."""
    return list(PROCESSOR_REGISTRY.keys())
