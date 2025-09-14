#!/usr/bin/env python3
"""
Script de automação diária para coleta de literatura científica
Mantém o RAG++ atualizado com os últimos avanços em:
- Machine Learning
- Statistics
- Mathematics
- Visualization
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import aiohttp

# Adicionar o diretório scripts ao path
sys.path.append(os.path.join(os.path.dirname(__file__), "scripts"))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("literature_automation.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Configurações
RAG_SERVER_URL = "http://127.0.0.1:8000"
COLLECTION_CONFIG = {
    "machine_learning": {"max_papers": 10, "days_back": 7, "min_significance": 3.0},
    "statistics": {"max_papers": 8, "days_back": 7, "min_significance": 2.8},
    "mathematics": {"max_papers": 6, "days_back": 7, "min_significance": 3.2},
    "visualization": {"max_papers": 5, "days_back": 7, "min_significance": 2.5},
}


async def check_server_health():
    """Verificar se o servidor RAG++ está funcionando"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{RAG_SERVER_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(
                        f"✅ Servidor RAG++ está saudável: {data.get('status')}"
                    )
                    return True
                else:
                    logger.error(f"❌ Servidor não está saudável: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com servidor: {e}")
        return False


async def collect_papers_for_area(collector, area, config):
    """Coletar papers para uma área específica"""
    logger.info(f"🔍 Coletando papers para área: {area}")

    try:
        # Coletar do arXiv
        papers = await collector.search_arxiv(
            area=area, days_back=config["days_back"], max_results=config["max_papers"]
        )

        # Filtrar por significância
        high_quality_papers = [
            paper
            for paper in papers
            if paper.significance_score >= config["min_significance"]
        ]

        logger.info(
            f"  📚 Coletados {len(papers)} papers, {len(high_quality_papers)} de alta qualidade"
        )
        return high_quality_papers

    except Exception as e:
        logger.error(f"❌ Erro ao coletar papers para {area}: {e}")
        return []


async def send_papers_to_rag(papers_by_area):
    """Enviar papers coletados para o RAG++"""
    if not papers_by_area or all(
        len(papers) == 0 for papers in papers_by_area.values()
    ):
        logger.warning("⚠️ Nenhum paper coletado para enviar")
        return False

    # Converter papers para formato do endpoint
    papers_data = {}
    for area, papers in papers_by_area.items():
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

    payload = {
        "papers": papers_data,
        "collection_metadata": {
            "collection_date": datetime.now().isoformat(),
            "collector_version": "1.0",
            "automated": True,
            "collection_type": "daily_update",
            "areas_collected": list(papers_by_area.keys()),
            "collection_config": COLLECTION_CONFIG,
        },
        "processing_options": {
            "high_impact_threshold": 3.5,
            "store_individual_papers": True,
        },
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{RAG_SERVER_URL}/admin/feed-literature",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ Literatura enviada com sucesso!")
                    logger.info(
                        f"   📝 Memórias armazenadas: {result.get('memories_stored', 0)}"
                    )
                    logger.info(
                        f"   📚 Papers processados: {result.get('papers_processed', 0)}"
                    )

                    stats = result.get("collection_stats", {})
                    logger.info(f"   📊 Estatísticas:")
                    logger.info(
                        f"       - Total papers: {stats.get('total_papers', 0)}"
                    )
                    logger.info(
                        f"       - Alto impacto: {stats.get('high_impact_papers', 0)}"
                    )
                    logger.info(
                        f"       - Significância média: {stats.get('avg_significance', 0):.2f}"
                    )

                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Erro ao enviar literatura: {response.status}")
                    logger.error(f"   Detalhes: {error_text}")
                    return False

    except Exception as e:
        logger.error(f"❌ Erro na requisição: {e}")
        return False


