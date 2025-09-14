#!/usr/bin/env python3
"""
Teste simples de cache RAG++
"""

import time

import requests


def test_simple():
    """Teste básico."""
    base_url = "http://127.0.0.1:8000"

    print("🧪 Teste Cache RAG++")

    # Teste health
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health: {resp.status_code}")
    except:
        print("❌ Health falhou")
        return

    # Teste cache stats
    try:
        resp = requests.get(f"{base_url}/cache/stats", timeout=5)
        if resp.status_code == 200:
            print("✅ Cache ativo")
        else:
            print("⚠️ Cache não ativo")
    except:
        print("❌ Cache stats falhou")

    print("🎉 Teste concluído!")


if __name__ == "__main__":
    test_simple()
