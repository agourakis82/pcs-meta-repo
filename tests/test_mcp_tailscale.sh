#!/bin/bash

# DEPRECATED: Script de teste para MCP via Tailscale
# ===================================================
# ⚠️  ESTE ARQUIVO FOI DEPRECIADO ⚠️
# 
# MIGRADO PARA: Cloudflare Tunnel (cloudflared)
# TESTES AGORA EM: docs/infra_cloudflare_tunnel.md
# 
# Novos endpoints de teste:
# - https://agourakis.med.br/
# - https://mcp.agourakis.med.br/health
# 
# Este arquivo permanece apenas para referência histórica.
# ===================================================

# Script de teste para MCP via Tailscale (DEPRECATED)
TAILSCALE_DOMAIN="demetriospcs.tail21cbc4.ts.net"
MCP_PORT="8000"
AUTH_TOKEN="wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo"

echo "🧪 Testando MCP via Tailscale..."

# Teste de saúde
echo "1. Teste de saúde:"
curl -s http://$TAILSCALE_DOMAIN:$MCP_PORT/health | jq .

# Teste de categorias de pesquisa
echo -e "\n2. Categorias de pesquisa:"
curl -s http://$TAILSCALE_DOMAIN:$MCP_PORT/research/categories | jq .

# Teste de busca na memória
echo -e "\n3. Teste de busca na memória:"
curl -s -X POST http://$TAILSCALE_DOMAIN:$MCP_PORT/memory/search \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "PCS project", "max_results": 3}' | jq .

echo -e "\n✅ Testes concluídos"
