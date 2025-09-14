#!/bin/bash

# Script de teste para MCP via Cloudflare Tunnel
# Testa os novos endpoints HTTPS públicos
# Documentação: docs/infra_cloudflare_tunnel.md

set -e

# Configurações
WEBSITE_URL="https://agourakis.med.br"
MCP_URL="https://mcp.agourakis.med.br"

# Colors para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Teste MCP via Cloudflare Tunnel${NC}"
echo "=================================="

# Função para testar endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local timeout="${3:-10}"
    
    echo -n "Testing $name... "
    
    if curl -s -f --connect-timeout "$timeout" "$url" > /dev/null; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

# Função para teste com output
test_with_output() {
    local name="$1"
    local url="$2"
    local timeout="${3:-10}"
    
    echo -e "${BLUE}Testing $name:${NC}"
    
    local response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}" --connect-timeout "$timeout" "$url" 2>/dev/null || echo "CURL_ERROR")
    
    if echo "$response" | grep -q "CURL_ERROR"; then
        echo -e "${RED}❌ Connection failed${NC}"
        return 1
    fi
    
    local http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    local time_total=$(echo "$response" | grep "TIME:" | cut -d: -f2)
    local body=$(echo "$response" | sed '/HTTP_CODE:/,$d')
    
    if [[ "$http_code" == "200" ]]; then
        echo -e "${GREEN}✅ HTTP $http_code (${time_total}s)${NC}"
        if [[ ${#body} -gt 100 ]]; then
            echo "Response (first 100 chars): ${body:0:100}..."
        else
            echo "Response: $body"
        fi
        return 0
    else
        echo -e "${RED}❌ HTTP $http_code (${time_total}s)${NC}"
        return 1
    fi
}

echo -e "\n${YELLOW}1. Testes básicos de conectividade${NC}"

# Testes básicos
test_endpoint "Website" "$WEBSITE_URL/"
test_endpoint "MCP Health" "$MCP_URL/health"
test_endpoint "MCP Test" "$MCP_URL/test"

echo -e "\n${YELLOW}2. Testes detalhados com output${NC}"

# Testes com output
test_with_output "MCP Health (detailed)" "$MCP_URL/health" 5
test_with_output "MCP Test (detailed)" "$MCP_URL/test" 5

echo -e "\n${YELLOW}3. Teste de API Search${NC}"

# Teste de POST para search
echo -e "${BLUE}Testing MCP Search API:${NC}"
search_response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -X POST "$MCP_URL/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "machine learning", "max_results": 3}' \
    --connect-timeout 30 2>/dev/null || echo "CURL_ERROR")

if echo "$search_response" | grep -q "CURL_ERROR"; then
    echo -e "${RED}❌ Search API connection failed${NC}"
else
    http_code=$(echo "$search_response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$search_response" | sed '/HTTP_CODE:/,$d')
    
    if [[ "$http_code" == "200" ]]; then
        echo -e "${GREEN}✅ Search API HTTP $http_code${NC}"
        echo "Response: ${body:0:200}..."
    else
        echo -e "${RED}❌ Search API HTTP $http_code${NC}"
    fi
fi

echo -e "\n${YELLOW}4. Teste SSE (Server-Sent Events)${NC}"

# Teste SSE (apenas por alguns segundos)
echo -e "${BLUE}Testing SSE Stream (5 segundos):${NC}"
timeout 5 curl -N -H "Accept: text/event-stream" "$MCP_URL/sse/" 2>/dev/null && echo -e "\n${GREEN}✅ SSE stream working${NC}" || echo -e "${RED}❌ SSE stream failed${NC}"

echo -e "\n${YELLOW}5. Verificação DNS${NC}"

# Verificar resolução DNS
echo -e "${BLUE}DNS Resolution:${NC}"
nslookup agourakis.med.br | grep -A1 "Non-authoritative" || echo "DNS resolution might be pending"
nslookup mcp.agourakis.med.br | grep -A1 "Non-authoritative" || echo "DNS resolution might be pending"

echo -e "\n${BLUE}🏁 Teste concluído!${NC}"
echo "Para mais informações: docs/infra_cloudflare_tunnel.md"