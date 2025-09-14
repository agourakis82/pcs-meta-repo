# Tree Search System - RAG++

## 🌳 Visão Geral

O Tree Search System é um componente avançado do RAG++ que permite organizar e buscar informações de forma hierárquica usando algoritmos de busca em árvore.

## 🚀 Funcionalidades

### Estruturas de Dados
- **TreeNode**: Nós da árvore com conteúdo, metadados e relacionamentos
- **SearchResult**: Resultados de busca com score de relevância e caminho
- **TreeSearchEngine**: Motor de busca com indexação e algoritmos

### Estratégias de Busca
- **Best First**: Prioriza nós com maior relevância (padrão)
- **Depth First**: Busca em profundidade
- **Breadth First**: Busca em largura  
- **A***: Busca heurística otimizada
- **Iterative Deepening**: Aprofundamento iterativo

### Tipos de Nós
- **ROOT**: Nó raiz da árvore
- **CATEGORY**: Categorias organizacionais
- **DOCUMENT**: Documentos e papers
- **SECTION**: Seções dentro de documentos
- **CONCEPT**: Conceitos e tópicos
- **REFERENCE**: Referências e citações
- **MEMORY**: Memórias do sistema RAG++
- **SEARCH_RESULT**: Resultados de busca

## 🔧 API Endpoints

### 1. Buscar na Árvore
```http
POST /tree/search
Content-Type: application/json

{
    "query": "machine learning transformers",
    "strategy": "best_first",
    "max_results": 10,
    "node_types": ["document", "memory"],
    "min_score": 0.0
}
```

**Resposta:**
```json
{
    "query": "machine learning transformers",
    "strategy": "best_first",
    "results": [
        {
            "node_id": "abc-123",
            "name": "Attention Is All You Need",
            "content": "We propose a new simple network architecture...",
            "node_type": "document",
            "relevance_score": 0.85,
            "path": ["root-id", "ml-category-id", "abc-123"],
            "tags": ["transformers", "attention"],
            "metadata": {"authors": ["Vaswani et al."], "year": 2017},
            "score": 4.8,
            "depth": 2
        }
    ],
    "total_found": 1,
    "timestamp": "2024-01-01T12:00:00"
}
```

### 2. Adicionar Nó
```http
POST /tree/add_node
Content-Type: application/json

{
    "name": "New Research Paper",
    "content": "Abstract and content of the paper...",
    "node_type": "document",
    "parent_id": "category-id",
    "tags": ["research", "ai"],
    "metadata": {"authors": ["Author Name"], "year": 2024},
    "score": 4.5
}
```

### 3. Obter Estrutura da Árvore
```http
GET /tree/structure?node_id=root-id&max_depth=3
```

**Resposta:**
```json
{
    "tree_id": "main",
    "root_id": "root-id",
    "total_nodes": 25,
    "max_depth": 4,
    "structure": {
        "id": "root-id",
        "name": "Research Tree",
        "type": "root",
        "score": 0.0,
        "depth": 0,
        "children_count": 4,
        "children": [...]
    }
}
```

### 4. Exportar Árvore
```http
GET /tree/export
```

### 5. Popular com Memórias
```http
POST /tree/populate_from_memories
```

## 💻 Uso Programático

### Importar e Criar Árvore
```python
from ragpp.tree_search_optimized import TreeFactory, TreeNode, NodeType

# Criar árvore de pesquisa
tree = TreeFactory.create_research_tree()

# Criar árvore de conhecimento
knowledge_tree = TreeFactory.create_knowledge_tree()

# Criar árvore de memórias
memory_tree = TreeFactory.create_memory_tree()
```

### Adicionar Nós
```python
# Criar nó
paper = TreeNode(
    name="Attention Is All You Need",
    content="We propose a new simple network architecture...",
    node_type=NodeType.DOCUMENT,
    tags=["transformers", "attention", "neural_networks"],
    metadata={"authors": ["Vaswani et al."], "year": 2017},
    score=4.8
)

# Adicionar à categoria Machine Learning
ml_category_id = "ml-category-id"
tree.add_node(paper, ml_category_id)
```

