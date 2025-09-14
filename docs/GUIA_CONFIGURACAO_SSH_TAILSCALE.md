# ⚠️ DEPRECATED: Guia SSH + Tailscale para MCP

> **ESTE GUIA FOI DEPRECIADO** - Migrado para **Cloudflare Tunnel**
>
> **Novo guia**: [docs/infra_cloudflare_tunnel.md](docs/infra_cloudflare_tunnel.md)
>
> **Vantagens da migração:**
>
> - ✅ Melhor performance e latência global
> - ✅ Domínio personalizado sem limitações
> - ✅ DDoS protection e CDN incluídos
> - ✅ TLS automático via Cloudflare
> - ✅ Configuração mais simples e confiável
>
> Este arquivo permanece apenas para referência histórica.

---

## 🚀 Guia Passo a Passo: Configurar SSH + Tailscale para MCP (DEPRECATED)

## 📋 Pré-requisitos

- Servidor Linux: `192.168.4.198`
- Tailscale instalado no servidor
- Conta Tailscale configurada

---

## 🔑 Passo 1: Configurar SSH no Servidor

### Opção A: Executar script automático (Recomendado)

```bash
# No servidor 192.168.4.198, execute:
curl -fsSL https://raw.githubusercontent.com/seu-repo/setup_ssh_key.sh | bash
```

### Opção B: Configuração manual

```bash
# No servidor, crie/edit ~/.ssh/authorized_keys e adicione:
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCshzvo42A0n7slhnG9laBOlnjN/rATS23BE7L0e+B8c+5NKHY1s2k2cm9reHpIFjEfgN8nZj6VkwltT0TL6xwZWzPxvKbxdOcbbWXPmU5DoyYg6Gb3MjbCX1rwC4LsHcImQ/6xSh7w/b/ntemf6JF1e0FJDjUVdFutmzXfzTwsmJnyZAcbzgVlgdSjn/6dzWOGYqXfC81CEk2VSOgm3kbWWbmY/SH0hduy9F8KTHPOq2AEisISNrMIIriLtgpm/UFqos1MgjAQkZxtsjQcHaYnQ7yuq72nWDoHD39iwbdUtpCs+s+V1MgxjtZWj6qqVzpkvMkXw4ceD/dGysl+ZcVtWDOJssxz9eZV1emj/vcOwiqeNIomdQ1JFIsb5s/bqP+753kAcUf3yoOQePBiSN1sxCpis89o2hvenCHcZxlE+rSLkLnOotSdgfwDWwd9PitSBR2m49EThPVBEweyVvVWxVyp8Eytqk9nM9sEV0y2hVBh9D7SV77iNmFgyOhdPUVVTNh+8YF8FOyGp1ugqgxJbkqyB4CT9zK+xT7zTrksbqgBJtfaMFyKrgoVuaDHShFhOOzEaccqKYITqbWPYYogQq400LeAbcn9QAE/Zj7Di9lxKQTQclc0vzC1JIynqvlhTwKzjl4Nef6zBdCPxk4NU2MUZYrTcW2jRekh3k8HFw== agourakis82@github
```

### Testar SSH

```bash
# Do WSL2, teste a conexão:
ssh seu_usuario@192.168.4.198
```

---

## 🌐 Passo 2: Configurar Tailscale Funnel

### No servidor (192.168.4.198)

```bash
# 1. Instalar Tailscale (se não estiver instalado):
curl -fsSL https://tailscale.com/install.sh | sh

# 2. Conectar ao Tailscale:
sudo tailscale up --ssh

# 3. Acesse o link fornecido no terminal para autenticar

# 4. Executar script de configuração:
curl -fsSL https://raw.githubusercontent.com/seu-repo/setup_tailscale_funnel.sh | bash
```

---

## 🧪 Passo 3: Testar Configuração

### Do seu WSL2

```bash
# Executar testes:
curl -fsSL https://raw.githubusercontent.com/seu-repo/test_mcp_funnel.sh | bash
```

### Verificar se está funcionando

- ✅ Health endpoint responde
- ✅ MCP initialize funciona
- ✅ SSE endpoint conecta
- ✅ SSL/TLS ativo

---

## 🔗 Passo 4: Configurar Domínio Personalizado

### No seu provedor DNS

1. Crie CNAME: `mcp.agourakis.med.br` → `demetriospcs.tail21cbc4.ts.net`

### No Tailscale Admin Console

1. Vá para: <https://login.tailscale.com/admin/dns>
2. Adicione domínio customizado: `mcp.agourakis.med.br`
3. Habilite "Custom Domain" para o seu tailnet

---

## 🤖 Passo 5: Configurar ChatGPT MCP

### No ChatGPT

1. Vá para Settings → Beta features → Model Context Protocol
2. Adicione novo servidor:
   - **Name**: RAG++ MCP Server
   - **Server URL**: `https://mcp.agourakis.med.br/sse/`
   - **Auth**: None (ou configure se necessário)

### Headers necessários

```text
Accept: application/json, text/event-stream
mcp-protocol-version: 2024-11-05
```

---

## 🔍 Solução de Problemas

### SSH não conecta

```bash
# Verificar se SSH está rodando no servidor:
sudo systemctl status ssh

# Verificar authorized_keys:
cat ~/.ssh/authorized_keys
```

### Tailscale não conecta

```bash
# Verificar status:
tailscale status

# Reconectar se necessário:
sudo tailscale up --ssh
```

### MCP não responde

```bash
# Verificar se Nginx está rodando:
sudo systemctl status nginx

# Verificar logs:
sudo tailscale serve logs
sudo tailscale funnel logs
```

---

## 📞 Suporte

Se algo der errado:

1. Execute os testes: `./test_mcp_funnel.sh`
2. Verifique logs no servidor
3. Compartilhe a saída dos comandos de diagnóstico

**URLs finais esperadas:**

- MCP Server: `https://mcp.agourakis.med.br/mcp/`
- SSE: `https://mcp.agourakis.med.br/sse/`
- Health: `https://mcp.agourakis.med.br/health`

---

## 🔍 Solução de Problemas

### SSH não conecta

```bash
# Verificar se SSH está rodando no servidor:
sudo systemctl status ssh

# Verificar authorized_keys:
cat ~/.ssh/authorized_keys
```

### Tailscale não conecta

```bash
# Verificar status:
tailscale status

# Reconectar se necessário:
sudo tailscale up --ssh
```

### MCP não responde

```bash
# Verificar se Nginx está rodando:
sudo systemctl status nginx

# Verificar logs:
sudo tailscale serve logs
sudo tailscale funnel logs
```

---

## 📞 Suporte

Se algo der errado:

1. Execute os testes: `./test_mcp_funnel.sh`
2. Verifique logs no servidor
3. Compartilhe a saída dos comandos de diagnóstico

**URLs finais esperadas:**

- MCP Server: `https://mcp.agourakis.med.br/mcp/`
- SSE: `https://mcp.agourakis.med.br/sse/`
- Health: `https://mcp.agourakis.med.br/health`
