#!/usr/bin/env python3
"""
Script para inicializar e testar a Interface de Busca na Literatura
"""

import os
import subprocess
import sys
import time

import requests


def check_server_status():
    """Verifica se o servidor RAG++ está rodando"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def start_ragpp_server():
    """Tenta iniciar o servidor RAG++"""
    print("🚀 Tentando iniciar o servidor RAG++...")

    # Verificar se o serviço systemd existe
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "status", "ragpp-mcp-server"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if "could not be found" not in result.stderr:
            print("📋 Serviço encontrado, tentando reiniciar...")
            subprocess.run(
                ["sudo", "systemctl", "restart", "ragpp-mcp-server"], timeout=30
            )
            time.sleep(5)

            if check_server_status():
                print("✅ Servidor iniciado com sucesso!")
                return True

    except Exception as e:
        print(f"⚠️  Erro ao gerenciar serviço systemd: {e}")

    # Tentar iniciar manualmente
    print("🔧 Tentando iniciar manualmente...")
    try:
        # Verificar se existe o script do servidor
        server_script = (
            "/home/agourakis82/workspace/pcs-meta-repo/ragpp/ragpp_web_server.py"
        )
        if os.path.exists(server_script):
            print(f"📁 Script encontrado: {server_script}")

            # Configurar ambiente
            env = os.environ.copy()
            env.update(
                {
                    "RAG_HOST": "127.0.0.1",
                    "RAG_PORT": "8000",
                    "RAG_DB_PATH": "/home/agourakis82/workspace/pcs-meta-repo/ragpp/data",
                    "RAG_API_TOKEN": "wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo",
                }
            )

            print("🐍 Iniciando servidor Python...")
            process = subprocess.Popen(
                [sys.executable, server_script],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Aguardar alguns segundos
            time.sleep(10)

            if check_server_status():
                print("✅ Servidor iniciado manualmente!")
                return True
            else:
                print("❌ Servidor não respondeu após inicialização")
                process.terminate()

    except Exception as e:
        print(f"❌ Erro ao iniciar servidor manualmente: {e}")

    return False


def demonstrate_interface():
    """Demonstra o uso da interface"""
    print("\n" + "=" * 60)
    print("📚 DEMONSTRAÇÃO DA INTERFACE DE BUSCA NA LITERATURA")
    print("=" * 60)

    print("\n🔍 Interface criada com as seguintes funcionalidades:")
    print("• Busca na literatura científica usando API RAG++")
    print("• Busca na memória do projeto")
    print("• Modo interativo e linha de comando")
    print("• Formatação rica dos resultados")
    print("• Suporte a múltiplos tipos de busca")

    print("\n📁 Arquivos criados:")
    print("• scripts/literature_search_interface.py - Interface principal")
    print("• scripts/demo_literature_search.py - Demonstração")
    print("• docs/INTERFACE_BUSCA_LITERATURA.md - Documentação")

    print("\n🚀 Exemplos de uso:")
    print("# Modo interativo:")
    print("python scripts/literature_search_interface.py")
    print()
    print("# Busca específica:")
    print('python scripts/literature_search_interface.py "EEG transformers" -n 10')
    print()
    print("# Busca na memória:")
    print('python scripts/literature_search_interface.py "mixed models" --memory')

    print("\n📊 Quando o servidor estiver ativo, você poderá buscar por:")
    example_queries = [
        "EEG semantic processing transformers",
        "eye tracking reading comprehension",
        "surprisal language models brain activity",
        "mixed effects models EEG",
        "ZuCo dataset GECO corpus",
        "cluster-based permutation tests",
        "neural language processing GPU",
    ]

    for i, query in enumerate(example_queries, 1):
        print(f"  {i}. {query}")

    print("\n🔧 Para configurar o servidor RAG++:")
    print("1. Configurar variáveis de ambiente:")
    print("   export RAG_API_TOKEN='wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo'")
    print("   export RAG_HOST='127.0.0.1'")
    print("   export RAG_PORT='8000'")
    print()
    print("2. Inicializar base de dados:")
    print("   python ragpp/ragpp_web_server.py")
    print()
    print("3. Publicar documentação:")
    print("   python scripts/publish_ragpp_playbook.py")


def main():
    """Função principal"""
    print("🔍 Inicializador da Interface de Busca na Literatura")
    print("=" * 55)

    # Verificar se servidor já está rodando
    if check_server_status():
        print("✅ Servidor RAG++ já está ativo!")

        # Testar a interface
        print("\n🧪 Testando interface...")
        try:
            from literature_search_interface import LiteratureSearchInterface

            interface = LiteratureSearchInterface()
            health = interface.health_check()
            print(f"📊 Status do servidor: {health}")

            # Tentar uma busca simples
            if health.get("status") != "error":
                print("\n🔍 Testando busca na memória...")
                result = interface.search_memory("pipeline", max_results=2)
                print(f"📋 Resultados encontrados: {len(result.get('results', []))}")

        except Exception as e:
            print(f"⚠️  Erro ao testar interface: {e}")

    else:
        print("⚠️  Servidor RAG++ não está ativo")

        response = input("\n🤔 Tentar iniciar o servidor? (y/n): ").strip().lower()
        if response == "y":
            if start_ragpp_server():
                print("🎉 Servidor iniciado! Agora você pode usar a interface.")
            else:
                print("❌ Não foi possível iniciar o servidor automaticamente.")
                print("💡 Veja a documentação para inicialização manual.")

    # Sempre mostrar a demonstração
    demonstrate_interface()

    print("\n📖 Para mais informações, veja:")
    print("   docs/INTERFACE_BUSCA_LITERATURA.md")


if __name__ == "__main__":
    main()
