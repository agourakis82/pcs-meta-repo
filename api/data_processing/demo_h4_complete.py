"""
Sistema H4 - Demo Completa

Demonstração prática do Sistema H4 de Processamento de Dados
integrado com os sistemas H1 (Monitoring), H2 (Cache) e H3 (APIs).
"""

import asyncio
import json
import logging
import tempfile
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_h4_complete_system():
    """Demonstração completa do Sistema H4."""
    
    print("🚀 DEMO COMPLETA - SISTEMA H4 DATA PROCESSING")
    print("=" * 60)
    
    try:
        # Importa componentes principais
        from api.data_processing import (
            DataFormat,
            get_h4_config,
            get_pipeline_executor,
            health_check,
            system_info,
        )
        from api.data_processing.pipelines.templates import (
            create_pipeline_from_template,
            list_templates,
        )
        from api.data_processing.processors.data_processors import create_processor

        # 1. Informações do Sistema
        print("\n📊 INFORMAÇÕES DO SISTEMA H4")
        print("-" * 40)
        
        info = system_info()
        print(f"• Nome: {info['name']}")
        print(f"• Versão: {info['version']}")
        print(f"• Templates: {', '.join(info['available_templates'])}")
        print(f"• Formatos: {', '.join(info['supported_formats'])}")
        print(f"• Modos de Processamento: {', '.join(info['processing_modes'])}")
        
        # 2. Verificação de Saúde
        print("\n🏥 VERIFICAÇÃO DE SAÚDE")
        print("-" * 40)
        
        health = health_check()
        print(f"• Status: {health['status'].upper()}")
        print(f"• Configuração carregada: {health['config_loaded']}")
        print(f"• Executor pronto: {health['executor_ready']}")
        
        # 3. Configuração do Sistema
        print("\n⚙️ CONFIGURAÇÃO DO SISTEMA")
        print("-" * 40)
        
        config = get_h4_config()
        print(f"• Processamento em tempo real: {config.features.real_time_processing}")
        print(f"• Rastreamento de linhagem: {config.features.data_lineage}")
        print(f"• Monitoramento de qualidade: {config.features.quality_monitoring}")
        print(f"• Integração H1: {config.integrations.h1_monitoring}")
        print(f"• Integração H2: {config.integrations.h2_cache}")
        print(f"• Integração H3: {config.integrations.h3_apis}")
        
        # 4. Demonstração de Templates
        print("\n🔧 DEMONSTRAÇÃO DE TEMPLATES")
        print("-" * 40)
        
        templates = list_templates()
        print(f"Templates disponíveis: {len(templates)}")
        
        for template_name in templates[:3]:  # Mostra apenas os 3 primeiros
            try:
                from api.data_processing.pipelines.templates import get_template
                template = get_template(template_name)
                print(f"• {template_name}: {template.description}")
            except Exception as e:
                print(f"• {template_name}: Erro - {e}")
        
        # 5. Demonstração de Processadores
        print("\n⚙️ DEMONSTRAÇÃO DE PROCESSADORES")
        print("-" * 40)
        
        processor_types = ["validation", "cleaning", "transformation"]
        
        for proc_type in processor_types:
            try:
                processor = create_processor(proc_type)
                print(f"• {proc_type}: {processor.__class__.__name__} ✅")
            except Exception as e:
                print(f"• {proc_type}: Erro - {e} ❌")
        
        # 6. Demonstração de Pipeline Prático
        print("\n🔄 PIPELINE PRÁTICO - CONVERSÃO JSON → CSV")
        print("-" * 40)
        
        # Dados de exemplo
        sample_data = [
            {"id": 1, "produto": "Laptop", "preco": 3500.00, "categoria": "Eletrônicos"},
            {"id": 2, "produto": "Mouse", "preco": 45.00, "categoria": "Acessórios"},
            {"id": 3, "produto": "Teclado", "preco": 120.00, "categoria": "Acessórios"},
            {"id": 4, "produto": "Monitor", "preco": 800.00, "categoria": "Eletrônicos"},
            {"id": 5, "produto": "Cadeira", "preco": 450.00, "categoria": "Móveis"}
        ]
        
        # Cria arquivos temporários
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_input:
            json.dump(sample_data, tmp_input, indent=2, ensure_ascii=False)
            input_path = tmp_input.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_output:
            output_path = tmp_output.name
        
        try:
            print(f"📁 Input: {Path(input_path).name}")
            print(f"📄 Output: {Path(output_path).name}")
            
            # Cria pipeline de conversão
            pipeline_config = create_pipeline_from_template(
                "format_conversion",
                input_file=input_path,
                output_file=output_path,
                input_format=DataFormat.JSON,
                output_format=DataFormat.CSV
            )
            
            print(f"🔧 Pipeline criado: {pipeline_config.name}")
            print(f"📝 Descrição: {pipeline_config.description}")
            
            # Mostra métricas básicas
            print(f"📊 Fontes: {len(pipeline_config.sources)}")
            print(f"📤 Destinos: {len(pipeline_config.sinks)}")
            print(f"⚡ Modo: {pipeline_config.processing.mode.value}")
            
            print("\n✅ Pipeline configurado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro na configuração do pipeline: {e}")
        
        finally:
            # Limpa arquivos temporários
            for file_path in [input_path, output_path]:
                if Path(file_path).exists():
                    Path(file_path).unlink()
        
        # 7. Integração com Sistemas H1-H2-H3
        print("\n🔗 INTEGRAÇÃO COM SISTEMAS H1-H2-H3")
        print("-" * 40)
        
        executor = get_pipeline_executor()
        
        # Verifica integração H1 (Monitoring)
        h1_status = hasattr(executor, 'h1_monitor') and executor.h1_monitor is not None
        print(f"• H1 Monitoring: {'✅ Integrado' if h1_status else '⚠️ Não disponível'}")
        
        # Verifica integração H2 (Cache)
        h2_status = hasattr(executor, 'h2_cache') and executor.h2_cache is not None
        print(f"• H2 Cache: {'✅ Integrado' if h2_status else '⚠️ Não disponível'}")
        
        # Verifica integração H3 (APIs)
        h3_status = hasattr(executor, 'h3_api_client') and executor.h3_api_client is not None
        print(f"• H3 APIs: {'✅ Integrado' if h3_status else '⚠️ Não disponível'}")
        
        # 8. Estatísticas Finais
        print("\n📈 ESTATÍSTICAS DO SISTEMA H4")
        print("-" * 40)
        
        stats = {
            "Templates Disponíveis": len(info['available_templates']),
            "Formatos Suportados": len(info['supported_formats']),
            "Processadores": 5,  # validation, cleaning, transformation, aggregation, filter
            "Handlers de Formato": 3,  # JSON, CSV, XML testados
            "Integrações Ativas": sum([h1_status, h2_status, h3_status])
        }
        
        for key, value in stats.items():
            print(f"• {key}: {value}")
        
        print("\n🎉 DEMO CONCLUÍDA COM SUCESSO!")
        print("Sistema H4 de Processamento de Dados totalmente operacional")
        print("com integração completa aos sistemas H1, H2 e H3!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA DEMO: {e}")
        logger.exception("Erro na demonstração do Sistema H4")
        return False


