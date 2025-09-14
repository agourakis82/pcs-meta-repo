# 🔄 Guia de Migração ChatGPT → MCP

## 📥 Métodos de Exportação

### 1. Export Oficial do ChatGPT (Recomendado)

1. **Acesse suas configurações**: 
   - Vá para [https://chat.openai.com/settings](https://chat.openai.com/settings)
   - Clique em "Data controls"
   - Selecione "Export data"

2. **Aguarde o arquivo**: 
   - OpenAI enviará um email com link para download
   - Baixe o arquivo `conversations.json`

3. **Execute a migração**:
   ```bash
   python chatgpt_conversation_migrator.py conversations.json --project-name "Minhas Conversas"
   ```

### 2. Copy-Paste Manual (Alternativa)

1. **Crie arquivo de texto** (`minhas_conversas.txt`):
   ```
   User: Como implementar cache multi-IA?
   
   Assistant: Para implementar um cache multi-IA você precisa criar endpoints...
   
   User: E como posso migrar conversas do ChatGPT?
   
   Assistant: Existem várias formas de migrar conversas...
   ```

2. **Execute a migração**:
   ```bash
   python chatgpt_conversation_migrator.py minhas_conversas.txt --project-name "Conversas Manuais"
   ```

### 3. API do Servidor (Upload de Arquivo)

1. **Upload direto via API**:
   ```bash
   curl -X POST https://mcp.agourakis.med.br/import/conversations/file \
        -F "file=@conversations.json" \
        -F "project_name=Meu Projeto" \
        -F "ai_type=chatgpt"
   ```

2. **Importação em lote via JSON**:
   ```bash
   curl -X POST https://mcp.agourakis.med.br/import/conversations/bulk \
        -H "Content-Type: application/json" \
        -d @bulk_import.json
   ```

## 📊 Formatos Suportados

### JSON Export (ChatGPT Oficial)
```json
{
  "id": "conversation_123",
  "title": "Discussão sobre IA",
  "mapping": {
    "message_1": {
      "message": {
        "author": {"role": "user"},
        "content": {"parts": ["Pergunta aqui"]}
      }
    }
  }
}
```

### Texto Simples
```
User: Sua pergunta aqui
Assistant: Resposta do ChatGPT aqui

User: Outra pergunta
Assistant: Outra resposta
```

### Bulk Import JSON
```json
{
  "conversations": [
    {
      "title": "Conversa 1",
      "messages": [
        {"role": "user", "content": "Pergunta", "timestamp": "2025-09-14T12:00:00Z"},
        {"role": "assistant", "content": "Resposta", "timestamp": "2025-09-14T12:00:01Z"}
      ]
    }
  ],
  "project_name": "Meu Projeto",
  "ai_type": "chatgpt"
}
```

## 🚀 Exemplos de Uso

### Migração Simples
```bash
# Migrar arquivo oficial do ChatGPT
python chatgpt_conversation_migrator.py conversations.json

# Com nome personalizado do projeto
python chatgpt_conversation_migrator.py conversations.json --project-name "Trabalho de IA"

# Para servidor personalizado
python chatgpt_conversation_migrator.py conversations.json --mcp-url https://meu-servidor.com
```

### Verificar Status
```bash
# Ver status do sistema de importação
curl https://mcp.agourakis.med.br/import/status

# Ver exemplo de formato
curl https://mcp.agourakis.med.br/import/example
```

### Após a Migração
```bash
# Verificar sessões criadas
curl https://mcp.agourakis.med.br/cache/ai/sessions

# Buscar conversas migradas
curl -X POST https://mcp.agourakis.med.br/cache/ai/search \
     -H "Content-Type: application/json" \
     -d '{"query": "cache multi-IA", "ai_types": ["chatgpt"]}'
```

## 📋 Checklist de Migração

- [ ] ✅ Servidor MCP rodando (`curl https://mcp.agourakis.med.br/health`)
- [ ] 📥 Arquivo de conversas preparado
- [ ] 🔧 Script de migração executado
- [ ] ✅ Verificar relatório de migração (`migration_report.json`)
- [ ] 🔍 Testar busca de conversas migradas
- [ ] 📊 Conferir estatísticas (`/cache/ai/stats`)

## 🛠️ Troubleshooting

### Erro de Conexão
```bash
# Verificar se servidor está acessível
curl -I https://mcp.agourakis.med.br/health
```

### Arquivo Não Reconhecido
- Verificar encoding (deve ser UTF-8)
- Conferir formato JSON válido
- Tentar método de texto simples

### Falhas na Migração
- Verificar logs no `migration_report.json`
- Tentar migração em lotes menores
- Conferir permissões de arquivo

## 🎯 Próximos Passos

Após migrar suas conversas:

1. **Configure ChatGPT Actions** usando a documentação em `CHATGPT_CONFIGURACAO_FINAL.md`
2. **Use transferência cross-AI** para mover conversas entre diferentes IAs
3. **Aproveite a busca inteligente** para encontrar conversas relevantes
4. **Monitore estatísticas** para acompanhar uso do cache

---

*Migração ChatGPT → MCP v1.0*
