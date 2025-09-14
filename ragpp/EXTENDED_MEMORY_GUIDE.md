# 🧠 RAG++ Extended Memory - Sistema de Memória Extendida

## 📋 Visão Geral

Seu sistema RAG++ agora tem uma **memória extendida verdadeira** que:

✅ **Inicia automaticamente** quando o computador liga  
✅ **Armazena conversas** do ChatGPT permanentemente  
✅ **Mantém contexto** do projeto e decisões  
✅ **Busca semântica** inteligente  
✅ **Acesso remoto** via IP fixo  
✅ **Backup automático** de segurança  

---

## 🚀 Status Atual

### Sistema Operacional
- **Status**: ✅ Ativo e funcionando
- **URL Local**: http://localhost:8000
- **URL Remoto**: http://179.125.169.148:8000
- **PID**: 275444
- **Auto-start**: ✅ Configurado

### Componentes Ativos
1. **RAG++ Core**: 168 papers indexados
2. **Extended Memory Service**: ChromaDB + SQLite
3. **Web API**: FastAPI com endpoints de memória
4. **Auto-start Service**: Systemd configurado
5. **ChatGPT Integration**: Endpoints prontos

---

## 🔧 Gerenciamento do Serviço

### Comandos Principais
```bash
# Iniciar serviço
./manage_memory_service.sh start

# Parar serviço
./manage_memory_service.sh stop

# Reiniciar serviço
./manage_memory_service.sh restart

# Ver status
./manage_memory_service.sh status

# Ver logs em tempo real
./manage_memory_service.sh logs
```

### Systemd (Alternativo)
```bash
# Controle via systemd
systemctl --user start ragpp-memory-service
systemctl --user stop ragpp-memory-service
systemctl --user status ragpp-memory-service

# Ver logs
journalctl --user -u ragpp-memory-service -f
```

---

## 🧠 API de Memória

### Endpoints Principais

#### Armazenar Memória
```bash
POST /memory/store
{
  "content": "Sua memória aqui",
  "memory_type": "insight|context|decision|conversation",
  "tags": ["tag1", "tag2"],
  "importance_score": 0.8
}
```

#### Buscar na Memória
```bash
POST /memory/search
{
  "query": "sua busca aqui",
  "max_results": 10,
  "importance_threshold": 0.5
}
```

#### Armazenar Conversa ChatGPT
```bash
POST /memory/store/conversation
{
  "conversation_data": {
    "messages": [...],
    "summary": "resumo"
  },
  "title": "Título da conversa",
  "importance_score": 0.9
}
```

#### Recuperar Contexto
```bash
GET /memory/chatgpt/recall?query=sua_consulta
```

---

## 🎯 Como Usar com ChatGPT

### 1. Armazenar Conversas Importantes
Sempre que tiver uma conversa importante no ChatGPT:

```bash
curl -X POST "http://localhost:8000/memory/store/conversation" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_data": {
      "messages": [/* suas mensagens */],
      "summary": "Resumo da conversa"
    },
    "title": "Nome descritivo",
    "importance_score": 0.8
  }'
```

### 2. Buscar Contexto Anterior
Antes de continuar uma conversa:

```bash
curl "http://localhost:8000/memory/chatgpt/recall?query=assunto_relevante"
```

### 3. Armazenar Decisões e Insights
Para decisões importantes do projeto:

```bash
curl -X POST "http://localhost:8000/memory/store" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Decisão tomada ou insight importante",
    "memory_type": "decision",
    "tags": ["projeto", "decisao"],
    "importance_score": 0.9
  }'
```

---

## 🔗 Integração com ChatGPT Web

### Custom Actions (Recomendado)
1. Vá em ChatGPT → Settings → Actions
2. Crie nova ação:
   - **URL**: `http://179.125.169.148:8000`
   - **Token**: `Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo`
   - **Schema**: `http://179.125.169.148:8000/actions/schema`

### Custom GPT (Mais Poderoso)
Use as configurações em:
- `custom_gpt_instructions.md`
- `custom_gpt_schema.json`

