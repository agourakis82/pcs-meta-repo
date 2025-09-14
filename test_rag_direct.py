#!/usr/bin/env python3
"""
Teste direto do RAG++ Search
Script simples para testar a funcionalidade de busca sem servidor web.
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from ragpp.tools.mcp_rag_integration import MCPRAGIntegration

    print("✅ MCPRAGIntegration importado com sucesso")

    # Initialize RAG system
    rag = MCPRAGIntegration()
    print("✅ Sistema RAG++ inicializado")

    # Test search
    print("\n🔍 Testando busca...")
    results = rag.hybrid_search(
        "machine learning psychiatry", max_rag_results=3, max_mcp_results=2
    )
    print("✅ Busca realizada com sucesso!")

    # Print results
    print("\n📊 Resultados da busca:")
    print(json.dumps(results, indent=2, ensure_ascii=False))

    print("\n🎉 Teste concluído com sucesso!")

except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback

    traceback.print_exc()
