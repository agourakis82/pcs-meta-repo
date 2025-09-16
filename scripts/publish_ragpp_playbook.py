#!/usr/bin/env python3
"""
Publica o playbook de modelagem/estatística no servidor RAG++ (memória MCP).

- Lê docs/RAGPP_modelagem_estatistica_robusta.md e
    docs/RAGPP_modelagem_estatistica_robusta.yaml
- Envia como registros de memória de projeto para facilitar RAG interno.
- Controlado via env MCP_FEED (padrão on), RAG_BASE_URL ou RAG_HOST/RAG_PORT.
"""

from __future__ import annotations

import json
import os
import urllib.request as url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DOCS_DIR = BASE_DIR / "docs"


def _base_url() -> str:
    base = os.getenv("RAG_BASE_URL")
    if base:
        return base
    host = os.getenv("RAG_HOST", "127.0.0.1").strip()
    port = os.getenv("RAG_PORT", "8000").strip()
    scheme = os.getenv("RAG_SCHEME", "http").strip()
    return f"{scheme}://{host}:{port}"


def publish() -> None:
    if str(os.getenv("MCP_FEED", "1")).strip().lower() in ("0", "false", "no"):
        print("MCP_FEED disabled; skipping publish")
        return
    endpoint = f"{_base_url()}/memory/store/project"
    # Publica todos os docs que começam com RAGPP_
    for path in sorted(DOCS_DIR.glob("RAGPP_*")):
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        payload = {
            "project_name": os.getenv("PROJECT_NAME", "pcs-meta-repo"),
            "context_type": "playbook_modelagem",
            "content": content,
            "metadata": {
                "filename": str(path.relative_to(BASE_DIR)),
                "tags": ["playbook", "modelagem", "estatistica", "RAG++"],
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = url.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with url.urlopen(req, timeout=float(os.getenv("MCP_TIMEOUT", "5"))):
            print(f"Publicado em MCP: {endpoint} ({path.name})")


if __name__ == "__main__":
    publish()
