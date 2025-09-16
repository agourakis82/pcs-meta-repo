#!/usr/bin/env bash
set -euo pipefail

DOMAIN="mcp.agourakis.med.br"
SITE_CONF_SRC="$(cd "$(dirname "$0")/.." && pwd)/deploy/nginx_mcp_agourakis.conf"
SITE_CONF_DST="/etc/nginx/sites-available/${DOMAIN}.conf"

echo "[1/6] Installing nginx + certbot..."
sudo apt-get update -y
sudo apt-get install -y nginx certbot python3-certbot-nginx

echo "[2/6] Opening firewall ports 80/443..."
if command -v ufw >/dev/null 2>&1; then
  sudo ufw allow 80/tcp || true
  sudo ufw allow 443/tcp || true
fi

echo "[3/6] Installing site config for ${DOMAIN}..."
sudo cp -f "${SITE_CONF_SRC}" "${SITE_CONF_DST}"
sudo ln -sf "${SITE_CONF_DST}" "/etc/nginx/sites-enabled/${DOMAIN}.conf"
sudo nginx -t
sudo systemctl reload nginx

echo "[4/6] Issuing TLS certificate with Let’s Encrypt..."
sudo certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos -m "admin@${DOMAIN}" --redirect || true

echo "[5/6] Reloading nginx..."
sudo nginx -t
sudo systemctl reload nginx

echo "[6/6] Done. Test endpoints:"
echo " - Health:  https://${DOMAIN}/health"
echo " - MCP SSE: curl -N -H 'Accept: text/event-stream' https://${DOMAIN}/mcp"
echo " - Tools:   curl -X POST https://${DOMAIN}/mcp -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":"1","method":"tools/list"}'"

