#!/usr/bin/env python3
"""
Script de teste para o endpoint de literatura científica do RAG++
"""

import asyncio
import json
import os
import sys
from datetime import datetime

import aiohttp

# Adicionar o diretório scripts ao path
sys.path.append(os.path.join(os.path.dirname(__file__), "scripts"))

# Importar nosso coletor
try:
    from advanced_literature_collector import AdvancedLiteratureCollector, Paper
except ImportError as e:
    print(f"Erro ao importar o coletor: {e}")
    print(
        "Certifique-se de que o arquivo advanced_literature_collector.py está em scripts/"
    )
    sys.exit(1)

RAG_SERVER_URL = "http://127.0.0.1:8000"


async def test_collect_and_feed():
    """
    Teste completo: coleta papers e alimenta o RAG++
    """
    print("🔬 Iniciando teste de coleta e alimentação de literatura...")

    # 1. Inicializar coletor
    collector = AdvancedLiteratureCollector()

    # 2. Coletar papers (amostra pequena para teste)
    print("\n📚 Coletando papers de teste...")

    areas_to_collect = {
        "machine_learning": 1,  # Número de papers para coletar
        "statistics": 1,
        "mathematics": 1,
        "visualization": 1,
    }

    collected_papers = {}

    for area, num_papers in areas_to_collect.items():
        print(f"\n🔍 Coletando para área: {area}")
        papers = []

        # Coletar de arXiv
        arxiv_papers = await collector.search_arxiv(
            area=area,
            days_back=30,  # Últimos 30 dias
            max_results=num_papers,
        )
        papers.extend(arxiv_papers[:num_papers])

        # Filtrar por qualidade (já é feito internamente)
        quality_papers = papers if papers else []
        collected_papers[area] = quality_papers

        print(f"  ✅ Coletados {len(quality_papers)} papers de qualidade")

    # 3. Preparar dados para o endpoint
    total_papers = sum(len(papers) for papers in collected_papers.values())
    print(f"\n📊 Total de papers coletados: {total_papers}")

    if total_papers == 0:
        print("❌ Nenhum paper coletado. Verifique a conexão e APIs.")
        return False

    # Converter para formato do endpoint
    papers_data = {}
    for area, papers in collected_papers.items():
        papers_data[area] = [
            {
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "url": paper.url,
                "source": paper.source,
                "categories": paper.categories,
                "published_date": paper.published_date,
                "keywords": paper.keywords,
                "citation_count": paper.citation_count,
                "doi": paper.doi,
                "venue": paper.venue,
                "significance_score": paper.significance_score,
                "technical_concepts": paper.technical_concepts,
                "methodology": paper.methodology,
                "results_summary": paper.results_summary,
                "code_availability": paper.code_availability,
            }
            for paper in papers
        ]

    # 4. Testar endpoint do RAG++
    print(f"\n🚀 Enviando dados para RAG++ em {RAG_SERVER_URL}...")

    async with aiohttp.ClientSession() as session:
        # Verificar se o servidor está rodando
        try:
            async with session.get(f"{RAG_SERVER_URL}/health") as response:
                if response.status != 200:
                    print(f"❌ Servidor RAG++ não está saudável: {response.status}")
                    return False
                print("✅ Servidor RAG++ está rodando")
        except Exception as e:
            print(f"❌ Erro ao conectar com RAG++: {e}")
            return False

        # Enviar dados
        payload = {
            "papers": papers_data,
            "collection_metadata": {
                "collection_date": datetime.now().isoformat(),
                "collector_version": "1.0",
                "test_mode": True,
                "areas_collected": list(areas_to_collect.keys()),
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
                    print(f"   📊 Estatísticas:")
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


async def main():
    """
    Executa todos os testes
    """
    print("🧪 TESTE DO SISTEMA DE LITERATURA CIENTÍFICA RAG++")
    print("=" * 60)

    # Teste 1: Coleta e alimentação
    success1 = await test_collect_and_feed()

    # Aguardar um pouco para processamento
    if success1:
        print("\n⏳ Aguardando processamento...")
        await asyncio.sleep(2)

        # Teste 2: Estatísticas
        success2 = await test_literature_stats()

        if success1 and success2:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            print(
                "   O sistema de literatura científica está funcionando corretamente."
            )
            print(f"   Acesse {RAG_SERVER_URL}/docs para ver a documentação da API.")
        else:
            print("\n⚠️ Alguns testes falharam.")
    else:
        print("\n❌ Teste de coleta falhou. Sistema não está funcionando.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Verificar se o arquivo do coletor existe
    collector_path = os.path.join(
        os.path.dirname(__file__), "scripts", "advanced_literature_collector.py"
    )
    if not os.path.exists(collector_path):
        print(f"❌ Arquivo não encontrado: {collector_path}")
        print("   Execute este script no diretório principal do projeto.")
        sys.exit(1)

    # Executar testes
    asyncio.run(main())
