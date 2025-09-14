# 🤖 ChatGPT Custom Action Setup Guide

## Como Configurar RAG++ no ChatGPT Web

### Pré-requisitos ✅
- [ ] RAG++ servidor web deployado (Railway, Heroku, etc.)
- [ ] URL HTTPS funcionando
- [ ] API Token salvo
- [ ] ChatGPT Plus ou Pro subscription

---

## 📋 Passo a Passo Completo

### 1. Deploy do Servidor (Escolha uma opção)

#### Opção A: Railway (Recomendado - HTTPS automático)
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Fazer deploy
./deploy_railway.sh
```

#### Opção B: Render (Gratuito)
1. Acesse: https://render.com
2. "New" → "Web Service"
3. Conecte seu GitHub repo
4. Configure:
   - **Build Command:** `pip install -r requirements-web.txt`
   - **Start Command:** `python ragpp/ragpp_web_server.py`
   - **Environment Variables:**
     ```
     RAG_API_TOKEN=seu-token-gerado
     RAG_SERVER_URL=https://sua-app.onrender.com
     ```

#### Opção C: Heroku
```bash
# Criar app
heroku create sua-ragpp-app

# Configurar variáveis
heroku config:set RAG_API_TOKEN=seu-token
heroku config:set RAG_SERVER_URL=https://sua-ragpp-app.herokuapp.com

# Deploy
git push heroku main
```

### 2. Teste do Servidor 🧪

```bash
# Health check
curl https://sua-url.com/health

# Teste de busca
curl -X POST "https://sua-url.com/search" \
  -H "Authorization: Bearer seu-token" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning psychiatry"}'
```

---

## 🔧 Configuração no ChatGPT

### Método 1: Custom Actions (Recomendado)

1. **Acesse ChatGPT:** https://chat.openai.com

2. **Vá em Settings:**
   - Clique no seu perfil (canto superior direito)
   - Settings → Beta Features
   - Ative "Custom Actions" (se disponível)

3. **Criar Nova Action:**
   - Settings → Actions → "Create new action"
   - Ou crie um Custom GPT e adicione Actions

4. **Configuração da Action:**

   **Nome:** `RAG++ Research Assistant`
   
   **Descrição:** `Access recent scientific literature and research insights using RAG++ system`
   
   **Authentication Type:** `API Key`
   
   **API Key Header:** `Authorization`
   
   **API Key Value:** `Bearer SEU_TOKEN_AQUI`
   
   **Schema:** Cole o conteúdo de `chatgpt_action_config.json` ou use:

   ```json
   {
     "openapi": "3.0.0",
     "info": {
       "title": "RAG++ Research API",
       "version": "1.0.0",
       "description": "Advanced research assistant with literature search"
     },
     "servers": [
       {
         "url": "https://sua-url.com"
       }
     ],
     "paths": {
       "/search": {
         "post": {
           "operationId": "searchResearch",
           "summary": "Search scientific literature",
           "description": "Search through indexed research papers and scientific literature",
           "requestBody": {
             "required": true,
             "content": {
               "application/json": {
                 "schema": {
                   "type": "object",
                   "properties": {
                     "query": {
                       "type": "string",
                       "description": "Research question or topic"
                     },
                     "max_results": {
                       "type": "integer",
                       "default": 10,
                       "description": "Maximum number of results"
                     }
                   },
                   "required": ["query"]
                 }
               }
             }
           },
           "responses": {
             "200": {
               "description": "Search results"
             }
           }
         }
       },
       "/research/recent": {
         "get": {
           "operationId": "getRecentFindings",
           "summary": "Get recent research findings",
           "description": "Retrieve latest indexed research papers",
           "parameters": [
             {
               "name": "limit",
               "in": "query",
               "schema": {
                 "type": "integer",
                 "default": 20
               }
             }
           ],
           "responses": {
             "200": {
               "description": "Recent findings"
             }
           }
         }
       }
     }
   }
   ```

5. **Salvar e Testar:**
   - Clique "Save"
   - Teste com: "Test action"

### Método 2: Custom GPT com Actions

1. **Criar Custom GPT:**
   - ChatGPT → "Explore" → "Create a GPT"

2. **Configure:**
   - **Name:** `RAG++ Research Assistant`
   - **Description:** `I help you search and analyze recent scientific literature using an advanced RAG++ system with hybrid search capabilities.`
   
   **Instructions:**
   ```
   You are a research assistant with access to a RAG++ system containing recent scientific literature. When users ask research questions:

   1. Use the searchResearch action to find relevant papers
   2. Analyze and synthesize the findings
   3. Provide comprehensive, evidence-based responses
   4. Always cite sources when available
   5. For broad topics, use getRecentFindings to show latest research

   Focus on: computational psychiatry, machine learning in healthcare, digital phenotyping, neuroimaging, and related fields.
   ```

3. **Adicionar Actions:** Cole a mesma configuração do Método 1

---

## 🎯 Exemplos de Uso

### Perguntas Básicas:
- "What are the latest findings in computational psychiatry?"
- "Search for recent research on digital phenotyping"
- "Find studies about machine learning in mental health"

### Perguntas Avançadas:
- "Compare different approaches to EEG-based emotion recognition"
- "What are the limitations of current psychiatric prediction models?"
- "Show me recent advances in natural language processing for healthcare"

### Comandos Específicos:
- "Search the literature for 'fMRI depression biomarkers'"
- "Get recent findings from the last year"
- "Find papers about 'transformer models psychiatry'"

---

## 🔍 Verificação e Troubleshooting

### Checklist de Funcionamento:
- [ ] Servidor responde em `/health`
- [ ] Authentication funciona com token
- [ ] ChatGPT consegue acessar o schema
- [ ] Actions aparecem disponíveis
- [ ] Busca retorna resultados

### Problemas Comuns:

**❌ "Action failed to execute"**
- Verifique se o token está correto
- Confirme que a URL está acessível
- Teste manualmente com curl

**❌ "Schema validation error"**
- Valide o JSON schema em https://jsonschemavalidator.net/
- Verifique se todos os endpoints existem

**❌ "CORS error"**
- Confirme que o servidor tem CORS configurado
- Verifique se chat.openai.com está na allowlist

**❌ "No results returned"**
- Confirme que há dados indexados no RAG++
- Teste com queries simples primeiro

### Debug Commands:
```bash
# Verificar logs do servidor
railway logs  # (se usando Railway)

# Testar endpoints manualmente
curl -v https://sua-url.com/health
curl -v https://sua-url.com/.well-known/ai-plugin.json

# Verificar dados
curl -H "Authorization: Bearer token" https://sua-url.com/research/recent
```

---

## 🚀 Conclusão

Após a configuração, você terá:
- ✅ ChatGPT com acesso a literatura científica recente
- ✅ Busca híbrida (vetorial + semântica)
- ✅ Base de conhecimento em psiquiatria computacional
- ✅ API REST completa para outras integrações

**Pronto!** Seu RAG++ está integrado ao ChatGPT web! 🎉
