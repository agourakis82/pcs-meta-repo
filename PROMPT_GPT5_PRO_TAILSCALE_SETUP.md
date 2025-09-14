# 🚀 PROMPT PARA GPT-5 PRO: Configuração Completa RAG++ + MCP + Tailscale

## 🎯 OBJETIVO PRINCIPAL
Configure completamente o sistema RAG++ para integração com ChatGPT via MCP (Model Context Protocol) usando Tailscale Funnel para exposição HTTPS pública, resolvendo todos os problemas de conectividade identificados.

## 📊 CONTEXTO ATUAL (IMPORTANTE - LEIA COMPLETAMENTE)

### ✅ COMPONENTES FUNCIONANDO
1. **FastAPI Server** (porta 8000) - Funcionando localmente
2. **Nginx Reverse Proxy** (porta 8443) - HTTPS com Let's Encrypt
3. **MCP Architecture** - HTTP + SSE transport implementado
4. **Scripts de Configuração** - SSH, Tailscale, testes criados

### ❌ PROBLEMAS PENDENTES
1. **Tailscale Funnel** - Não configurado (exit code 2)
2. **Domínio Customizado** - CNAME não configurado
3. **ChatGPT Connector** - Não integrado

### 🔧 INFRAESTRUTURA
- **Servidor Linux:** 192.168.4.198 (Ubuntu/Debian)
- **UDM Pro:** 192.168.3.1 (porta 443 bloqueada)
- **Domínio:** mcp.agourakis.med.br
- **Tailscale:** demetriospcs.tail21cbc4.ts.net

## 📋 TAREFAS ESPECÍFICAS (EXECUTE EM ORDEM)

### FASE 1: DIAGNÓSTICO DETALHADO
```bash
# 1. Verificar status atual do servidor
ssh user@192.168.4.198
sudo systemctl status nginx
sudo systemctl status ragpp-mcp-server.service
ps aux | grep uvicorn
tailscale status

# 2. Testar conectividade local
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8443/health

# 3. Verificar certificados SSL
sudo certbot certificates
ls -la /etc/letsencrypt/live/mcp.agourakis.med.br/
```

### FASE 2: CONFIGURAÇÃO TAILSCALE FUNNEL
```bash
# 1. Conectar via SSH com chave
ssh -i ~/.ssh/id_rsa user@192.168.4.198

# 2. Instalar/verificar Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh

# 3. Resetar configurações anteriores
sudo tailscale serve reset
sudo tailscale funnel reset

# 4. Configurar serve para porta 8443
sudo tailscale serve --https=443 http://127.0.0.1:8443

# 5. Aguardar e verificar
sleep 5
tailscale serve status

# 6. Habilitar funnel
sudo tailscale funnel --https=443 on

# 7. Verificar status final
tailscale funnel status
tailscale status --json | jq -r '.Self.DNSName'
```

### FASE 3: CONFIGURAÇÃO DE DOMÍNIO
```bash
# 1. Obter domínio Tailscale
DOMAIN=$(tailscale status --json | jq -r '.Self.DNSName')
echo "Domínio Tailscale: $DOMAIN"

# 2. Instruções para DNS (manual)
echo "Configure CNAME: mcp.agourakis.med.br -> $DOMAIN"

# 3. Tailscale Admin Console (manual)
echo "Acesse: https://login.tailscale.com/admin/dns"
echo "Habilite Custom Domain para: mcp.agourakis.med.br"
```

### FASE 4: TESTES DE CONECTIVIDADE
```bash
# 1. Testar domínio Tailscale
curl -I https://$DOMAIN/health
curl -X POST https://$DOMAIN/mcp/ \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{}}'

# 2. Testar domínio personalizado (após DNS)
curl -I https://mcp.agourakis.med.br/health
curl -X POST https://mcp.agourakis.med.br/mcp/ \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{}}'

# 3. Testar SSE
curl -N https://mcp.agourakis.med.br/sse/ \
  -H "Accept: text/event-stream" \
  -H "mcp-protocol-version: 2024-11-05"
```

### FASE 5: INTEGRAÇÃO CHATGPT
```bash
# 1. URL final para ChatGPT
echo "URL MCP: https://mcp.agourakis.med.br/sse/"

# 2. Headers necessários
echo "Accept: application/json, text/event-stream"
echo "mcp-protocol-version: 2024-11-05"

# 3. Configuração no ChatGPT
echo "Settings → Beta features → Model Context Protocol"
echo "Add server: RAG++ MCP Server"
echo "URL: https://mcp.agourakis.med.br/sse/"
echo "Auth: None"
```

