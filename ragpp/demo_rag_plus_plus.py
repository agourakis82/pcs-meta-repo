#!/usr/bin/env python3
"""
RAG++ Demo: Mostra como usar MCP + RAG para pesquisa avançada
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ragpp.tools.mcp_rag_integration import MCPRAGIntegration


def demo_rag_plus_plus():
    """Demonstração completa do sistema RAG++."""
    
    print("🚀 Demonstração RAG++ com MCP Server")
    print("=" * 60)
    
    # Inicializar integração
    mcp_rag = MCPRAGIntegration()
    
    # Exemplos de perguntas para testar
    test_questions = [
        # Pergunta específica do projeto
        "Como funciona nosso pipeline ZuCo v4.4?",
        
        # Pergunta de literatura científica  
        "What are the latest findings on EEG-eye tracking integration?",
        
        # Pergunta híbrida
        "How does semantic curvature relate to psychiatric disorders?",
        
        # Pergunta metodológica
        "What are the best practices for entropy calculation in networks?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*20} PERGUNTA {i} {'='*20}")
        print(f"❓ {question}")
        print("-" * 60)
        
        # Usar o sistema híbrido RAG++
        response = mcp_rag.enhanced_qa(question)
        
        # Mostrar resultados
        print(f"🎯 Confiança: {response['confidence']}")
        print(f"📊 Fontes: Literatura={response['sources_found']['literature']}, "
              f"Memória={response['sources_found']['memory']}")
        
        if response['synthesis']:
            print(f"\n💡 Síntese:\n{response['synthesis'][:500]}...")
        
        print(f"\n📋 Recomendações:")
        for rec in response['recommendations'][:2]:
            print(f"  • {rec}")
        
        print(f"\n{'='*60}")


def demo_store_finding():
    """Demonstra como armazenar descobertas no sistema."""
    
    print("\n🔬 Demonstração: Armazenar Descoberta Científica")
    print("=" * 60)
    
    mcp_rag = MCPRAGIntegration()
    
    # Exemplo de descoberta científica
    finding = """
Descoberta importante sobre entropia em redes semânticas:

Nossa análise do dataset ZuCo v2.0 revelou que a entropia de transição 
em grafos semânticos correlaciona fortemente (r=0.78, p<0.001) com 
medidas de compreensão leitora derivadas de EEG.

Especificamente:
- Entropia alta (>2.5 bits) associada com maior dificuldade de processamento
- Curvatura de Ricci negativa coincide com regiões de alta entropia
- Padrões consistentes em ambos os idiomas (EN/DE)

Implicações: Entropia semântica pode ser preditor robusto de carga cognitiva.
Próximos passos: Validar em dataset independente (GECO).
"""
    
    # Armazenar na memória e indexar no RAG
    success = mcp_rag.store_research_finding(
        content=finding,
        category="research_findings", 
        tags=["entropy", "semantic_networks", "zuco", "eeg", "reading_comprehension"],
        importance=5,  # Muito importante
        auto_index_to_rag=True
    )
    
    if success:
        print("✅ Descoberta armazenada com sucesso!")
        print("📊 Agora disponível para buscas futuras via RAG++ híbrido")
        
        # Testar busca imediata
        print("\n🔍 Testando busca imediata...")
        results = mcp_rag.hybrid_search(
            "semantic entropy cognitive load", 
            max_rag_results=3, 
            max_mcp_results=2
        )
        
        print(f"Encontrou {results['sources']['total']} resultados relevantes")
        
    else:
        print("❌ Falha ao armazenar descoberta")


def demo_knowledge_export():
    """Demonstra exportação do grafo de conhecimento."""
    
    print("\n📊 Demonstração: Exportar Grafo de Conhecimento")
    print("=" * 60)
    
    mcp_rag = MCPRAGIntegration()
    
    # Exportar grafo completo
    output_path = "ragpp/outputs/demo_knowledge_graph.json"
    success = mcp_rag.export_knowledge_graph(output_path)
    
    if success:
        print(f"✅ Grafo de conhecimento exportado para {output_path}")
        print("📋 Conteúdo inclui:")
        print("  • Nós de literatura científica indexada")
        print("  • Nós de memórias do projeto")
        print("  • Metadados e estatísticas")
        print("  • Estrutura para análise de redes")
        
        # Ler e mostrar estatísticas
        import json
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
            
            stats = graph_data.get('statistics', {})
            print(f"\n📊 Estatísticas:")
            print(f"  • Nós literatura: {stats.get('total_literature_nodes', 0)}")
            print(f"  • Nós memória: {stats.get('total_memory_nodes', 0)}")
            print(f"  • Total: {stats.get('total_nodes', 0)}")
            
        except Exception as e:
            print(f"⚠️ Erro ao ler estatísticas: {e}")
    
    else:
        print("❌ Falha ao exportar grafo")


def demo_advanced_search():
    """Demonstra buscas avançadas com filtros."""
    
    print("\n🔍 Demonstração: Buscas Avançadas")
    print("=" * 60)
    
    mcp_rag = MCPRAGIntegration()
    
    # Busca focada em métodos
    print("🔬 Busca focada em MÉTODOS:")
    methods_results = mcp_rag.hybrid_search(
        "experimental methodology statistical analysis",
        max_rag_results=3,
        max_mcp_results=2,
        include_mcp_categories=["methodology", "computational_results"]
    )
    
    print(f"Encontrou {methods_results['sources']['total']} resultados metodológicos")
    
    # Busca focada em descobertas
    print("\n🧪 Busca focada em DESCOBERTAS:")
    findings_results = mcp_rag.hybrid_search(
        "significant findings novel results",
        max_rag_results=3, 
        max_mcp_results=2,
        include_mcp_categories=["research_findings", "theoretical_insights"]
    )
    
    print(f"Encontrou {findings_results['sources']['total']} resultados de descobertas")
    
    # Busca do projeto atual
    print("\n🚧 Busca focada no PROJETO:")
    project_results = mcp_rag.hybrid_search(
        "current project status development",
        max_rag_results=1,
        max_mcp_results=4,
        include_mcp_categories=["project_progress", "methodology"]
    )
    
    print(f"Encontrou {project_results['sources']['total']} resultados do projeto")


def main():
    """Executa todas as demonstrações."""
    
    print("🧠 SISTEMA RAG++ COM MCP SERVER")
    print("Integração avançada de busca científica")
    print("=" * 70)
    
    try:
        # Demo 1: Q&A híbrido
        demo_rag_plus_plus()
        
        # Demo 2: Armazenar descobertas
        demo_store_finding()
        
        # Demo 3: Exportar conhecimento
        demo_knowledge_export()
        
        # Demo 4: Buscas avançadas
        demo_advanced_search()
        
        print("\n" + "=" * 70)
        print("✅ DEMONSTRAÇÃO COMPLETA!")
        print("\n🎯 Próximos passos recomendados:")
        print("  1. Configure seus caminhos de dados reais no config/")
        print("  2. Execute o pipeline v4.4 com RUN_REAL=1")
        print("  3. Use o sistema RAG++ para análise contínua")
        print("  4. Documente descobertas automaticamente via MCP")
        
    except Exception as e:
        print(f"\n❌ Erro na demonstração: {e}")
        print("💡 Verifique se o MCP server está configurado corretamente")


if __name__ == "__main__":
    main()
