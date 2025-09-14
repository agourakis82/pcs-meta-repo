#!/usr/bin/env python3
"""
Teste rápido dos endpoints Tree Search
"""

import json
import os
import subprocess
import sys
import time

import requests


def start_server():
    """Inicia o servidor em background"""
    env = os.environ.copy()
    env["RAG_WORKERS"] = "1"
    env["RAG_PORT"] = "8002"

    try:
        process = subprocess.Popen(
            [sys.executable, "ragpp/ragpp_web_server.py"],
            cwd="/home/agourakis82/workspace/pcs-meta-repo",
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Aguardar inicialização
        print("🚀 Iniciando servidor na porta 8002...")
        time.sleep(15)

        return process
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        return None


def test_tree_endpoints():
    """Testa os endpoints tree search"""
    base_url = "http://127.0.0.1:8002"

    print("🌳 Testando Tree Search Endpoints")
    print("=" * 50)

    # Teste 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Servidor online: {data['status']}")
        else:
            print(f"❌ Health check falhou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Não foi possível conectar ao servidor: {e}")
        return False

    # Teste 2: Tree structure
    try:
        response = requests.get(f"{base_url}/tree/structure", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Tree structure: {data['total_nodes']} nós")
            print(f"   Root: {data['structure']['name']}")
        else:
            print(f"❌ Tree structure falhou: {response.status_code}")
            print(f"   Response: {response.text[:100]}")
    except Exception as e:
        print(f"❌ Erro tree structure: {e}")

    # Teste 3: Add node
    try:
        node_data = {
            "name": "Test Node",
            "content": "This is a test node for tree search validation",
            "node_type": "document",
            "tags": ["test", "validation"],
            "score": 4.0,
        }

        response = requests.post(
            f"{base_url}/tree/add_node", json=node_data, timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Nó adicionado: {data['node_id'][:8]}...")
        else:
            print(f"❌ Add node falhou: {response.status_code}")
            print(f"   Response: {response.text[:100]}")
    except Exception as e:
        print(f"❌ Erro add node: {e}")

    # Teste 4: Search
    try:
        search_data = {
            "query": "test validation",
            "strategy": "best_first",
            "max_results": 5,
        }

        response = requests.post(
            f"{base_url}/tree/search", json=search_data, timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Busca realizada: {data['total_found']} resultado(s)")
            for result in data["results"]:
                print(f"   - {result['name']}: {result['relevance_score']:.3f}")
        else:
            print(f"❌ Search falhou: {response.status_code}")
            print(f"   Response: {response.text[:100]}")
    except Exception as e:
        print(f"❌ Erro search: {e}")

    return True


def main():
    """Função principal"""
    process = start_server()

    if process:
        try:
            success = test_tree_endpoints()
            if success:
                print("\n✅ Testes Tree Search concluídos!")
            else:
                print("\n❌ Testes falharam")
        finally:
            print("\n🛑 Parando servidor...")
            process.terminate()
            process.wait()
    else:
        print("❌ Não foi possível iniciar o servidor")


if __name__ == "__main__":
    main()
