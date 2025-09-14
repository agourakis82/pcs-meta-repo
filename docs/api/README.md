# API Documentation - MCP Server v0.2.1

*Gerado automaticamente em 2025-09-14 19:59:31*

## Visão Geral

Esta documentação descreve todos os endpoints e funcionalidades da API do MCP Server.

## Estrutura da API

### Routers Disponíveis

- **Admin** (`/admin`) - Funcionalidades administrativas
- **RAG** (`/rag`) - Sistema de Retrieval-Augmented Generation  
- **Data** (`/data`) - Gerenciamento de dados e datasets
- **Notebooks** (`/notebooks`) - Execução e gerenciamento de notebooks
- **Processing** (`/processing`) - Sistema de processamento de jobs

### Autenticação

Todos os endpoints requerem autenticação via API key no header:
```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### Admin Router

#### GET /admin/health
- **Descrição**: Verifica saúde do sistema
- **Autenticação**: Requerida
- **Resposta**: Status da aplicação e componentes

#### GET /admin/stats  
- **Descrição**: Estatísticas do sistema
- **Autenticação**: Requerida
- **Resposta**: Métricas de uso e performance

### RAG Router

#### POST /rag/query
- **Descrição**: Executa consulta RAG
- **Autenticação**: Requerida
- **Body**: 
  ```json
  {
    "query": "string",
    "limit": "integer (opcional, default: 10)"
  }
  ```
- **Resposta**: Resultados da busca com contexto

#### GET /rag/documents
- **Descrição**: Lista documentos indexados
- **Autenticação**: Requerida
- **Resposta**: Lista de documentos com metadados

### Data Router

#### GET /data/datasets
- **Descrição**: Lista datasets disponíveis
- **Autenticação**: Requerida  
- **Resposta**: Lista de datasets com informações

#### POST /data/upload
- **Descrição**: Upload de novo dataset
- **Autenticação**: Requerida
- **Body**: Multipart form data
- **Resposta**: Confirmação de upload

### Notebooks Router

#### GET /notebooks/list
- **Descrição**: Lista notebooks disponíveis
- **Autenticação**: Requerida
- **Resposta**: Lista de notebooks

#### POST /notebooks/execute
- **Descrição**: Executa notebook
- **Autenticação**: Requerida
- **Body**:
  ```json
  {
    "notebook_path": "string",
    "parameters": "object (opcional)"
  }
  ```

### Processing Router

#### POST /processing/job
- **Descrição**: Submete job para processamento
- **Autenticação**: Requerida
- **Body**:
  ```json
  {
    "job_type": "string",
    "data": "object",
    "priority": "integer (opcional)"
  }
  ```

#### GET /processing/jobs
- **Descrição**: Lista jobs ativos
- **Autenticação**: Requerida
- **Resposta**: Lista de jobs com status

## Códigos de Resposta

- **200**: Sucesso
- **400**: Erro de validação
- **401**: Não autorizado
- **403**: Proibido
- **404**: Não encontrado
- **422**: Erro de processamento
- **500**: Erro interno do servidor

## Modelos de Dados

### Estruturas de Resposta

Todas as respostas seguem o formato padrão:
```json
{
  "status": "success|error",
  "data": "object|array",
  "message": "string (opcional)",
  "timestamp": "ISO 8601 datetime"
}
```

### Configuração

Ver arquivo `api/config.py` para todas as configurações disponíveis.

---

*Documentação gerada automaticamente pelo Sistema G1*
