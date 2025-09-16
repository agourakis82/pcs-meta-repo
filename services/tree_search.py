"""Darwin Platform Tree-Search PUCT Module

Tree-Search with Polynomial Upper Confidence Bounds (PUCT) exploration.
Implements Monte Carlo Tree Search algorithms for intelligent exploration.
"""

import logging
import math
import random
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Type for node states


class NodeStatus(Enum):
    """Node exploration status."""

    UNEXPLORED = "unexplored"
    EXPLORING = "exploring"
    EXPLORED = "explored"
    TERMINAL = "terminal"


@dataclass
class TreeSearchConfig:
    """Tree-Search configuration."""

    max_budget_nodes: int = 300
    max_depth: int = 5
    default_budget: int = 150
    c_puct: float = 1.414  # PUCT exploration constant
    expansion_threshold: int = 5  # Visit threshold before expansion
    simulation_rollouts: int = 3  # Number of rollout simulations
    temperature: float = 1.0  # Selection temperature
    use_progressive_widening: bool = True
    alpha_widening: float = 0.5  # Progressive widening parameter


@dataclass
class TreeNode(Generic[T]):
    """Tree-Search node with PUCT scoring."""

    # Core node properties
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    state: Optional[T] = None
    parent: Optional["TreeNode[T]"] = None
    children: List["TreeNode[T]"] = field(default_factory=list)

    # MCTS statistics
    visits: int = 0
    total_value: float = 0.0
    mean_value: float = 0.0

    # Search metadata
    depth: int = 0
    status: NodeStatus = NodeStatus.UNEXPLORED
    action_taken: Optional[str] = None
    prior_probability: float = 1.0

    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize derived properties."""
        if self.parent:
            self.depth = self.parent.depth + 1

    @property
    def is_root(self) -> bool:
        """Check if this is the root node."""
        return self.parent is None

    @property
    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return len(self.children) == 0

    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal node."""
        return self.status == NodeStatus.TERMINAL

    def add_child(self, child: "TreeNode[T]") -> "TreeNode[T]":
        """Add a child node."""
        child.parent = self
        child.depth = self.depth + 1
        self.children.append(child)
        return child

    def update_statistics(self, value: float) -> None:
        """Update visit statistics with new value."""
        self.visits += 1
        self.total_value += value
        self.mean_value = self.total_value / self.visits

    def puct_score(self, config: TreeSearchConfig) -> float:
        """
        Calculate PUCT (Polynomial Upper Confidence Bounds for Trees) score.

        Args:
            config: Tree-Search configuration

        Returns:
            PUCT score for node selection
        """
        if self.visits == 0:
            return float("inf")  # Unvisited nodes have infinite exploration value

        if not self.parent:
            return self.mean_value

        # PUCT formula: Q(s,a) + c_puct * P(s,a) * sqrt(N(s)) / (1 + N(s,a))
        exploitation = self.mean_value

        exploration = (
            config.c_puct
            * self.prior_probability
            * math.sqrt(self.parent.visits)
            / (1 + self.visits)
        )

        return exploitation + exploration

    def ucb1_score(self, config: TreeSearchConfig) -> float:
        """
        Calculate UCB1 (Upper Confidence Bound) score.

        Args:
            config: Tree-Search configuration

        Returns:
            UCB1 score for node selection
        """
        if self.visits == 0:
            return float("inf")

        if not self.parent:
            return self.mean_value

        # UCB1 formula: Q(s,a) + c * sqrt(log(N(s)) / N(s,a))
        exploitation = self.mean_value
        exploration = config.c_puct * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )

        return exploitation + exploration

    def select_best_child(
        self, config: TreeSearchConfig, scoring_function: str = "puct"
    ) -> Optional["TreeNode[T]"]:
        """
        Select best child using specified scoring function.

        Args:
            config: Tree-Search configuration
            scoring_function: "puct" or "ucb1"

        Returns:
            Best child node or None if no children
        """
        if not self.children:
            return None

        if scoring_function == "puct":

            def score_func(child):
                return child.puct_score(config)
        elif scoring_function == "ucb1":

            def score_func(child):
                return child.ucb1_score(config)
        else:
            raise ValueError(f"Unknown scoring function: {scoring_function}")

        return max(self.children, key=score_func)

    def select_child_with_temperature(
        self, config: TreeSearchConfig, scoring_function: str = "puct"
    ) -> Optional["TreeNode[T]"]:
        """
        Select child using temperature-based sampling.

        Args:
            config: Tree-Search configuration
            scoring_function: "puct" or "ucb1"

        Returns:
            Sampled child node or None if no children
        """
        if not self.children:
            return None

        if config.temperature == 0:
            return self.select_best_child(config, scoring_function)

        # Calculate scores for all children
        if scoring_function == "puct":
            scores = [child.puct_score(config) for child in self.children]
        elif scoring_function == "ucb1":
            scores = [child.ucb1_score(config) for child in self.children]
        else:
            raise ValueError(f"Unknown scoring function: {scoring_function}")

        # Apply temperature scaling
        temp_scores = [score / config.temperature for score in scores]

        # Softmax sampling
        max_score = max(temp_scores)
        exp_scores = [math.exp(score - max_score) for score in temp_scores]
        total = sum(exp_scores)
        probs = [exp_score / total for exp_score in exp_scores]

        # Sample according to probabilities
        rand = random.random()
        cumulative = 0.0
        for i, prob in enumerate(probs):
            cumulative += prob
            if rand <= cumulative:
                return self.children[i]

        return self.children[-1]  # Fallback

    def get_path_to_root(self) -> List["TreeNode[T]"]:
        """Get path from this node to root."""
        path = []
        current = self
        while current:
            path.append(current)
            current = current.parent
        return list(reversed(path))

    def get_subtree_stats(self) -> Dict[str, Any]:
        """Get statistics for entire subtree."""
        nodes_count = 1
        total_visits = self.visits
        max_depth = self.depth
        terminal_nodes = 1 if self.is_terminal else 0

        def traverse(node: "TreeNode[T]"):
            nonlocal nodes_count, total_visits, max_depth, terminal_nodes
            for child in node.children:
                nodes_count += 1
                total_visits += child.visits
                max_depth = max(max_depth, child.depth)
                if child.is_terminal:
                    terminal_nodes += 1
                traverse(child)

        traverse(self)

        return {
            "nodes_count": nodes_count,
            "total_visits": total_visits,
            "max_depth": max_depth,
            "terminal_nodes": terminal_nodes,
            "avg_visits_per_node": total_visits / nodes_count if nodes_count > 0 else 0,
        }


