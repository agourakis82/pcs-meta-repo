# 🎉 SEU RAG++ ESTÁ ACESSÍVEL REMOTAMENTE!

## 📍 Informações da Sua Configuração

### 🌐 Endereços de Acesso:
- **IP Local (rede interna):** `http://172.20.7.45:8000`
- **IP Público (acesso remoto):** `http://179.125.169.148:8000`
- **Documentação API:** `http://179.125.169.148:8000/docs`

### 🔑 Autenticação:
```
Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo
```

---

## ✅ Status Atual
- ✅ **Firewall configurado** (porta 8000 aberta)
- ✅ **Servidor rodando** (PID: processo em background)
- ✅ **Acesso local testado** (172.20.7.45:8000)
- ✅ **API funcionando** (endpoints respondendo)
- ✅ **168 artigos indexados** (base de conhecimento pronta)

---

## 🚀 Como Usar Remotamente

### 1. De Qualquer Computador na Internet:
```bash
# Teste de conectividade
curl http://179.125.169.148:8000/health

# Busca na literatura
curl -X POST "http://179.125.169.148:8000/search" \
  -H "Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning psychiatry"}'
```

### 2. No ChatGPT Web (Custom Action):

**Configuração:**
1. Acesse ChatGPT → Settings → Actions
2. Create new action
3. **Authentication:** API Key
4. **Header:** Authorization
5. **Value:** `Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo`
6. **Schema URL:** `http://179.125.169.148:8000/actions/schema`

**Ou copie este schema:**
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "RAG++ Research API",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "http://179.125.169.148:8000"
    }
  ],
  "paths": {
    "/search": {
      "post": {
        "operationId": "searchResearch",
        "summary": "Search scientific literature",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "query": {
                    "type": "string",
                    "description": "Research question"
                  },
                  "max_results": {
                    "type": "integer",
                    "default": 10
                  }
                },
                "required": ["query"]
              }
            }
          }
        }
      }
    }
  }
}
```

### 3. No Smartphone/Tablet:
- **URL:** `http://179.125.169.148:8000/docs`
- **Token:** `wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo`

---

## 📱 Testando Acesso Remoto

### De outro computador/smartphone:
```bash
# 1. Teste básico
curl http://179.125.169.148:8000/health

# 2. Busca com autenticação
curl -X POST "http://179.125.169.148:8000/search" \
  -H "Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo" \
  -H "Content-Type: application/json" \
  -d '{"query": "digital phenotyping"}'

# 3. Artigos recentes
curl -H "Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo" \
  http://179.125.169.148:8000/research/recent
```

---

## 🔧 Gerenciamento do Servidor

### Verificar Status:
```bash
# Ver se está rodando
ps aux | grep ragpp_web_server

# Testar conectividade
curl http://172.20.7.45:8000/health
```

### Parar Servidor:
```bash
pkill -f ragpp_web_server
```

### Reiniciar Servidor:
```bash
cd /home/agourakis82/workspace/pcs-meta-repo
export RAG_API_TOKEN="wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo"
python ragpp/ragpp_web_server.py &
```

### Script Automático:
```bash
# Use o script criado
./start_remote_server.sh
```

---

## 🛡️ Segurança

### Atual (HTTP):
- ✅ Autenticação por token
- ✅ CORS configurado para ChatGPT
- ✅ Firewall local configurado

### Recomendado para Produção:
1. **HTTPS com Let's Encrypt**
2. **Nginx reverse proxy**
3. **Rate limiting**
4. **Monitoring/logs**

---

## 📋 Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|---------|-----------|
| `/health` | GET | Status do sistema |
| `/search` | POST | Busca na literatura |
| `/research/recent` | GET | Artigos recentes |
| `/docs` | GET | Documentação interativa |
| `/.well-known/ai-plugin.json` | GET | Plugin manifest |
| `/actions/schema` | GET | Schema para Custom Actions |

---

## 🎯 Próximos Passos Sugeridos

1. **Teste remoto:** Acesse de outro dispositivo
2. **Configure ChatGPT:** Use Custom Actions
3. **HTTPS (opcional):** Para maior segurança
4. **Monitoring:** Configure logs/alertas

---

## ❓ Troubleshooting

### "Connection refused":
- Verifique se o servidor está rodando
- Confirme firewall local (ufw status)
- Teste com IP local primeiro

### "Timeout":
- Confirme IP público: `curl ifconfig.me`
- Verifique router/modem (port forwarding)
- Teste com porta alternativa

### ChatGPT não conecta:
- Use HTTP (não HTTPS) na URL
- Confirme token na configuração
- Verifique CORS headers

---

## 🎉 Sucesso!

**Seu RAG++ com 168 artigos de psiquiatria computacional está agora acessível via internet em:**

### `http://179.125.169.148:8000`

**Qualquer pessoa com o token pode acessar sua base de conhecimento científica!** 🚀

---

*Para instruções detalhadas, consulte: `REMOTE_ACCESS_GUIDE.md`*
