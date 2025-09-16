#!/bin/bash

# DEPRECATED: Setup MCP via Tailscale with Custom Domain
# =======================================================
# ⚠️  ESTE ARQUIVO FOI DEPRECIADO ⚠️
# 
# MIGRADO PARA: Cloudflare Tunnel (cloudflared)
# NOVO GUIA: docs/infra_cloudflare_tunnel.md
# NOVOS TEMPLATES: cloudflared/ e nginx/sites-available/
# 
# Este arquivo permanece apenas para compatibilidade histórica.
# =======================================================

# Setup MCP via Tailscale with Custom Domain (DEPRECATED)
# Configuração do servidor MCP para acesso via Tailscale e domínio personalizado

set -e

echo "🚀 Configurando MCP via Tailscale com domínio personalizado..."

# Informações do Tailscale e domínio personalizado
CUSTOM_DOMAIN="agourakis.med.br"
MCP_PORT="8000"
HTTPS_PORT="443"
HTTP_PORT="80"
MCP_SERVICE_NAME="ragpp-mcp-server"

# Obter informações dinâmicas do Tailscale (SINTAXE CORRETA)
echo "🔍 Obtendo informações do Tailscale..."
TAILSCALE_IP=$(tailscale status --json | jq -r '.Self.TailscaleIPs[0]' 2>/dev/null || echo "unknown")
TAILSCALE_DOMAIN=$(tailscale status --json | jq -r '.Self.DNSName' 2>/dev/null || echo "unknown")

echo "📋 Informações da configuração:"
echo "   Domínio Personalizado: $CUSTOM_DOMAIN"
echo "   IP Tailscale: $TAILSCALE_IP"
echo "   Domínio Tailscale: $TAILSCALE_DOMAIN"
echo "   Porta MCP: $MCP_PORT"

# 1. Verificar se o Tailscale está ativo
echo "🔍 Verificando status do Tailscale..."
if ! tailscale status &> /dev/null; then
    echo "❌ Tailscale não está ativo ou configurado corretamente"
    echo "Para corrigir:"
    echo "1. Inicie o Tailscale: sudo systemctl start tailscaled"
    echo "2. Faça login: tailscale up"
    exit 1
fi
echo "✅ Tailscale ativo"

# 2. Verificar se o serviço MCP está rodando
echo "🔍 Verificando serviço MCP..."
if ! systemctl is-active --quiet $MCP_SERVICE_NAME; then
    echo "⚠️  Serviço MCP não está ativo. Iniciando..."
    sudo systemctl start $MCP_SERVICE_NAME
    sleep 3
fi

if systemctl is-active --quiet $MCP_SERVICE_NAME; then
    echo "✅ Serviço MCP ativo"
else
    echo "❌ Falha ao iniciar serviço MCP"
    exit 1
fi

# 3. Testar conectividade local
echo "🔍 Testando conectividade local..."
if curl -s -f http://localhost:$MCP_PORT/health > /dev/null; then
    echo "✅ Servidor MCP respondendo localmente"
else
    echo "❌ Servidor MCP não está respondendo localmente"
    exit 1
fi

# 4. Limpar configurações existentes do Tailscale
echo "🔧 Limpando configurações existentes..."
tailscale serve reset 2>/dev/null || true
tailscale funnel --https=$HTTPS_PORT off 2>/dev/null || true
tailscale funnel --http=$HTTP_PORT off 2>/dev/null || true
echo "✅ Configurações anteriores limpas"

# 5. Configurar Tailscale Serve (NOVA SINTAXE)
echo "🔧 Configurando Tailscale Serve..."
echo "Tentando HTTPS primeiro..."
if tailscale serve --https=$HTTPS_PORT $MCP_PORT; then
    echo "✅ Tailscale serve HTTPS configurado"
    SERVE_PROTOCOL="https"
    SERVE_PORT=$HTTPS_PORT
else
    echo "⚠️  HTTPS falhou, tentando HTTP..."
    if tailscale serve --http=$HTTP_PORT $MCP_PORT; then
        echo "✅ Tailscale serve HTTP configurado"
        SERVE_PROTOCOL="http"
        SERVE_PORT=$HTTP_PORT
    else
        echo "❌ Falha ao configurar Tailscale serve"
        exit 1
    fi
fi

