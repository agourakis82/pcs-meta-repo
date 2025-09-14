#!/bin/bash

echo "🔍 Diagnóstico do Cloudflare Tunnel"
echo "=================================="
echo

echo "1. Status do tunnel:"
cloudflared tunnel list
echo

echo "2. Status do serviço:"
sudo systemctl status cloudflared --no-pager -l
echo

echo "3. Conectividade local:"
echo "  - Testando 127.0.0.1:8080 (nginx website):"
curl -I -s http://127.0.0.1:8080 | head -2
echo "  - Testando 127.0.0.1:8081 (nginx MCP proxy):"
curl -I -s http://127.0.0.1:8081/health | head -2
echo "  - Testando 127.0.0.1:8000 (MCP direto):"
curl -s http://127.0.0.1:8000/health | jq -r '.status // "erro"'
echo

echo "4. DNS:"
echo "  - agourakis.med.br:"
dig +short agourakis.med.br
echo "  - mcp.agourakis.med.br:"
dig +short mcp.agourakis.med.br
echo

echo "5. Teste Cloudflare (HTTP):"
echo "  - agourakis.med.br:"
curl -H "Host: agourakis.med.br" -s -I http://104.21.78.69/ | head -2
echo "  - mcp.agourakis.med.br:"
curl -H "Host: mcp.agourakis.med.br" -s -I http://104.21.78.69/health | head -2
echo

echo "6. Configuração do tunnel:"
echo "  - Arquivo de config:"
sudo cat /etc/cloudflared/config.yml | grep -v "^#" | grep -v "^$"
echo

echo "7. Últimos logs do cloudflared:"
sudo journalctl -u cloudflared --no-pager -n 5 --since "5 minutes ago"
echo

echo "🔧 Possíveis soluções:"
echo "- Se erro 522: verificar se o SSL mode no Cloudflare está em 'Flexible' ou 'Full'"
echo "- Se SSL handshake failure: aguardar propagação do certificado (até 24h)"
echo "- Se connectividade local falha: verificar firewall e serviços"