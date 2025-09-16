# Interface de Busca na Literatura Científica

## Visão Geral

Esta interface permite buscar na literatura científica e na memória do projeto usando a API RAG++ que foi implementada. A interface suporta tanto modo interativo quanto linha de comando.

## Arquivos

- `scripts/literature_search_interface.py`: Interface principal de busca
- `scripts/demo_literature_search.py`: Demonstração e exemplos de uso

## Funcionalidades

### 🔍 Busca na Literatura
- **Busca híbrida**: Combina busca semântica e por palavras-chave
- **Busca semântica**: Usa embeddings para encontrar conteúdo relacionado
- **Busca por palavras-chave**: Busca tradicional por termos específicos

### 🧠 Busca na Memória do Projeto
- Busca no contexto armazenado do projeto
- Inclui conversas, insights e documentação
- Filtros por tipo de memória e relevância

### 📊 Formatação Rica
- Metadados completos (autores, DOI, ano, revista)
- Scores de relevância
- Links para fontes
- Resumos truncados automaticamente
- Informações sobre fontes dos resultados

## Configuração

### Variáveis de Ambiente

```bash
export RAG_API_TOKEN="seu_token_aqui"
export RAG_BASE_URL="http://localhost:8000"  # opcional
```

### Servidor RAG++

O servidor deve estar rodando em `http://localhost:8000` (ou URL configurada).

## Uso

### Modo Interativo

```bash
python scripts/literature_search_interface.py
```

Interface com menu que permite:
1. Buscar na literatura científica
2. Buscar na memória do projeto  
3. Ver categorias disponíveis
4. Ver pesquisas recentes
5. Sair

### Linha de Comando

```bash
# Busca básica
python scripts/literature_search_interface.py "EEG transformers"

# Com opções
python scripts/literature_search_interface.py "mixed models EEG" -n 15 -t semantic

# Buscar na memória
python scripts/literature_search_interface.py "surprisal models" --memory

# Sem informações das fontes
python scripts/literature_search_interface.py "ZuCo dataset" --no-sources
```

### Parâmetros da Linha de Comando

- `query`: Consulta de busca (obrigatório)
- `-n, --max-results`: Número máximo de resultados (padrão: 10)
- `-t, --search-type`: Tipo de busca - `hybrid`, `semantic`, `keyword` (padrão: `hybrid`)
- `--no-sources`: Não incluir informações das fontes
- `--base-url`: URL base do servidor (padrão: `http://localhost:8000`)
- `--token`: Token de autenticação
- `--memory`: Buscar na memória em vez da literatura

## Exemplos de Consultas Úteis

### Para nosso projeto de EEG/Eye-tracking:

1. **Processamento Semântico EEG**:
   ```
   "EEG semantic processing transformers language models"
   ```

2. **Eye-tracking e Compreensão**:
   ```
   "eye tracking reading comprehension neural networks"
   ```

3. **Surprisal e Atividade Cerebral**:
   ```
   "surprisal language models brain activity"
   ```

4. **Modelos Estatísticos para EEG**:
   ```
   "mixed effects models EEG time series"
   ```

5. **Datasets Específicos**:
   ```
   "ZuCo dataset reading comprehension"
   "GECO corpus eye tracking"
   "SWOW word association networks"
   ```

6. **Métodos Avançados**:
   ```
   "cluster-based permutation tests EEG"
   "brain encoding decoding language"
   "neural language processing GPU acceleration"
   ```

## Estrutura de Resposta

### Literatura Científica

```json
{
  "query": "consulta realizada",
  "confidence": 0.87,
  "timestamp": "2025-09-12T10:30:00Z",
  "results": [
    {
      "title": "Título do artigo",
      "authors": "Autores",
      "year": 2024,
      "journal": "Revista",
      "doi": "10.xxxx/xxxx",
      "url": "https://...",
      "abstract": "Resumo do artigo",
      "keywords": ["palavra1", "palavra2"],
      "relevance_score": 0.95
    }
  ],
  "sources": {
    "published_papers": 5,
    "project_docs": 2
  }
}
```

### Memória do Projeto

```json
{
  "results": [
    {
      "content": "Conteúdo da memória",
      "memory_type": "general",
      "importance_score": 0.8,
      "timestamp": "2025-09-12T10:30:00Z"
    }
  ]
}
```

## Integração com Pipeline

A interface pode ser integrada ao pipeline principal para:

1. **Busca automática de literatura relevante** durante execução
2. **Documentação automática** de métodos usados
3. **Validação de abordagens** contra literatura recente
4. **Descoberta de novos métodos** e datasets

## Troubleshooting

### Erro 403/401 - Não autorizado
- Verificar se `RAG_API_TOKEN` está configurado
- Verificar se o token está correto

### Erro 503 - Servidor indisponível  
- Verificar se o servidor RAG++ está rodando
- Verificar se a URL está correta

### Nenhum resultado encontrado
- Tentar consultas mais gerais
- Usar busca semântica em vez de keywords
- Verificar se há dados indexados no servidor

### Servidor RAG não inicializado
- Verificar logs do servidor: `journalctl -u ragpp-mcp-server`
- Reiniciar o serviço: `sudo systemctl restart ragpp-mcp-server`

## Extensões Futuras

1. **Cache local** de resultados frequentes
2. **Exportação** para BibTeX/EndNote
3. **Filtros avançados** por ano, revista, tipo de estudo
4. **Notificações** de novos artigos relevantes
5. **Integração com Zotero/Mendeley**
6. **Análise de citações** e redes de colaboração
