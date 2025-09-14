#!/usr/bin/env bash
set -euo pipefail
HOSTS=("agourakis.med.br" "mcp.agourakis.med.br")

for h in "${HOSTS[@]}"; do
  echo "== $h =="
  curl -sS -I "https://$h" | sed -n '1,8p' || true
  echo | openssl s_client -servername "$h" -connect "$h:443" -brief -showcerts 2>/dev/null | sed -n '1,20p' || true
  echo
  if [ "$h" = "mcp.agourakis.med.br" ]; then
    curl -sS -I "https://$h/health" | sed -n '1,8p' || true
  fi
  echo
  dig +short "$h" A @1.1.1.1
  dig +short CNAME "$h" @1.1.1.1
  echo "--------------"
  echo
done

echo "_acme-challenge TXT:"
dig +short TXT _acme-challenge.agourakis.med.br @1.1.1.1
