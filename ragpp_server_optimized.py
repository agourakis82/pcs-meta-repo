#!/usr/bin/env python3
"""
RAG++ Web Server - Versão Otimizada para Performance
Servidor web otimizado com múltiplos workers e configurações de alta performance.
"""

import multiprocessing
import os
import sys
from pathlib import Path

# Adicionar dependências opcionais para performance
try:
    import uvloop

    USE_UVLOOP = True
except ImportError:
    USE_UVLOOP = False
    print("ℹ️ uvloop não disponível - usando asyncio padrão")

try:
    import httptools

    USE_HTTPTOOLS = True
except ImportError:
    USE_HTTPTOOLS = False
    print("ℹ️ httptools não disponível - usando HTTP parser padrão")


def get_optimal_workers():
    """Calcula número ótimo de workers baseado nos recursos do sistema."""
    cpu_count = multiprocessing.cpu_count()

    # Regra geral: 2x núcleos para I/O bound, 1x para CPU bound
    # RAG++ é principalmente I/O bound (buscas, bancos de dados)
    optimal = min(cpu_count * 2, 8)  # Máximo 8 workers para evitar sobrecarga

    return max(optimal, 1)  # Mínimo 1 worker


def start_optimized_server():
    """Inicia servidor com configurações otimizadas."""
    # Configurações de ambiente
    host = os.getenv("RAG_HOST", "0.0.0.0")
    port = int(os.getenv("RAG_PORT", "8000"))
    workers = int(os.getenv("RAG_WORKERS", str(get_optimal_workers())))
    production = os.getenv("PRODUCTION", "0") == "1"

    print("🚀 Iniciando RAG++ Server Otimizado")
    print(f"📍 Host: {host}:{port}")
    print(f"⚡ Workers: {workers} (ótimo para {multiprocessing.cpu_count()} CPUs)")
    print(f"🔧 Modo: {'Produção' if production else 'Desenvolvimento'}")
    print(f"🎯 Loop: {'uvloop' if USE_UVLOOP else 'asyncio'}")
    print(f"🌐 HTTP: {'httptools' if USE_HTTPTOOLS else 'auto'}")

    # Configurações de performance
    if USE_UVLOOP:
        uvloop.install()

    # Importar e configurar uvicorn
    import uvicorn

    # Configurações otimizadas
    config = {
        "app": "ragpp.ragpp_web_server:app",
        "host": host,
        "port": port,
        "workers": workers,
        "loop": "uvloop" if USE_UVLOOP else "asyncio",
        "http": "httptools" if USE_HTTPTOOLS else "auto",
        "log_level": "warning" if production else "info",
        "access_log": not production,
        # Timeouts otimizados
        "timeout_keep_alive": 30,
        "timeout_graceful_shutdown": 10,
    }

    print("\n📊 Configurações de Performance:")
    print(f"   • Workers: {workers}")
    print(f"   • CPU Cores: {multiprocessing.cpu_count()}")
    print(f"   • Timeout Keep-Alive: {config['timeout_keep_alive']}s")
    print(f"   • Timeout Shutdown: {config['timeout_graceful_shutdown']}s")

    print("\n🔗 URLs:")
    print(f"   📖 API Docs: http://{host}:{port}/docs")
    print(f"   🔌 Health Check: http://{host}:{port}/health")
    print(f"   🧠 Memory API: http://{host}:{port}/memory/")

    # Iniciar servidor
    uvicorn.run(**config)


if __name__ == "__main__":
    start_optimized_server()
