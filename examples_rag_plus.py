"""
RAG++ Enhanced Research Agent - Usage Examples
==============================================

Este arquivo demonstra como usar o sistema RAG++ programaticamente
com diferentes cenários e casos de uso.

Execute: python examples_rag_plus.py
"""

import asyncio
import os
from typing import Dict, List

# Configurar variáveis de ambiente se necessário
os.environ.setdefault("GCP_PROJECT_ID", "your-gcp-project")

# Importar módulos do sistema
from rag_plus_agent import RAGConfig, RAGPlusPlusAgent
from scientific_discovery_radar import ScientificDiscoveryRadar, SourceConfig


class RAGPlusExamples:
    """Exemplos de uso do sistema RAG++"""

    def __init__(self):
        # Configuração básica
        self.config = RAGConfig(
            project_id=os.getenv("GCP_PROJECT_ID", "demo-project"),
            location="us-central1",
            dataset_id="knowledge_base_demo",
            table_id="documents_demo",
            novelty_threshold=0.7,  # Threshold mais baixo para demo
            max_iterations=5,  # Menos iterações para demo
            top_k_retrieval=3,  # Menos resultados para demo
        )

        self.agent = None
        self.radar = None

    def setup_demo_agent(self) -> bool:
        """Configurar agente para demonstração"""
        try:
            print("🔧 Configurando agente RAG++...")
            self.agent = RAGPlusPlusAgent(self.config)

            # Configurar fontes para demo (apenas arXiv)
            demo_sources = [
                SourceConfig(
                    name="arXiv_CS_AI_Demo",
                    type="rss",
                    url="http://export.arxiv.org/rss/cs.AI",
                    enabled=True,
                    check_interval=7200,
                )
            ]

            self.radar = ScientificDiscoveryRadar(self.agent, demo_sources)
            print("✅ Agente configurado com sucesso!")
            return True

        except Exception as e:
            print(f"❌ Erro na configuração: {e}")
            return False

    def example_1_basic_questions(self):
        """Exemplo 1: Perguntas básicas com RAG simples"""
        print("\n" + "=" * 60)
        print("📚 Exemplo 1: Perguntas Básicas")
        print("=" * 60)

        questions = [
            "O que é machine learning?",
            "Como funcionam as redes neurais?",
            "Qual a diferença entre AI e ML?",
        ]

        for i, question in enumerate(questions, 1):
            print(f"\n🔍 Pergunta {i}: {question}")
            print("-" * 40)

            try:
                answer = self.agent.answer_question(question)
                print(f"📝 Resposta: {answer}")
            except Exception as e:
                print(f"❌ Erro: {e}")

    def example_2_iterative_reasoning(self):
        """Exemplo 2: Raciocínio iterativo para perguntas complexas"""
        print("\n" + "=" * 60)
        print("🧠 Exemplo 2: Raciocínio Iterativo")
        print("=" * 60)

        complex_questions = [
            "Compare as arquiteturas de transformers e RNNs, considerando eficiência e performance",
            "Analise as implicações éticas do uso de IA generativa na educação",
        ]

        for i, question in enumerate(complex_questions, 1):
            print(f"\n🔍 Pergunta Complexa {i}: {question}")
            print("-" * 50)

            try:
                # Mostrar tanto resposta simples quanto iterativa
                print("📄 Resposta Simples:")
                simple_answer = self.agent.answer_question(question)
                print(f"   {simple_answer}\n")

                print("🧠 Resposta com Raciocínio Iterativo:")
                iterative_answer = self.agent.answer_question_iterative(question)
                print(f"   {iterative_answer}")

            except Exception as e:
                print(f"❌ Erro: {e}")

    def example_3_knowledge_base_population(self):
        """Exemplo 3: Populando a base de conhecimento"""
        print("\n" + "=" * 60)
        print("📊 Exemplo 3: Populando Base de Conhecimento")
        print("=" * 60)

        # Dados de exemplo para popular a base
        demo_documents = [
            {
                "id": "transformers_attention",
                "content": "Transformers revolucionaram o processamento de linguagem natural através do mecanismo de atenção, permitindo paralelização e captura de dependências de longo alcance de forma mais eficiente que RNNs.",
                "source": "https://arxiv.org/abs/1706.03762",
                "metadata": {"topic": "deep_learning", "year": "2017"},
            },
            {
                "id": "few_shot_learning",
                "content": "Few-shot learning permite que modelos aprendam novas tarefas com apenas alguns exemplos, usando técnicas como meta-learning, transfer learning e in-context learning.",
                "source": "https://arxiv.org/abs/1904.05046",
                "metadata": {"topic": "machine_learning", "year": "2019"},
            },
            {
                "id": "ethical_ai",
                "content": "A ética em IA envolve questões de bias, fairness, transparência, accountability e impacto social, sendo crucial para o desenvolvimento responsável de sistemas inteligentes.",
                "source": "https://example.com/ai-ethics",
                "metadata": {"topic": "ai_ethics", "year": "2023"},
            },
        ]

        print("📥 Adicionando documentos de exemplo...")
        added_count = 0

        for doc in demo_documents:
            try:
                success = self.agent.add_document(
                    doc_id=doc["id"],
                    content=doc["content"],
                    source=doc["source"],
                    metadata=doc["metadata"],
                )

                if success:
                    added_count += 1
                    print(f"✅ Adicionado: {doc['id']}")
                else:
                    print(f"❌ Falha ao adicionar: {doc['id']}")

            except Exception as e:
                print(f"❌ Erro ao adicionar {doc['id']}: {e}")

        print(
            f"\n📊 Resumo: {added_count}/{len(demo_documents)} documentos adicionados"
        )

    def example_4_scientific_discovery(self):
        """Exemplo 4: Descoberta científica automática"""
        print("\n" + "=" * 60)
        print("🔬 Exemplo 4: Descoberta Científica")
        print("=" * 60)

        print("📡 Iniciando descoberta de novos artigos...")

        try:
            # Executar uma rodada de descoberta
            stats = self.radar.update_knowledge_base_from_feeds()

            print("📊 Estatísticas da descoberta:")
            print(f"   • Artigos encontrados: {stats['fetched']}")
            print(f"   • Artigos considerados novos: {stats['novel']}")
            print(f"   • Artigos adicionados: {stats['added']}")
            print(f"   • Erros encontrados: {stats['errors']}")

            if stats["added"] > 0:
                print("\n✨ Novos conhecimentos adicionados à base!")
                print("Agora você pode fazer perguntas sobre descobertas recentes.")
            else:
                print("\n💡 Nenhum artigo novo detectado nesta execução.")
                print("Isso é normal - o sistema filtra conteúdo duplicado.")

        except Exception as e:
            print(f"❌ Erro na descoberta: {e}")

    def example_5_advanced_queries(self):
        """Exemplo 5: Consultas avançadas e edge cases"""
        print("\n" + "=" * 60)
        print("🎯 Exemplo 5: Consultas Avançadas")
        print("=" * 60)

        advanced_scenarios = [
            {
                "name": "Consulta Multi-hop",
                "question": "Como os avanços em transformers influenciaram o desenvolvimento de modelos de few-shot learning?",
                "use_iterative": True,
            },
            {
                "name": "Consulta Específica",
                "question": "Quais são as principais preocupações éticas com IA generativa?",
                "use_iterative": False,
            },
            {
                "name": "Consulta com Contexto Limitado",
                "question": "Explique quantum computing para iniciantes",
                "use_iterative": False,
            },
        ]

        for scenario in advanced_scenarios:
            print(f"\n🎯 {scenario['name']}")
            print(f"❓ {scenario['question']}")
            print("-" * 40)

            try:
                if scenario["use_iterative"]:
                    answer = self.agent.answer_question_iterative(scenario["question"])
                else:
                    answer = self.agent.answer_question(scenario["question"])

                print(f"📝 {answer}")

            except Exception as e:
                print(f"❌ Erro: {e}")

    async def example_6_continuous_monitoring(self):
        """Exemplo 6: Monitoramento contínuo (demonstração curta)"""
        print("\n" + "=" * 60)
        print("📡 Exemplo 6: Monitoramento Contínuo (Demo)")
        print("=" * 60)

        print("🔄 Iniciando monitoramento por 30 segundos...")
        print("(Em produção, isso rodaria 24/7)")

        try:
            # Monitorar por apenas 30 segundos para demo
            task = asyncio.create_task(
                self.radar.run_continuous_monitoring(check_interval=15)
            )

            # Cancelar após 30 segundos
            await asyncio.sleep(30)
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            print("✅ Demo de monitoramento concluída!")

        except Exception as e:
            print(f"❌ Erro no monitoramento: {e}")

    def run_all_examples(self):
        """Executar todos os exemplos"""
        print("🚀 RAG++ Enhanced Research Agent - Exemplos de Uso")
        print("=" * 60)

        if not self.setup_demo_agent():
            print("❌ Falha na configuração. Verifique suas credenciais GCP.")
            return

        try:
            # Exemplos síncronos
            self.example_3_knowledge_base_population()  # Popular primeiro
            self.example_1_basic_questions()
            self.example_2_iterative_reasoning()
            self.example_4_scientific_discovery()
            self.example_5_advanced_queries()

            # Exemplo assíncrono
            print("\n⏳ Executando exemplo assíncrono...")
            asyncio.run(self.example_6_continuous_monitoring())

        except KeyboardInterrupt:
            print("\n⏹️  Exemplos interrompidos pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro durante execução: {e}")

        print("\n🎉 Todos os exemplos concluídos!")
        print("\nPara uso interativo, execute:")
        print("   python rag_plus_main.py --interactive")


def main():
    """Função principal"""
    examples = RAGPlusExamples()
    examples.run_all_examples()


if __name__ == "__main__":
    main()