async def get_current_stats():
    """Obter estatísticas atuais do RAG++"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{RAG_SERVER_URL}/admin/literature-stats"
            ) as response:
                if response.status == 200:
                    stats = await response.json()
                    logger.info("📈 Estatísticas atuais do RAG++:")
                    logger.info(
                        f"   📚 Total de papers: {stats.get('total_papers', 0)}"
                    )
                    logger.info(
                        f"   🌟 Papers de alto impacto: {stats.get('high_impact_papers', 0)}"
                    )
                    logger.info(
                        f"   📅 Papers recentes: {stats.get('recent_papers', 0)}"
                    )
                    return stats
                else:
                    logger.error(f"❌ Erro ao obter estatísticas: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        return None


async def main():
    """Função principal de automação"""
    logger.info("🤖 INICIANDO COLETA AUTOMÁTICA DE LITERATURA CIENTÍFICA")
    logger.info("=" * 70)

    start_time = datetime.now()

    # 1. Verificar servidor
    if not await check_server_health():
        logger.error("❌ Servidor RAG++ não está disponível. Abortando coleta.")
        return False

    # 2. Obter estatísticas atuais
    await get_current_stats()

    # 3. Importar e inicializar coletor
    try:
        from advanced_literature_collector import AdvancedLiteratureCollector

        collector = AdvancedLiteratureCollector()
        logger.info("✅ Coletor de literatura inicializado")
    except ImportError as e:
        logger.error(f"❌ Erro ao importar coletor: {e}")
        return False

    # 4. Coletar papers por área
    collected_papers = {}
    total_papers = 0

    for area, config in COLLECTION_CONFIG.items():
        papers = await collect_papers_for_area(collector, area, config)
        collected_papers[area] = papers
        total_papers += len(papers)

    logger.info(f"📊 Total de papers coletados: {total_papers}")

    if total_papers == 0:
        logger.warning("⚠️ Nenhum paper novo coletado. Isso é normal em alguns dias.")
        return True

    # 5. Enviar para RAG++
    success = await send_papers_to_rag(collected_papers)

    # 6. Obter estatísticas finais
    if success:
        logger.info("\n📈 Estatísticas após atualização:")
        await get_current_stats()

    # 7. Resumo final
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info("\n" + "=" * 70)
    if success:
        logger.info("🎉 COLETA AUTOMÁTICA CONCLUÍDA COM SUCESSO!")
        logger.info(f"   ⏱️  Duração: {duration.total_seconds():.1f} segundos")
        logger.info(f"   📚 Papers processados: {total_papers}")
        logger.info(f"   🕒 Próxima execução: em 24 horas")
    else:
        logger.error("❌ Coleta automática falhou!")
        logger.error(f"   ⏱️  Duração: {duration.total_seconds():.1f} segundos")

    logger.info("=" * 70)
    return success


def create_cron_job():
    """Criar job no cron para execução diária"""
    script_path = os.path.abspath(__file__)
    python_path = sys.executable
    log_path = os.path.join(os.path.dirname(script_path), "literature_automation.log")

    cron_command = f"0 9 * * * cd {os.path.dirname(script_path)} && {python_path} {script_path} >> {log_path} 2>&1"

    print("📅 Para automatizar a execução diária, adicione esta linha ao crontab:")
    print(f"   {cron_command}")
    print("\nPara editar o crontab:")
    print("   crontab -e")
    print("\nEste comando executará a coleta todos os dias às 09:00")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Automação de coleta de literatura científica"
    )
    parser.add_argument(
        "--setup-cron",
        action="store_true",
        help="Mostra instruções para configurar execução automática diária",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Executar sem enviar dados para o RAG++"
    )

    args = parser.parse_args()

    if args.setup_cron:
        create_cron_job()
    else:
        # Verificar se o arquivo do coletor existe
        collector_path = os.path.join(
            os.path.dirname(__file__), "scripts", "advanced_literature_collector.py"
        )
        if not os.path.exists(collector_path):
            logger.error(f"❌ Arquivo não encontrado: {collector_path}")
            logger.error("   Execute este script no diretório principal do projeto.")
            sys.exit(1)

        # Executar coleta
        try:
            success = asyncio.run(main())
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            logger.info("\n⚠️ Coleta interrompida pelo usuário")
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Erro inesperado: {e}")
            sys.exit(1)