## 🔍 DIAGNÓSTICO DE PROBLEMAS COMUNS

### Problema: Tailscale serve falha (exit code 2)
```bash
# Verificar logs
sudo tailscale serve logs
sudo tailscale funnel logs

# Verificar conflitos
sudo netstat -tlnp | grep :443
sudo lsof -i :443

# Reset completo
sudo tailscale serve reset
sudo tailscale funnel reset
sudo systemctl restart tailscaled
```

### Problema: Nginx não responde na 8443
```bash
# Verificar configuração
sudo nginx -t
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log

# Verificar firewall
sudo ufw status
sudo iptables -L | grep 8443
```

### Problema: MCP initialize falha
```bash
# Verificar FastAPI
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/mcp/ \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{}}'

# Verificar logs do FastAPI
tail -f /home/user/ragpp_server.log
```

### Problema: Certificado SSL expirado
```bash
# Renovar Let's Encrypt
sudo certbot renew
sudo systemctl reload nginx

# Verificar certificado
openssl s_client -connect mcp.agourakis.med.br:8443 -servername mcp.agourakis.med.br < /dev/null
```

## 📊 MÉTRICAS DE SUCESSO

Execute estes testes para confirmar tudo funcionando:

```bash
#!/bin/bash
echo "🧪 TESTE FINAL DE SUCESSO"
echo "========================"

# 1. Health check
if curl -s https://mcp.agourakis.med.br/health | grep -q "ok"; then
    echo "✅ Health: OK"
else
    echo "❌ Health: FAIL"
fi

# 2. MCP Initialize
RESPONSE=$(curl -s -X POST https://mcp.agourakis.med.br/mcp/ \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{}}')

if echo "$RESPONSE" | grep -q "mcp-session-id"; then
    echo "✅ MCP Initialize: OK"
else
    echo "❌ MCP Initialize: FAIL"
fi

# 3. SSE Connection
SSE_TEST=$(timeout 3 curl -s -N https://mcp.agourakis.med.br/sse/ \
  -H "Accept: text/event-stream" \
  -H "mcp-protocol-version: 2024-11-05" | head -n 1)

if echo "$SSE_TEST" | grep -q "event:"; then
    echo "✅ SSE: OK"
else
    echo "❌ SSE: FAIL"
fi

# 4. SSL Certificate
CERT_INFO=$(openssl s_client -connect mcp.agourakis.med.br:443 \
  -servername mcp.agourakis.med.br < /dev/null 2>/dev/null | openssl x509 -noout -dates)

if echo "$CERT_INFO" | grep -q "notAfter"; then
    echo "✅ SSL Certificate: OK"
else
    echo "❌ SSL Certificate: FAIL"
fi

echo ""
echo "🎉 Se todos os testes passarem, configuração concluída!"
```

## 🎯 INSTRUÇÕES ESPECÍFICAS PARA GPT-5 PRO

1. **ANÁLISE PRIMEIRO:** Leia todo o contexto e entenda a arquitetura
2. **EXECUTE PASSO A PASSO:** Não pule fases, execute na ordem correta
3. **DIAGNÓSTICO DETALHADO:** Para cada erro, forneça análise completa
4. **LOGS E OUTPUT:** Mostre sempre os comandos executados e suas saídas
5. **VERIFICAÇÃO:** Teste cada componente antes de prosseguir
6. **DOCUMENTAÇÃO:** Explique cada comando e seu propósito
7. **FALLBACKS:** Tenha planos alternativos para cada etapa
8. **SEGURANÇA:** Mantenha boas práticas de segurança

## 🚨 PRIORIDADES CRÍTICAS

1. **SSH Key Authentication** - Essencial para acesso seguro
2. **Tailscale Funnel** - Crítico para exposição HTTPS pública
3. **MCP Endpoints** - initialize e SSE devem funcionar
4. **SSL/TLS** - Certificados válidos obrigatórios
5. **ChatGPT Integration** - Objetivo final da configuração

---

**IMPORTANTE:** Execute tudo no servidor `192.168.4.198` via SSH. Teste cada etapa antes de prosseguir. Forneça outputs completos de todos os comandos para diagnóstico preciso.</content>
<parameter name="filePath">/home/agourakis82/workspace/pcs-meta-repo/PROMPT_GPT5_PRO_TAILSCALE_SETUP.md