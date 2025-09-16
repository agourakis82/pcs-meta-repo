#!/usr/bin/env python3
"""
Teste do Sistema de Cache Multi-IA
Valida funcionalidades de salvar/recuperar contexto entre diferentes sistemas de IA.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict

import requests

# Configuração
BASE_URL = "http://127.0.0.1:8000"


class MultiAICacheTest:
    """Classe para testar o sistema de cache multi-IA."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.test_sessions = {}

    def test_health(self) -> bool:
        """Testa se o servidor está funcionando."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Servidor healthy: {health_data['indexed_articles']} artigos")
                return True
            else:
                print(f"❌ Servidor unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro de conexão: {str(e)}")
            return False

    def create_test_session(self, ai_type: str, session_name: str) -> Dict[str, Any]:
        """Cria uma sessão de teste."""
        try:
            payload = {
                "ai_type": ai_type,
                "session_name": session_name,
                "context_summary": f"Sessão de teste para {ai_type}",
                "initial_prompt": f"Prompt inicial de teste para {ai_type}",
                "user_id": "test_user",
                "metadata": {
                    "test": True,
                    "created_by": "multi_ai_cache_test",
                    "ai_version": "test",
                },
            }

            response = requests.post(
                f"{self.base_url}/ai/sessions", json=payload, timeout=10
            )

            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data["session_id"]
                self.test_sessions[ai_type] = session_id
                print(f"✅ Sessão {ai_type} criada: {session_id[:8]}...")
                return session_data
            else:
                print(f"❌ Erro criando sessão {ai_type}: {response.status_code}")
                print(f"    Response: {response.text}")
                return {}

        except Exception as e:
            print(f"❌ Erro na criação de sessão {ai_type}: {str(e)}")
            return {}

    def store_context(self, ai_type: str, messages: list, context_summary: str) -> bool:
        """Armazena contexto para uma sessão."""
        try:
            if ai_type not in self.test_sessions:
                print(f"❌ Sessão {ai_type} não encontrada")
                return False

            session_id = self.test_sessions[ai_type]

            payload = {
                "session_id": session_id,
                "ai_type": ai_type,
                "messages": messages,
                "context_summary": context_summary,
                "importance_score": 0.7,
                "tags": ["test", ai_type, "conversation"],
                "metadata": {
                    "test_case": "context_storage",
                    "message_count": len(messages),
                },
            }

            response = requests.post(
                f"{self.base_url}/ai/sessions/{session_id}/context",
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                result = response.json()
                print(
                    f"✅ Contexto {ai_type} armazenado: {result['messages_count']} mensagens"
                )
                return True
            else:
                print(f"❌ Erro armazenando contexto {ai_type}: {response.status_code}")
                print(f"    Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Erro no armazenamento {ai_type}: {str(e)}")
            return False

    def retrieve_context(self, ai_type: str) -> Dict[str, Any]:
        """Recupera contexto de uma sessão."""
        try:
            if ai_type not in self.test_sessions:
                print(f"❌ Sessão {ai_type} não encontrada")
                return {}

            session_id = self.test_sessions[ai_type]

            response = requests.get(
                f"{self.base_url}/ai/sessions/{session_id}/context",
                params={"include_messages": True, "max_messages": 20},
                timeout=10,
            )

            if response.status_code == 200:
                context_data = response.json()
                print(
                    f"✅ Contexto {ai_type} recuperado: {context_data.get('total_messages', 0)} mensagens"
                )
                return context_data
            else:
                print(f"❌ Erro recuperando contexto {ai_type}: {response.status_code}")
                return {}

        except Exception as e:
            print(f"❌ Erro na recuperação {ai_type}: {str(e)}")
            return {}

    def test_cross_ai_transfer(self, source_ai: str, target_ai: str) -> bool:
        """Testa transferência entre IAs."""
        try:
            if source_ai not in self.test_sessions:
                print(f"❌ Sessão origem {source_ai} não encontrada")
                return False

            source_session_id = self.test_sessions[source_ai]

            payload = {
                "source_session_id": source_session_id,
                "target_ai_type": target_ai,
                "transfer_type": "full",
                "include_messages": True,
                "include_context": True,
                "custom_prompt": f"Contexto transferido de {source_ai} para {target_ai} para teste",
            }

            response = requests.post(
                f"{self.base_url}/ai/transfer", json=payload, timeout=15
            )

            if response.status_code == 200:
                transfer_data = response.json()
                target_session_id = transfer_data["target_session_id"]
                self.test_sessions[f"{target_ai}_transfer"] = target_session_id
                print(
                    f"✅ Transferência {source_ai} → {target_ai}: {transfer_data['contexts_transferred']} contextos"
                )
                return True
            else:
                print(
                    f"❌ Erro na transferência {source_ai} → {target_ai}: {response.status_code}"
                )
                print(f"    Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Erro na transferência {source_ai} → {target_ai}: {str(e)}")
            return False

    def test_smart_search(self, query: str) -> Dict[str, Any]:
        """Testa busca inteligente no cache."""
        try:
            payload = {
                "query": query,
                "ai_types": ["chatgpt", "claude", "copilot"],
                "time_range": 30,
                "include_cross_ai": True,
                "similarity_threshold": 0.5,
                "max_results": 10,
            }

            response = requests.post(
                f"{self.base_url}/ai/cache/search", json=payload, timeout=10
            )

            if response.status_code == 200:
                search_data = response.json()
                print(f"✅ Busca '{query}': {len(search_data['results'])} resultados")
                return search_data
            else:
                print(f"❌ Erro na busca '{query}': {response.status_code}")
                return {}

        except Exception as e:
            print(f"❌ Erro na busca '{query}': {str(e)}")
            return {}

    def get_cache_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache."""
        try:
            response = requests.get(f"{self.base_url}/ai/cache/stats", timeout=10)

            if response.status_code == 200:
                stats_data = response.json()
                cache_stats = stats_data["cache_stats"]
                print(
                    f"✅ Estatísticas: {cache_stats['active_sessions']} sessões ativas"
                )
                return stats_data
            else:
                print(f"❌ Erro obtendo estatísticas: {response.status_code}")
                return {}

        except Exception as e:
            print(f"❌ Erro nas estatísticas: {str(e)}")
            return {}

    def run_full_test(self):
        """Executa teste completo do sistema."""
        print("🚀 INICIANDO TESTE DO SISTEMA DE CACHE MULTI-IA")
        print("=" * 60)

        # 1. Verificar saúde do servidor
        if not self.test_health():
            print("❌ Servidor não está funcionando. Abortando teste.")
            return False

        # 2. Criar sessões para diferentes IAs
        print("\n📝 Criando sessões de teste...")
        ais = ["chatgpt", "claude", "copilot"]
        for ai in ais:
            self.create_test_session(ai, f"Teste {ai.upper()}")

        time.sleep(1)

        # 3. Armazenar contextos
        print("\n💾 Armazenando contextos...")

        # Contexto ChatGPT
        chatgpt_messages = [
            {
                "role": "user",
                "content": "Olá, preciso de ajuda com análise de dados",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "role": "assistant",
                "content": "Claro! Posso ajudar com análise de dados. Que tipo de dados você tem?",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "role": "user",
                "content": "Tenho dados de EEG para análise de padrões neurais",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "role": "assistant",
                "content": "Excelente! Para análise de EEG, recomendo usar Python com bibliotecas como MNE-Python. Vamos começar?",
                "timestamp": datetime.now().isoformat(),
            },
        ]
        self.store_context(
            "chatgpt", chatgpt_messages, "Discussão sobre análise de dados EEG"
        )

        # Contexto Claude
        claude_messages = [
            {
                "role": "user",
                "content": "Preciso implementar machine learning em Python",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "role": "assistant",
                "content": "Ótimo! Que tipo de problema de ML você quer resolver?",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "role": "user",
                "content": "Classificação de sinais neurais",
                "timestamp": datetime.now().isoformat(),
            },
        ]
        self.store_context(
            "claude", claude_messages, "Implementação de ML para sinais neurais"
        )

        # Contexto Copilot
        copilot_messages = [
            {
                "role": "user",
                "content": "Como otimizar código Python para análise em tempo real?",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "role": "assistant",
                "content": "Para otimização em tempo real, use NumPy, numba para JIT compilation, e processamento vetorizado",
                "timestamp": datetime.now().isoformat(),
            },
        ]
        self.store_context("copilot", copilot_messages, "Otimização de código Python")

        time.sleep(2)

        # 4. Recuperar contextos
        print("\n📖 Recuperando contextos...")
        for ai in ais:
            self.retrieve_context(ai)

        # 5. Testar transferência cross-AI
        print("\n🔄 Testando transferência cross-AI...")
        self.test_cross_ai_transfer("chatgpt", "claude")
        self.test_cross_ai_transfer("claude", "copilot")

        time.sleep(1)

        # 6. Testar busca inteligente
        print("\n🔍 Testando busca inteligente...")
        self.test_smart_search("análise de dados EEG machine learning")
        self.test_smart_search("Python otimização tempo real")

        # 7. Obter estatísticas finais
        print("\n📊 Estatísticas finais...")
        stats = self.get_cache_stats()

        print("\n✅ TESTE COMPLETO FINALIZADO!")
        print("=" * 60)

        if stats:
            cache_stats = stats.get("cache_stats", {})
            print(f"📈 Resumo:")
            print(f"   - Sessões ativas: {cache_stats.get('active_sessions', 0)}")
            print(f"   - Memórias totais: {cache_stats.get('total_memories', 0)}")
            print(
                f"   - Transferências cross-AI: {cache_stats.get('cross_ai_transfers', 0)}"
            )
            print(
                f"   - Tipos de IA testados: {len(cache_stats.get('by_ai_type', {}))}"
            )

        return True


def main():
    """Função principal do teste."""
    print("🧠 SISTEMA DE CACHE INTELIGENTE MULTI-IA")
    print("   RAG++ Multi-AI Context Cache System")
    print("=" * 60)

    # Verificar se servidor está rodando
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Servidor não está rodando em {BASE_URL}")
            print("   Inicie o servidor com: python ragpp/ragpp_web_server.py")
            return
    except:
        print(f"❌ Não foi possível conectar ao servidor em {BASE_URL}")
        print("   Verifique se o servidor RAG++ está rodando")
        return

    # Executar teste
    tester = MultiAICacheTest(BASE_URL)
    tester.run_full_test()


if __name__ == "__main__":
    main()
