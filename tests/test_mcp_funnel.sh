#!/bin/bash
# Script de teste para Tailscale Funnel + MCP Server
# Execute após configurar o Funnel

set -e

echo "🧪 Testando Tailscale Funnel + MCP Server"
echo "=========================================="

# Obter domínio Tailscale
DOMAIN=$(tailscale status --json | jq -r '.Self.DNSName' 2>/dev/null || echo "")

if [ -z "$DOMAIN" ]; then
    echo "❌ Erro: Tailscale não está conectado ou jq não está instalado"
    echo "Execute: sudo tailscale up --ssh"
    exit 1
fi

echo "🌐 Domínio detectado: $DOMAIN"
echo ""

# Teste 1: Status do Tailscale
echo "📊 1. Verificando status do Tailscale..."
tailscale serve status
echo ""
tailscale funnel status
echo ""

# Teste 2: Conectividade básica
echo "🌐 2. Testando conectividade básica..."
echo "Testando: https://$DOMAIN/health"
if curl -s -I https://$DOMAIN/health | grep -q "200"; then
    echo "✅ Health check: OK"
else
    echo "❌ Health check: FALHA"
fi
echo ""

# Teste 3: MCP Initialize
echo "🤖 3. Testando MCP Initialize..."
RESPONSE=$(curl -s -X POST https://$DOMAIN/mcp/ \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{}}' 2>/dev/null)

if echo "$RESPONSE" | grep -q "mcp-session-id"; then
    echo "✅ MCP Initialize: OK"
    SESSION_ID=$(echo "$RESPONSE" | grep -o 'mcp-session-id: [^"]*' | cut -d' ' -f2 | tr -d '\r')
    echo "📝 Session ID: $SESSION_ID"
else
    echo "❌ MCP Initialize: FALHA"
    echo "Resposta: $RESPONSE"
    exit 1
fi
echo ""

# Teste 4: MCP SSE
echo "📡 4. Testando MCP SSE..."
SSE_TEST=$(timeout 5 curl -s -N https://$DOMAIN/sse/ \
  -H "Accept: text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -H "mcp-protocol-version: 2024-11-05" 2>/dev/null | head -n 3)

if echo "$SSE_TEST" | grep -q "event:"; then
    echo "✅ MCP SSE: OK"
    echo "Primeiras linhas SSE:"
    echo "$SSE_TEST"
else
    echo "❌ MCP SSE: FALHA"
    echo "Resposta: $SSE_TEST"
fi
echo ""

# Teste 5: Certificado SSL
echo "🔒 5. Verificando certificado SSL..."
CERT_INFO=$(curl -s -I https://$DOMAIN/health 2>/dev/null | grep -i "server\|strict-transport-security\|x-content-type-options" || echo "N/A")
if [ "$CERT_INFO" != "N/A" ]; then
    echo "✅ Certificado SSL: OK"
    echo "$CERT_INFO"
else
    echo "❌ Certificado SSL: Verificar configuração"
fi
echo ""

# Resumo
echo "📋 RESUMO DOS TESTES"
echo "===================="
echo "🌐 Domínio público: https://$DOMAIN"
echo "🔗 URL MCP para ChatGPT: https://$DOMAIN/sse/"
echo ""
echo "✅ Próximos passos:"
echo "1. Configure CNAME: mcp.agourakis.med.br -> $DOMAIN"
echo "2. No Tailscale Admin Console, habilite Custom Domain"
echo "3. Teste novamente com seu domínio personalizado"
echo "4. Configure o conector MCP no ChatGPT usando https://mcp.agourakis.med.br/sse/"