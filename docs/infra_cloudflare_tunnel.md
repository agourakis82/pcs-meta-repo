# Cloudflare Tunnel — Operação

> **Substitui**: Tailscale Funnel → agora usamos Cloudflare Tunnel (`cloudflared`) para exposição pública HTTPS.

## 📋 Visão Geral

Este guia configura **Cloudflare Tunnel** para expor publicamente:

- `https://agourakis.med.br` → Website estático (Nginx loopback)
- `https://mcp.agourakis.med.br` → MCP API e SSE (Nginx proxy → Uvicorn)

**Vantagens vs Tailscale Funnel:**

- ✅ Domínio personalizado sem limitações
- ✅ TLS automático e renovação via Cloudflare
- ✅ DDoS protection e CDN gratuito
- ✅ Latência global otimizada
- ✅ Sem dependência de conta Tailscale paga

---

## 🛠️ Pré-requisitos

1. **Zona DNS** `agourakis.med.br` configurada na Cloudflare (plano free OK)
2. **WSL/Ubuntu** com systemd ou Linux nativo
3. **Nginx** instalado e rodando
4. **MCP Server** (Uvicorn) rodando em `127.0.0.1:8000`

---

## 📦 Instalação

### 1. Instalar cloudflared

```bash
# Via repositório oficial (recomendado)
curl -fsSL https://pkg.cloudflare.com/install.sh | sudo bash
sudo apt update && sudo apt install -y cloudflared

# Verificar instalação
cloudflared version
```

### 2. Autenticar com Cloudflare

```bash
# Login via browser (abre automaticamente)
cloudflared tunnel login

# Verificar credenciais
ls -la ~/.cloudflared/
```

### 3. Criar túnel

```bash
# Criar túnel nomeado
cloudflared tunnel create pcs-tunnel

# Anotar o UUID exibido (exemplo: a1b2c3d4-e5f6-7890-abcd-1234567890ef)
# Verificar arquivo de credenciais criado
ls -la ~/.cloudflared/
```

### 4. Configurar DNS

```bash
# Adicionar registros DNS (automatizado)
cloudflared tunnel route dns pcs-tunnel agourakis.med.br
cloudflared tunnel route dns pcs-tunnel mcp.agourakis.med.br

# Verificar no dashboard Cloudflare:
# DNS > Records: agourakis.med.br CNAME pcs-tunnel.cfargotunnel.com
```

---

## ⚙️ Configuração

### 1. Arquivo de configuração principal

```bash
# Copiar template do repositório
sudo cp cloudflared/config.yml /etc/cloudflared/config.yml

# Editar e substituir <UUID> pelo UUID real do túnel
sudo nano /etc/cloudflared/config.yml
```

**Exemplo de `/etc/cloudflared/config.yml`:**

```yaml
tunnel: pcs-tunnel
credentials-file: /etc/cloudflared/a1b2c3d4-e5f6-7890-abcd-1234567890ef.json

ingress:
  - hostname: agourakis.med.br
    service: http://127.0.0.1:8080    # Nginx website

  - hostname: mcp.agourakis.med.br
    service: http://127.0.0.1:8081    # Nginx proxy MCP

  - service: http_status:404
```

### 2. Copiar credenciais

```bash
# Copiar credenciais para local do sistema
sudo cp ~/.cloudflared/<UUID>.json /etc/cloudflared/
sudo chown root:root /etc/cloudflared/<UUID>.json
sudo chmod 600 /etc/cloudflared/<UUID>.json
```

### 3. Configurar Nginx (loopback)

```bash
# Habilitar sites (vhosts loopback)
sudo ln -sf $PWD/nginx/sites-available/site.conf /etc/nginx/sites-enabled/
sudo ln -sf $PWD/nginx/sites-available/mcp.conf /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Recarregar
sudo systemctl reload nginx
```

### 4. Instalar como serviço

```bash
# Instalar serviço systemd
sudo cloudflared service install

# Habilitar e iniciar
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# Verificar status
sudo systemctl status cloudflared
```

---

## 🧪 Testes

### 1. Verificação básica

```bash
# Website principal
curl -I https://agourakis.med.br/

# MCP Health check
curl -I https://mcp.agourakis.med.br/health

# MCP API (exemplo)
curl -X POST https://mcp.agourakis.med.br/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "max_results": 3}'
```

### 2. Teste SSE (Server-Sent Events)

