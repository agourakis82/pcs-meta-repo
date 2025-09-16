# 🤖 Guia de Configuração do ChatGPT — Cloudflare Tunnel (Sem Autenticação)

Atualizado para usar o endpoint via Cloudflare Tunnel com Authentication = No Auth  
Data: 13 de setembro de 2025

## 📋 Informações do Servidor

- URL Base: `https://mcp.agourakis.med.br`
- Endpoint de Pesquisa: `https://mcp.agourakis.med.br/search`
- Health Check: `https://mcp.agourakis.med.br/health`

## 🚀 Método 1: GPT Action (recomendado)

1) Abra ChatGPT → Configure → Actions → Create new action  
2) Em Authentication selecione “No authentication”  
3) Cole o OpenAPI abaixo em “Schema”:

```yaml
openapi: 3.0.0
info:
  title: PCS Meta-Repo Research API
  description: Acesso à literatura científica e insights de pesquisa em psiquiatria computacional
  version: 1.0.0
servers:
  - url: https://mcp.agourakis.med.br
    description: Cloudflare Tunnel Production Server
paths:
  /health:
    get:
      operationId: checkHealth
      summary: Verificar status do servidor
      responses:
        '200':
          description: Servidor operacional
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: { type: string }
                  version: { type: string }
                  capabilities:
                    type: array
                    items: { type: string }
                  indexed_articles: { type: integer }
  /search:
    post:
      operationId: searchLiterature
      summary: Buscar literatura científica
      description: Realiza busca semântica na base de artigos científicos indexados
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [query]
              properties:
                query:
                  type: string
                  example: "machine learning in psychiatry"
                max_results:
                  type: integer
                  default: 10
                  minimum: 1
                  maximum: 50
                search_type:
                  type: string
                  enum: [literature, hybrid, memory]
                  default: literature
      responses:
        '200':
          description: Resultados da busca
```

### Testar

- Em “Test”, execute `checkHealth` (esperado: status healthy)  
- Faça uma busca: “Buscar artigos sobre machine learning em psiquiatria”

## 🔧 Alternativa: Custom Instructions

Se Actions não estiver disponível, adicione instruções ao GPT:

```text
Use a API pública de pesquisa:
- URL: https://mcp.agourakis.med.br/search (POST, application/json)
- Body: { "query": "<pergunta>", "max_results": 10, "search_type": "literature" }
```

## ✅ Teste rápido

Comando básico (sem autenticação):

```bash
curl -s https://mcp.agourakis.med.br/health | jq .status
```

## 🛡️ Segurança recomendada (No Auth)

- WAF/Rate limiting no Cloudflare para `POST /search` (ex.: 60 req/min/IP)  
- Bloquear paths não usados; permitir apenas `/health`, `/search` e necessários  
- Ativar Bot Fight Mode e DDoS protections  
- (Opcional) Cloudflare Access ou allowlist por IP/ASN se necessário

## 🧪 Troubleshooting rápido

- Se HTTPS oscilar (erro 522/handshake), teste via `ngrok http 8081` e use a URL HTTPS do ngrok temporariamente nas Actions  
- Verifique local: `curl -s http://127.0.0.1:8081/health` → deve retornar JSON  
- Confirme que o túnel do Cloudflare está ativo e DNS proxied

---

Documento atualizado para “Sem Autenticação”.
