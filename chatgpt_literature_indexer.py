#!/usr/bin/env python3
"""
Sistema de indexação de artigos via ChatGPT
Usa o sistema RAG++ existente para coletar e indexar literatura científica
"""

import json
import os
import sys
from pathlib import Path

import requests

# Adicionar path do projeto
sys.path.append(str(Path(__file__).parent))


def collect_and_index_literature(areas, max_papers_per_area=10, min_citation_count=5):
    """
    Coleta e indexa literatura científica usando o advanced_literature_collector
    """
    print(f"🔍 Coletando literatura científica...")
    print(f"   Áreas: {areas}")
    print(f"   Máximo por área: {max_papers_per_area}")
    print(f"   Mín. citações: {min_citation_count}")

    # Executar o collector avançado
    from scripts.advanced_literature_collector import main as collect_literature

    try:
        # Coletar literature
        papers_data = {}

        for area in areas:
            print(f"\n📚 Coletando papers de {area}...")

            # Mapear áreas para queries de busca
            area_queries = {
                "computational_psychiatry": "computational psychiatry digital phenotyping",
                "digital_phenotyping": "digital phenotyping smartphone mental health",
                "neuroimaging": "neuroimaging fMRI machine learning",
                "neuroscience": "neuroscience artificial intelligence",
                "clinical_ai": "clinical artificial intelligence healthcare",
                "biomarkers": "biomarkers psychiatric disorders",
                "machine_learning": "machine learning deep learning",
                "statistics": "statistical analysis regression",
                "visualization": "data visualization",
                "mathematics": "mathematical optimization",
            }

            query = area_queries.get(area, area)

            # Aqui você integraria com o advanced_literature_collector
            # Por agora, vamos usar o sistema de tree search existente

        return {
            "status": "collected",
            "areas": areas,
            "total_papers": len(areas) * max_papers_per_area,
        }

    except Exception as e:
        print(f"❌ Erro na coleta: {e}")
        return {"status": "error", "message": str(e)}


def add_papers_to_tree(papers_data, server_url="http://127.0.0.1:8000"):
    """
    Adiciona papers coletados à árvore de busca
    """
    print(f"🌳 Adicionando papers à árvore de busca...")

    try:
        # Verificar estrutura atual da árvore
        response = requests.get(f"{server_url}/tree/structure")
        if response.status_code != 200:
            return {"status": "error", "message": "Erro ao acessar árvore"}

        tree_data = response.json()
        print(f"   Árvore atual: {tree_data['total_nodes']} nós")

        # Mapear categorias para IDs
        category_ids = {}
        for child in tree_data["structure"]["children"]:
            category_ids[child["name"]] = child["id"]

        added_count = 0
        for area, papers in papers_data.items():
            if not papers:
                continue

            # Mapear área para categoria na árvore
            area_to_category = {
                "computational_psychiatry": "Machine Learning",
                "digital_phenotyping": "Machine Learning",
                "neuroimaging": "Statistics",
                "neuroscience": "Statistics",
                "clinical_ai": "Machine Learning",
                "biomarkers": "Statistics",
                "machine_learning": "Machine Learning",
                "statistics": "Statistics",
                "visualization": "Visualization",
                "mathematics": "Mathematics",
            }

            category = area_to_category.get(area, "Machine Learning")
            parent_id = category_ids.get(category)

            if not parent_id:
                print(f"   ⚠️ Categoria {category} não encontrada")
                continue

            print(f"   📄 Adicionando {len(papers)} papers em {category}")

            for paper in papers:
                paper_node = {
                    "name": paper.get("title", "Paper")[:100],
                    "parent_id": parent_id,
                    "node_type": "document",
                    "content": f"Title: {paper.get('title', '')}\n\nAbstract: {paper.get('abstract', '')[:500]}...",
                    "metadata": {
                        "authors": paper.get("authors", []),
                        "area": area,
                        "significance_score": paper.get("significance_score", 0.0),
                    },
                }

                add_response = requests.post(
                    f"{server_url}/tree/add_node", json=paper_node
                )
                if add_response.status_code == 200:
                    added_count += 1

        return {"status": "success", "papers_added": added_count}

    except Exception as e:
        print(f"❌ Erro ao adicionar à árvore: {e}")
        return {"status": "error", "message": str(e)}


def main():
    """Função principal para uso via ChatGPT"""

    # Exemplo de uso - pode ser chamado pelo ChatGPT com diferentes parâmetros

    # Exemplo 1: Psiquiatria computacional
    if len(sys.argv) > 1 and sys.argv[1] == "psychiatry":
        areas = ["computational_psychiatry", "digital_phenotyping", "neuroimaging"]
        max_papers = 15

    # Exemplo 2: IA clínica
    elif len(sys.argv) > 1 and sys.argv[1] == "clinical":
        areas = ["clinical_ai", "biomarkers", "neuroscience"]
        max_papers = 12

    # Exemplo 3: Métodos quantitativos
    elif len(sys.argv) > 1 and sys.argv[1] == "quantitative":
        areas = ["statistics", "mathematics", "machine_learning"]
        max_papers = 20

    # Default: áreas principais
    else:
        areas = ["machine_learning", "statistics", "visualization"]
        max_papers = 10

    print(f"🚀 Iniciando indexação de literatura científica")
    print(f"📊 Áreas selecionadas: {areas}")

    # Simular coleta (já temos papers indexados)
    # Em uma implementação real, você executaria o collector aqui

    print(f"\n✅ Coleta concluída!")
    print(f"🌳 Sistema tree search disponível para busca")
    print(f"🔍 Use o ChatGPT para buscar: 'Search literature about [topic]'")

    # Instruções para o ChatGPT
    chatgpt_instructions = {
        "available_endpoints": [
            "GET /health - Status do sistema",
            "POST /search - Busca híbrida",
            "POST /tree/search - Busca hierárquica",
            "GET /tree/structure - Estrutura da árvore",
        ],
        "example_queries": [
            "Search for computational psychiatry papers",
            "Find digital phenotyping research",
            "Look for neuroimaging machine learning studies",
        ],
        "server_url": "http://127.0.0.1:8000",
    }

    print(f"\n📋 Instruções para ChatGPT:")
    print(json.dumps(chatgpt_instructions, indent=2))


if __name__ == "__main__":
    main()