# 6. Habilitar Tailscale Funnel (NOVA SINTAXE)
echo "🔧 Habilitando Tailscale Funnel..."
if [ "$SERVE_PROTOCOL" = "https" ]; then
    if tailscale funnel --https=$HTTPS_PORT on; then
        echo "✅ Tailscale funnel HTTPS habilitado"
        FUNNEL_URL="https://$TAILSCALE_DOMAIN"
        CUSTOM_URL="https://$CUSTOM_DOMAIN"
    else
        echo "❌ Falha ao habilitar funnel HTTPS"
        echo "Tentando HTTP como alternativa..."
        tailscale serve reset
        tailscale serve --http=$HTTP_PORT $MCP_PORT
        if tailscale funnel --http=$HTTP_PORT on; then
            echo "✅ Tailscale funnel HTTP habilitado"
            FUNNEL_URL="http://$TAILSCALE_DOMAIN"
            CUSTOM_URL="http://$CUSTOM_DOMAIN"
            SERVE_PROTOCOL="http"
            SERVE_PORT=$HTTP_PORT
        else
            echo "❌ Falha ao habilitar funnel HTTP"
            exit 1
        fi
    fi
else
    if tailscale funnel --http=$HTTP_PORT on; then
        echo "✅ Tailscale funnel HTTP habilitado"
        FUNNEL_URL="http://$TAILSCALE_DOMAIN"
        CUSTOM_URL="http://$CUSTOM_DOMAIN"
    else
        echo "❌ Falha ao habilitar funnel HTTP"
        exit 1
    fi
fi

# 7. Configurar firewall para permitir acesso via Tailscale
echo "🔧 Configurando firewall..."
sudo ufw allow from 100.64.0.0/10 to any port $MCP_PORT comment "MCP via Tailscale"
echo "✅ Firewall configurado"

# 8. Criar arquivo de configuração para ChatGPT
echo "📝 Criando configuração para ChatGPT..."
cat > mcp_tailscale_config.json << EOF
{
  "mcp_server": {
    "custom_domain": "$CUSTOM_DOMAIN",
    "tailscale_ip": "$TAILSCALE_IP",
    "tailscale_domain": "$TAILSCALE_DOMAIN",
    "port": $MCP_PORT,
    "protocol": "$SERVE_PROTOCOL",
    "endpoints": {
      "health": "$CUSTOM_URL/health",
      "memory_search": "$CUSTOM_URL/memory/search",
      "memory_store": "$CUSTOM_URL/memory/store",
      "research_categories": "$CUSTOM_URL/research/categories",
      "docs": "$CUSTOM_URL/docs"
    },
    "tailscale_endpoints": {
      "health": "$FUNNEL_URL/health",
      "memory_search": "$FUNNEL_URL/memory/search",
      "memory_store": "$FUNNEL_URL/memory/store",
      "research_categories": "$FUNNEL_URL/research/categories",
      "docs": "$FUNNEL_URL/docs"
    },
    "authentication": {
      "type": "Bearer",
      "token": "wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo"
    }
  }
}
EOF

# 9. Testar acesso via Tailscale
echo "🔍 Testando acesso via Tailscale..."
sleep 5  # Aguardar propagação da configuração

if curl -s -f --connect-timeout 10 "$FUNNEL_URL/health" > /dev/null; then
    echo "✅ Acesso via Tailscale funcionando: $FUNNEL_URL"
else
    echo "⚠️  Acesso via Tailscale pode levar alguns minutos para funcionar"
    echo "   URL: $FUNNEL_URL/health"
fi

# 10. Criar script de teste atualizado
echo "📝 Criando script de teste..."
cat > test_mcp_tailscale.sh << EOF
#!/bin/bash

# Script de teste para MCP via Tailscale com domínio personalizado
CUSTOM_DOMAIN="$CUSTOM_DOMAIN"
TAILSCALE_DOMAIN="$TAILSCALE_DOMAIN"
CUSTOM_URL="$CUSTOM_URL"
FUNNEL_URL="$FUNNEL_URL"
AUTH_TOKEN="wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo"

echo "🧪 Testando MCP via Tailscale e domínio personalizado..."
echo ""

# Teste via domínio Tailscale
echo "1. Testando via domínio Tailscale:"
echo "URL: \$FUNNEL_URL/health"
curl -s "\$FUNNEL_URL/health" | jq . || echo "❌ Falhou"
echo ""

# Teste via domínio personalizado
echo "2. Testando via domínio personalizado:"
echo "URL: \$CUSTOM_URL/health"
curl -s "\$CUSTOM_URL/health" | jq . || echo "❌ Falhou ou DNS não configurado"
echo ""

# Teste de categorias de pesquisa
echo "3. Categorias de pesquisa:"
curl -s "\$FUNNEL_URL/research/categories" | jq . || echo "❌ Falhou"
echo ""

# Teste de busca na memória
echo "4. Teste de busca na memória:"
curl -s -X POST "\$FUNNEL_URL/memory/search" \\
  -H "Authorization: Bearer \$AUTH_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "PCS project", "max_results": 3}' | jq . || echo "❌ Falhou"

echo ""
echo "✅ Testes concluídos"
EOF

chmod +x test_mcp_tailscale.sh

