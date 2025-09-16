#!/usr/bin/env python3
"""
RAG++ Setup: Configuração rápida do sistema integrado MCP + RAG
"""

import os
import json
import subprocess
from pathlib import Path


def setup_rag_plus_plus():
    """Configura o sistema RAG++ completo."""
    
    print("🚀 Configurando Sistema RAG++ com MCP")
    print("=" * 50)
    
    # 1. Verificar estrutura de diretórios
    print("📁 Verificando estrutura de diretórios...")
    
    required_dirs = [
        "ragpp/data/processed/2025_sweep",
        "ragpp/index", 
        "ragpp/outputs",
        "config"
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {dir_path}")
    
    # 2. Criar dados demo se não existirem
    print("\n📊 Verificando dados demo...")
    
    chunks_file = Path("ragpp/data/processed/2025_sweep/YEAR-2025_chunks.jsonl")
    notes_file = Path("ragpp/data/processed/2025_sweep/YEAR-2025_active_reading_notes.jsonl")
    
    if not chunks_file.exists() or not notes_file.exists():
        print("  📝 Criando dados demo...")
        try:
            subprocess.run([
                "python", "ragpp/tools/bootstrap_demo_records.py"
            ], check=True)
            print("  ✅ Dados demo criados")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️ Erro criando dados demo: {e}")
    else:
        print("  ✅ Dados demo já existem")
    
    # 3. Construir índice RAG
    print("\n🔍 Construindo índice RAG...")
    
    try:
        subprocess.run([
            "python", "ragpp/tools/build_index.py",
            "--db", "ragpp/index/lit2025",
            "--chunks", str(chunks_file),
            "--notes", str(notes_file)
        ], check=True)
        print("  ✅ Índice RAG construído")
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️ Erro construindo índice: {e}")
    
    # 4. Verificar MCP server
    print("\n🧠 Verificando MCP server...")
    
    mcp_settings_path = Path.home() / ".vscode-server/data/User/globalStorage/blackboxapp.blackboxagent/settings/blackbox_mcp_settings.json"
    
    if mcp_settings_path.exists():
        print("  ✅ MCP server configurado")
        try:
            with open(mcp_settings_path, 'r') as f:
                mcp_config = json.load(f)
            
            if any("pcs-memory-server" in str(server) for server in mcp_config.get("mcpServers", {})):
                print("  ✅ PCS Memory Server encontrado")
            else:
                print("  ⚠️ PCS Memory Server não encontrado na configuração")
        except Exception as e:
            print(f"  ⚠️ Erro lendo configuração MCP: {e}")
    else:
        print("  ⚠️ MCP server não configurado")
        print("  💡 Configure o MCP server primeiro")
    
    # 5. Testar integração
    print("\n🧪 Testando integração RAG++...")
    
    try:
        # Importar e testar rapidamente
        from ragpp.tools.mcp_rag_integration import MCPRAGIntegration
        
        mcp_rag = MCPRAGIntegration()
        
        # Teste simples
        test_results = mcp_rag.hybrid_search("test query", max_rag_results=1, max_mcp_results=1)
        
        total_sources = test_results["sources"]["total"] 
        print(f"  ✅ Integração funcionando (encontrou {total_sources} fontes)")
        
    except Exception as e:
        print(f"  ⚠️ Erro testando integração: {e}")
    
    # 6. Criar arquivo de configuração
    print("\n⚙️ Criando configuração RAG++...")
    
    rag_config = {
        "version": "4.4",
        "description": "RAG++ Configuration for PCS Project",
        "rag_database": {
            "path": "ragpp/index/lit2025",
            "collection": "lit2025",
            "embedding_model": "default"
        },
        "mcp_integration": {
            "memory_manager": "scripts/memory_manager.py",
            "categories": [
                "research_findings",
                "methodology", 
                "literature_review",
                "project_progress",
                "computational_results",
                "theoretical_insights"
            ]
        },
        "search_defaults": {
            "max_rag_results": 5,
            "max_mcp_results": 3,
            "confidence_threshold": 0.3
        },
        "data_sources": {
            "chunks": "ragpp/data/processed/2025_sweep/YEAR-2025_chunks.jsonl",
            "notes": "ragpp/data/processed/2025_sweep/YEAR-2025_active_reading_notes.jsonl",
            "records": "ragpp/data/processed/2025_sweep/YEAR-2025_psy-neuro_records.jsonl"
        }
    }
    
    config_path = Path("config/ragpp_config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(rag_config, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ Configuração salva em {config_path}")
    
    # 7. Criar script de uso rápido
    print("\n📋 Criando scripts de uso...")
    
    quick_search_script = '''#!/bin/bash
# Script de busca rápida RAG++

if [ $# -eq 0 ]; then
    echo "Uso: ./ragpp_search.sh 'sua pergunta aqui'"
    echo "Exemplo: ./ragpp_search.sh 'What is semantic entropy?'"
    exit 1
fi

QUERY="$1"
echo "🔍 Buscando: $QUERY"
echo "=================================="

python ragpp/tools/mcp_rag_integration.py qa --query "$QUERY"
'''
    
    script_path = Path("ragpp_search.sh")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(quick_search_script)
    
    # Tornar executável
    os.chmod(script_path, 0o755)
    print(f"  ✅ Script de busca criado: {script_path}")
    
    # Script de armazenamento
    store_script = '''#!/bin/bash
# Script para armazenar descobertas no RAG++

if [ $# -eq 0 ]; then
    echo "Uso: ./ragpp_store.sh 'sua descoberta aqui' [categoria] [tags...]"
    echo "Exemplo: ./ragpp_store.sh 'Nova descoberta sobre entropia' research_findings entropy semantic"
    exit 1
fi

CONTENT="$1"
CATEGORY="${2:-research_findings}"
shift 2
TAGS="$@"

echo "💾 Armazenando descoberta..."
echo "Categoria: $CATEGORY"
echo "Tags: $TAGS"
echo "=================================="

python ragpp/tools/mcp_rag_integration.py store --content "$CONTENT" --category "$CATEGORY" --tags $TAGS
'''
    
    store_script_path = Path("ragpp_store.sh")
    with open(store_script_path, 'w', encoding='utf-8') as f:
        f.write(store_script)
    
    os.chmod(store_script_path, 0o755)
    print(f"  ✅ Script de armazenamento criado: {store_script_path}")
    
    # 8. Sumário final
    print("\n" + "=" * 50)
    print("✅ CONFIGURAÇÃO RAG++ COMPLETA!")
    print("\n🎯 Como usar:")
    print("  • Busca rápida: ./ragpp_search.sh 'sua pergunta'")
    print("  • Armazenar: ./ragpp_store.sh 'descoberta' categoria tag1 tag2")
    print("  • Demo completa: python ragpp/demo_rag_plus_plus.py")
    print("  • Integração direta: python ragpp/tools/mcp_rag_integration.py")
    
    print("\n📁 Estrutura criada:")
    for dir_path in required_dirs:
        print(f"  • {dir_path}/")
    
    print(f"\n⚙️ Configuração: {config_path}")
    print(f"🔍 Scripts: {script_path}, {store_script_path}")
    
    print("\n💡 Próximos passos:")
    print("  1. Configure dados reais em config/data_root.yaml")
    print("  2. Execute pipeline v4.4 com RUN_REAL=1")
    print("  3. Use RAG++ para análise contínua")
    print("  4. Documente descobertas automaticamente")


if __name__ == "__main__":
    setup_rag_plus_plus()
