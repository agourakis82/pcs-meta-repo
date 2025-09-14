#!/bin/bash
# Deploy Script - Arquitetura de Produção PCS Meta Repo
# Senior SRE/DevOps deployment automation

set -euo pipefail

echo "🚀 Iniciando deploy da arquitetura de produção..."

# 1. Backup configurações atuais
echo "📦 Backup de configurações..."
sudo cp /etc/cloudflared/config.yml /etc/cloudflared/config.yml.backup-$(date +%Y%m%d-%H%M%S)
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup-$(date +%Y%m%d-%H%M%S)

# 2. Deploy nova configuração Cloudflare Tunnel
echo "🌩️ Atualizando Cloudflare Tunnel..."
sudo cp cloudflared-production.yml /etc/cloudflared/config.yml
sudo chown root:root /etc/cloudflared/config.yml
sudo chmod 644 /etc/cloudflared/config.yml

# 3. Deploy configuração nginx
echo "🔧 Atualizando nginx..."
sudo cp nginx-production.conf /etc/nginx/sites-available/agourakis-production
sudo ln -sf /etc/nginx/sites-available/agourakis-production /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 4. Teste de sintaxe nginx
echo "✅ Testando configuração nginx..."
sudo nginx -t

# 5. Criar diretórios e logs
echo "📁 Preparando estrutura de arquivos..."
sudo mkdir -p /var/www/pcs-meta-repo
sudo mkdir -p /var/log/nginx
sudo touch /var/log/nginx/agourakis-access.log
sudo touch /var/log/nginx/agourakis-error.log  
sudo touch /var/log/nginx/mcp-access.log
sudo touch /var/log/nginx/mcp-error.log
sudo chown -R www-data:www-data /var/www/pcs-meta-repo
sudo chown -R www-data:adm /var/log/nginx

# 6. Deploy website (se existir)
if [ -d "website" ] || [ -f "index.html" ]; then
    echo "🌐 Deployando website..."
    sudo cp -r website/* /var/www/pcs-meta-repo/ 2>/dev/null || true
    sudo cp index.html /var/www/pcs-meta-repo/ 2>/dev/null || true
fi

# 7. Reload serviços
echo "🔄 Recarregando serviços..."
sudo systemctl reload nginx
sudo systemctl restart cloudflared

# 8. Verificações pós-deploy
echo "🔍 Verificações pós-deploy..."
sleep 5

# Teste nginx local
curl -sI http://127.0.0.1:8080 | head -1
curl -sI http://127.0.0.1:8081 | head -1

# Status serviços
sudo systemctl is-active nginx
sudo systemctl is-active cloudflared
sudo systemctl is-active ragpp-mcp-server

echo ""
echo "✅ Deploy concluído com sucesso!"
echo ""
echo "🌍 Arquitetura de produção ativa:"
echo "   • www.agourakis.med.br  → Site principal"
echo "   • agourakis.med.br      → Redirect 301 → www"  
echo "   • mcp.agourakis.med.br  → API/MCP"
echo ""
echo "📊 Próximos passos:"
echo "   1. Aguardar propagação DNS (2-5 min)"
echo "   2. Testar todos os domínios"
echo "   3. Configurar monitoramento"
echo "   4. Validar ChatGPT Actions"