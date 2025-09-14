# 🚀 Configuração Rápida do ChatGPT - PCS Meta-Repo

Para uso imediato enquanto o HTTPS do Cloudflare estabiliza.

## 🎯 Opção 1: Configuração Local (Desenvolvimento)

Se você estiver na máquina/loopback, use o proxy nginx local em `127.0.0.1:8081`.

```yaml
openapi: 3.0.0
info:
  title: PCS Meta-Repo Research API (Local)
  version: 1.0.0
  description: Busca semântica em literatura científica de psiquiatria
servers:
  - url: http://127.0.0.1:8081
    description: Servidor local via nginx proxy
paths:
  /health:
    get:
      operationId: checkHealth
      summary: Verificar status
      responses:
        '200':
          description: Status do servidor
  /search:
    post:
      operationId: searchLiterature
      summary: Buscar literatura
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                query:
                  type: string
                max_results:
                  type: integer
                  default: 10
                  minimum: 1
                  maximum: 20
              required:
                - query
      responses:
        '200':
          description: Resultados da busca
```

- Authentication: selecione “No authentication”.

## 🌐 Opção 2: Tunnel Temporário (ngrok)

1) Instalar ngrok:

```bash
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install -y ngrok
```

2) Expor o servidor MCP (via nginx 8081):

```bash
ngrok http 8081
```

Use a URL HTTPS do ngrok como `servers[0].url` no OpenAPI acima.

## 🔧 Opção 3: Cloudflare (produção)

- Quando o HTTPS estiver estável, use `https://mcp.agourakis.med.br` como `servers[0].url`.
- Authentication: “No authentication”.

## ⚡ Teste Rápido

```bash
# Local via nginx
curl -s http://127.0.0.1:8081/health | jq .status

# Ngrok (exemplo)
curl -s https://<subdomínio>.ngrok-free.app/health | jq .status
```

## 📞 Troubleshooting

- Verifique se o MCP server está rodando: `ps aux | grep uvicorn`
- Teste o endpoint local: `curl http://127.0.0.1:8000/health`
- Verifique nginx: `sudo systemctl status nginx`

Status atual:

- ✅ Servidor MCP: Funcionando
- ✅ Nginx proxy: Funcionando
- ⚠️ Cloudflare HTTPS: Em propagação
- ✅ Configuração local/ngrok: Pronta

---

Use a Opção 1 para teste imediato ou Opção 2 para acesso remoto via ngrok.