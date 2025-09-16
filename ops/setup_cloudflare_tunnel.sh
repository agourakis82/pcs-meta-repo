#!/bin/bash

# Script de configuração rápida para Cloudflare Tunnel
# Aplica as configurações do repositório para o sistema
# Documentação: docs/infra_cloudflare_tunnel.md

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Cloudflare Tunnel Quick Setup${NC}"
echo "=================================="

# Verificar se está rodando como root para algumas operações
check_root() {
    if [[ $EUID -eq 0 ]]; then
        echo -e "${YELLOW}⚠️  Rodando como root - cuidado com permissões${NC}"
    fi
}

# Função para aplicar configurações Nginx
setup_nginx() {
    echo -e "\n${BLUE}📋 Configurando Nginx...${NC}"
    
    # Verificar se nginx está instalado
    if ! command -v nginx &> /dev/null; then
        echo -e "${RED}❌ Nginx não encontrado${NC}"
        echo "Instale primeiro: sudo apt install nginx"
        return 1
    fi
    
    # Copiar configurações se existirem
    if [[ -f "nginx/sites-available/site.conf" && -f "nginx/sites-available/mcp.conf" ]]; then
        echo "Copiando configurações Nginx..."
        
        # Sites available
        sudo cp nginx/sites-available/site.conf /etc/nginx/sites-available/ 2>/dev/null || {
            echo -e "${YELLOW}⚠️  Copiando manualmente (sem sudo)${NC}"
            echo "Execute: sudo cp nginx/sites-available/*.conf /etc/nginx/sites-available/"
        }
        
        # Habilitar sites (criar symlinks)
        sudo ln -sf /etc/nginx/sites-available/site.conf /etc/nginx/sites-enabled/ 2>/dev/null || true
        sudo ln -sf /etc/nginx/sites-available/mcp.conf /etc/nginx/sites-enabled/ 2>/dev/null || true
        
        # Testar configuração
        if sudo nginx -t 2>/dev/null; then
            echo -e "${GREEN}✅ Configuração Nginx válida${NC}"
            
            # Recarregar se possível
            sudo systemctl reload nginx 2>/dev/null && echo -e "${GREEN}✅ Nginx recarregado${NC}" || {
                echo -e "${YELLOW}⚠️  Execute manualmente: sudo systemctl reload nginx${NC}"
            }
        else
            echo -e "${RED}❌ Erro na configuração Nginx${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  Arquivos de configuração Nginx não encontrados${NC}"
        echo "Verifique se os arquivos existem em nginx/sites-available/"
        return 1
    fi
}

# Função para configurar cloudflared
setup_cloudflared() {
    echo -e "\n${BLUE}📋 Configurando Cloudflare Tunnel...${NC}"
    
    # Verificar se cloudflared está instalado
    if ! command -v cloudflared &> /dev/null; then
        echo -e "${RED}❌ cloudflared não encontrado${NC}"
        echo "Instale primeiro seguindo: docs/infra_cloudflare_tunnel.md"
        return 1
    fi
    
    # Verificar se config template existe
    if [[ -f "cloudflared/config.yml" ]]; then
        echo "Template de configuração encontrado"
        
        # Mostrar instruções para copiar
        echo -e "${YELLOW}📝 Para aplicar a configuração:${NC}"
        echo "1. sudo cp cloudflared/config.yml /etc/cloudflared/"
        echo "2. Editar /etc/cloudflared/config.yml e substituir <UUID>"
        echo "3. sudo cp ~/.cloudflared/<UUID>.json /etc/cloudflared/"
        echo "4. sudo cloudflared service install"
        echo "5. sudo systemctl enable --now cloudflared"
        
        # Verificar se já está configurado
        if [[ -f "/etc/cloudflared/config.yml" ]]; then
            echo -e "${GREEN}✅ Configuração já existe em /etc/cloudflared/${NC}"
            
            # Verificar status do serviço
            if systemctl is-active --quiet cloudflared 2>/dev/null; then
                echo -e "${GREEN}✅ Serviço cloudflared está ativo${NC}"
            else
                echo -e "${YELLOW}⚠️  Serviço cloudflared não está ativo${NC}"
                echo "Execute: sudo systemctl start cloudflared"
            fi
        fi
    else
        echo -e "${RED}❌ Template cloudflared/config.yml não encontrado${NC}"
        return 1
    fi
}

