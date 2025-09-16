#!/usr/bin/env bash
set -euo pipefail

# Expor o proxy nginx local (8081) via ngrok para testes temporários
# Uso: ./scripts/ngrok_expose.sh [port]
# Requisitos: ngrok instalado e autenticado (ngrok config add-authtoken <token>)

PORT="${1:-8081}"

if ! command -v ngrok >/dev/null 2>&1; then
  echo "ngrok não encontrado. Instale com: sudo apt install -y ngrok" >&2
  exit 1
fi

echo "Iniciando ngrok http ${PORT}..."
exec ngrok http "${PORT}"
