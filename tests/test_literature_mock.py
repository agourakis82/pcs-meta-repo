#!/usr/bin/env python3
"""
Teste mock do endpoint de literatura científica do RAG++
(não depende de APIs externas)
"""

import asyncio
import json
import os
import sys
from datetime import datetime

import aiohttp

RAG_SERVER_URL = "http://127.0.0.1:8000"


async def test_with_mock_data():
    """
    Teste com dados mock para verificar se o endpoint funciona
    """
    print("🧪 Testando endpoint com dados mock...")

    # Dados mock de papers científicos
    mock_papers = {
        "machine_learning": [
            {
                "title": "Efficient Transformers: A Survey",
                "authors": ["Yi Tay", "Mostafa Dehghani", "Jai Gupta"],
                "abstract": "Transformer model architectures have garnered immense interest lately due to their effectiveness across a range of domains like language, vision and reinforcement learning. With the burgeoning application of transformers in many domains, a variety of efficient transformer designs have been proposed.",
                "url": "http://arxiv.org/abs/2009.06732",
                "source": "arXiv",
                "categories": ["cs.LG", "cs.AI"],
                "published_date": "2020-09-14",
                "keywords": ["transformers", "efficiency", "survey"],
                "citation_count": 1200,
                "doi": None,
                "venue": "ACM Computing Surveys",
                "significance_score": 4.8,
                "technical_concepts": [
                    "attention mechanisms",
                    "computational efficiency",
                    "model compression",
                ],
                "methodology": "Survey and comparative analysis of efficient transformer architectures",
                "results_summary": "Comprehensive review of 50+ efficient transformer variants with performance comparisons",
                "code_availability": True,
            }
        ],
        "statistics": [
            {
                "title": "Bayesian Deep Learning for Medical Diagnosis",
                "authors": ["Sarah Johnson", "Michael Chen"],
                "abstract": "This paper presents a comprehensive approach to uncertainty quantification in medical diagnosis using Bayesian deep learning techniques. We demonstrate improved reliability and interpretability compared to standard deterministic approaches.",
                "url": "http://arxiv.org/abs/2021.03456",
                "source": "arXiv",
                "categories": ["stat.ML", "cs.LG"],
                "published_date": "2021-03-15",
                "keywords": ["bayesian learning", "medical diagnosis", "uncertainty"],
                "citation_count": 450,
                "doi": "10.1038/s41591-021-01234-5",
                "venue": "Nature Medicine",
                "significance_score": 4.2,
                "technical_concepts": [
                    "bayesian inference",
                    "uncertainty quantification",
                    "medical AI",
                ],
                "methodology": "Variational inference with deep neural networks",
                "results_summary": "15% improvement in diagnostic accuracy with calibrated uncertainty estimates",
                "code_availability": True,
            }
        ],
        "mathematics": [
            {
                "title": "Optimal Transport for Machine Learning: Theory and Applications",
                "authors": ["Gabriel Peyré", "Marco Cuturi"],
                "abstract": "Optimal transport (OT) theory can be informally described using the words of the French mathematician Gaspard Monge (1746-1818): how to move a pile of sand to an excavation of the same volume with the least effort?",
                "url": "http://arxiv.org/abs/1803.00567",
                "source": "arXiv",
                "categories": ["math.OC", "cs.LG"],
                "published_date": "2018-03-01",
                "keywords": [
                    "optimal transport",
                    "wasserstein distance",
                    "machine learning",
                ],
                "citation_count": 2100,
                "doi": None,
                "venue": "Foundations and Trends in Machine Learning",
                "significance_score": 4.9,
                "technical_concepts": [
                    "optimal transport",
                    "wasserstein metrics",
                    "computational geometry",
                ],
                "methodology": "Theoretical analysis with algorithmic implementations",
                "results_summary": "Unified framework for OT applications in ML with computational advances",
                "code_availability": True,
            }
        ],
        "visualization": [
            {
                "title": "Grammar of Graphics for Neural Network Visualization",
                "authors": ["Lisa Wang", "Robert Taylor"],
                "abstract": "We propose a new framework for visualizing neural networks based on the grammar of graphics, enabling more intuitive and informative visualizations of complex model architectures and learned representations.",
                "url": "http://arxiv.org/abs/2022.05789",
                "source": "arXiv",
                "categories": ["cs.LG", "cs.HC"],
                "published_date": "2022-05-20",
                "keywords": [
                    "neural network visualization",
                    "grammar of graphics",
                    "interpretability",
                ],
                "citation_count": 180,
                "doi": None,
                "venue": "IEEE VIS",
                "significance_score": 3.8,
                "technical_concepts": [
                    "neural network interpretation",
                    "data visualization",
                    "visual analytics",
                ],
                "methodology": "Extension of ggplot2 grammar for neural network components",
                "results_summary": "Improved model understanding and debugging capabilities",
                "code_availability": True,
            }
        ],
    }

    # Verificar se o servidor está rodando
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{RAG_SERVER_URL}/health") as response:
                if response.status != 200:
                    print(f"❌ Servidor RAG++ não está saudável: {response.status}")
                    return False
                print("✅ Servidor RAG++ está rodando")
        except Exception as e:
            print(f"❌ Erro ao conectar com RAG++: {e}")
            return False

        # Enviar dados mock
        payload = {
            "papers": mock_papers,
            "collection_metadata": {
                "collection_date": datetime.now().isoformat(),
                "collector_version": "1.0",
                "test_mode": True,
                "mock_data": True,
                "areas_collected": list(mock_papers.keys()),
            },
            "processing_options": {
                "high_impact_threshold": 3.5,
                "store_individual_papers": True,
            },
        }

        try:
            async with session.post(
                f"{RAG_SERVER_URL}/admin/feed-literature",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Literatura enviada com sucesso!")
                    print(
                        f"   📝 Memórias armazenadas: {result.get('memories_stored', 0)}"
                    )
                    print(
                        f"   📚 Papers processados: {result.get('papers_processed', 0)}"
                    )

                    stats = result.get("collection_stats", {})
                    print("   📊 Estatísticas:")
                    print(f"       - Total papers: {stats.get('total_papers', 0)}")
                    print(
                        f"       - Alto impacto: {stats.get('high_impact_papers', 0)}"
                    )
                    print(f"       - Áreas cobertas: {stats.get('areas_covered', 0)}")
                    print(
                        f"       - Significância média: {stats.get('avg_significance', 0):.2f}"
                    )

                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Erro ao enviar literatura: {response.status}")
                    print(f"   Detalhes: {error_text}")
                    return False

        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return False


async def test_literature_stats():
    """
    Testa o endpoint de estatísticas de literatura
    """
    print("\n📈 Testando endpoint de estatísticas...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{RAG_SERVER_URL}/admin/literature-stats"
            ) as response:
                if response.status == 200:
                    stats = await response.json()
                    print("✅ Estatísticas obtidas com sucesso!")
                    print(f"   📚 Total de papers: {stats.get('total_papers', 0)}")
                    print(
                        f"   🌟 Papers de alto impacto: {stats.get('high_impact_papers', 0)}"
                    )
                    print(f"   📅 Papers recentes: {stats.get('recent_papers', 0)}")

                    print("   📊 Papers por área:")
                    for area, count in stats.get("papers_by_area", {}).items():
                        print(f"       - {area}: {count}")

                    print("   🔗 Papers por fonte:")
                    for source, count in stats.get("papers_by_source", {}).items():
                        print(f"       - {source}: {count}")

                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Erro ao obter estatísticas: {response.status}")
                    print(f"   Detalhes: {error_text}")
                    return False

        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return False


async def test_search_memory():
    """
    Testa busca na memória para verificar se os papers foram armazenados
    """
    print("\n🔍 Testando busca na memória RAG++...")

    async with aiohttp.ClientSession() as session:
        try:
            # Buscar papers de machine learning
            search_payload = {"query": "transformers neural networks"}

            async with session.post(
                f"{RAG_SERVER_URL}/memory/search",
                json=search_payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Busca na memória realizada com sucesso!")
                    print(f"   🔍 Query: {result.get('query', 'N/A')}")
                    print(f"   📊 Resultados encontrados: {result.get('count', 0)}")

                    # Mostrar alguns resultados
                    results = result.get("results", [])
                    if results:
                        print("   📄 Primeiros resultados:")
                        for i, mem in enumerate(results[:2], 1):
                            content_preview = mem.get("content", "")[:100] + "..."
                            print(f"       {i}. {content_preview}")
                            print(f"          Tipo: {mem.get('memory_type', 'N/A')}")
                            print(
                                f"          Relevância: {mem.get('relevance_score', 0):.2f}"
                            )

                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Erro na busca: {response.status}")
                    print(f"   Detalhes: {error_text}")
                    return False

        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return False


async def main():
    """
    Executa todos os testes com dados mock
    """
    print("🧪 TESTE MOCK DO SISTEMA DE LITERATURA CIENTÍFICA RAG++")
    print("=" * 60)

    # Teste 1: Envio de dados mock
    success1 = await test_with_mock_data()

    if success1:
        print("\n⏳ Aguardando processamento...")
        await asyncio.sleep(2)

        # Teste 2: Estatísticas
        success2 = await test_literature_stats()

        # Teste 3: Busca na memória
        await asyncio.sleep(1)
        success3 = await test_search_memory()

        if success1 and success2 and success3:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            print(
                "   O sistema de literatura científica está funcionando corretamente."
            )
            print(f"   Acesse {RAG_SERVER_URL}/docs para ver a documentação da API.")
            print("   📝 Próximo passo: Configurar coleta automática diária")
        else:
            print("\n⚠️ Alguns testes falharam.")
    else:
        print("\n❌ Teste principal falhou. Verificar configuração do endpoint.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