---

## 💾 Backup e Segurança

### Backup Automático
- **Frequência**: A cada 1 hora
- **Localização**: `ragpp/data/memory/backups/`
- **Formato**: SQLite + ChromaDB

### Backup Manual
```bash
curl -X POST "http://localhost:8000/memory/backup"
```

### Estatísticas
```bash
curl "http://localhost:8000/memory/stats"
```

---

## 🔍 Troubleshooting

### Serviço não está rodando
```bash
# Verificar status
./manage_memory_service.sh status

# Ver logs
./manage_memory_service.sh logs

# Reiniciar
./manage_memory_service.sh restart
```

### API não responde
```bash
# Testar saúde
curl http://localhost:8000/health

# Verificar firewall
sudo ufw status

# Testar porta
netstat -tlnp | grep :8000
```

### Memória não funciona
```bash
# Testar endpoint
curl http://localhost:8000/memory/stats

# Verificar logs
tail -f ragpp/logs/memory_server.log

# Verificar banco de dados
ls -la ragpp/data/memory/
```

---

## 🎉 Funcionalidades Avançadas

### 1. Categorização Automática
O sistema automaticamente categoriza memórias por:
- Tipo de conteúdo
- Importância
- Frequência de acesso
- Tags relacionadas

### 2. Busca Inteligente
- **Semântica**: Encontra por significado, não apenas palavras
- **Contextual**: Considera conversas relacionadas
- **Temporal**: Prioriza informações recentes

### 3. Limpeza Automática
- Remove memórias antigas e pouco importantes
- Mantém backups antes da limpeza
- Configura retenção por tipo

### 4. Integração Multi-Modal
- Armazena texto, contexto e metadados
- Suporta diferentes fontes (ChatGPT, manual, automático)
- Mantém histórico de mudanças

---

## 📊 Métricas e Monitoramento

### Dashboard de Memória
Acesse: `http://179.125.169.148:8000/docs`

### Estatísticas Disponíveis
- Total de memórias armazenadas
- Distribuição por tipo
- Memórias recentes
- Backup status
- Uso de espaço

### Alertas Automáticos
- Backup falhando
- Espaço em disco baixo
- Serviço offline
- Erros de API

---

## 🚀 Próximos Passos

### Para Você
1. **Comece a usar**: Armazene suas próximas conversas importantes
2. **Configure ChatGPT**: Use as Actions ou Custom GPT
3. **Desenvolva o hábito**: Sempre consulte a memória antes de conversas importantes
4. **Monitore**: Verifique periodicamente as estatísticas

### Futuras Melhorias
- Interface web para visualização
- Exportação de memórias
- Sincronização com outros dispositivos
- Análise de padrões de conversas
- Sugestões automáticas de contexto

---

## 📞 Acesso Rápido

### URLs Importantes
- **Saúde**: http://179.125.169.148:8000/health
- **Docs**: http://179.125.169.148:8000/docs
- **Memória**: http://179.125.169.148:8000/memory/stats
- **Busca**: http://179.125.169.148:8000/memory/search

### Arquivos de Configuração
- **Serviço**: `/home/agourakis82/.config/systemd/user/ragpp-memory-service.service`
- **Auto-start**: `/home/agourakis82/.config/autostart/ragpp-memory-service.desktop`
- **Logs**: `ragpp/logs/memory_server.log`
- **Dados**: `ragpp/data/memory/`

---

## 🎯 Resumo

**Sua memória extendida está 100% operacional!** 

Agora você tem:
- ✅ Sistema que **nunca esquece** suas conversas importantes
- ✅ **Auto-inicialização** transparente 
- ✅ **Busca inteligente** para recuperar contexto
- ✅ **Backup automático** para segurança
- ✅ **Integração perfeita** com ChatGPT
- ✅ **Acesso remoto** de qualquer lugar

**Não precisa mais relembrar tudo - sua memória extendida faz isso por você!** 🧠✨
