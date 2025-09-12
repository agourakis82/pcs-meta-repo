#!/usr/bin/env bash
set -euo pipefail

# Emite/renova certificado Let's Encrypt (HTTP-01) para Nginx no backend.
# Estratégia: abrir temporariamente porta 80 na UDM e servir /.well-known via Nginx.
# Requer acesso root no backend e Nginx instalado com site para o domínio.

# Uso:
#   ./scripts/issue_lets_encrypt_cert.sh -d mcp.agourakis.med.br -e admin@exemplo.com
# Opções:
#   -d|--domain       Domínio alvo (CN)
#   -e|--email        Email para registro LE
#   --staging         Usa ambiente de testes LE (evita rate limits)
#   --webroot PATH    Caminho webroot (default: /var/www/letsencrypt)

DOMAIN=""
EMAIL=""
STAGING=0
WEBROOT="/var/www/letsencrypt"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--domain) DOMAIN="$2"; shift 2;;
    -e|--email) EMAIL="$2"; shift 2;;
    --staging) STAGING=1; shift;;
    --webroot) WEBROOT="$2"; shift 2;;
    *) echo "Uso: $0 -d <dominio> -e <email> [--staging] [--webroot PATH]"; exit 1;;
  esac
done

if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
  echo "Erro: informe -d <dominio> e -e <email>." >&2
  exit 1
fi

if ! command -v certbot >/dev/null 2>&1; then
  echo "Instalando certbot..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y certbot
  else
    echo "Instale o certbot manualmente e reexecute." >&2
    exit 1
  fi
fi

echo "Preparando webroot em $WEBROOT"
sudo mkdir -p "$WEBROOT/.well-known/acme-challenge"
sudo chown -R www-data:www-data "$WEBROOT"

NGINX_SNIPPET="/etc/nginx/snippets/letsencrypt_webroot.conf"
if [[ ! -f "$NGINX_SNIPPET" ]]; then
  echo "Criando snippet Nginx: $NGINX_SNIPPET"
  sudo bash -c "cat > '$NGINX_SNIPPET' <<'SNIP'
location ^~ /.well-known/acme-challenge/ {
    alias WEBROOT_PLACEHOLDER/.well-known/acme-challenge/;
    try_files $uri =404;
    default_type text/plain;
}
SNIP"
  sudo sed -i "s|WEBROOT_PLACEHOLDER|$WEBROOT|g" "$NGINX_SNIPPET"
fi

SITE_FILE="/etc/nginx/sites-available/${DOMAIN}_80.conf"
if [[ ! -f "$SITE_FILE" ]]; then
  echo "Criando site temporário http em $SITE_FILE"
  sudo bash -c "cat > '$SITE_FILE' <<'EOF'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER;

    include /etc/nginx/snippets/letsencrypt_webroot.conf;

    location / {
        return 200 'LE http-01 ok';
        add_header Content-Type text/plain;
    }
}
EOF"
  sudo sed -i "s|DOMAIN_PLACEHOLDER|$DOMAIN|g" "$SITE_FILE"
  sudo ln -sf "$SITE_FILE" "/etc/nginx/sites-enabled/${DOMAIN}_80.conf"
fi

echo "Testando configuração Nginx..."
sudo nginx -t
echo "Recarregando Nginx..."
sudo systemctl reload nginx || sudo service nginx reload

echo "Certifique-se de que a UDM encaminhe porta 80 (temporário) para este host."
echo "No UDM, execute:"
echo "  iptables -t nat -I PREROUTING -i ppp0 -p tcp --dport 80 -j DNAT --to-destination $(hostname -I | awk '{print $1}'):80"
echo "  iptables -I FORWARD -p tcp -d $(hostname -I | awk '{print $1}') --dport 80 -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT"
echo "  iptables -I FORWARD -p tcp -s $(hostname -I | awk '{print $1}') --sport 80 -m state --state ESTABLISHED,RELATED -j ACCEPT"

args=(--webroot -w "$WEBROOT" -d "$DOMAIN" --email "$EMAIL" --agree-tos -n)
if [[ $STAGING -eq 1 ]]; then args+=(--staging); fi

echo "Executando certbot..."
sudo certbot certonly "${args[@]}"

echo "Concluído. Certificados em /etc/letsencrypt/live/$DOMAIN/"
echo "Atualize seu server block 8443 para usar os caminhos abaixo e recarregue Nginx:"
echo "  ssl_certificate     /etc/letsencrypt/live/$DOMAIN/fullchain.pem;"
echo "  ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;"
echo "Depois remova as regras temporárias de porta 80 no UDM."
