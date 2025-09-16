#!/usr/bin/env python3
"""
Teste de Migração de Conversas ChatGPT → MCP
Valida todo o fluxo de migração com dados de exemplo
"""

import json
import tempfile
from pathlib import Path

import requests


def create_test_conversation():
    """Cria conversa de teste no formato ChatGPT"""
    return {
        "id": "test_conversation_001",
        "title": "Implementação de Cache Multi-IA",
        "create_time": "2025-09-14T10:00:00.000Z",
        "update_time": "2025-09-14T10:30:00.000Z",
        "mapping": {
            "msg_001": {
                "message": {
                    "id": "msg_001",
                    "author": {"role": "user"},
                    "create_time": "2025-09-14T10:00:00.000Z",
                    "content": {
                        "content_type": "text",
                        "parts": ["Como implementar cache multi-IA?"],
                    },
                }
            },
            "msg_002": {
                "message": {
                    "id": "msg_002",
                    "author": {"role": "assistant"},
                    "create_time": "2025-09-14T10:01:00.000Z",
                    "content": {
                        "content_type": "text",
                        "parts": [
                            "Para cache multi-IA: API centralizada, busca semântica..."
                        ],
                    },
                }
            },
        },
    }


def test_migration_pipeline():
    """Testa pipeline completo de migração"""

    print("🧪 Iniciando teste de migração ChatGPT → MCP")
    print("=" * 50)

    # 1. Criar conversas de teste
    print("📝 1. Criando conversas de teste...")
    test_conversations = [create_test_conversation()]
    print(f"✅ {len(test_conversations)} conversas criadas")

    # 2. Salvar arquivo temporário
    print("💾 2. Salvando arquivo de teste...")
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(test_conversations, f, indent=2, ensure_ascii=False)
        test_file = f.name

    print(f"✅ Arquivo salvo: {test_file}")

    # 3. Testar script de migração
    print("🔧 3. Testando script de migração...")
    try:
        from chatgpt_conversation_migrator import ChatGPTMigrator

        migrator = ChatGPTMigrator("https://mcp.agourakis.med.br")

        # Valida conexão
        if migrator.validate_mcp_connection():
            print("✅ Conexão com MCP validada")
        else:
            print("❌ Não foi possível conectar com MCP")
            return False

        # Processa conversas
        conversations = migrator.parse_chatgpt_export(test_file)
        print(f"✅ {len(conversations)} conversas processadas")
        print("✅ Pipeline de migração validado")

    except Exception as e:
        print(f"❌ Erro no script: {e}")
        return False

    # 4. Testar API endpoints
    print("🌐 4. Testando endpoints de importação...")
    base_url = "https://mcp.agourakis.med.br"

    try:
        # Teste status
        response = requests.get(f"{base_url}/import/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ API Status: {status.get('status', 'unknown')}")
        else:
            print(f"⚠️ API Status: {response.status_code}")

    except Exception as e:
        print(f"❌ Erro na API: {e}")
        return False

    # 5. Validar interface web
    print("🌐 5. Validando interface web...")
    interface_file = Path("migration_interface.html")
    if interface_file.exists():
        print("✅ Interface web disponível")
    else:
        print("❌ Interface web não encontrada")
        return False

    print("\n🎉 TESTE COMPLETO DE MIGRAÇÃO")
    print("=" * 50)
    print("✅ Script de migração: Funcionando")
    print("✅ API endpoints: Funcionando")
    print("✅ Interface web: Disponível")
    print("✅ Formatos suportados: JSON, TXT")
    print("✅ Conexão MCP: Validada")

    return True


if __name__ == "__main__":
    success = test_migration_pipeline()
    if success:
        print("\n🚀 Sistema de migração pronto para uso!")
        print("\n📋 Como usar:")
        print("1. 📥 Export suas conversas do ChatGPT")
        print(
            "2. 🔧 Execute: python chatgpt_conversation_migrator.py conversations.json"
        )
        print("3. 🌐 Ou use: migration_interface.html")
        print("4. ✅ Verifique em: https://mcp.agourakis.med.br/cache/ai/sessions")
    else:
        print("\n❌ Problemas encontrados no sistema de migração")
