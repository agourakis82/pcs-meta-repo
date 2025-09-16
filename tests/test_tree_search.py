#!/usr/bin/env python3
"""
Teste dos endpoints Tree Search do RAG++ Web Server
"""

import asyncio
import json
import time
from datetime import datetime

import requests

BASE_URL = "http://127.0.0.1:8000"


def test_tree_search_endpoints():
    """Testa todos os endpoints de tree search"""
    print("🌳 Testando Tree Search Endpoints")
    print("=" * 50)

    # Teste 1: Obter estrutura da árvore
    print("\n1. Testando GET /tree/structure")
    try:
        response = requests.get(f"{BASE_URL}/tree/structure")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Estrutura da árvore obtida:")
            print(f"   - Total de nós: {data['total_nodes']}")
            print(f"   - Profundidade máxima: {data['max_depth']}")
            print(f"   - Root ID: {data['root_id']}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")

    # Teste 2: Adicionar nó
    print("\n2. Testando POST /tree/add_node")
    try:
        node_data = {
            "name": "Test Paper: Advanced Neural Networks",
            "content": "This paper discusses advanced techniques in neural network architectures, focusing on transformer models and attention mechanisms.",
            "node_type": "document",
            "tags": ["neural_networks", "transformers", "attention", "deep_learning"],
            "metadata": {"authors": ["Test Author"], "year": 2024, "source": "test"},
            "score": 4.2,
        }

        response = requests.post(f"{BASE_URL}/tree/add_node", json=node_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Nó adicionado:")
            print(f"   - Node ID: {data['node_id']}")
            print(f"   - Status: {data['status']}")
            node_id = data["node_id"]
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
            node_id = None
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        node_id = None

    # Teste 3: Buscar na árvore
    print("\n3. Testando POST /tree/search")
    try:
        search_data = {
            "query": "neural networks transformers",
            "strategy": "best_first",
            "max_results": 5,
            "min_score": 0.0,
        }

        response = requests.post(f"{BASE_URL}/tree/search", json=search_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Busca realizada:")
            print(f"   - Query: {data['query']}")
            print(f"   - Estratégia: {data['strategy']}")
            print(f"   - Resultados encontrados: {data['total_found']}")

            for i, result in enumerate(data["results"][:3], 1):
                print(f"   {i}. {result['name'][:50]}...")
                print(f"      Score: {result['relevance_score']:.3f}")
                print(f"      Tipo: {result['node_type']}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")

    # Teste 4: Exportar árvore
    print("\n4. Testando GET /tree/export")
    try:
        response = requests.get(f"{BASE_URL}/tree/export")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Árvore exportada:")
            print(f"   - Total de nós: {data['metadata']['total_nodes']}")
            print(f"   - Tipos de nós: {data['metadata']['node_types']}")
            print(f"   - Exportado em: {data['metadata']['exported_at']}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")

    # Teste 5: Popular com memórias (se disponível)
    print("\n5. Testando POST /tree/populate_from_memories")
    try:
        response = requests.post(f"{BASE_URL}/tree/populate_from_memories")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Árvore populada com memórias:")
            print(f"   - Nós adicionados: {data['added_nodes']}")
            print(f"   - Mensagem: {data['message']}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")


def test_server_status():
    """Verifica se o servidor está rodando"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"🟢 Servidor RAG++ está online")
            print(f"   Status: {data['status']}")
            print(f"   Versão: {data['version']}")
            return True
        else:
            print(f"🔴 Servidor respondeu com erro: {response.status_code}")
            return False
    except Exception as e:
        print(f"🔴 Servidor não está acessível: {e}")
        return False


def main():
    """Função principal de teste"""
    print(f"🚀 Iniciando testes Tree Search - {datetime.now()}")
    print(f"🔗 URL base: {BASE_URL}")

    # Verificar se servidor está rodando
    if not test_server_status():
        print("\n❌ Servidor não está disponível. Inicie o servidor com:")
        print("python ragpp/ragpp_web_server.py")
        return

    # Aguardar um pouco para inicialização
    print("\n⏳ Aguardando inicialização do servidor...")
    time.sleep(2)

    # Executar testes
    test_tree_search_endpoints()

    print(f"\n✅ Testes concluídos - {datetime.now()}")


if __name__ == "__main__":
    main()
