"""Darwin Platform Tree-Search Router

REST endpoints for Tree-Search PUCT exploration.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from api.security import rate_limit, require_api_key
from services.tree_search import (
    TestStateEvaluator,
    TreeNode,
    TreeSearch,
    TreeSearchConfig,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tree-search",
    tags=["Tree-Search"],
    dependencies=[Depends(require_api_key), Depends(rate_limit)],
)


class SearchConfigRequest(BaseModel):
    """Tree-Search configuration request."""

    max_budget_nodes: Optional[int] = Field(300, ge=10, le=1000)
    max_depth: Optional[int] = Field(5, ge=1, le=10)
    default_budget: Optional[int] = Field(150, ge=10, le=500)
    c_puct: Optional[float] = Field(1.414, ge=0.1, le=5.0)
    expansion_threshold: Optional[int] = Field(5, ge=1, le=20)
    simulation_rollouts: Optional[int] = Field(3, ge=1, le=10)
    temperature: Optional[float] = Field(1.0, ge=0.0, le=2.0)
    use_progressive_widening: Optional[bool] = Field(True)
    alpha_widening: Optional[float] = Field(0.5, ge=0.1, le=1.0)


class SearchRequest(BaseModel):
    """Tree-Search request."""

    initial_state: str = Field(..., description="Initial state (string)")
    budget: Optional[int] = Field(150, ge=10, le=500, description="Search budget")
    config: Optional[SearchConfigRequest] = Field(None, description="Search config")


class NodeInfo(BaseModel):
    """Tree node information."""

    node_id: str
    depth: int
    visits: int
    mean_value: float
    status: str
    action_taken: Optional[str]
    is_terminal: bool
    puct_score: Optional[float]
    children_count: int


class SearchResult(BaseModel):
    """Tree-Search result."""

    root_node: NodeInfo
    best_action_sequence: List[str]
    search_statistics: Dict[str, Any]
    nodes_explored: int
    search_tree: List[NodeInfo]  # Flattened tree representation


class QuickSearchRequest(BaseModel):
    """Quick search request for simple exploration."""

    query: str = Field(..., description="Search query")
    depth: Optional[int] = Field(3, ge=1, le=5, description="Max search depth")
    budget: Optional[int] = Field(50, ge=10, le=200, description="Search budget")


class QuickSearchResult(BaseModel):
    """Quick search result."""

    query: str
    best_path: List[str]
    exploration_score: float
    nodes_explored: int


def _tree_search_config_from_request(
    config_req: Optional[SearchConfigRequest],
) -> TreeSearchConfig:
    """Convert request config to TreeSearchConfig."""
    if not config_req:
        return TreeSearchConfig()

    return TreeSearchConfig(
        max_budget_nodes=config_req.max_budget_nodes or 300,
        max_depth=config_req.max_depth or 5,
        default_budget=config_req.default_budget or 150,
        c_puct=config_req.c_puct or 1.414,
        expansion_threshold=config_req.expansion_threshold or 5,
        simulation_rollouts=config_req.simulation_rollouts or 3,
        temperature=config_req.temperature or 1.0,
        use_progressive_widening=config_req.use_progressive_widening or True,
        alpha_widening=config_req.alpha_widening or 0.5,
    )


def _node_to_info(node: TreeNode[str], config: TreeSearchConfig) -> NodeInfo:
    """Convert TreeNode to NodeInfo."""
    return NodeInfo(
        node_id=node.node_id,
        depth=node.depth,
        visits=node.visits,
        mean_value=node.mean_value,
        status=node.status.value,
        action_taken=node.action_taken,
        is_terminal=node.is_terminal,
        puct_score=node.puct_score(config) if node.parent else None,
        children_count=len(node.children),
    )


def _flatten_tree(root: TreeNode[str], config: TreeSearchConfig) -> List[NodeInfo]:
    """Flatten tree into list of NodeInfo."""
    nodes = []

    def traverse(node: TreeNode[str]):
        nodes.append(_node_to_info(node, config))
        for child in node.children:
            traverse(child)

    traverse(root)
    return nodes


@router.post("/search", response_model=SearchResult)
async def tree_search(request: SearchRequest, response: Response) -> SearchResult:
    """
    Perform Tree-Search PUCT exploration.

    Args:
        request: Search request with initial state and configuration
        response: FastAPI response for headers

    Returns:
        Tree-Search results with best action sequence
    """
    try:
        # Create configuration
        config = _tree_search_config_from_request(request.config)

        # Use test evaluator for string states
        evaluator = TestStateEvaluator()

        # Create and run tree search
        search = TreeSearch(evaluator, config)
        root_node = await search.search(request.initial_state, request.budget)

        # Get results
        best_sequence = search.get_best_action_sequence()
        statistics = search.get_search_statistics()
        tree_nodes = _flatten_tree(root_node, config)

        # Set response headers
        response.headers["X-Tree-Search-Nodes"] = str(len(tree_nodes))
        response.headers["X-Tree-Search-Depth"] = str(statistics.get("max_depth", 0))

        return SearchResult(
            root_node=_node_to_info(root_node, config),
            best_action_sequence=best_sequence,
            search_statistics=statistics,
            nodes_explored=search.nodes_explored,
            search_tree=tree_nodes,
        )

    except Exception as e:
        logger.error(f"Tree-Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Tree-Search failed: {str(e)}")


@router.post("/quick-search", response_model=QuickSearchResult)
async def quick_search(
    request: QuickSearchRequest, response: Response
) -> QuickSearchResult:
    """
    Quick Tree-Search for simple exploration.

    Args:
        request: Quick search request
        response: FastAPI response for headers

    Returns:
        Quick search results
    """
    try:
        # Simple configuration for quick search
        config = TreeSearchConfig(
            max_depth=request.depth,
            default_budget=request.budget,
            c_puct=1.0,  # Lower exploration for quick search
            expansion_threshold=2,
            simulation_rollouts=1,
            temperature=0.5,
        )

        # Use test evaluator
        evaluator = TestStateEvaluator()

        # Run search
        search = TreeSearch(evaluator, config)
        await search.search(request.query, request.budget)

        # Get best path
        best_path = search.get_best_action_sequence(max_length=request.depth)

        # Calculate exploration score based on tree statistics
        stats = search.get_search_statistics()
        exploration_score = min(
            stats.get("search_efficiency", 0) * stats.get("nodes_count", 1) / 100.0, 1.0
        )

        # Set response headers
        response.headers["X-Quick-Search-Budget"] = str(request.budget)
        response.headers["X-Quick-Search-Depth"] = str(request.depth)

        return QuickSearchResult(
            query=request.query,
            best_path=best_path,
            exploration_score=exploration_score,
            nodes_explored=search.nodes_explored,
        )

    except Exception as e:
        logger.error(f"Quick search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Quick search failed: {str(e)}")


@router.get("/config/defaults")
async def get_default_config() -> SearchConfigRequest:
    """
    Get default Tree-Search configuration.

    Returns:
        Default configuration parameters
    """
    config = TreeSearchConfig()
    return SearchConfigRequest(
        max_budget_nodes=config.max_budget_nodes,
        max_depth=config.max_depth,
        default_budget=config.default_budget,
        c_puct=config.c_puct,
        expansion_threshold=config.expansion_threshold,
        simulation_rollouts=config.simulation_rollouts,
        temperature=config.temperature,
        use_progressive_widening=config.use_progressive_widening,
        alpha_widening=config.alpha_widening,
    )


@router.get("/algorithms")
async def get_algorithms() -> Dict[str, Any]:
    """
    Get information about available Tree-Search algorithms.

    Returns:
        Algorithm information and capabilities
    """
    return {
        "algorithms": [
            {
                "name": "PUCT",
                "description": "Polynomial Upper Confidence Bounds for Trees",
                "best_for": "Exploration with known priors",
                "parameters": ["c_puct", "expansion_threshold"],
            },
            {
                "name": "UCB1",
                "description": "Upper Confidence Bound",
                "best_for": "Pure exploration without priors",
                "parameters": ["c_puct"],
            },
        ],
        "selection_strategies": [
            {"name": "best", "description": "Select highest scoring child"},
            {"name": "temperature", "description": "Temperature-based sampling"},
        ],
        "features": [
            "Progressive widening",
            "Multiple rollout simulations",
            "Configurable depth limits",
            "Statistical tracking",
            "Tree visualization",
        ],
    }


@router.get("/health")
async def tree_search_health() -> Dict[str, str]:
    """
    Health check for Tree-Search service.

    Returns:
        Health status
    """
    try:
        # Test basic tree search functionality
        evaluator = TestStateEvaluator()
        config = TreeSearchConfig(default_budget=5, max_depth=2)
        search = TreeSearch(evaluator, config)

        # Quick test search
        await asyncio.wait_for(search.search("test", budget=5), timeout=2.0)

        return {"status": "healthy", "message": "Tree-Search service operational"}

    except asyncio.TimeoutError:
        return {"status": "degraded", "message": "Tree-Search response slow"}
    except Exception as e:
        logger.error(f"Tree-Search health check failed: {e}")
        return {"status": "unhealthy", "message": f"Tree-Search error: {str(e)}"}