### Buscar
```python
from ragpp.tree_search_optimized import SearchStrategy

# Busca simples
results = tree.search("attention transformers")

# Busca avançada
results = tree.search(
    query="deep learning networks",
    strategy=SearchStrategy.BEST_FIRST,
    max_results=5,
    node_types=[NodeType.DOCUMENT, NodeType.MEMORY],
    min_score=0.3
)

# Processar resultados
for result in results:
    print(f"{result.node.name}: {result.relevance_score:.3f}")
    print(f"Path: {' > '.join(result.path)}")
```

### Exportar/Importar
```python
# Exportar árvore
data = tree.export_tree()

# Importar árvore
new_tree = TreeSearchEngine()
new_tree.import_tree(data)
```

## 🎯 Casos de Uso

### 1. Organização de Literatura Científica
```python
# Criar hierarquia: Root > Área > Subárea > Papers
tree = TreeFactory.create_research_tree()

# Adicionar paper a Machine Learning
paper = TreeNode(
    name="BERT: Pre-training of Deep Bidirectional Transformers",
    content="We introduce BERT, which stands for Bidirectional...",
    node_type=NodeType.DOCUMENT,
    tags=["bert", "transformers", "nlp"],
    score=4.9
)

ml_category = tree.get_children(tree.root_id)[0]  # Machine Learning
tree.add_node(paper, ml_category.id)
```

### 2. Navegação de Memórias RAG++
```python
# Popular árvore com memórias existentes
# Isso é feito automaticamente via endpoint
# POST /tree/populate_from_memories

# Buscar memórias específicas
results = tree.search(
    "conversation about neural networks",
    node_types=[NodeType.MEMORY],
    max_results=10
)
```

### 3. Análise de Relacionamentos
```python
# Obter estrutura para visualização
structure = tree.get_tree_structure(max_depth=3)

# Analisar caminhos
for result in results:
    ancestors = tree.get_ancestors(result.node.id)
    print(f"Caminho: {' > '.join(n.name for n in ancestors)}")
```

## ⚙️ Configuração

### Inicialização no Servidor
O tree search é inicializado automaticamente quando o servidor RAG++ é iniciado:

```python
# Em ragpp_web_server.py
tree_search_engine = TreeFactory.create_research_tree()
```

### Índices Personalizados
O sistema indexa automaticamente:
- **Conteúdo**: Palavras no texto e nome
- **Tags**: Tags associadas aos nós
- **Tipo**: Tipo do nó
- **Metadados**: Pares chave-valor dos metadados

## 🔍 Algoritmos de Busca

### Best First (Padrão)
Ordena candidatos por relevância e retorna os melhores primeiro.

### Depth First (DFS)
Explora profundamente antes de expandir lateralmente.

### Breadth First (BFS)
Explora todos os nós de uma profundidade antes de avançar.

### A*
Usa heurística baseada na relevância para busca otimizada.

### Iterative Deepening
Combina vantagens de DFS e BFS com múltiplas passadas.

## 📊 Scoring e Relevância

### Cálculo de Relevância
```python
def _calculate_relevance(node, query):
    score = 0.0
    
    # Palavras em comum no conteúdo (70%)
    content_score = len(common_words) / len(query_words) * 0.7
    
    # Palavras em comum nas tags (20%)
    tag_score = len(tag_common) / len(query_words) * 0.2
    
    # Bonus por score do nó (10%)
    bonus = min(node.score / 10.0, 0.1)
    
    return content_score + tag_score + bonus
```

## 🧪 Testes

Execute o script de teste:
```bash
python test_tree_search.py
```

Ou teste individualmente:
```bash
# Testar o módulo
python ragpp/tree_search_optimized.py

# Testar no servidor (primeiro inicie o servidor)
python ragpp/ragpp_web_server.py
```

## 🚀 Próximos Passos

1. **Persistência**: Salvar árvore em banco de dados
2. **Visualização**: Interface web para navegar na árvore
3. **Clustering**: Agrupamento automático de nós similares
4. **Recomendações**: Sugestões baseadas na estrutura da árvore
5. **Métricas**: Analytics de uso e performance

## 📝 Logs e Debugging

O sistema gera logs detalhados:
```
INFO:ragpp.tree_search_optimized:Added node abc-123 (document): Paper Title
INFO:ragpp.tree_search_optimized:Searching: 'query' using best_first
INFO:ragpp.tree_search_optimized:Found 5 results
```

Para debug, aumente o nível de log:
```python
import logging
logging.getLogger('ragpp.tree_search_optimized').setLevel(logging.DEBUG)
```