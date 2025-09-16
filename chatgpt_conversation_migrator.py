#!/usr/bin/env python3
"""
ChatGPT Conversation Migrator
Ferramenta para transferir conversas do ChatGPT Web para o servidor MCP
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests


class ChatGPTMigrator:
    """Migra conversas do ChatGPT para o servidor MCP"""

    def __init__(self, mcp_base_url: str = "https://mcp.agourakis.med.br"):
        self.mcp_base_url = mcp_base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "ChatGPT-MCP-Migrator/1.0",
            }
        )

    def validate_mcp_connection(self) -> bool:
        """Valida se o servidor MCP está acessível"""
        try:
            response = self.session.get(f"{self.mcp_base_url}/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao conectar com MCP: {e}")
            return False

    def parse_chatgpt_export(self, export_file: str) -> List[Dict[str, Any]]:
        """
        Processa arquivo de exportação do ChatGPT

        Formatos suportados:
        1. JSON Export do ChatGPT (conversations.json)
        2. Manual copy-paste conversation
        """
        export_path = Path(export_file)

        if not export_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {export_file}")

        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # Tenta parsear como JSON primeiro
        try:
            data = json.loads(content)
            return self._parse_json_export(data)
        except json.JSONDecodeError:
            # Se não for JSON, trata como texto simples
            return self._parse_text_export(content)

    def _parse_json_export(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Processa exportação JSON do ChatGPT"""
        conversations = []

        # Formato oficial do ChatGPT export
        if isinstance(data, list):
            # Lista de conversas
            for conv in data:
                conversations.append(self._process_conversation(conv))
        elif isinstance(data, dict):
            if "conversations" in data:
                # Wrapper com conversas
                for conv in data["conversations"]:
                    conversations.append(self._process_conversation(conv))
            else:
                # Conversa única
                conversations.append(self._process_conversation(data))

        return conversations

    def _parse_text_export(self, content: str) -> List[Dict[str, Any]]:
        """Processa conversas em formato texto"""
        lines = content.split("\n")
        conversations = []
        current_conv = {
            "title": "Conversa Importada",
            "messages": [],
            "created_at": datetime.now().isoformat(),
        }

        current_role = None
        current_message = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detecta roles
            if line.lower().startswith(("user:", "você:", "pergunta:")):
                if current_role and current_message:
                    current_conv["messages"].append(
                        {
                            "role": current_role,
                            "content": "\n".join(current_message),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                current_role = "user"
                current_message = [line.split(":", 1)[1].strip()]
            elif line.lower().startswith(("assistant:", "chatgpt:", "resposta:")):
                if current_role and current_message:
                    current_conv["messages"].append(
                        {
                            "role": current_role,
                            "content": "\n".join(current_message),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                current_role = "assistant"
                current_message = [line.split(":", 1)[1].strip()]
            else:
                if current_role:
                    current_message.append(line)

        # Adiciona última mensagem
        if current_role and current_message:
            current_conv["messages"].append(
                {
                    "role": current_role,
                    "content": "\n".join(current_message),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        if current_conv["messages"]:
            conversations.append(current_conv)

        return conversations

    def _process_conversation(self, conv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa uma conversa individual"""
        processed = {
            "title": conv_data.get("title", "Conversa sem título"),
            "created_at": conv_data.get("create_time", datetime.now().isoformat()),
            "updated_at": conv_data.get("update_time", datetime.now().isoformat()),
            "messages": [],
        }

        # Processa mensagens
        mapping = conv_data.get("mapping", {})
        for msg_id, msg_data in mapping.items():
            message = msg_data.get("message")
            if not message:
                continue

            author = message.get("author", {})
            role = author.get("role", "unknown")

            content_parts = message.get("content", {}).get("parts", [])
            if content_parts:
                processed["messages"].append(
                    {
                        "role": role,
                        "content": "\n".join(str(part) for part in content_parts),
                        "timestamp": processed["created_at"],
                    }
                )

        return processed

    def migrate_to_mcp(
        self, conversations: List[Dict[str, Any]], project_name: str = "ChatGPT Import"
    ) -> Dict[str, Any]:
        """Migra conversas para o servidor MCP"""
        results = {
            "total_conversations": len(conversations),
            "successful_migrations": 0,
            "failed_migrations": 0,
            "session_ids": [],
            "errors": [],
        }

        print(f"🚀 Iniciando migração de {len(conversations)} conversas...")

        for i, conv in enumerate(conversations, 1):
            try:
                print(
                    f"📤 Migrando conversa {i}/{len(conversations)}: {conv['title'][:50]}..."
                )

                # 1. Criar sessão no MCP
                session_data = {
                    "ai_type": "chatgpt",
                    "session_name": f"{project_name} - {conv['title']}",
                    "context_summary": f"Conversa importada: {conv['title']}",
                }

                session_response = self.session.post(
                    f"{self.mcp_base_url}/cache/ai/session",
                    json=session_data,
                    timeout=30,
                )

                if session_response.status_code != 200:
                    raise Exception(f"Erro ao criar sessão: {session_response.text}")

                session_id = session_response.json().get("session_id")
                results["session_ids"].append(session_id)

                # 2. Armazenar contexto da conversa
                context_data = {
                    "session_id": session_id,
                    "ai_type": "chatgpt",
                    "messages": conv["messages"],
                    "context_summary": f"Conversa '{conv['title']}' importada do ChatGPT Web",
                    "importance_score": 0.8,  # Score alto para conversas importadas
                    "metadata": {
                        "original_title": conv["title"],
                        "created_at": conv.get("created_at"),
                        "updated_at": conv.get("updated_at"),
                        "import_timestamp": datetime.now().isoformat(),
                        "source": "chatgpt_web_export",
                    },
                }

                context_response = self.session.post(
                    f"{self.mcp_base_url}/cache/ai/context",
                    json=context_data,
                    timeout=60,
                )

                if context_response.status_code != 200:
                    raise Exception(
                        f"Erro ao armazenar contexto: {context_response.text}"
                    )

                results["successful_migrations"] += 1
                print(f"✅ Conversa migrada com sucesso (ID: {session_id})")

                # Delay entre migrações para não sobrecarregar
                time.sleep(0.5)

            except Exception as e:
                results["failed_migrations"] += 1
                error_msg = f"Erro na conversa {i}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"❌ {error_msg}")

        return results

    def create_migration_report(
        self, results: Dict[str, Any], output_file: str = "migration_report.json"
    ) -> None:
        """Cria relatório da migração"""
        report = {
            "migration_timestamp": datetime.now().isoformat(),
            "results": results,
            "mcp_server": self.mcp_base_url,
            "summary": {
                "success_rate": f"{(results['successful_migrations'] / results['total_conversations'] * 100):.1f}%",
                "total_sessions_created": len(results["session_ids"]),
            },
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📊 Relatório salvo em: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Migra conversas do ChatGPT para o servidor MCP"
    )
    parser.add_argument("export_file", help="Arquivo de exportação do ChatGPT")
    parser.add_argument(
        "--mcp-url", default="https://mcp.agourakis.med.br", help="URL do servidor MCP"
    )
    parser.add_argument(
        "--project-name",
        default="ChatGPT Import",
        help="Nome do projeto para as conversas",
    )
    parser.add_argument(
        "--report", default="migration_report.json", help="Arquivo de relatório"
    )

    args = parser.parse_args()

    # Inicializa migrador
    migrator = ChatGPTMigrator(args.mcp_url)

    # Valida conexão
    print(f"🔗 Validando conexão com {args.mcp_url}...")
    if not migrator.validate_mcp_connection():
        print("❌ Não foi possível conectar com o servidor MCP")
        return 1
    print("✅ Conexão com MCP validada")

    try:
        # Processa exportação
        print(f"📖 Processando arquivo: {args.export_file}...")
        conversations = migrator.parse_chatgpt_export(args.export_file)
        print(f"✅ {len(conversations)} conversas encontradas")

        # Migra conversas
        results = migrator.migrate_to_mcp(conversations, args.project_name)

        # Cria relatório
        migrator.create_migration_report(results, args.report)

        # Resumo final
        print("\n" + "=" * 50)
        print("📋 RESUMO DA MIGRAÇÃO")
        print("=" * 50)
        print(f"Total de conversas: {results['total_conversations']}")
        print(f"Migrações bem-sucedidas: {results['successful_migrations']}")
        print(f"Migrações falharam: {results['failed_migrations']}")
        print(
            f"Taxa de sucesso: {(results['successful_migrations'] / results['total_conversations'] * 100):.1f}%"
        )

        if results["errors"]:
            print("\n❌ Erros encontrados:")
            for error in results["errors"]:
                print(f"  - {error}")

        return 0 if results["failed_migrations"] == 0 else 1

    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