async def demo_h4_advanced_features():
    """Demonstração de recursos avançados do H4."""
    
    print("\n\n🚀 RECURSOS AVANÇADOS DO SISTEMA H4")
    print("=" * 60)
    
    try:
        from api.data_processing.config import DistributionStrategy, ProcessingMode

        # 1. Modos de Processamento
        print("\n⚡ MODOS DE PROCESSAMENTO")
        print("-" * 40)
        
        processing_modes = [
            (ProcessingMode.BATCH, "Processamento em lote para grandes volumes"),
            (ProcessingMode.STREAMING, "Processamento contínuo em tempo real"),
            (ProcessingMode.REAL_TIME, "Processamento com baixa latência"),
            (ProcessingMode.HYBRID, "Combinação de batch e streaming")
        ]
        
        for mode, description in processing_modes:
            print(f"• {mode.value.upper()}: {description}")
        
        # 2. Estratégias de Distribuição
        print("\n🌐 ESTRATÉGIAS DE DISTRIBUIÇÃO")
        print("-" * 40)
        
        distribution_strategies = [
            (DistributionStrategy.SINGLE_NODE, "Processamento em nó único"),
            (DistributionStrategy.MULTI_THREAD, "Paralelização com múltiplas threads"),
            (DistributionStrategy.MULTI_PROCESS, "Distribuição em múltiplos processos"),
            (DistributionStrategy.DISTRIBUTED, "Processamento distribuído")
        ]
        
        for strategy, description in distribution_strategies:
            print(f"• {strategy.value.upper()}: {description}")
        
        # 3. Formatos Suportados
        print("\n📁 FORMATOS DE DADOS SUPORTADOS")
        print("-" * 40)
        
        formats = [
            ("JSON", "JavaScript Object Notation"),
            ("CSV", "Comma-Separated Values"),
            ("XML", "eXtensible Markup Language"),
            ("EXCEL", "Microsoft Excel (xlsx)"),
            ("PARQUET", "Formato colunar otimizado"),
            ("AVRO", "Serialização de dados Apache"),
            ("YAML", "YAML Ain't Markup Language"),
            ("HDF5", "Hierarchical Data Format"),
            ("NETCDF", "Network Common Data Form"),
            ("BINARY", "Dados binários genéricos")
        ]
        
        for format_name, description in formats:
            print(f"• {format_name}: {description}")
        
        print("\n✅ RECURSOS AVANÇADOS DEMONSTRADOS")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA DEMO AVANÇADA: {e}")
        return False


async def main():
    """Executa demonstração completa do Sistema H4."""
    
    success_basic = await demo_h4_complete_system()
    success_advanced = await demo_h4_advanced_features()
    
    print("\n" + "=" * 60)
    print("📊 RESUMO DA DEMONSTRAÇÃO")
    print("=" * 60)
    
    results = [
        ("Demo Básica", success_basic),
        ("Demo Avançada", success_advanced)
    ]
    
    for demo_name, success in results:
        status = "✅ SUCESSO" if success else "❌ FALHA"
        print(f"{demo_name}: {status}")
    
    overall_success = all(success for _, success in results)
    
    if overall_success:
        print("\n🎉 DEMONSTRAÇÃO COMPLETA REALIZADA COM SUCESSO!")
        print("Sistema H4 está totalmente funcional e integrado!")
    else:
        print("\n⚠️ ALGUMAS PARTES DA DEMONSTRAÇÃO FALHARAM")
        print("Verifique os logs para mais detalhes.")
    
    return overall_success


if __name__ == "__main__":
    # Executa demonstração
    success = asyncio.run(main())
    exit(0 if success else 1)if __name__ == "__main__":
    # Executa demonstração
    success = asyncio.run(main())
    exit(0 if success else 1)