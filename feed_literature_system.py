#!/usr/bin/env python3
"""
Converter papers coletados e alimentar o sistema RAG++
"""

import json
from pathlib import Path

import requests


def convert_and_feed_papers():
    """Converter papers e alimentar sistema RAG++"""

    # Encontrar arquivo mais recente
    paper_files = list(Path("/tmp").glob("advanced_papers_*.json"))
    if not paper_files:
        print("❌ Nenhum arquivo de papers encontrado")
        return

    latest_file = max(paper_files, key=lambda f: f.stat().st_mtime)
    print(f"📁 Usando arquivo: {latest_file}")

    # Carregar papers
    with open(latest_file, "r") as f:
        data = json.load(f)

    print(f"📊 Total de áreas: {len(data)}")

    # Converter para formato esperado pelo endpoint
    papers_by_area = {}
    for area, papers in data.items():
        converted_papers = []
        for paper in papers:
            converted_paper = {
                "title": paper.get("title", ""),
                "authors": paper.get("authors", []),
                "abstract": paper.get("abstract", ""),
                "url": paper.get("url", ""),
                "source": paper.get("source", ""),
                "published_date": paper.get("published_date") or "",
                "keywords": paper.get("keywords", []),
                "citation_count": paper.get("citation_count", 0),
                "doi": paper.get("doi") or "",
                "venue": paper.get("venue", ""),
                "significance_score": paper.get("significance_score", 0.0),
                "technical_concepts": paper.get("technical_concepts", []),
                "methodology": paper.get("methodology", ""),
                "results_summary": paper.get("results_summary", ""),
                "code_availability": paper.get("code_availability", False),
                "categories": [area],  # Adicionar área como categoria
            }
            converted_papers.append(converted_paper)

        papers_by_area[area] = converted_papers
        print(f"  {area}: {len(converted_papers)} papers")

    # Preparar payload
    payload = {
        "papers": papers_by_area,
        "collection_metadata": {
            "collection_date": "2025-09-14",
            "collection_method": "advanced_literature_collector",
            "areas": list(papers_by_area.keys()),
        },
        "processing_options": {
            "create_tree_nodes": True,
            "auto_categorize": True,
            "high_impact_only": False,
        },
    }

    # Enviar para RAG++
    url = "http://127.0.0.1:8003/admin/feed-literature"

    total_papers = sum(len(papers) for papers in papers_by_area.values())
    print(f"\n🚀 Enviando {total_papers} papers para RAG++...")

    try:
        response = requests.post(url, json=payload, timeout=120)

        if response.status_code == 200:
            result = response.json()
            print("✅ Literatura alimentada com sucesso!")
            print(f"   Papers processados: {result.get('papers_stored', 0)}")
            print(f"   Memórias criadas: {result.get('memories_created', 0)}")
            print(f"   Status: {result.get('status', 'unknown')}")

            if "summary" in result:
                summary = result["summary"]
                print("\n📈 Resumo por área:")
                for area, count in summary.get("papers_by_area", {}).items():
                    print(f"   {area}: {count} papers")

        else:
            print(f"❌ Erro HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Erro na requisição: {e}")


if __name__ == "__main__":
    convert_and_feed_papers()