# Função para testar conectividade
test_setup() {
    echo -e "\n${BLUE}🧪 Testando configuração...${NC}"
    
    # Testar serviços locais
    echo "Testando serviços locais:"
    
    # MCP Server (porta 8000)
    if curl -s -f --connect-timeout 5 "127.0.0.1:8000/health" > /dev/null; then
        echo -e "  MCP Server (8000): ${GREEN}✅ OK${NC}"
    else
        echo -e "  MCP Server (8000): ${RED}❌ FAIL${NC}"
        echo "    Execute: cd /path/to/project && python -m uvicorn ragpp.ragpp_web_server:app --host 127.0.0.1 --port 8000"
    fi
    
    # Nginx (portas 8080 e 8081)
    if curl -s -f --connect-timeout 5 "127.0.0.1:8080/" > /dev/null; then
        echo -e "  Nginx Website (8080): ${GREEN}✅ OK${NC}"
    else
        echo -e "  Nginx Website (8080): ${RED}❌ FAIL${NC}"
    fi
    
    if curl -s -f --connect-timeout 5 "127.0.0.1:8081/health" > /dev/null; then
        echo -e "  Nginx MCP Proxy (8081): ${GREEN}✅ OK${NC}"
    else
        echo -e "  Nginx MCP Proxy (8081): ${RED}❌ FAIL${NC}"
    fi
    
    # Testar endpoints públicos (se DNS estiver configurado)
    echo -e "\nTestando endpoints públicos:"
    
    if curl -s -f --connect-timeout 10 "https://agourakis.med.br/" > /dev/null; then
        echo -e "  Website público: ${GREEN}✅ OK${NC}"
    else
        echo -e "  Website público: ${YELLOW}⚠️  Aguardando DNS/tunnel${NC}"
    fi
    
    if curl -s -f --connect-timeout 10 "https://mcp.agourakis.med.br/health" > /dev/null; then
        echo -e "  MCP público: ${GREEN}✅ OK${NC}"
    else
        echo -e "  MCP público: ${YELLOW}⚠️  Aguardando DNS/tunnel${NC}"
    fi
}

# Função para mostrar status geral
show_status() {
    echo -e "\n${BLUE}📊 Status Geral${NC}"
    echo "==================="
    
    # Status dos serviços
    echo -e "\n${YELLOW}Serviços:${NC}"
    systemctl is-active nginx 2>/dev/null && echo -e "  nginx: ${GREEN}✅ active${NC}" || echo -e "  nginx: ${RED}❌ inactive${NC}"
    systemctl is-active cloudflared 2>/dev/null && echo -e "  cloudflared: ${GREEN}✅ active${NC}" || echo -e "  cloudflared: ${RED}❌ inactive${NC}"
    
    # Arquivos de configuração
    echo -e "\n${YELLOW}Configurações:${NC}"
    [[ -f "/etc/nginx/sites-enabled/site.conf" ]] && echo -e "  Nginx site: ${GREEN}✅ enabled${NC}" || echo -e "  Nginx site: ${RED}❌ missing${NC}"
    [[ -f "/etc/nginx/sites-enabled/mcp.conf" ]] && echo -e "  Nginx MCP: ${GREEN}✅ enabled${NC}" || echo -e "  Nginx MCP: ${RED}❌ missing${NC}"
    [[ -f "/etc/cloudflared/config.yml" ]] && echo -e "  Cloudflared: ${GREEN}✅ configured${NC}" || echo -e "  Cloudflared: ${RED}❌ missing${NC}"
    
    echo -e "\n${YELLOW}Próximos passos:${NC}"
    echo "1. Verificar logs: sudo journalctl -u cloudflared -f"
    echo "2. Testar endpoints: ./test_cloudflare_tunnel.sh"
    echo "3. Documentação: docs/infra_cloudflare_tunnel.md"
}

# Menu principal
main() {
    check_root
    
    echo -e "\n${YELLOW}Escolha uma opção:${NC}"
    echo "1. Configurar Nginx"
    echo "2. Configurar Cloudflare Tunnel"  
    echo "3. Testar configuração"
    echo "4. Mostrar status geral"
    echo "5. Fazer tudo (1-4)"
    echo "0. Sair"
    
    read -p "Opção [0-5]: " choice
    
    case $choice in
        1) setup_nginx ;;
        2) setup_cloudflared ;;
        3) test_setup ;;
        4) show_status ;;
        5) 
            setup_nginx
            setup_cloudflared
            test_setup
            show_status
            ;;
        0) echo "Saindo..."; exit 0 ;;
        *) echo -e "${RED}Opção inválida${NC}"; main ;;
    esac
    
    echo -e "\n${YELLOW}Pressione Enter para continuar...${NC}"
    read
    main
}

# Verificar se é execução não-interativa
if [[ "$1" == "--auto" ]]; then
    echo "Modo automático - executando todas as configurações..."
    setup_nginx
    setup_cloudflared
    test_setup
    show_status
else
    main
fi