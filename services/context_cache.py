"""Darwin Platform Context Caching

Context caching awareness for Gemini prompts with stable prefixes.
Implements intelligent prefix detection and caching strategies.
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Context cache entry."""

    cache_key: str
    prefix: str
    suffix: str
    timestamp: datetime
    hit_count: int = 0
    model: str = "gemini-1.5-pro"
    metadata: Optional[Dict[str, Any]] = None


class ContextCache:
    """
    Context caching system for Gemini prompts.

    Detects stable prefixes and manages cache entries for efficient
    prompt processing with Gemini's context caching features.
    """

    def __init__(self, max_cache_size: int = 1000):
        """
        Initialize context cache.

        Args:
            max_cache_size: Maximum number of cache entries
        """
        self.max_cache_size = max_cache_size
        self.cache: Dict[str, CacheEntry] = {}
        self.prefix_stats: Dict[str, int] = {}

    def compute_cache_key(self, prefix: str, model: str = "gemini-1.5-pro") -> str:
        """Compute cache key for prefix and model."""
        content = f"{model}:{prefix}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _find_stable_prefix(self, prompt: str, min_length: int = 50) -> Optional[str]:
        """
        Find stable prefix in prompt.

        Args:
            prompt: Full prompt text
            min_length: Minimum prefix length

        Returns:
            Stable prefix if found, None otherwise
        """
        if len(prompt) < min_length:
            return None

        # Look for common prompt patterns that indicate stable prefixes
        patterns = [
            "You are a",
            "You are an",
            "Act as",
            "Role:",
            "Instructions:",
            "Context:",
            "System:",
            "Background:",
            "The following is",
        ]

        for pattern in patterns:
            if prompt.startswith(pattern):
                # Find natural breakpoints
                breakpoints = ["\n\n", "\n---", "\n###", "\nUser:", "\nHuman:"]

                for breakpoint in breakpoints:
                    pos = prompt.find(breakpoint)
                    if pos > min_length:
                        return prompt[:pos].strip()

        # Fallback: Look for first paragraph break after min_length
        lines = prompt.split("\n")
        accumulated = ""

        for line in lines:
            accumulated += line + "\n"
            if len(accumulated) > min_length and line.strip() == "":
                return accumulated.strip()

        return None

    def analyze_prompt(
        self, prompt: str, model: str = "gemini-1.5-pro"
    ) -> Tuple[Optional[str], str, bool]:
        """
        Analyze prompt for caching opportunities.

        Args:
            prompt: Full prompt text
            model: Model name for caching

        Returns:
            Tuple of (prefix, suffix, cache_available)
        """
        stable_prefix = self._find_stable_prefix(prompt)

        if not stable_prefix:
            return None, prompt, False

        # Check if we've seen this prefix before
        cache_key = self.compute_cache_key(stable_prefix, model)
        cache_available = cache_key in self.cache

        suffix = prompt[len(stable_prefix) :].strip()

        # Update prefix statistics
        prefix_hash = hashlib.sha256(stable_prefix.encode()).hexdigest()[:8]
        self.prefix_stats[prefix_hash] = self.prefix_stats.get(prefix_hash, 0) + 1

        return stable_prefix, suffix, cache_available

    def cache_prefix(
        self,
        prefix: str,
        model: str = "gemini-1.5-pro",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Cache a stable prefix.

        Args:
            prefix: Stable prefix to cache
            model: Model name
            metadata: Optional metadata

        Returns:
            Cache key for the prefix
        """
        cache_key = self.compute_cache_key(prefix, model)

        # Create or update cache entry
        if cache_key in self.cache:
            self.cache[cache_key].hit_count += 1
        else:
            self.cache[cache_key] = CacheEntry(
                cache_key=cache_key,
                prefix=prefix,
                suffix="",  # Will be filled when used
                timestamp=datetime.now(timezone.utc),
                model=model,
                metadata=metadata or {},
            )

        # Evict old entries if cache is full
        if len(self.cache) > self.max_cache_size:
            self._evict_oldest()

        logger.debug(f"Cached prefix with key {cache_key[:8]}...")
        return cache_key

    def get_cached_prompt(
        self, cache_key: str, suffix: str
    ) -> Optional[Tuple[str, str]]:
        """
        Get cached prompt parts.

        Args:
            cache_key: Cache key for prefix
            suffix: New suffix to append

        Returns:
            Tuple of (prefix, full_prompt) if cached, None otherwise
        """
        if cache_key not in self.cache:
            return None

        entry = self.cache[cache_key]
        entry.hit_count += 1
        entry.suffix = suffix

        full_prompt = entry.prefix + "\n\n" + suffix if suffix else entry.prefix

        return entry.prefix, full_prompt

    def _evict_oldest(self):
        """Evict oldest cache entries."""
        if not self.cache:
            return

        # Sort by timestamp and remove oldest 10%
        sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].timestamp)

        evict_count = max(1, len(self.cache) // 10)

        for i in range(evict_count):
            key, _ = sorted_entries[i]
            del self.cache[key]
            logger.debug(f"Evicted cache entry {key[:8]}...")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.cache:
            return {
                "total_entries": 0,
                "hit_ratio": 0.0,
                "cache_utilization": 0.0,
                "top_prefixes": [],
            }

        total_hits = sum(entry.hit_count for entry in self.cache.values())
        total_requests = sum(self.prefix_stats.values())
        hit_ratio = total_hits / total_requests if total_requests > 0 else 0.0

        # Get top prefixes by usage
        top_prefixes = sorted(
            self.prefix_stats.items(), key=lambda x: x[1], reverse=True
        )[:5]

        return {
            "total_entries": len(self.cache),
            "hit_ratio": hit_ratio,
            "cache_utilization": len(self.cache) / self.max_cache_size,
            "total_hits": total_hits,
            "total_requests": total_requests,
            "top_prefixes": [
                {"prefix_hash": prefix_hash, "count": count}
                for prefix_hash, count in top_prefixes
            ],
        }

    def optimize_prompt_for_caching(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze and optimize prompt for context caching.

        Args:
            prompt: Prompt to analyze

        Returns:
            Optimization recommendations
        """
        stable_prefix, suffix, cache_available = self.analyze_prompt(prompt)

        recommendations = []

        if not stable_prefix:
            recommendations.append(
                {
                    "type": "structure",
                    "message": "Consider adding a stable system prompt or context section",
                    "impact": "Could enable context caching for future similar prompts",
                }
            )
        elif len(stable_prefix) < 100:
            recommendations.append(
                {
                    "type": "prefix_length",
                    "message": "Stable prefix is short, consider expanding context section",
                    "impact": "Longer prefixes provide better caching efficiency",
                }
            )

        if cache_available:
            recommendations.append(
                {
                    "type": "cache_hit",
                    "message": "This prompt can use cached context",
                    "impact": "Significant performance improvement expected",
                }
            )

        return {
            "cacheable": stable_prefix is not None,
            "cache_available": cache_available,
            "prefix_length": len(stable_prefix) if stable_prefix else 0,
            "suffix_length": len(suffix),
            "recommendations": recommendations,
            "estimated_savings": self._estimate_savings(stable_prefix, suffix),
        }

    def _estimate_savings(self, prefix: Optional[str], suffix: str) -> Dict[str, Any]:
        """Estimate potential savings from caching."""
        if not prefix:
            return {"tokens_saved": 0, "cost_savings_percent": 0}

        # Rough token estimation (1 token ≈ 4 characters)
        prefix_tokens = len(prefix) // 4
        suffix_tokens = len(suffix) // 4
        total_tokens = prefix_tokens + suffix_tokens

        # Assume cached prefix processing is 80% faster
        savings_percent = (prefix_tokens / total_tokens) * 80 if total_tokens > 0 else 0

        return {
            "prefix_tokens": prefix_tokens,
            "suffix_tokens": suffix_tokens,
            "total_tokens": total_tokens,
            "tokens_saved": prefix_tokens,
            "time_savings_percent": savings_percent,
            "cost_savings_percent": savings_percent * 0.7,  # Conservative estimate
        }

    def export_cache_config(self) -> Dict[str, Any]:
        """
        Export cache configuration for external use.

        Returns:
            Cache configuration for Gemini API
        """
        cached_prefixes = []

        for entry in self.cache.values():
            if entry.hit_count > 1:  # Only export frequently used prefixes
                cached_prefixes.append(
                    {
                        "cache_key": entry.cache_key,
                        "model": entry.model,
                        "content": entry.prefix,
                        "hit_count": entry.hit_count,
                        "created_at": entry.timestamp.isoformat(),
                    }
                )

        return {
            "cached_prefixes": cached_prefixes,
            "cache_stats": self.get_cache_stats(),
            "recommendations": {
                "enable_context_caching": len(cached_prefixes) > 0,
                "optimal_prefix_patterns": self._get_optimal_patterns(),
            },
        }

    def _get_optimal_patterns(self) -> List[str]:
        """Get optimal prefix patterns for caching."""
        return [
            "You are an expert [domain] assistant...",
            "Context: [background information]\\n\\nInstructions:",
            "System: [role and capabilities]\\n\\nUser guidelines:",
            "Background: [domain knowledge]\\n\\nTask:",
        ]


# Global context cache instance
context_cache = ContextCache()


def get_context_cache() -> ContextCache:
    """Get the global context cache instance."""
    return context_cache


def analyze_prompt_caching(
    prompt: str, model: str = "gemini-1.5-pro"
) -> Dict[str, Any]:
    """
    Analyze a prompt for caching opportunities.

    Args:
        prompt: Prompt text to analyze
        model: Target model for caching

    Returns:
        Analysis results and recommendations
    """
    cache = get_context_cache()
    return cache.optimize_prompt_for_caching(prompt)


def prepare_cached_prompt(prompt: str, model: str = "gemini-1.5-pro") -> Dict[str, Any]:
    """
    Prepare a prompt with context caching.

    Args:
        prompt: Original prompt
        model: Target model

    Returns:
        Prepared prompt with caching information
    """
    cache = get_context_cache()
    prefix, suffix, cache_available = cache.analyze_prompt(prompt, model)

    if prefix and not cache_available:
        # Cache the prefix for future use
        cache_key = cache.cache_prefix(prefix, model)
    elif prefix and cache_available:
        # Use existing cache
        cache_key = cache.compute_cache_key(prefix, model)
    else:
        cache_key = None

    return {
        "original_prompt": prompt,
        "cached_prefix": prefix,
        "dynamic_suffix": suffix,
        "cache_key": cache_key,
        "cache_available": cache_available,
        "model": model,
        "optimization": cache.optimize_prompt_for_caching(prompt),
    }
