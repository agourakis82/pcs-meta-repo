#!/bin/bash

# DEPRECATED: Script para configurar Tailscale Funnel
# ===================================================
# ⚠️  ESTE ARQUIVO FOI DEPRECIADO ⚠️
# 
# MIGRADO PARA: Cloudflare Tunnel (cloudflared)
# NOVO GUIA: docs/infra_cloudflare_tunnel.md
# 
# Para configurar a nova infraestrutura:
# 1. Siga as instruções em docs/infra_cloudflare_tunnel.md
# 2. Use os templates em cloudflared/ e nginx/sites-available/
# 
# Este arquivo permanece apenas para compatibilidade histórica.
# ===================================================

# Script para configurar Tailscale Funnel no servidor 192.168.4.198 (DEPRECATED)
# Execute este script no servidor Linux (192.168.4.198)

set -e

echo "🚀 Configurando Tailscale Funnel para MCP Server"
echo "================================================"

# Verificar se Tailscale está instalado
if ! command -v tailscale &> /dev/null; then
    echo "📦 Instalando Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
fi

# Verificar se está logado
if ! tailscale status &> /dev/null; then
    echo "🔐 Tailscale não está logado. Execute:"
    echo "sudo tailscale up --ssh"
    echo "Depois acesse o link fornecido para autenticar."
    exit 1
fi

echo "✅ Tailscale está conectado"

# Resetar configurações anteriores
echo "🔄 Limpando configurações anteriores..."
sudo tailscale serve reset || true
sudo tailscale funnel reset || true

# Aguardar um pouco
sleep 2

# Configurar serve para localhost (porta 8443 do Nginx)
echo "⚙️  Configurando Tailscale serve..."
sudo tailscale serve --https=443 http://127.0.0.1:8443

# Aguardar configuração
sleep 3

# Verificar configuração
echo "📋 Verificando configuração serve..."
tailscale serve status

# Habilitar Funnel
echo "🌐 Habilitando Tailscale Funnel..."
sudo tailscale funnel --https=443 on

# Aguardar ativação
sleep 3

# Verificar status final
echo "📊 Status final:"
tailscale serve status
tailscale funnel status

# Obter domínio público
DOMAIN=$(tailscale status --json | jq -r '.Self.DNSName')
echo ""
echo "🎉 Configuração concluída!"
echo "=========================="
echo "🌐 Domínio público: https://$DOMAIN"
echo "🔗 URL MCP: https://$DOMAIN/sse/"
echo ""
echo "📝 Para usar seu domínio personalizado:"
echo "1. Configure CNAME: mcp.agourakis.med.br -> $DOMAIN"
echo "2. No Tailscale Admin Console, habilite 'Custom Domain' para mcp.agourakis.med.br"
echo ""
echo "🧪 Teste:"
echo "curl -Iv https://$DOMAIN/health"
echo "curl -i -X POST https://$DOMAIN/mcp/ -H 'Accept: application/json, text/event-stream' -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"id\":\"1\",\"method\":\"initialize\",\"params\":{}}'"