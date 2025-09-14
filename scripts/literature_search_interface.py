#!/usr/bin/env python3
"""
Interface de Busca na Literatura Científica
Utiliza a API RAG++ para buscar na literatura de AI/EEG/Semântica publicada
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

import requests
import urllib3

# Suprimir warnings de SSL se necessário
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class LiteratureSearchInterface:
    def __init__(
        self, base_url: str = "http://localhost:8000", api_token: Optional[str] = None
    ):
        """
        Inicializa a interface de busca

        Args:
            base_url: URL base do servidor RAG++
            api_token: Token de autenticação (opcional)
        """
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token or os.getenv("RAG_API_TOKEN")
        self.session = requests.Session()

        if self.api_token:
            self.session.headers.update(
                {
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                }
            )
        else:
            self.session.headers.update({"Content-Type": "application/json"})

    def health_check(self) -> Dict[str, Any]:
        """Verifica o status do servidor"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def search_literature(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "hybrid",
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        """
        Busca na literatura científica

        Args:
            query: Consulta de busca
            max_results: Número máximo de resultados
            search_type: Tipo de busca ("hybrid", "semantic", "keyword")
            include_sources: Incluir informações das fontes
        """
        search_payload = {
            "query": query,
            "max_results": max_results,
            "search_type": search_type,
            "include_sources": include_sources,
        }

        try:
            response = self.session.post(f"{self.base_url}/search", json=search_payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "query": query}

    def search_memory(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        max_results: int = 10,
        importance_threshold: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Busca na memória do projeto

        Args:
            query: Consulta de busca
            memory_types: Tipos de memória para buscar
            max_results: Número máximo de resultados
            importance_threshold: Limiar de importância
        """
        search_payload = {
            "query": query,
            "max_results": max_results,
            "importance_threshold": importance_threshold,
        }

        if memory_types:
            search_payload["memory_types"] = memory_types

        try:
            response = self.session.post(
                f"{self.base_url}/memory/search", json=search_payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "query": query}

    def get_categories(self) -> Dict[str, Any]:
        """Obtém as categorias disponíveis"""
        try:
            response = self.session.get(f"{self.base_url}/research/categories")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_recent_research(self, limit: int = 10) -> Dict[str, Any]:
        """Obtém pesquisas recentes"""
        try:
            response = self.session.get(
                f"{self.base_url}/research/recent", params={"limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def format_search_results(self, results: Dict[str, Any]) -> str:
        """Formata os resultados de busca para exibição"""
        if "error" in results:
            return f"❌ Erro na busca: {results['error']}"

        output = []
        output.append(f"🔍 Consulta: {results.get('query', 'N/A')}")
        output.append(f"📊 Confiança: {results.get('confidence', 0):.2f}")
        output.append(f"🕒 Timestamp: {results.get('timestamp', 'N/A')}")
        output.append("")

        search_results = results.get("results", [])
        if not search_results:
            output.append("❌ Nenhum resultado encontrado.")
            return "\n".join(output)

        output.append(f"📚 {len(search_results)} resultado(s) encontrado(s):")
        output.append("=" * 60)

        for i, result in enumerate(search_results, 1):
            output.append(f"\n[{i}] {result.get('title', 'Sem título')}")

            if "authors" in result and result["authors"]:
                authors = (
                    result["authors"]
                    if isinstance(result["authors"], str)
                    else ", ".join(result["authors"])
                )
                output.append(f"👥 Autores: {authors}")

            if "year" in result:
                output.append(f"📅 Ano: {result['year']}")

            if "journal" in result:
                output.append(f"📖 Revista: {result['journal']}")

            if "doi" in result:
                output.append(f"🔗 DOI: {result['doi']}")

            if "url" in result:
                output.append(f"🌐 URL: {result['url']}")

            if "abstract" in result and result["abstract"]:
                abstract = (
                    result["abstract"][:300] + "..."
                    if len(result["abstract"]) > 300
                    else result["abstract"]
                )
                output.append(f"📄 Resumo: {abstract}")

            if "keywords" in result and result["keywords"]:
                keywords = (
                    result["keywords"]
                    if isinstance(result["keywords"], str)
                    else ", ".join(result["keywords"])
                )
                output.append(f"🏷️  Palavras-chave: {keywords}")

            if "relevance_score" in result:
                output.append(f"⭐ Relevância: {result['relevance_score']:.3f}")

            output.append("-" * 40)

        # Mostrar fontes se disponíveis
        sources = results.get("sources", {})
        if sources:
            output.append("\n📊 Fontes dos resultados:")
            for source, count in sources.items():
                output.append(f"  • {source}: {count} resultado(s)")

        return "\n".join(output)


def interactive_search():
    """Interface interativa de busca"""
    print("🔍 Interface de Busca na Literatura Científica")
    print("=" * 50)

    # Configuração
    base_url = os.getenv("RAG_BASE_URL", "http://localhost:8000")
    api_token = os.getenv("RAG_API_TOKEN")

    interface = LiteratureSearchInterface(base_url, api_token)

    # Verificar conexão
    print("⚡ Verificando conexão com o servidor...")
    health = interface.health_check()
    if health.get("status") == "error":
        print(f"❌ Erro de conexão: {health.get('message')}")
        return

    print(f"✅ Servidor ativo: {health.get('status')}")
    print(f"📚 Artigos indexados: {health.get('indexed_articles', 'N/A')}")
    print(f"🚀 Capacidades: {', '.join(health.get('capabilities', []))}")
    print()

    while True:
        print("\n" + "=" * 60)
        print("Opções disponíveis:")
        print("1. 🔍 Buscar na literatura")
        print("2. 🧠 Buscar na memória do projeto")
        print("3. 📋 Ver categorias disponíveis")
        print("4. 📰 Ver pesquisas recentes")
        print("5. ❌ Sair")

        choice = input("\nEscolha uma opção (1-5): ").strip()

        if choice == "1":
            query = input("\n🔍 Digite sua consulta de busca: ").strip()
            if not query:
                print("❌ Consulta vazia!")
                continue

            max_results = input("📊 Número máximo de resultados (padrão: 10): ").strip()
            max_results = int(max_results) if max_results.isdigit() else 10

            search_type_prompt = (
                "🎯 Tipo de busca (hybrid/literature/memory/live_literature, "
                "padrão: hybrid): "
            )
            search_type = input(search_type_prompt).strip() or "hybrid"

            print(f"\n🔍 Buscando por: '{query}'...")
            results = interface.search_literature(query, max_results, search_type)
            print(interface.format_search_results(results))

        elif choice == "2":
            query = input("\n🧠 Digite sua consulta na memória: ").strip()
            if not query:
                print("❌ Consulta vazia!")
                continue

            print(f"\n🧠 Buscando na memória: '{query}'...")
            results = interface.search_memory(query)

            if "error" in results:
                print(f"❌ Erro: {results['error']}")
            else:
                count = len(results.get("results", []))
                print(f"🔍 Encontrados {count} resultado(s) na memória")
                for i, result in enumerate(results.get("results", []), 1):
                    print(f"\n[{i}] {result.get('content', 'Sem conteúdo')[:200]}...")

        elif choice == "3":
            print("\n📋 Obtendo categorias...")
            categories = interface.get_categories()
            if "error" in categories:
                print(f"❌ Erro: {categories['error']}")
            else:
                print("📋 Categorias disponíveis:")
                print(json.dumps(categories, indent=2, ensure_ascii=False))

        elif choice == "4":
            limit = input("\n📰 Número de pesquisas recentes (padrão: 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10

            print(f"\n📰 Obtendo {limit} pesquisas recentes...")
            recent = interface.get_recent_research(limit)
            if "error" in recent:
                print(f"❌ Erro: {recent['error']}")
            else:
                print("📰 Pesquisas recentes:")
                print(json.dumps(recent, indent=2, ensure_ascii=False))

        elif choice == "5":
            print("\n👋 Saindo da interface de busca. Até logo!")
            break

        else:
            print("❌ Opção inválida! Escolha entre 1-5.")


def cli_search():
    """Interface de linha de comando"""
    parser = argparse.ArgumentParser(
        description="Interface de Busca na Literatura Científica"
    )
    parser.add_argument("query", help="Consulta de busca")
    parser.add_argument(
        "-n", "--max-results", type=int, default=10, help="Número máximo de resultados"
    )
    parser.add_argument(
        "-t",
        "--search-type",
        choices=["hybrid", "literature", "memory", "live_literature"],
        default="hybrid",
        help="Tipo de busca",
    )
    parser.add_argument(
        "--no-sources", action="store_true", help="Não incluir informações das fontes"
    )
    parser.add_argument(
        "--base-url", default="http://localhost:8000", help="URL base do servidor"
    )
    parser.add_argument("--token", help="Token de autenticação")
    parser.add_argument(
        "--memory", action="store_true", help="Buscar na memória em vez da literatura"
    )

    args = parser.parse_args()

    interface = LiteratureSearchInterface(args.base_url, args.token)

    if args.memory:
        results = interface.search_memory(args.query, max_results=args.max_results)
        if "error" in results:
            print(f"❌ Erro: {results['error']}")
        else:
            print(f"🧠 Memória - {len(results.get('results', []))} resultado(s):")
            for i, result in enumerate(results.get("results", []), 1):
                print(f"[{i}] {result.get('content', 'Sem conteúdo')[:200]}...")
    else:
        results = interface.search_literature(
            args.query, args.max_results, args.search_type, not args.no_sources
        )
        print(interface.format_search_results(results))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli_search()
    else:
        interactive_search()
