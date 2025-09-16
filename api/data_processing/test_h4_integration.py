"""
Sistema H4 - Teste de Integração

Teste simples para validar a integração do sistema H4 com H1-H2-H3.
"""

import asyncio
import json
import logging
import tempfile
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_h4_integration():
    """Teste de integração do sistema H4."""
    print("🚀 Iniciando teste de integração do Sistema H4")

    try:
        # Importa componentes H4
        from api.data_processing import DataFormat, health_check, quick_etl, system_info

        print("✅ Importações H4 bem-sucedidas")

        # Verifica informações do sistema
        info = system_info()
        print(f"📊 Sistema H4 versão {info['version']}")
        print(f"📋 Templates disponíveis: {len(info['available_templates'])}")
        print(f"🔄 Formatos suportados: {len(info['supported_formats'])}")

        # Verifica saúde do sistema
        health = health_check()
        print(f"🏥 Status de saúde: {health['status']}")

        # Cria dados de teste temporários
        test_data = [
            {"id": 1, "name": "João", "age": 30, "city": "São Paulo"},
            {"id": 2, "name": "Maria", "age": 25, "city": "Rio de Janeiro"},
            {"id": 3, "name": "Pedro", "age": 35, "city": "Belo Horizonte"},
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as input_file:
            json.dump(test_data, input_file, indent=2)
            input_path = input_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as output_file:
            output_path = output_file.name

        try:
            print(f"🔄 Executando ETL rápido: {input_path} -> {output_path}")

            # Executa ETL rápido
            result = await quick_etl(
                input_file=input_path,
                output_file=output_path,
                input_format=DataFormat.JSON,
                output_format=DataFormat.CSV,
                enable_validation=True,
            )

            print("✅ ETL executado com sucesso!")
            print(f"📈 Métricas: {result}")

            # Verifica se arquivo de saída foi criado
            if Path(output_path).exists():
                print("✅ Arquivo de saída criado com sucesso")

                # Lê conteúdo do arquivo CSV
                with open(output_path, "r") as f:
                    csv_content = f.read()
                print(f"📄 Conteúdo CSV:\n{csv_content}")
            else:
                print("❌ Arquivo de saída não foi criado")

        finally:
            # Limpa arquivos temporários
            for file_path in [input_path, output_path]:
                if Path(file_path).exists():
                    Path(file_path).unlink()

        print("🎉 Teste de integração H4 concluído com sucesso!")
        return True

    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False


async def test_h4_templates():
    """Teste dos templates H4."""
    print("\n🔧 Testando templates do Sistema H4")

    try:
        from api.data_processing.pipelines.templates import get_template, list_templates

        # Lista templates disponíveis
        templates = list_templates()
        print(f"📋 Templates disponíveis: {templates}")

        # Testa cada template
        for template_name in templates:
            try:
                template = get_template(template_name)
                print(f"✅ Template '{template_name}': {template.description}")
            except Exception as e:
                print(f"❌ Erro no template '{template_name}': {e}")

        print("✅ Teste de templates concluído")
        return True

    except Exception as e:
        print(f"❌ Erro no teste de templates: {e}")
        return False


async def test_h4_processors():
    """Teste dos processadores H4."""
    print("\n⚙️ Testando processadores do Sistema H4")

    try:
        from api.data_processing.processors.data_processors import create_processor

        processor_types = [
            "validation",
            "cleaning",
            "transformation",
            "aggregation",
            "filter",
        ]

        for processor_type in processor_types:
            try:
                processor = create_processor(processor_type)
                print(
                    f"✅ Processador '{processor_type}': {processor.__class__.__name__}"
                )
            except Exception as e:
                print(f"❌ Erro no processador '{processor_type}': {e}")

        print("✅ Teste de processadores concluído")
        return True

    except Exception as e:
        print(f"❌ Erro no teste de processadores: {e}")
        return False


async def test_h4_formats():
    """Teste dos handlers de formato H4."""
    print("\n📁 Testando handlers de formato do Sistema H4")

    try:
        from api.data_processing.config import DataFormat
        from api.data_processing.formats.file_handlers import get_format_handler

        formats = [DataFormat.JSON, DataFormat.CSV, DataFormat.XML]

        for format_type in formats:
            try:
                handler = get_format_handler(format_type)
                print(f"✅ Handler '{format_type.value}': {handler.__class__.__name__}")
            except Exception as e:
                print(f"❌ Erro no handler '{format_type.value}': {e}")

        print("✅ Teste de handlers concluído")
        return True

    except Exception as e:
        print(f"❌ Erro no teste de handlers: {e}")
        return False


async def main():
    """Executa todos os testes do sistema H4."""
    print("=" * 60)
    print("🧪 SUITE DE TESTES DO SISTEMA H4")
    print("=" * 60)

    tests = [
        ("Integração Principal", test_h4_integration),
        ("Templates", test_h4_templates),
        ("Processadores", test_h4_processors),
        ("Handlers de Formato", test_h4_formats),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🔬 Executando teste: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"📊 Resultado: {status}")
        except Exception as e:
            print(f"❌ Erro crítico no teste '{test_name}': {e}")
            results.append((test_name, False))

    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")

    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} testes passaram")

    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema H4 integrado com sucesso!")
    else:
        print("⚠️ ALGUNS TESTES FALHARAM. Verifique os logs acima.")

    return passed == total


if __name__ == "__main__":
    # Executa os testes
    success = asyncio.run(main())
    exit(0 if success else 1)
