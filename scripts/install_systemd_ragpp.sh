#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="ragpp_web_server"
SERVICE_FILE_SRC="$REPO_ROOT/deploy/${SERVICE_NAME}.service"
SERVICE_FILE_DST="/etc/systemd/system/${SERVICE_NAME}.service"
ENV_FILE_SRC="$REPO_ROOT/deploy/ragpp_env.example"
ENV_FILE_DST="/etc/default/${SERVICE_NAME}"

echo "[1/5] Requiring root privileges..."
if [[ $EUID -ne 0 ]]; then
  echo "Please run as root: sudo $0"; exit 1;
fi

echo "[2/5] Installing environment file to ${ENV_FILE_DST} (won't overwrite if exists)"
if [[ -f "$ENV_FILE_DST" ]]; then
  echo "Environment file already exists. Skipping copy."
else
  install -m 0640 "$ENV_FILE_SRC" "$ENV_FILE_DST"
  echo "Copied. Edit ${ENV_FILE_DST} and set MCP_BEARER_TOKEN."
fi

echo "[3/5] Installing systemd unit to ${SERVICE_FILE_DST}"
install -m 0644 "$SERVICE_FILE_SRC" "$SERVICE_FILE_DST"

echo "[4/5] Reloading systemd and enabling service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo "[5/5] Starting service..."
systemctl restart "$SERVICE_NAME"
sleep 1
systemctl --no-pager --full status "$SERVICE_NAME" || true

echo "Done. Logs: journalctl -u ${SERVICE_NAME} -f"

