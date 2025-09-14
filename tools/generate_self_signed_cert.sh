#!/usr/bin/env bash
set -euo pipefail

# Generate self-signed certificate for local HTTPS testing

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SSL_DIR="$ROOT_DIR/ssl"
mkdir -p "$SSL_DIR"

CERT="$SSL_DIR/dev_cert.pem"
KEY="$SSL_DIR/dev_key.pem"

if [[ -f "$CERT" && -f "$KEY" ]]; then
  echo "[ssl] Existing self-signed cert found at $CERT"
  exit 0
fi

echo "[ssl] Generating self-signed certificate..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$KEY" -out "$CERT" \
  -subj "/C=US/ST=Local/L=Local/O=RAGPP/OU=Dev/CN=localhost"

echo "[ssl] Wrote cert: $CERT"
echo "[ssl] Wrote key:  $KEY"
echo "[ssl] Update .env with:\nSSL_CERT_PATH=$CERT\nSSL_KEY_PATH=$KEY"