# 11. Criar guia de configuração atualizado
echo "📝 Criando guia de configuração..."
cat > CHATGPT_TAILSCALE_SETUP.md << EOF
# Configuração MCP via Tailscale para ChatGPT

## 🌐 Informações de Acesso

- **Domínio Personalizado**: $CUSTOM_DOMAIN
- **Domínio Tailscale**: $TAILSCALE_DOMAIN
- **IP Tailscale**: $TAILSCALE_IP
- **Protocolo**: $SERVE_PROTOCOL
- **Porta MCP**: $MCP_PORT

## 🔗 URLs de Acesso

- **URL Principal**: $CUSTOM_URL
- **URL Tailscale**: $FUNNEL_URL

## 🔑 Autenticação

- **Tipo**: Bearer Token
- **Token**: wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo

## 📡 Endpoints Disponíveis

### Saúde do Sistema
\`\`\`
GET $CUSTOM_URL/health
\`\`\`

### Busca na Memória
\`\`\`
POST $CUSTOM_URL/memory/search
Headers: Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo
Body: {"query": "sua busca aqui", "max_results": 5}
\`\`\`

### Armazenar Memória
\`\`\`
POST $CUSTOM_URL/memory/store
Headers: Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo
Body: {"content": "conteúdo", "title": "título", "type": "conversation"}
\`\`\`

### Categorias de Pesquisa
\`\`\`
GET $CUSTOM_URL/research/categories
\`\`\`

## 🧪 Teste Rápido

Execute o script de teste:
\`\`\`bash
./test_mcp_tailscale.sh
\`\`\`

## 🔧 Configuração no ChatGPT

1. Acesse as configurações de Custom GPT
2. Configure a ação com a URL base: $CUSTOM_URL
3. Adicione o header de autenticação: Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo
4. Importe o schema OpenAPI de: $CUSTOM_URL/openapi.json

## 🌐 Configuração DNS Necessária

Para usar o domínio personalizado $CUSTOM_DOMAIN, crie este registro DNS:

\`\`\`
Tipo: CNAME
Nome: $CUSTOM_DOMAIN
Valor: $TAILSCALE_DOMAIN
\`\`\`

## 📱 Acesso de Outros Dispositivos

Qualquer dispositivo na sua rede Tailscale pode acessar:
- **Desktop**: $CUSTOM_URL
- **Mobile**: $CUSTOM_URL
- **Outros**: $CUSTOM_URL

## 🔒 Segurança

- Acesso via Tailscale funnel (público mas seguro)
- Autenticação via Bearer Token
- Firewall configurado para permitir apenas tráfego Tailscale
- HTTPS habilitado (se suportado)

## 🔧 Comandos de Gerenciamento

\`\`\`bash
# Verificar status
tailscale serve status
tailscale funnel status

# Parar funnel
tailscale funnel --$SERVE_PROTOCOL=$SERVE_PORT off

# Resetar configuração
tailscale serve reset
\`\`\`
EOF

# 12. Mostrar status atual
echo ""
echo "📊 Status atual da configuração:"
echo "================================"
tailscale serve status
echo ""
tailscale funnel status
echo ""

echo "🎉 Configuração MCP via Tailscale concluída!"
echo "============================================="
echo ""
echo "📋 Arquivos criados:"
echo "   - mcp_tailscale_config.json (configuração JSON)"
echo "   - test_mcp_tailscale.sh (script de teste)"
echo "   - CHATGPT_TAILSCALE_SETUP.md (guia completo)"
echo ""
echo "🔗 URLs de acesso:"
echo "   - Domínio personalizado: $CUSTOM_URL"
echo "   - Domínio Tailscale: $FUNNEL_URL"
echo ""
echo "🧪 Endpoints principais:"
echo "   - Saúde: $CUSTOM_URL/health"
echo "   - Docs: $CUSTOM_URL/docs"
echo "   - Memória: $CUSTOM_URL/memory/search"
echo ""
echo "🌐 Configuração DNS necessária:"
echo "   Tipo: CNAME"
echo "   Nome: $CUSTOM_DOMAIN"
echo "   Valor: $TAILSCALE_DOMAIN"
echo ""
echo "🧪 Para testar:"
echo "   ./test_mcp_tailscale.sh"
echo ""
echo "📖 Para configurar no ChatGPT:"
echo "   Consulte: CHATGPT_TAILSCALE_SETUP.md"
echo ""
echo "🔧 Comandos úteis:"
echo "   - Ver status: tailscale serve status && tailscale funnel status"
echo "   - Parar funnel: tailscale funnel --$SERVE_PROTOCOL=$SERVE_PORT off"
echo "   - Resetar: tailscale serve reset"
echo ""
echo "✅ Seu MCP server está agora acessível publicamente via Tailscale funnel!"
