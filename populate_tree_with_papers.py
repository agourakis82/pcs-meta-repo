#!/usr/bin/env python3
"""
Adicionar papers coletados como nós na árvore de busca
"""

import json
from pathlib import Path

import requests


def add_papers_to_tree():
    """Adicionar papers como nós na árvore de busca"""

    # Carregar papers
    paper_files = list(Path("/tmp").glob("advanced_papers_*.json"))
    latest_file = max(paper_files, key=lambda f: f.stat().st_mtime)

    with open(latest_file, "r") as f:
        data = json.load(f)

    # Mapear categorias para IDs dos nós na árvore
    category_mapping = {
        "machine_learning": "Machine Learning",
        "statistics": "Statistics",
        "mathematics": "Mathematics",
        "visualization": "Visualization",
    }

    # Obter estrutura da árvore
    tree_response = requests.get("http://127.0.0.1:8003/tree/structure")
    tree_data = tree_response.json()

    # Mapear nomes das categorias para IDs
    category_ids = {}
    for child in tree_data["structure"]["children"]:
        category_ids[child["name"]] = child["id"]

    print(f"🌳 IDs das categorias encontradas:")
    for name, node_id in category_ids.items():
        print(f"   {name}: {node_id}")

    added_papers = 0

    # Adicionar papers como nós filhos das categorias
    for area, papers in data.items():
        if area not in category_mapping:
            continue

        category_name = category_mapping[area]
        parent_id = category_ids.get(category_name)

        if not parent_id:
            print(f"❌ Categoria {category_name} não encontrada na árvore")
            continue

        print(f"\n📚 Adicionando {len(papers)} papers em {category_name}...")

        for i, paper in enumerate(papers):
            paper_node = {
                "name": paper.get("title", f"Paper {i+1}")[:100],  # Limitar tamanho
                "parent_id": parent_id,
                "node_type": "document",
                "content": f"Title: {paper.get('title', '')}\n\nAbstract: {paper.get('abstract', '')[:500]}...",
                "metadata": {
                    "authors": paper.get("authors", []),
                    "url": paper.get("url", ""),
                    "source": paper.get("source", ""),
                    "significance_score": paper.get("significance_score", 0.0),
                    "technical_concepts": paper.get("technical_concepts", []),
                },
            }

            try:
                response = requests.post(
                    "http://127.0.0.1:8003/tree/add_node", json=paper_node, timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    added_papers += 1
                    if (i + 1) % 5 == 0 or i == len(papers) - 1:
                        print(f"   ✅ {i+1}/{len(papers)} papers adicionados")
                else:
                    print(
                        f"   ❌ Erro ao adicionar paper {i+1}: {response.status_code}"
                    )

            except Exception as e:
                print(f"   ❌ Erro na requisição para paper {i+1}: {e}")

    print(f"\n🎉 Total de papers adicionados: {added_papers}")

    # Verificar estrutura final
    final_response = requests.get("http://127.0.0.1:8003/tree/structure")
    final_data = final_response.json()
    print(
        f"🌳 Estrutura final da árvore: {final_data['total_nodes']} nós, profundidade {final_data['max_depth']}"
    )


if __name__ == "__main__":
    add_papers_to_tree()
