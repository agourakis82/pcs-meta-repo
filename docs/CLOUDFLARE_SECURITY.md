# 🛡️ Cloudflare — Guia de Segurança para API (No Auth)

Este guia recomenda proteções no Cloudflare para operar a API sem autenticação direta, reduzindo abuso e custos.

## 🎯 Escopo

- Host: `mcp.agourakis.med.br`
- Endpoints permitidos: `GET /health`, `POST /search` (ajuste conforme necessário)

## 1) Rate Limiting Rules

Crie regra de rate limit específica para `POST /search` por IP.

- Condição: `(http.host eq "mcp.agourakis.med.br" and http.request.method eq "POST" and http.request.uri.path eq "/search")`
- Limite: 60 requisições por 1 minuto por IP (ajuste se necessário)
- Ação: `Block` ou `Challenge`

Via Dashboard: Security → WAF → Rate limiting rules → Create.  
Via API (exemplo):

```bash
CF_API="https://api.cloudflare.com/client/v4"
ZONE_ID="<SEU_ZONE_ID>"
API_TOKEN="<SEU_API_TOKEN_COM_PERMISSOES_WAF>"

curl -s -X POST "$CF_API/zones/$ZONE_ID/rate_limits" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "disabled": false,
    "description": "Rate limit POST /search",
    "match": {
      "request": {
        "methods": ["POST"],
        "schemes": ["HTTPS"],
        "url": "mcp.agourakis.med.br/search"
      }
    },
    "threshold": 60,
    "period": 60,
    "action": { "mode": "block" }
  }'
```

## 2) WAF Custom Rules — Restringir Paths

Permitir apenas os caminhos necessários no host `mcp.agourakis.med.br`.

- Regra 1 (Allow): `(http.host eq "mcp.agourakis.med.br" and http.request.method eq "GET" and http.request.uri.path eq "/health")`
- Regra 2 (Allow): `(http.host eq "mcp.agourakis.med.br" and http.request.method eq "POST" and http.request.uri.path eq "/search")`
- Regra 3 (Block default): `(http.host eq "mcp.agourakis.med.br")`

Ordem importa: coloque as regras de Allow acima do Block default.

## 3) Bot Fight Mode e DDoS

- Ative "Bot Fight Mode" em Security → Bots.
- Ative proteções DDoS automáticas (padrão em planos pagos; em Free/Pro já há mitigação básica).

## 4) (Opcional) Cloudflare Access

Se quiser exigir autenticação do usuário final sem mudar a API:

- Zero Trust → Access → Applications → Add → Self-hosted.  
- Aplicar para `mcp.agourakis.med.br/*` ou somente `POST /search` via políticas.  
- Políticas: Email corporativo, GitHub/Google, One-time PIN, etc.

Observação: ChatGPT Actions podem não seguir redirects/Access challenge. Use com cautela.

## 5) (Opcional) Allowlist por IP/ASN/País

Crie regras de WAF adicionais:

- Permitir apenas Brasil (ex.: `ip.src.country in {"BR"}`)
- Allowlist de IPs de administração
- Bloquear ASNs conhecidos por abuso

## 6) Observabilidade

- Ative logs no Cloudflare (HTTP requests) para monitorar picos.  
- Configure alertas de taxa de bloqueios (Rate limiting/WAF) para tuning.

## 7) SSL/TLS e Tunnel

- O tráfego ao origin usa Cloudflare Tunnel (cloudflared); certs de origem em nginx não são necessários.  
- Se houver 522/handshake, verifique: Túnel ativo, DNS proxied (nuvem laranja), e regras não bloqueando `/health`.

---

Com estas proteções, operar em "No Auth" fica mais seguro. Ajuste limites conforme carga real.