```bash
# Stream de eventos (Ctrl+C para parar)
curl -N -H "Accept: text/event-stream" \
  https://mcp.agourakis.med.br/sse/
```

### 3. Verificação de DNS

```bash
# Verificar resolução DNS
nslookup agourakis.med.br
nslookup mcp.agourakis.med.br

# Verificar propagação global
dig agourakis.med.br
dig mcp.agourakis.med.br
```

---

## 🔧 Operação e Manutenção

### Logs e Monitoramento

```bash
# Logs do túnel
sudo journalctl -u cloudflared -f

# Logs do Nginx
sudo tail -f /var/log/nginx/mcp_access.log
sudo tail -f /var/log/nginx/site_access.log

# Status do túnel
cloudflared tunnel info pcs-tunnel
```

### Comandos Úteis

```bash
# Reiniciar túnel
sudo systemctl restart cloudflared

# Parar/iniciar
sudo systemctl stop cloudflared
sudo systemctl start cloudflared

# Testar configuração
cloudflared tunnel --config /etc/cloudflared/config.yml ingress validate

# Teste manual (debug)
sudo cloudflared tunnel --config /etc/cloudflared/config.yml run pcs-tunnel
```

### Renovação TLS

- ✅ **Automático**: Cloudflare renova certificados automaticamente
- ✅ **Sem ação necessária**: Edge termina TLS; Nginx só recebe HTTP loopback
- ✅ **Monitoramento**: Verificar dashboard Cloudflare para status SSL

---

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Túnel não conecta

```bash
# Verificar credenciais
sudo ls -la /etc/cloudflared/
sudo cloudflared tunnel list

# Testar conectividade
sudo cloudflared tunnel --config /etc/cloudflared/config.yml run pcs-tunnel
```

#### 2. DNS não resolve

```bash
# Aguardar propagação (até 24h, normalmente poucos minutos)
dig @8.8.8.8 agourakis.med.br
dig @1.1.1.1 mcp.agourakis.med.br

# Verificar no dashboard Cloudflare: DNS > Records
```

#### 3. Nginx erro 502/503

```bash
# Verificar se serviços estão rodando
sudo systemctl status nginx
curl 127.0.0.1:8000/health  # MCP Server
curl 127.0.0.1:8080/        # Website
curl 127.0.0.1:8081/health  # Nginx proxy

# Verificar logs
sudo tail -f /var/log/nginx/mcp_error.log
```

#### 4. CORS errors

```bash
# Verificar headers no browser DevTools
# Ajustar configuração CORS no nginx/sites-available/mcp.conf se necessário
```

### Verificação de Saúde

```bash
#!/bin/bash
echo "🔍 Cloudflare Tunnel Health Check"
echo "================================="

echo "1. Túnel Status:"
sudo systemctl is-active cloudflared

echo "2. DNS Resolution:"
nslookup agourakis.med.br | grep -A1 "Non-authoritative"
nslookup mcp.agourakis.med.br | grep -A1 "Non-authoritative"

echo "3. HTTPS Endpoints:"
curl -s -o /dev/null -w "%{http_code}" https://agourakis.med.br/
echo " - Website"
curl -s -o /dev/null -w "%{http_code}" https://mcp.agourakis.med.br/health
echo " - MCP API"

echo "4. Local Services:"
curl -s -o /dev/null -w "%{http_code}" 127.0.0.1:8000/health
echo " - Uvicorn MCP"
curl -s -o /dev/null -w "%{http_code}" 127.0.0.1:8080/
echo " - Nginx Website"
curl -s -o /dev/null -w "%{http_code}" 127.0.0.1:8081/health
echo " - Nginx MCP Proxy"
```

---

## 📚 Recursos Adicionais

- **Cloudflare Tunnel Docs**: <https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/>
- **Dashboard**: <https://dash.cloudflare.com/> → Zero Trust → Access → Tunnels
- **Nginx Proxy**: <https://nginx.org/en/docs/http/ngx_http_proxy_module.html>

---

## 🔄 Migração do Tailscale

**Arquivos depreciados (mantidos por compatibilidade):**

- `fix_tailscale_funnel.sh` → Use este guia
- `setup_tailscale_funnel.sh` → Use este guia  
- `GUIA_CONFIGURACAO_SSH_TAILSCALE.md` → Use este guia

**Vantagens da migração:**

- ✅ Domínio personalizado sem limitações de conta
- ✅ Performance e latência globais melhores  
- ✅ DDoS protection incluído
- ✅ Configuração mais simples e confiável
