#!/usr/bin/env python3
"""
Gemini Function-Calling Bridge for RAG++

- Exposes three functions to the Gemini model:
  1) ragpp_search(query, max_results=10, search_type="hybrid")
     -> POST {RAGPP_BASE_URL}/search
  2) ragpp_recall_context(query, include_conversations=True, include_insights=True, max_results=10)
     -> GET  {RAGPP_BASE_URL}/memory/chatgpt/recall
  3) ragpp_store_context(conversation_title, messages, context_summary="", importance_score=0.7)
     -> POST {RAGPP_BASE_URL}/memory/chatgpt/context

- Drives a simple loop: send user prompt → handle functionCall → send functionResponse → final text.

ENV
  GEMINI_API_KEY      (required)
  GEMINI_MODEL        (default: gemini-1.5-pro)
  RAGPP_BASE_URL      (default: http://127.0.0.1:8000)
  RAG_API_TOKEN       (optional, Bearer for protected endpoints)

Usage
  python scripts/gemini_ragpp_bridge.py --prompt "Pergunta sobre PCS"

Note
  This script uses direct REST to Gemini v1beta. No extra deps are required beyond requests.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

import requests


API_BASE = os.getenv("RAGPP_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
RAG_TOKEN = os.getenv("RAG_API_TOKEN")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def _auth_headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if GEMINI_KEY:
        h["x-goog-api-key"] = GEMINI_KEY
    return h


def _rag_headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if RAG_TOKEN:
        h["Authorization"] = f"Bearer {RAG_TOKEN}"
    return h


FUNCTION_DECLS = [
    {
        "name": "ragpp_search",
        "description": "Search recent literature and project knowledge via RAG++",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 10},
                "search_type": {
                    "type": "string",
                    "enum": ["hybrid", "literature", "memory", "live_literature"],
                    "default": "hybrid",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "ragpp_recall_context",
        "description": "Recall relevant project context from Extended Memory",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "include_conversations": {"type": "boolean", "default": True},
                "include_insights": {"type": "boolean", "default": True},
                "max_results": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "ragpp_store_context",
        "description": "Store ChatGPT/Gemini conversation context in Extended Memory",
        "parameters": {
            "type": "object",
            "properties": {
                "conversation_title": {"type": "string"},
                "messages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["role", "content"],
                    },
                },
                "context_summary": {"type": "string", "default": ""},
                "importance_score": {"type": "number", "default": 0.7},
            },
            "required": ["conversation_title", "messages"],
        },
    },
]


def _dispatch_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "ragpp_search":
        url = f"{API_BASE}/search"
        body = {
            "query": args.get("query", ""),
            "max_results": args.get("max_results", 10),
            "search_type": args.get("search_type", "hybrid"),
        }
        r = requests.post(url, headers=_rag_headers(), json=body, timeout=60)
        r.raise_for_status()
        return r.json()

    if name == "ragpp_recall_context":
        url = f"{API_BASE}/memory/chatgpt/recall"
        params = {
            "query": args.get("query", ""),
            "include_conversations": args.get("include_conversations", True),
            "include_insights": args.get("include_insights", True),
            "max_results": args.get("max_results", 10),
        }
        r = requests.get(url, headers=_rag_headers(), params=params, timeout=60)
        r.raise_for_status()
        return r.json()

    if name == "ragpp_store_context":
        url = f"{API_BASE}/memory/chatgpt/context"
        body = {
            "conversation_title": args.get("conversation_title", "Session"),
            "messages": args.get("messages", []),
            "context_summary": args.get("context_summary", ""),
            "importance_score": args.get("importance_score", 0.7),
        }
        r = requests.post(url, headers=_rag_headers(), json=body, timeout=60)
        r.raise_for_status()
        return r.json()

    return {"error": f"Unknown function: {name}"}


def _gen_request(contents: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "contents": contents,
        "tools": [{"function_declarations": FUNCTION_DECLS}],
        "tool_config": {"function_calling_config": {"mode": "AUTO"}},
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 2048,
        },
    }


def _extract_function_call(resp: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        parts = resp["candidates"][0]["content"]["parts"]
        for p in parts:
            if "functionCall" in p:
                return p["functionCall"]
        return None
    except Exception:
        return None


def run_dialog(prompt: str) -> str:
    if not GEMINI_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    # Turn 1: user prompt
    contents: List[Dict[str, Any]] = [
        {"role": "user", "parts": [{"text": prompt}]}
    ]

    # First call
    r = requests.post(GEMINI_URL, headers=_auth_headers(), json=_gen_request(contents), timeout=120)
    r.raise_for_status()
    resp = r.json()

    fc = _extract_function_call(resp)
    steps = 0
    # Up to 3 tool calls
    while fc and steps < 3:
        steps += 1
        name = fc.get("name")
        args = json.loads(fc.get("args", "{}")) if isinstance(fc.get("args"), str) else fc.get("args", {})
        tool_result = _dispatch_tool(name, args)

        # Append model functionCall and tool functionResponse
        contents.append({"role": "model", "parts": [{"functionCall": {"name": name, "args": args}}]})
        contents.append(
            {
                "role": "tool",
                "parts": [
                    {
                        "functionResponse": {
                            "name": name,
                            "response": {
                                "name": name,
                                "content": [{"text": json.dumps(tool_result)}],
                            },
                        }
                    }
                ],
            }
        )

        r = requests.post(GEMINI_URL, headers=_auth_headers(), json=_gen_request(contents), timeout=120)
        r.raise_for_status()
        resp = r.json()
        fc = _extract_function_call(resp)

    # Final text
    try:
        parts = resp["candidates"][0]["content"]["parts"]
        for p in parts:
            if "text" in p:
                final_text = p["text"].strip()
                # Optional auto-store conversation
                if os.getenv("BRIDGE_AUTO_STORE", "0").strip() in ("1", "true", "yes"):
                    try:
                        _ = _dispatch_tool(
                            "ragpp_store_context",
                            {
                                "conversation_title": prompt[:80],
                                "messages": [
                                    {"role": "user", "content": prompt},
                                    {"role": "assistant", "content": final_text},
                                ],
                                "context_summary": "Gemini function-calling session",
                                "importance_score": 0.7,
                            },
                        )
                    except Exception:
                        pass
                return final_text
        return json.dumps(resp)
    except Exception:
        return json.dumps(resp)


def main():
    parser = argparse.ArgumentParser(description="Gemini bridge for RAG++ with function calling")
    parser.add_argument("--prompt", required=True, help="User prompt to send to Gemini")
    args = parser.parse_args()

    try:
        answer = run_dialog(args.prompt)
        print(answer)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
