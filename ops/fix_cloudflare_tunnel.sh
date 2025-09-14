#!/bin/bash

echo "🔧 Configuração Alternativa do Cloudflare Tunnel"
echo "=============================================="

# Backup da configuração atual
sudo cp /etc/cloudflared/config.yml /etc/cloudflared/config.yml.backup

# Criar nova configuração sem origincert
sudo tee /etc/cloudflared/config.yml > /dev/null << 'EOF'
tunnel: pcs-tunnel
credentials-file: /etc/cloudflared/147fc4b5-1631-4196-ba8e-967b92178761.json

ingress:
  # Website principal (Nginx loopback)
  - hostname: agourakis.med.br
    service: http://127.0.0.1:8080

  # MCP API e SSE (Nginx proxy para Uvicorn)
  - hostname: mcp.agourakis.med.br
    service: http://127.0.0.1:8081

  # Catch-all para outros subdomínios/requests
  - service: http_status:404

# Configurações de performance
tunnel-timeout: 300s
connection-timeout: 10s
logfile: /var/log/cloudflared.log
loglevel: info
EOF

echo "✅ Nova configuração criada"

# Validar configuração
echo "🔍 Validando configuração..."
sudo cloudflared tunnel ingress validate

echo ""
echo "🚀 Reiniciando serviço..."
sudo systemctl restart cloudflared

echo ""
echo "⏰ Aguardando 15 segundos..."
sleep 15

echo ""
echo "🧪 Testando conectividade..."
curl -H "Host: agourakis.med.br" http://104.21.78.69/ -I
echo ""
curl -H "Host: mcp.agourakis.med.br" http://104.21.78.69/health -I

echo ""
echo "📋 Se ainda houver erro 522, verificar:"
echo "   1. SSL/TLS mode no Cloudflare deve estar em 'Flexible'"
echo "   2. Aguardar até 5 minutos para propagação"
echo "   3. Verificar se Cloudflare Proxy está ativo (nuvem laranja)"