class StateEvaluator(ABC, Generic[T]):
    """Abstract base class for state evaluation."""

    @abstractmethod
    async def evaluate_state(self, state: T) -> float:
        """
        Evaluate the value of a state.

        Args:
            state: State to evaluate

        Returns:
            State value between -1 and 1
        """
        pass

    @abstractmethod
    async def is_terminal_state(self, state: T) -> bool:
        """
        Check if state is terminal.

        Args:
            state: State to check

        Returns:
            True if state is terminal
        """
        pass

    @abstractmethod
    async def generate_actions(self, state: T) -> List[str]:
        """
        Generate possible actions from state.

        Args:
            state: Current state

        Returns:
            List of possible action strings
        """
        pass

    @abstractmethod
    async def apply_action(self, state: T, action: str) -> T:
        """
        Apply action to state to get new state.

        Args:
            state: Current state
            action: Action to apply

        Returns:
            New state after applying action
        """
        pass


class TreeSearch(Generic[T]):
    """Tree-Search with PUCT exploration."""

    def __init__(
        self, evaluator: StateEvaluator[T], config: Optional[TreeSearchConfig] = None
    ):
        """
        Initialize Tree-Search.

        Args:
            evaluator: State evaluator
            config: Tree-Search configuration
        """
        self.evaluator = evaluator
        self.config = config or TreeSearchConfig()
        self.root: Optional[TreeNode[T]] = None
        self.nodes_explored = 0
        self.search_history: List[Dict[str, Any]] = []

    async def search(
        self, initial_state: T, budget: Optional[int] = None
    ) -> TreeNode[T]:
        """
        Run Tree-Search from initial state.

        Args:
            initial_state: Starting state
            budget: Search budget (nodes to explore)

        Returns:
            Root node of search tree
        """
        budget = budget or self.config.default_budget

        # Initialize root node
        self.root = TreeNode(state=initial_state, status=NodeStatus.EXPLORED)
        self.nodes_explored = 0
        self.search_history = []

        logger.info(f"Starting Tree-Search with budget {budget}")

        for iteration in range(budget):
            try:
                # 1. Selection - traverse from root to leaf
                leaf_node = await self._select_leaf(self.root)

                # 2. Expansion - add children to leaf if not terminal
                expansion_threshold = self.config.expansion_threshold
                if (
                    not leaf_node.is_terminal
                    and leaf_node.visits >= expansion_threshold
                ):
                    expanded_nodes = await self._expand_node(leaf_node)
                    if expanded_nodes:
                        # Select one of the new children for simulation
                        leaf_node = random.choice(expanded_nodes)

                # 3. Simulation - rollout from leaf
                value = await self._simulate(leaf_node)

                # 4. Backpropagation - update path to root
                await self._backpropagate(leaf_node, value)

                self.nodes_explored += 1

                # Log progress
                if iteration % 50 == 0:
                    stats = self.root.get_subtree_stats()
                    logger.debug(
                        f"Iteration {iteration}: {stats['nodes_count']} nodes, "
                        f"avg visits {stats['avg_visits_per_node']:.2f}"
                    )

                # Record iteration history
                self.search_history.append(
                    {
                        "iteration": iteration,
                        "leaf_node_id": leaf_node.node_id,
                        "value": value,
                        "nodes_count": self.root.get_subtree_stats()["nodes_count"],
                    }
                )

            except Exception as e:
                logger.error(f"Error in Tree-Search iteration {iteration}: {e}")
                break

        logger.info(
            f"Tree-Search completed: {self.nodes_explored} iterations, "
            f"{self.root.get_subtree_stats()['nodes_count']} total nodes"
        )

        return self.root

    async def _select_leaf(self, node: TreeNode[T]) -> TreeNode[T]:
        """Select a leaf node using PUCT."""
        current = node

        while not current.is_leaf and not current.is_terminal:
            current = current.select_child_with_temperature(
                self.config, scoring_function="puct"
            )
            if current is None:
                break

        return current

    async def _expand_node(self, node: TreeNode[T]) -> List[TreeNode[T]]:
        """Expand node by adding children for possible actions."""
        if node.is_terminal:
            return []

        try:
            actions = await self.evaluator.generate_actions(node.state)

            # Progressive widening - limit number of children
            if self.config.use_progressive_widening:
                alpha = self.config.alpha_widening
                max_children = int(alpha * (node.visits**alpha))
                max_children = max(1, min(max_children, len(actions)))
                actions = actions[:max_children]

            new_children = []
            for action in actions:
                try:
                    new_state = await self.evaluator.apply_action(node.state, action)

                    child = TreeNode(
                        state=new_state,
                        action_taken=action,
                        status=NodeStatus.UNEXPLORED,
                        prior_probability=1.0 / len(actions),  # Uniform prior
                    )

                    # Check if new state is terminal
                    if await self.evaluator.is_terminal_state(new_state):
                        child.status = NodeStatus.TERMINAL

                    node.add_child(child)
                    new_children.append(child)

                except Exception as e:
                    logger.warning(f"Failed to apply action {action}: {e}")
                    continue

            node.status = NodeStatus.EXPLORED
            return new_children

        except Exception as e:
            logger.error(f"Failed to expand node {node.node_id}: {e}")
            return []

    async def _simulate(self, node: TreeNode[T]) -> float:
        """Simulate rollout from node to estimate value."""
        if node.is_terminal:
            return await self.evaluator.evaluate_state(node.state)

        # Simple random rollout
        total_value = 0.0
        for _ in range(self.config.simulation_rollouts):
            try:
                current_state = node.state
                depth = 0

                # Random rollout until terminal or max depth
                while depth < self.config.max_depth:
                    if await self.evaluator.is_terminal_state(current_state):
                        break

                    actions = await self.evaluator.generate_actions(current_state)
                    if not actions:
                        break

                    action = random.choice(actions)
                    current_state = await self.evaluator.apply_action(
                        current_state, action
                    )
                    depth += 1

                # Evaluate final state
                value = await self.evaluator.evaluate_state(current_state)
                total_value += value

            except Exception as e:
                logger.warning(f"Rollout simulation failed: {e}")
                # Use current node's evaluation as fallback
                total_value += await self.evaluator.evaluate_state(node.state)

        return total_value / self.config.simulation_rollouts

    async def _backpropagate(self, node: TreeNode[T], value: float) -> None:
        """Backpropagate value up the tree."""
        current = node

        while current is not None:
            current.update_statistics(value)
            current = current.parent

    def get_best_action_sequence(self, max_length: int = 10) -> List[str]:
        """
        Get best action sequence from root.

        Args:
            max_length: Maximum sequence length

        Returns:
            List of action strings
        """
        if not self.root:
            return []

        sequence = []
        current = self.root

        for _ in range(max_length):
            if not current.children:
                break

            # Select child with highest visit count (most explored)
            best_child = max(current.children, key=lambda c: c.visits)

            if best_child.action_taken:
                sequence.append(best_child.action_taken)

            current = best_child

        return sequence

    def get_search_statistics(self) -> Dict[str, Any]:
        """Get comprehensive search statistics."""
        if not self.root:
            return {}

        stats = self.root.get_subtree_stats()

        return {
            **stats,
            "iterations_completed": self.nodes_explored,
            "search_efficiency": (
                self.nodes_explored / stats["nodes_count"]
                if stats["nodes_count"] > 0
                else 0
            ),
            "average_depth": stats["max_depth"] / 2,  # Rough estimate
            "config": {
                "max_budget_nodes": self.config.max_budget_nodes,
                "c_puct": self.config.c_puct,
                "expansion_threshold": self.config.expansion_threshold,
                "temperature": self.config.temperature,
            },
        }


# Example StateEvaluator for testing
class TestStateEvaluator(StateEvaluator[str]):
    """Simple test evaluator for string states."""

    async def evaluate_state(self, state: str) -> float:
        """Evaluate based on string length."""
        return min(len(state) / 10.0, 1.0)

    async def is_terminal_state(self, state: str) -> bool:
        """Terminal if string length >= 10."""
        return len(state) >= 10

    async def generate_actions(self, state: str) -> List[str]:
        """Generate character additions."""
        if len(state) >= 10:
            return []
        return ["a", "b", "c"]

    async def apply_action(self, state: str, action: str) -> str:
        """Append character to state."""
        return state + action
