#!/usr/bin/env python3
"""
Tree Search System for RAG++
Sistema avançado de busca em árvore para navegação hierárquica de dados
"""

import asyncio
import heapq
import json
import logging
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

# Configurar logging
logger = logging.getLogger(__name__)


class SearchStrategy(Enum):
    """Estratégias de busca em árvore"""

    DEPTH_FIRST = "dfs"  # Busca em profundidade
    BREADTH_FIRST = "bfs"  # Busca em largura
    A_STAR = "a_star"  # A* (heurística)
    BEST_FIRST = "best_first"  # Best-first search
    ITERATIVE_DEEPENING = "iterative_deepening"  # Aprofundamento iterativo


class NodeType(Enum):
    """Tipos de nós na árvore"""

    ROOT = "root"
    CATEGORY = "category"
    DOCUMENT = "document"
    SECTION = "section"
    CONCEPT = "concept"
    REFERENCE = "reference"
    MEMORY = "memory"
    SEARCH_RESULT = "search_result"


@dataclass
class TreeNode:
    """Nó da árvore de busca"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    content: str = ""
    node_type: NodeType = NodeType.DOCUMENT
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0  # Score de relevância/importância
    depth: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Processar após inicialização"""
        if not self.name and self.content:
            # Usar as primeiras palavras do conteúdo como nome
            if len(self.content) > 50:
                self.name = self.content[:50] + "..."
            else:
                self.name = self.content

    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário"""
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "node_type": self.node_type.value,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "metadata": self.metadata,
            "score": self.score,
            "depth": self.depth,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TreeNode":
        """Criar a partir de dicionário"""
        node = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            content=data.get("content", ""),
            node_type=NodeType(data.get("node_type", "document")),
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            metadata=data.get("metadata", {}),
            score=data.get("score", 0.0),
            depth=data.get("depth", 0),
            tags=data.get("tags", []),
        )

        if "created_at" in data:
            try:
                node.created_at = datetime.fromisoformat(data["created_at"])
            except Exception:
                pass

        return node


@dataclass
class SearchResult:
    """Resultado de uma busca em árvore"""

    node: TreeNode
    path: List[str]  # Caminho do root até o nó
    relevance_score: float
    strategy_used: SearchStrategy
    search_metadata: Dict[str, Any] = field(default_factory=dict)


class TreeSearchEngine:
    """Motor de busca em árvore avançado"""

    def __init__(self):
        self.nodes: Dict[str, TreeNode] = {}
        self.root_id: Optional[str] = None
        self.indexes: Dict[str, Dict[str, Set[str]]] = {
            "content": defaultdict(set),  # palavra -> set de node_ids
            "tags": defaultdict(set),
            "node_type": defaultdict(set),
            "metadata": defaultdict(set),
        }

    def add_node(self, node: TreeNode, parent_id: Optional[str] = None) -> str:
        """Adicionar nó à árvore"""
        if parent_id:
            if parent_id not in self.nodes:
                raise ValueError(f"Parent node {parent_id} not found")

            parent = self.nodes[parent_id]
            node.parent_id = parent_id
            node.depth = parent.depth + 1

            if node.id not in parent.children_ids:
                parent.children_ids.append(node.id)
        else:
            # Nó raiz
            if self.root_id is None:
                self.root_id = node.id
                node.depth = 0

        # Adicionar aos índices
        self._index_node(node)

        # Armazenar nó
        self.nodes[node.id] = node

        logger.info(f"Added node {node.id} ({node.node_type.value}): {node.name[:50]}")
        return node.id

    def _index_node(self, node: TreeNode):
        """Indexar nó para buscas rápidas"""
        # Indexar conteúdo
        words = self._extract_words(node.content + " " + node.name)
        for word in words:
            self.indexes["content"][word.lower()].add(node.id)

        # Indexar tags
        for tag in node.tags:
            self.indexes["tags"][tag.lower()].add(node.id)

        # Indexar tipo
        self.indexes["node_type"][node.node_type.value].add(node.id)

        # Indexar metadados
        for key, value in node.metadata.items():
            if isinstance(value, str):
                self.indexes["metadata"][f"{key}:{value.lower()}"].add(node.id)

    def _extract_words(self, text: str) -> List[str]:
        """Extrair palavras do texto"""
        import re

        # Remove pontuação e divide em palavras
        words = re.findall(r"\b\w+\b", text.lower())
        return [w for w in words if len(w) > 2]  # Palavras com mais de 2 caracteres

    def get_node(self, node_id: str) -> Optional[TreeNode]:
        """Obter nó por ID"""
        return self.nodes.get(node_id)

    def get_children(self, node_id: str) -> List[TreeNode]:
        """Obter filhos de um nó"""
        node = self.nodes.get(node_id)
        if not node:
            return []

        return [
            self.nodes[child_id]
            for child_id in node.children_ids
            if child_id in self.nodes
        ]

    def get_ancestors(self, node_id: str) -> List[TreeNode]:
        """Obter ancestrais de um nó (caminho até a raiz)"""
        ancestors = []
        current_id = node_id

        while current_id and current_id in self.nodes:
            node = self.nodes[current_id]
            if node.parent_id:
                parent = self.nodes.get(node.parent_id)
                if parent:
                    ancestors.append(parent)
                current_id = node.parent_id
            else:
                break

        return list(reversed(ancestors))  # Da raiz para o nó

    def search(
        self,
        query: str,
        strategy: SearchStrategy = SearchStrategy.BEST_FIRST,
        max_results: int = 10,
        node_types: Optional[List[NodeType]] = None,
        min_score: float = 0.0,
        search_depth: Optional[int] = None,
    ) -> List[SearchResult]:
        """Buscar na árvore usando diferentes estratégias"""

        logger.info(f"Searching: '{query}' using {strategy.value}")

        # Encontrar nós candidatos usando índices
        candidate_ids = self._find_candidates(query, node_types)

        if not candidate_ids:
            return []

        # Aplicar estratégia de busca
        if strategy == SearchStrategy.DEPTH_FIRST:
            results = self._depth_first_search(
                query, candidate_ids, max_results, min_score, search_depth
            )
        elif strategy == SearchStrategy.BREADTH_FIRST:
            results = self._breadth_first_search(
                query, candidate_ids, max_results, min_score, search_depth
            )
        elif strategy == SearchStrategy.A_STAR:
            results = self._a_star_search(query, candidate_ids, max_results, min_score)
        elif strategy == SearchStrategy.BEST_FIRST:
            results = self._best_first_search(
                query, candidate_ids, max_results, min_score
            )
        elif strategy == SearchStrategy.ITERATIVE_DEEPENING:
            results = self._iterative_deepening_search(
                query, candidate_ids, max_results, min_score
            )
        else:
            results = self._best_first_search(
                query, candidate_ids, max_results, min_score
            )

        logger.info(f"Found {len(results)} results")
        return results

    def _find_candidates(
        self, query: str, node_types: Optional[List[NodeType]] = None
    ) -> Set[str]:
        """Encontrar nós candidatos usando índices"""
        candidates = set()
        query_words = self._extract_words(query)

        # Buscar por palavras no conteúdo
        for word in query_words:
            candidates.update(self.indexes["content"].get(word, set()))

        # Filtrar por tipo se especificado
        if node_types:
            type_candidates = set()
            for node_type in node_types:
                type_candidates.update(
                    self.indexes["node_type"].get(node_type.value, set())
                )
            candidates = candidates.intersection(type_candidates)

        return candidates

    def _calculate_relevance(self, node: TreeNode, query: str) -> float:
        """Calcular relevância de um nó para a query"""
        score = 0.0
        query_words = set(self._extract_words(query))

        # Pontuação por conteúdo
        content_words = set(self._extract_words(node.content + " " + node.name))
        common_words = query_words.intersection(content_words)
        if query_words:
            content_score = len(common_words) / len(query_words)
            score += content_score * 0.7

        # Pontuação por tags
        tag_words = set(
            word.lower() for tag in node.tags for word in self._extract_words(tag)
        )
        tag_common = query_words.intersection(tag_words)
        if query_words:
            tag_score = len(tag_common) / len(query_words)
            score += tag_score * 0.2

        # Bonus por score do nó
        score += min(node.score / 10.0, 0.1)  # Máximo 0.1 de bonus

        return score

    def _depth_first_search(
        self,
        query: str,
        candidate_ids: Set[str],
        max_results: int,
        min_score: float,
        max_depth: Optional[int] = None,
    ) -> List[SearchResult]:
        """Busca em profundidade (DFS)"""
        results = []
        visited = set()

        def dfs(node_id: str, path: List[str]):
            if len(results) >= max_results:
                return

            if node_id in visited:
                return

            visited.add(node_id)
            node = self.nodes.get(node_id)

            if not node:
                return

            if max_depth is not None and node.depth > max_depth:
                return

            # Verificar se é candidato
            if node_id in candidate_ids:
                relevance = self._calculate_relevance(node, query)
                if relevance >= min_score:
                    result = SearchResult(
                        node=node,
                        path=path + [node_id],
                        relevance_score=relevance,
                        strategy_used=SearchStrategy.DEPTH_FIRST,
                    )
                    results.append(result)

            # Continuar para filhos
            for child_id in node.children_ids:
                dfs(child_id, path + [node_id])

        # Começar da raiz se existir
        if self.root_id:
            dfs(self.root_id, [])

        # Ordenar por relevância
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:max_results]

    def _breadth_first_search(
        self,
        query: str,
        candidate_ids: Set[str],
        max_results: int,
        min_score: float,
        max_depth: Optional[int] = None,
    ) -> List[SearchResult]:
        """Busca em largura (BFS)"""
        if not self.root_id:
            return []

        results = []
        visited = set()
        queue = deque([(self.root_id, [])])  # (node_id, path)

        while queue and len(results) < max_results:
            node_id, path = queue.popleft()

            if node_id in visited:
                continue

            visited.add(node_id)
            node = self.nodes.get(node_id)

            if not node:
                continue

            if max_depth is not None and node.depth > max_depth:
                continue

            # Verificar se é candidato
            if node_id in candidate_ids:
                relevance = self._calculate_relevance(node, query)
                if relevance >= min_score:
                    result = SearchResult(
                        node=node,
                        path=path + [node_id],
                        relevance_score=relevance,
                        strategy_used=SearchStrategy.BREADTH_FIRST,
                    )
                    results.append(result)

            # Adicionar filhos à queue
            for child_id in node.children_ids:
                if child_id not in visited:
                    queue.append((child_id, path + [node_id]))

        # Ordenar por relevância
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:max_results]

    def _best_first_search(
        self, query: str, candidate_ids: Set[str], max_results: int, min_score: float
    ) -> List[SearchResult]:
        """Busca best-first (prioriza nós com maior relevância)"""
        results = []

        # Calcular relevância para todos os candidatos
        candidates_with_score = []
        for node_id in candidate_ids:
            node = self.nodes.get(node_id)
            if node:
                relevance = self._calculate_relevance(node, query)
                if relevance >= min_score:
                    candidates_with_score.append((relevance, node_id))

        # Ordenar por relevância
        candidates_with_score.sort(reverse=True)

        # Criar resultados
        for relevance, node_id in candidates_with_score[:max_results]:
            node = self.nodes[node_id]
            path = [ancestor.id for ancestor in self.get_ancestors(node_id)] + [node_id]

            result = SearchResult(
                node=node,
                path=path,
                relevance_score=relevance,
                strategy_used=SearchStrategy.BEST_FIRST,
            )
            results.append(result)

        return results

    def _a_star_search(
        self, query: str, candidate_ids: Set[str], max_results: int, min_score: float
    ) -> List[SearchResult]:
        """Busca A* com heurística baseada na relevância"""
        if not self.root_id:
            return []

        results = []
        visited = set()
        # Priority queue: (f_score, g_score, node_id, path)
        heap = [(0, 0, self.root_id, [])]

        while heap and len(results) < max_results:
            f_score, g_score, node_id, path = heapq.heappop(heap)

            if node_id in visited:
                continue

            visited.add(node_id)
            node = self.nodes.get(node_id)

            if not node:
                continue

            # Verificar se é candidato
            if node_id in candidate_ids:
                relevance = self._calculate_relevance(node, query)
                if relevance >= min_score:
                    result = SearchResult(
                        node=node,
                        path=path + [node_id],
                        relevance_score=relevance,
                        strategy_used=SearchStrategy.A_STAR,
                        search_metadata={"g_score": g_score, "f_score": f_score},
                    )
                    results.append(result)

            # Expandir filhos
            for child_id in node.children_ids:
                if child_id not in visited:
                    child = self.nodes.get(child_id)
                    if child:
                        new_g_score = g_score + 1  # Custo uniforme
                        h_score = self._heuristic(child, query)  # Heurística
                        new_f_score = new_g_score + h_score

                        heapq.heappush(
                            heap, (new_f_score, new_g_score, child_id, path + [node_id])
                        )

        # Ordenar por relevância
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:max_results]

    def _heuristic(self, node: TreeNode, query: str) -> float:
        """Heurística para A* (menor é melhor)"""
        relevance = self._calculate_relevance(node, query)
        return 1.0 - relevance  # Inverter para que maior relevância = menor heurística

    def _iterative_deepening_search(
        self, query: str, candidate_ids: Set[str], max_results: int, min_score: float
    ) -> List[SearchResult]:
        """Busca com aprofundamento iterativo"""
        all_results = []
        max_depth = 10  # Profundidade máxima

        for depth in range(max_depth + 1):
            if len(all_results) >= max_results:
                break

            results = self._depth_first_search(
                query, candidate_ids, max_results - len(all_results), min_score, depth
            )

            # Adicionar novos resultados
            existing_ids = {r.node.id for r in all_results}
            new_results = [r for r in results if r.node.id not in existing_ids]
            all_results.extend(new_results)

        # Ordenar por relevância
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return all_results[:max_results]

    def get_tree_structure(
        self, node_id: Optional[str] = None, max_depth: int = 3
    ) -> Dict[str, Any]:
        """Obter estrutura da árvore para visualização"""
        start_node_id = node_id or self.root_id
        if not start_node_id or start_node_id not in self.nodes:
            return {}

        def build_structure(current_id: str, current_depth: int) -> Dict[str, Any]:
            if current_depth > max_depth:
                return {}

            node = self.nodes[current_id]
            children = []

            for child_id in node.children_ids:
                if child_id in self.nodes and current_depth < max_depth:
                    child_structure = build_structure(child_id, current_depth + 1)
                    if child_structure:
                        children.append(child_structure)

            return {
                "id": node.id,
                "name": node.name,
                "type": node.node_type.value,
                "score": node.score,
                "depth": node.depth,
                "children_count": len(node.children_ids),
                "children": children,
            }

        return build_structure(start_node_id, 0)

    def export_tree(self) -> Dict[str, Any]:
        """Exportar árvore completa para JSON"""
        return {
            "root_id": self.root_id,
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "metadata": {
                "total_nodes": len(self.nodes),
                "max_depth": max(
                    (node.depth for node in self.nodes.values()), default=0
                ),
                "node_types": list(
                    set(node.node_type.value for node in self.nodes.values())
                ),
                "exported_at": datetime.now().isoformat(),
            },
        }

    def import_tree(self, data: Dict[str, Any]):
        """Importar árvore de JSON"""
        self.nodes.clear()
        self.indexes = {
            "content": defaultdict(set),
            "tags": defaultdict(set),
            "node_type": defaultdict(set),
            "metadata": defaultdict(set),
        }

        self.root_id = data.get("root_id")

        # Importar nós
        for node_id, node_data in data.get("nodes", {}).items():
            node = TreeNode.from_dict(node_data)
            self.nodes[node_id] = node
            self._index_node(node)

        logger.info(f"Imported tree with {len(self.nodes)} nodes")


# Factory para diferentes tipos de árvores
class TreeFactory:
    """Factory para criar diferentes tipos de árvores especializadas"""

    @staticmethod
    def create_knowledge_tree() -> TreeSearchEngine:
        """Criar árvore de conhecimento para documentos acadêmicos"""
        tree = TreeSearchEngine()

        # Nó raiz
        root = TreeNode(
            name="Knowledge Base",
            content="Root of the knowledge base tree",
            node_type=NodeType.ROOT,
        )
        tree.add_node(root)

        return tree

    @staticmethod
    def create_memory_tree() -> TreeSearchEngine:
        """Criar árvore de memórias para o sistema RAG++"""
        tree = TreeSearchEngine()

        # Nó raiz
        root = TreeNode(
            name="Memory Tree",
            content="Hierarchical organization of RAG++ memories",
            node_type=NodeType.ROOT,
        )
        tree.add_node(root)

        return tree

    @staticmethod
    def create_research_tree() -> TreeSearchEngine:
        """Criar árvore de pesquisa para literatura científica"""
        tree = TreeSearchEngine()

        # Nó raiz
        root = TreeNode(
            name="Research Tree",
            content="Hierarchical organization of scientific literature",
            node_type=NodeType.ROOT,
        )
        tree.add_node(root)

        # Categorias principais
        categories = [
            ("Machine Learning", "Algorithms, models, and applications in ML"),
            ("Statistics", "Statistical methods and analysis"),
            ("Mathematics", "Mathematical foundations and theory"),
            ("Visualization", "Data visualization and graphics"),
        ]

        for cat_name, cat_desc in categories:
            category = TreeNode(
                name=cat_name,
                content=cat_desc,
                node_type=NodeType.CATEGORY,
                tags=[cat_name.lower().replace(" ", "_")],
            )
            tree.add_node(category, root.id)

        return tree


# Exemplo de uso
async def demo_tree_search():
    """Demonstração do sistema de tree search"""
    print("🌳 Tree Search System Demo")
    print("=" * 50)

    # Criar árvore de pesquisa
    tree = TreeFactory.create_research_tree()

    # Adicionar alguns documentos de exemplo
    root_id = tree.root_id
    categories = tree.get_children(root_id)

    if categories:
        ml_category = categories[0]  # Machine Learning

        # Adicionar paper sobre transformers
        paper1 = TreeNode(
            name="Attention Is All You Need",
            content="We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
            node_type=NodeType.DOCUMENT,
            tags=["transformers", "attention", "neural_networks"],
            score=4.8,
            metadata={"authors": ["Vaswani et al."], "year": 2017, "citations": 50000},
        )
        tree.add_node(paper1, ml_category.id)

        # Adicionar seção do paper
        section1 = TreeNode(
            name="Multi-Head Attention",
            content="Multi-head attention allows the model to jointly attend to information from different representation subspaces at different positions.",
            node_type=NodeType.SECTION,
            tags=["attention", "multi_head"],
            score=4.5,
        )
        tree.add_node(section1, paper1.id)

    # Fazer buscas
    print("\n🔍 Testing different search strategies:")

    strategies = [
        SearchStrategy.BEST_FIRST,
        SearchStrategy.DEPTH_FIRST,
        SearchStrategy.BREADTH_FIRST,
        SearchStrategy.A_STAR,
    ]

    query = "attention transformers"

    for strategy in strategies:
        results = tree.search(query, strategy=strategy, max_results=3)
        print(f"\n{strategy.value.upper()}:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.node.name} (score: {result.relevance_score:.3f})")

    # Mostrar estrutura da árvore
    print("\n🌲 Tree Structure:")
    structure = tree.get_tree_structure(max_depth=2)
    print(json.dumps(structure, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(demo_tree_search())
