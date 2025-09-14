#!/usr/bin/env bash
set -euo pipefail

# Run RAG++ FastAPI server with HTTPS via uvicorn using SSL cert/key from .env

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  # shellcheck disable=SC2046
  export $(grep -E '^(RAG_API_TOKEN|RAG_HOST|RAG_PORT|SSL_CERT_PATH|SSL_KEY_PATH|RAG_SERVER_URL)=' .env | xargs -d '\n')
fi

: "${RAG_HOST:=0.0.0.0}"
: "${RAG_PORT:=8000}"

if [[ -z "${SSL_CERT_PATH:-}" || -z "${SSL_KEY_PATH:-}" ]]; then
  echo "ERROR: SSL_CERT_PATH and SSL_KEY_PATH must be set (in .env or env)." >&2
  exit 1
fi

echo "🚀 Starting RAG++ (HTTPS) on ${RAG_HOST}:${RAG_PORT}"
echo "🔐 Using cert: ${SSL_CERT_PATH}"

python -m uvicorn ragpp.ragpp_web_server:app \
  --host "$RAG_HOST" \
  --port "$RAG_PORT" \
  --ssl-certfile "$SSL_CERT_PATH" \
  --ssl-keyfile "$SSL_KEY_PATH" \
  --log-level info

