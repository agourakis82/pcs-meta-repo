#!/usr/bin/env python3
"""
Exemplo de Uso da Interface de Busca na Literatura
Demonstra como usar a interface mesmo quando o servidor RAG não está totalmente configurado
"""

import os
import sys

# Adicionar o diretório de scripts ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from literature_search_interface import LiteratureSearchInterface


def demo_literature_search():
    """Demonstração da interface de busca na literatura"""

    print("🔍 Demonstração da Interface de Busca na Literatura Científica")
    print("=" * 60)

    # Configuração
    base_url = "http://localhost:8000"
    api_token = "wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo"

    interface = LiteratureSearchInterface(base_url, api_token)

    # Health check
    print("⚡ Verificando status do servidor...")
    health = interface.health_check()
    print(f"📊 Status: {health}")
    print()

    # Exemplos de consultas que seriam úteis para nosso projeto
    example_queries = [
        "EEG semantic processing transformers language models",
        "eye tracking reading comprehension neural networks",
        "surprisal language models brain activity",
        "mixed effects models EEG time series",
        "ZuCo dataset reading comprehension",
        "GECO corpus eye tracking",
        "word association networks SWOW",
        "cluster-based permutation tests EEG",
        "brain encoding decoding language",
        "neural language processing GPU acceleration",
    ]

    print("📚 Exemplos de consultas para nosso projeto:")
    print("-" * 40)

    for i, query in enumerate(example_queries, 1):
        print(f"{i:2d}. {query}")

    print("\n🔬 Funcionalidades disponíveis na interface:")
    print("-" * 40)
    print("• 🔍 Busca híbrida (semântica + palavras-chave)")
    print("• 🧠 Busca na memória do projeto")
    print("• 📋 Categorias de pesquisa")
    print("• 📰 Pesquisas recentes")
    print("• 📊 Formatação rica dos resultados")
    print("• 🏷️  Extração de metadados (autores, DOI, etc.)")
    print("• ⭐ Scores de relevância")
    print("• 📖 Links para fontes")

    print("\n🚀 Como usar:")
    print("-" * 40)
    print("# Modo interativo:")
    print("python scripts/literature_search_interface.py")
    print()
    print("# Linha de comando:")
    print('python scripts/literature_search_interface.py "EEG transformers" -n 10')
    print()
    print("# Buscar na memória:")
    print('python scripts/literature_search_interface.py "mixed models" --memory')
    print()

    print("📋 Variáveis de ambiente:")
    print("-" * 40)
    print("RAG_API_TOKEN: Token de autenticação")
    print("RAG_BASE_URL: URL do servidor (padrão: http://localhost:8000)")
    print()

    # Simular alguns resultados de exemplo quando o servidor estiver funcional
    print("📑 Exemplo de resultado esperado:")
    print("-" * 40)
    mock_result = {
        "query": "EEG semantic processing transformers",
        "confidence": 0.87,
        "timestamp": "2025-09-12T10:30:00Z",
        "results": [
            {
                "title": "Transformer-based Neural Language Models for EEG-based Reading Comprehension",
                "authors": "Smith, J. et al.",
                "year": 2024,
                "journal": "Nature Neuroscience",
                "doi": "10.1038/nn.2024.1234",
                "abstract": "We present a novel approach using transformer models to decode semantic processing from EEG signals during reading tasks...",
                "keywords": ["EEG", "transformers", "reading", "semantic processing"],
                "relevance_score": 0.95,
            }
        ],
        "sources": {"published_papers": 1, "project_docs": 0},
    }

    formatted = interface.format_search_results(mock_result)
    print(formatted)


if __name__ == "__main__":
    demo_literature_search()
