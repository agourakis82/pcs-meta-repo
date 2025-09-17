"""
Testes de Integração - Sistema H4 (Processamento de Dados)

Testes completos para validar o sistema de processamento de dados,
incluindo pipelines, transformações, ETL e análise de dados.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Adiciona o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging

from tests.test_framework import TestSuite, test_framework

logger = logging.getLogger(__name__)


class H4IntegrationTests:
    """Testes de integração para o Sistema H4."""
    
    @staticmethod
    async def setup():
        """Setup inicial para testes H4."""
        logger.info("Configurando ambiente de testes H4")
        # Cria dados de teste temporários
        test_data = {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "value": [10.5, 20.3, 15.7, 30.1, 25.9],
            "category": ["A", "B", "A", "C", "B"],
            "timestamp": [
                datetime.now() - timedelta(days=i) for i in range(5)
            ]
        }
        
        # Salva dados de teste
        df = pd.DataFrame(test_data)
        os.makedirs("/tmp/test_data", exist_ok=True)
        df.to_csv("/tmp/test_data/sample.csv", index=False)
        
        return True
    
    @staticmethod
    async def teardown():
        """Limpeza após testes H4."""
        logger.info("Limpando ambiente de testes H4")
        # Remove dados de teste
        import shutil
        try:
            shutil.rmtree("/tmp/test_data")
        except Exception:
            pass
    
    @staticmethod
    async def test_h4_data_ingestion():
        """Testa ingestão de dados do H4."""
        try:
            from data_processing.ingestion import DataIngestion
            
            ingestion = DataIngestion()
            
            # Testa ingestão de CSV
            df = await ingestion.ingest_csv("/tmp/test_data/sample.csv")
            
            assert df is not None, "DataFrame deve ser criado"
            assert len(df) > 0, "DataFrame deve ter dados"
            assert "id" in df.columns, "Deve ter coluna id"
            assert "name" in df.columns, "Deve ter coluna name"
            
            # Testa validação de dados
            validation_result = await ingestion.validate_data(df)
            
            return {
                "passed": validation_result,
                "metrics": {
                    "rows_ingested": len(df),
                    "columns_ingested": len(df.columns),
                    "data_valid": validation_result,
                    "file_processed": True
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de ingestão não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h4_data_transformation():
        """Testa transformações de dados do H4."""
        try:
            from data_processing.transformation import DataTransformer
            
            transformer = DataTransformer()
            
            # Cria dados de teste
            test_df = pd.DataFrame({
                "value": [1, 2, 3, 4, 5],
                "category": ["A", "B", "A", "C", "B"],
                "date": pd.date_range("2023-01-01", periods=5)
            })
            
            # Testa normalização
            normalized = await transformer.normalize_values(test_df, "value")
            assert normalized is not None, "Normalização deve funcionar"
            
            # Testa agregação por categoria
            aggregated = await transformer.aggregate_by_category(test_df)
            assert aggregated is not None, "Agregação deve funcionar"
            
            # Testa limpeza de dados
            cleaned = await transformer.clean_data(test_df)
            assert cleaned is not None, "Limpeza deve funcionar"
            
            return {
                "passed": True,
                "metrics": {
                    "normalization": normalized is not None,
                    "aggregation": aggregated is not None,
                    "cleaning": cleaned is not None,
                    "transformations_count": 3
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de transformação não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h4_pipeline_execution():
        """Testa execução de pipeline de dados."""
        try:
            from data_processing.pipeline import DataPipeline
            
            pipeline = DataPipeline()
            
            # Define pipeline de teste
            pipeline_config = {
                "stages": [
                    {"type": "ingest", "source": "/tmp/test_data/sample.csv"},
                    {"type": "validate", "rules": ["not_null", "type_check"]},
                    {"type": "transform", "operations": ["normalize", "clean"]},
                    {"type": "aggregate", "groupby": "category"}
                ]
            }
            
            # Executa pipeline
            result = await pipeline.execute(pipeline_config)
            
            assert result is not None, "Pipeline deve retornar resultado"
            assert result.get("status") == "success", "Pipeline deve ser bem-sucedido"
            
            # Verifica estágios executados
            stages_executed = result.get("stages_executed", 0)
            expected_stages = len(pipeline_config["stages"])
            
            return {
                "passed": stages_executed == expected_stages,
                "metrics": {
                    "stages_expected": expected_stages,
                    "stages_executed": stages_executed,
                    "pipeline_success": result.get("status") == "success",
                    "execution_time": result.get("execution_time", 0)
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de pipeline não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h4_ml_processing():
        """Testa processamento de machine learning."""
        try:
            from data_processing.ml import MLProcessor
            
            processor = MLProcessor()
            
            # Cria dataset de teste para ML
            X = np.random.rand(100, 5)
            y = np.random.rand(100)
            
            # Testa feature engineering
            features_engineered = await processor.engineer_features(X)
            assert features_engineered is not None, "Feature engineering deve funcionar"
            
            # Testa treinamento de modelo simples
            model = await processor.train_model(X, y, model_type="linear")
            assert model is not None, "Modelo deve ser treinado"
            
            # Testa predição
            predictions = await processor.predict(model, X[:10])
            assert predictions is not None, "Predições devem ser geradas"
            assert len(predictions) == 10, "Deve prever para 10 amostras"
            
            return {
                "passed": True,
                "metrics": {
                    "feature_engineering": features_engineered is not None,
                    "model_training": model is not None,
                    "predictions": predictions is not None,
                    "prediction_count": len(predictions) if predictions is not None else 0
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de ML não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h4_batch_processing():
        """Testa processamento em lote."""
        try:
            from data_processing.batch import BatchProcessor
            
            processor = BatchProcessor()
            
            # Cria múltiplos arquivos de teste
            batch_files = []
            for i in range(3):
                file_path = f"/tmp/test_data/batch_{i}.csv"
                test_data = pd.DataFrame({
                    "id": range(i*10, (i+1)*10),
                    "value": np.random.rand(10),
                    "batch": i
                })
                test_data.to_csv(file_path, index=False)
                batch_files.append(file_path)
            
            # Processa lote
            batch_config = {
                "files": batch_files,
                "chunk_size": 5,
                "parallel": True
            }
            
            result = await processor.process_batch(batch_config)
            
            assert result is not None, "Resultado do lote deve existir"
            files_processed = result.get("files_processed", 0)
            total_records = result.get("total_records", 0)
            
            return {
                "passed": files_processed == 3 and total_records == 30,
                "metrics": {
                    "files_processed": files_processed,
                    "total_records": total_records,
                    "processing_time": result.get("processing_time", 0),
                    "batch_success": result.get("status") == "success"
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de batch não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h4_streaming_processing():
        """Testa processamento em streaming."""
        try:
            from data_processing.streaming import StreamProcessor
            
            processor = StreamProcessor()
            
            # Simula stream de dados
            async def mock_data_stream():
                for i in range(10):
                    yield {
                        "id": i,
                        "value": np.random.rand(),
                        "timestamp": datetime.now()
                    }
                    await asyncio.sleep(0.01)  # Simula chegada de dados
            
            # Processa stream
            results = []
            async for processed_data in processor.process_stream(mock_data_stream()):
                results.append(processed_data)
                if len(results) >= 10:  # Processa 10 items
                    break
            
            stream_successful = len(results) == 10
            all_processed = all(item.get("processed", False) for item in results)
            
            return {
                "passed": stream_successful and all_processed,
                "metrics": {
                    "items_processed": len(results),
                    "stream_complete": stream_successful,
                    "all_processed": all_processed,
                    "avg_processing_time": np.mean([
                        item.get("processing_time", 0) for item in results
                    ])
                }
            }
            
        except ImportError:
            return {
                "passed": False,
                "error": "Módulo de streaming não encontrado"
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_h4_integration_with_other_systems():
        """Testa integração do H4 com outros sistemas."""
        try:
            # Testa integração com H1 (monitoring)
            h1_integration = False
            try:
                from data_processing.monitoring import send_metrics
                result = await send_metrics({
                    "processed_records": 100,
                    "processing_time": 1.5
                })
                h1_integration = result is not None
            except Exception:
                pass
            
            # Testa integração com H2 (cache)
            h2_integration = False
            try:
                from data_processing.cache import cache_results
                result = await cache_results("test_key", {"data": "test"})
                h2_integration = result is not None
            except Exception:
                pass
            
            # Testa integração com H3 (API)
            h3_integration = False
            try:
                from data_processing.api import expose_pipeline_status
                status = await expose_pipeline_status()
                h3_integration = status is not None
            except Exception:
                pass
            
            total_integrations = sum([h1_integration, h2_integration, h3_integration])
            
            return {
                "passed": total_integrations >= 1,  # Pelo menos 1 integração
                "metrics": {
                    "h1_integration": h1_integration,
                    "h2_integration": h2_integration,
                    "h3_integration": h3_integration,
                    "total_integrations": total_integrations
                }
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }


# Registra a suite de testes H4
def register_h4_tests():
    """Registra todos os testes H4 no framework."""
    
    suite = TestSuite(
        name="h4_integration",
        description="Testes de integração do Sistema H4 (Processamento de Dados)",
        setup_func=H4IntegrationTests.setup,
        teardown_func=H4IntegrationTests.teardown
    )
    
    # Adiciona todos os métodos de teste
    suite.tests = [
        H4IntegrationTests.test_h4_data_ingestion,
        H4IntegrationTests.test_h4_data_transformation,
        H4IntegrationTests.test_h4_pipeline_execution,
        H4IntegrationTests.test_h4_ml_processing,
        H4IntegrationTests.test_h4_batch_processing,
        H4IntegrationTests.test_h4_streaming_processing,
        H4IntegrationTests.test_h4_integration_with_other_systems
    ]
    
    test_framework.register_suite(suite)
    logger.info("Testes H4 registrados no framework")


# Função para executar apenas testes H4
async def run_h4_tests():
    """Executa apenas os testes H4."""
    register_h4_tests()
    
    results = await test_framework.run_suite("h4_integration")
    
    print("=" * 60)
    print("RESULTADOS DOS TESTES H4 (Processamento de Dados)")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print(f"Testes executados: {total}")
    print(f"Testes passaram: {passed}")
    print(f"Taxa de sucesso: {(passed/total*100):.1f}%")
    
    for result in results:
        status = "✅" if result.passed else "❌"
        print(f"{status} {result.test_name} ({result.duration:.2f}s)")
        if not result.passed:
            print(f"   Error: {result.error_message}")
    
    return passed == total


if __name__ == "__main__":
    # Executa testes H4 quando executado diretamente
    success = asyncio.run(run_h4_tests())
    exit(0 if success else 1)