#!/bin/bash

# Script de Aplicação Cloudflare Tunnel - PCS Meta-Repo
# Execute este script após fazer 'cloudflared tunnel login'

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Aplicando Configuração Cloudflare Tunnel${NC}"
echo "=============================================="

# Verificar se está autenticado
if [[ ! -f ~/.cloudflared/cert.pem ]]; then
    echo -e "${RED}❌ Não autenticado com Cloudflare${NC}"
    echo "Execute primeiro: cloudflared tunnel login"
    exit 1
fi

echo -e "${GREEN}✅ Autenticado com Cloudflare${NC}"

# Passo 1: Criar túnel
echo -e "\n${BLUE}📋 Passo 1: Criando túnel...${NC}"
TUNNEL_NAME="pcs-tunnel"

# Verificar se túnel já existe
if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo -e "${YELLOW}⚠️  Túnel $TUNNEL_NAME já existe${NC}"
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
else
    echo "Criando túnel $TUNNEL_NAME..."
    cloudflared tunnel create $TUNNEL_NAME
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
fi

echo -e "${GREEN}✅ Túnel ID: $TUNNEL_ID${NC}"

# Passo 2: Configurar DNS
echo -e "\n${BLUE}📋 Passo 2: Configurando DNS...${NC}"

echo "Configurando DNS para agourakis.med.br..."
cloudflared tunnel route dns $TUNNEL_NAME agourakis.med.br || echo "DNS agourakis.med.br já configurado"

echo "Configurando DNS para mcp.agourakis.med.br..."
cloudflared tunnel route dns $TUNNEL_NAME mcp.agourakis.med.br || echo "DNS mcp.agourakis.med.br já configurado"

echo -e "${GREEN}✅ DNS configurado${NC}"

# Passo 3: Criar configuração
echo -e "\n${BLUE}📋 Passo 3: Criando configuração...${NC}"

# Substituir UUID no template
sed "s/<UUID>/$TUNNEL_ID/g" cloudflared/config.yml > /tmp/config.yml

# Copiar para local do sistema
sudo mkdir -p /etc/cloudflared
sudo cp /tmp/config.yml /etc/cloudflared/config.yml

# Copiar credenciais
if [[ -f ~/.cloudflared/$TUNNEL_ID.json ]]; then
    sudo cp ~/.cloudflared/$TUNNEL_ID.json /etc/cloudflared/
    sudo chmod 600 /etc/cloudflared/$TUNNEL_ID.json
    echo -e "${GREEN}✅ Configuração criada${NC}"
else
    echo -e "${RED}❌ Arquivo de credenciais não encontrado: ~/.cloudflared/$TUNNEL_ID.json${NC}"
    exit 1
fi

# Passo 4: Instalar como serviço
echo -e "\n${BLUE}📋 Passo 4: Instalando serviço...${NC}"

sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# Aguardar um pouco para o serviço iniciar
sleep 5

# Verificar status
if systemctl is-active --quiet cloudflared; then
    echo -e "${GREEN}✅ Serviço cloudflared ativo${NC}"
else
    echo -e "${YELLOW}⚠️  Verificando status do serviço...${NC}"
    sudo systemctl status cloudflared
fi

# Passo 5: Testar configuração
echo -e "\n${BLUE}📋 Passo 5: Testando configuração...${NC}"

echo "Aguardando propagação DNS (30 segundos)..."
sleep 30

echo -e "\n${BLUE}🧪 Testando endpoints públicos:${NC}"

# Teste website
if curl -s -f --connect-timeout 10 "https://agourakis.med.br/" > /dev/null; then
    echo -e "  Website: ${GREEN}✅ https://agourakis.med.br/${NC}"
else
    echo -e "  Website: ${YELLOW}⚠️  Aguardando propagação DNS${NC}"
fi

# Teste MCP API
if curl -s -f --connect-timeout 10 "https://mcp.agourakis.med.br/health" > /dev/null; then
    echo -e "  MCP API: ${GREEN}✅ https://mcp.agourakis.med.br/health${NC}"
else
    echo -e "  MCP API: ${YELLOW}⚠️  Aguardando propagação DNS${NC}"
fi

echo -e "\n${GREEN}🎉 Configuração aplicada com sucesso!${NC}"
echo ""
echo -e "${BLUE}📋 Próximos passos:${NC}"
echo "1. Aguardar propagação DNS (pode levar até 24h, normalmente poucos minutos)"
echo "2. Testar endpoints: ./test_cloudflare_tunnel.sh"
echo "3. Verificar logs: sudo journalctl -u cloudflared -f"
echo ""
echo -e "${BLUE}🌐 URLs públicas:${NC}"
echo "  - Website: https://agourakis.med.br/"
echo "  - MCP API: https://mcp.agourakis.med.br/health"
echo "  - Search: https://mcp.agourakis.med.br/search"
echo "  - SSE Stream: https://mcp.agourakis.med.br/sse/"