#!/usr/bin/env bash
set -euo pipefail

# One-shot Let's Encrypt issuance for a domain using standalone HTTP-01.
# Usage: sudo ./scripts/issue_le_cert_standalone.sh <domain> <email>

DOMAIN="${1:-}"
EMAIL="${2:-}"

if [[ -z "${DOMAIN}" || -z "${EMAIL}" ]]; then
  echo "Usage: sudo $0 <domain> <email>" >&2
  exit 1
fi

echo "[0/5] Domain=${DOMAIN} Email=${EMAIL}"

echo "[1/5] Installing certbot (if missing) ..."
if ! command -v certbot >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y certbot
fi

echo "[2/5] Opening firewall ports 80/443 (if ufw present) ..."
if command -v ufw >/dev/null 2>&1; then
  ufw allow 80/tcp || true
  ufw allow 443/tcp || true
fi

echo "[3/5] Stopping Nginx (for standalone challenge) ..."
systemctl stop nginx || true
fuser -k 80/tcp || true

echo "[4/5] Issuing certificate via standalone HTTP-01 ..."
certbot certonly \
  --standalone \
  --preferred-challenges http \
  -d "${DOMAIN}" \
  -m "${EMAIL}" \
  --agree-tos \
  --non-interactive

echo "[5/5] Starting Nginx and validating configuration ..."
systemctl start nginx || true
nginx -t
systemctl reload nginx || true

echo
echo "✅ Certificate installed. Summary:"
certbot certificates | sed -n "/${DOMAIN}/,+12p"
echo
echo "Next: test TLS"
echo "  curl -vI https://${DOMAIN} | sed -n '1,12p'"
echo
