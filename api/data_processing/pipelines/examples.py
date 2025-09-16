"""
Sistema H4 - Exemplos de Pipelines

Exemplos práticos de como usar o sistema de processamento de dados.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List

from ..config import DataFormat, DistributionStrategy, ProcessingMode
from .templates import (
    aggregate_data_file,
    clean_data_file,
    convert_file_format,
    execute_template_pipeline,
    simple_file_to_file_etl,
    validate_data_file,
)

logger = logging.getLogger(__name__)


async def example_simple_etl():
    """Exemplo de ETL simples: JSON para CSV."""
    print("=== Exemplo: ETL Simples ===")

    # Dados de exemplo
    input_data = [
        {"name": "João", "age": 30, "city": "São Paulo"},
        {"name": "Maria", "age": 25, "city": "Rio de Janeiro"},
        {"name": "Pedro", "age": 35, "city": "Belo Horizonte"},
    ]

    # Salva dados de entrada
    import json

    input_file = "example_input.json"
    with open(input_file, "w") as f:
        json.dump(input_data, f, indent=2)

    # Configura e executa pipeline
    try:
        result = await execute_template_pipeline(
            "simple_etl",
            input_file=input_file,
            output_file="example_output.csv",
            input_format=DataFormat.JSON,
            output_format=DataFormat.CSV,
            enable_validation=True,
        )

        print(f"Pipeline executado com sucesso!")
        print(f"Métricas: {result.metrics}")

        # Verifica arquivo de saída
        if Path("example_output.csv").exists():
            print("Arquivo CSV criado com sucesso!")

    except Exception as e:
        print(f"Erro no pipeline: {e}")

    finally:
        # Limpa arquivos temporários
        for file in ["example_input.json", "example_output.csv"]:
            if Path(file).exists():
                Path(file).unlink()


async def example_data_validation():
    """Exemplo de validação de dados."""
    print("\n=== Exemplo: Validação de Dados ===")

    # Dados com alguns problemas
    input_data = [
        {"name": "João", "age": 30, "email": "joao@email.com"},
        {"name": "", "age": -5, "email": "invalid_email"},  # Problemas
        {"name": "Maria", "age": 25, "email": "maria@email.com"},
        {"name": "Pedro", "age": 200, "email": "pedro@email.com"},  # Idade suspeita
    ]

    # Regras de validação
    validation_rules = [
        {"field": "name", "rule_type": "required", "message": "Nome é obrigatório"},
        {
            "field": "name",
            "rule_type": "min_length",
            "value": 1,
            "message": "Nome deve ter pelo menos 1 caractere",
        },
        {
            "field": "age",
            "rule_type": "range",
            "min_value": 0,
            "max_value": 120,
            "message": "Idade deve estar entre 0 e 120 anos",
        },
        {
            "field": "email",
            "rule_type": "pattern",
            "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "message": "Email deve ter formato válido",
        },
    ]

    # Salva dados de entrada
    import json

    input_file = "validation_input.json"
    with open(input_file, "w") as f:
        json.dump(input_data, f, indent=2)

    try:
        result = await execute_template_pipeline(
            "data_validation",
            input_file=input_file,
            validation_rules=validation_rules,
            output_file="validated_output.json",
            generate_report=True,
        )

        print(f"Validação executada!")
        print(f"Métricas: {result.metrics}")

        # Lê relatório de validação
        report_file = "validation_input.validation_report.json"
        if Path(report_file).exists():
            with open(report_file, "r") as f:
                report = json.load(f)
            print(f"Relatório de validação: {report}")

    except Exception as e:
        print(f"Erro na validação: {e}")

    finally:
        # Limpa arquivos temporários
        for file in [
            "validation_input.json",
            "validated_output.json",
            "validation_input.validation_report.json",
        ]:
            if Path(file).exists():
                Path(file).unlink()


async def example_data_cleaning():
    """Exemplo de limpeza de dados."""
    print("\n=== Exemplo: Limpeza de Dados ===")

    # Dados com problemas de qualidade
    input_data = [
        {"name": "  João  ", "age": "30", "city": "são paulo"},
        {"name": "MARIA", "age": "25.0", "city": "RIO DE JANEIRO"},
        {"name": "pedro", "age": "35", "city": "   belo horizonte   "},
    ]

    # Regras de limpeza
    cleaning_rules = [
        {"field": "name", "operations": ["trim", "title_case"]},
        {"field": "age", "operations": ["to_int"]},
        {"field": "city", "operations": ["trim", "title_case"]},
    ]

    # Salva dados de entrada
    import json

    input_file = "cleaning_input.json"
    with open(input_file, "w") as f:
        json.dump(input_data, f, indent=2)

    try:
        result = await execute_template_pipeline(
            "data_cleaning",
            input_file=input_file,
            output_file="cleaned_output.json",
            cleaning_rules=cleaning_rules,
        )

        print(f"Limpeza executada!")
        print(f"Métricas: {result.metrics}")

        # Verifica dados limpos
        if Path("cleaned_output.json").exists():
            with open("cleaned_output.json", "r") as f:
                cleaned_data = json.load(f)
            print(f"Dados limpos: {cleaned_data}")

    except Exception as e:
        print(f"Erro na limpeza: {e}")

    finally:
        # Limpa arquivos temporários
        for file in ["cleaning_input.json", "cleaned_output.json"]:
            if Path(file).exists():
                Path(file).unlink()


async def example_format_conversion():
    """Exemplo de conversão de formato."""
    print("\n=== Exemplo: Conversão de Formato ===")

    # Dados de exemplo
    input_data = [
        {"produto": "Notebook", "preco": 2500.00, "categoria": "Eletrônicos"},
        {"produto": "Mesa", "preco": 450.00, "categoria": "Móveis"},
        {"produto": "Livro", "preco": 35.00, "categoria": "Educação"},
    ]

    # Salva como JSON
    import json

    input_file = "products.json"
    with open(input_file, "w") as f:
        json.dump(input_data, f, indent=2)

    try:
        # Converte JSON para CSV
        result = await execute_template_pipeline(
            "format_conversion",
            input_file=input_file,
            output_file="products.csv",
            input_format=DataFormat.JSON,
            output_format=DataFormat.CSV,
        )

        print(f"Conversão executada!")
        print(f"Métricas: {result.metrics}")

        # Verifica arquivo CSV
        if Path("products.csv").exists():
            with open("products.csv", "r") as f:
                content = f.read()
            print(f"Conteúdo CSV:\n{content}")

    except Exception as e:
        print(f"Erro na conversão: {e}")

    finally:
        # Limpa arquivos temporários
        for file in ["products.json", "products.csv"]:
            if Path(file).exists():
                Path(file).unlink()


async def example_data_aggregation():
    """Exemplo de agregação de dados."""
    print("\n=== Exemplo: Agregação de Dados ===")

    # Dados de vendas
    sales_data = [
        {
            "produto": "Notebook",
            "categoria": "Eletrônicos",
            "vendas": 10,
            "receita": 25000,
        },
        {"produto": "Mouse", "categoria": "Eletrônicos", "vendas": 50, "receita": 1500},
        {"produto": "Mesa", "categoria": "Móveis", "vendas": 8, "receita": 3600},
        {"produto": "Cadeira", "categoria": "Móveis", "vendas": 12, "receita": 2400},
        {"produto": "Livro", "categoria": "Educação", "vendas": 30, "receita": 1050},
    ]

    # Configuração de agregação
    group_by_fields = ["categoria"]
    aggregations = [
        {"field": "vendas", "function": "sum"},
        {"field": "receita", "function": "sum"},
        {"field": "receita", "function": "avg", "alias": "receita_media"},
    ]

    # Salva dados de entrada
    import json

    input_file = "sales.json"
    with open(input_file, "w") as f:
        json.dump(sales_data, f, indent=2)

    try:
        result = await execute_template_pipeline(
            "aggregation",
            input_file=input_file,
            output_file="sales_summary.json",
            group_by_fields=group_by_fields,
            aggregations=aggregations,
        )

        print(f"Agregação executada!")
        print(f"Métricas: {result.metrics}")

        # Verifica resultado
        if Path("sales_summary.json").exists():
            with open("sales_summary.json", "r") as f:
                summary = json.load(f)
            print(f"Resumo por categoria: {summary}")

    except Exception as e:
        print(f"Erro na agregação: {e}")

    finally:
        # Limpa arquivos temporários
        for file in ["sales.json", "sales_summary.json"]:
            if Path(file).exists():
                Path(file).unlink()


async def example_multi_file_processing():
    """Exemplo de processamento de múltiplos arquivos."""
    print("\n=== Exemplo: Processamento Multi-Arquivo ===")

    # Cria múltiplos arquivos de dados
    files_data = [
        ("data_2023_01.json", [{"month": "2023-01", "sales": 1000}]),
        ("data_2023_02.json", [{"month": "2023-02", "sales": 1200}]),
        ("data_2023_03.json", [{"month": "2023-03", "sales": 1100}]),
    ]

    import json

    for filename, data in files_data:
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    try:
        result = await execute_template_pipeline(
            "multi_file_etl",
            input_pattern="data_2023_*.json",
            output_file="consolidated_sales.json",
            input_format=DataFormat.JSON,
            output_format=DataFormat.JSON,
        )

        print(f"Consolidação executada!")
        print(f"Métricas: {result.metrics}")

        # Verifica arquivo consolidado
        if Path("consolidated_sales.json").exists():
            with open("consolidated_sales.json", "r") as f:
                consolidated = json.load(f)
            print(f"Dados consolidados: {consolidated}")

    except Exception as e:
        print(f"Erro na consolidação: {e}")

    finally:
        # Limpa arquivos temporários
        files_to_clean = [
            "data_2023_01.json",
            "data_2023_02.json",
            "data_2023_03.json",
            "consolidated_sales.json",
        ]
        for file in files_to_clean:
            if Path(file).exists():
                Path(file).unlink()


async def example_custom_pipeline():
    """Exemplo de pipeline customizado usando configuração manual."""
    print("\n=== Exemplo: Pipeline Customizado ===")

    from ..config import (
        PipelineConfig,
        ProcessingConfig,
        QualityConfig,
        create_file_sink,
        create_file_source,
    )
    from ..engine import get_pipeline_executor
    from ..processors.data_processors import create_processor

    # Dados de exemplo com diferentes tipos de problemas
    complex_data = [
        {
            "id": 1,
            "name": "  João  ",
            "age": "30",
            "email": "joao@email.com",
            "salary": "5000.50",
        },
        {"id": 2, "name": "", "age": "-5", "email": "invalid", "salary": "abc"},
        {
            "id": 3,
            "name": "MARIA",
            "age": "25",
            "email": "maria@email.com",
            "salary": "3500.00",
        },
        {
            "id": None,
            "name": "pedro",
            "age": "200",
            "email": "pedro@email.com",
            "salary": "",
        },
    ]

    # Salva dados de entrada
    import json

    input_file = "complex_data.json"
    with open(input_file, "w") as f:
        json.dump(complex_data, f, indent=2)

    try:
        # Configuração customizada
        source = create_file_source("input", input_file, format=DataFormat.JSON)
        sink = create_file_sink("output", "processed_data.json", format=DataFormat.JSON)

        processing_config = ProcessingConfig(
            mode=ProcessingMode.BATCH,
            distribution=DistributionStrategy.SINGLE_NODE,
            enable_caching=True,
        )

        quality_config = QualityConfig(
            enable_validation=True, enable_profiling=True, audit_trail=True
        )

        pipeline_config = PipelineConfig(
            name="custom_complex_pipeline",
            description="Pipeline customizado para dados complexos",
            sources=[source],
            sinks=[sink],
            processing=processing_config,
            quality=quality_config,
        )

        # Executor e processadores
        executor = get_pipeline_executor()

        # Processador de validação
        validator = create_processor("validation")
        validator.add_rule("id", "required", message="ID é obrigatório")
        validator.add_rule(
            "id", "type", expected_type="int", message="ID deve ser inteiro"
        )
        validator.add_rule("name", "required", message="Nome é obrigatório")
        validator.add_rule(
            "age", "range", min_value=0, max_value=120, message="Idade inválida"
        )
        validator.add_rule(
            "email",
            "pattern",
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            message="Email inválido",
        )

        # Processador de limpeza
        cleaner = create_processor("cleaning")
        cleaner.add_cleaning_rule("name", ["trim", "title_case"])
        cleaner.add_cleaning_rule("age", ["to_int"])
        cleaner.add_cleaning_rule("salary", ["to_float"])

        # Processador de transformação
        transformer = create_processor("transformation")
        transformer.add_calculated_field(
            "salary_category",
            lambda row: "Alto" if row.get("salary", 0) > 4000 else "Médio",
        )

        # Registra processadores
        executor.register_processor(validator)
        executor.register_processor(cleaner)
        executor.register_processor(transformer)

        # Executa pipeline
        result = await executor.execute_pipeline(pipeline_config)

        print(f"Pipeline customizado executado!")
        print(f"Métricas: {result.metrics}")

        # Verifica resultado
        if Path("processed_data.json").exists():
            with open("processed_data.json", "r") as f:
                processed = json.load(f)
            print(f"Dados processados: {processed}")

    except Exception as e:
        print(f"Erro no pipeline customizado: {e}")

    finally:
        # Limpa arquivos temporários
        for file in ["complex_data.json", "processed_data.json"]:
            if Path(file).exists():
                Path(file).unlink()


async def run_all_examples():
    """Executa todos os exemplos."""
    print("🚀 Executando exemplos do Sistema H4 de Processamento de Dados\n")

    examples = [
        example_simple_etl,
        example_data_validation,
        example_data_cleaning,
        example_format_conversion,
        example_data_aggregation,
        example_multi_file_processing,
        example_custom_pipeline,
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"Erro no exemplo {example.__name__}: {e}")

        print("-" * 50)


if __name__ == "__main__":
    # Configura logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Executa exemplos
    asyncio.run(run_all_examples())
    # Executa exemplos
    asyncio.run(run_all_examples())
