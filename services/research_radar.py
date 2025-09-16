"""
Continuous research radar: monitors RSS feeds, detects novelty, summarizes,
and injects into the BigQuery-backed knowledge base.

Depends on:
- services.rag_bigquery (ingestion + embeddings + retrieval)
- feedparser (RSS)
- pyyaml (config)
"""

from __future__ import annotations

import hashlib
import logging
from typing import Dict, Iterable, List, Tuple

import feedparser
import yaml

from services.rag_bigquery import add_document, get_embedding, query_knowledge_base
from services.rag_bigquery import _get_singleton as _kb_singleton

logger = logging.getLogger(__name__)


def load_radar_config(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _stable_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class RadarState:
    def __init__(self) -> None:
        self.seen_ids: set[str] = set()


def fetch_new_articles(config: Dict, state: RadarState) -> List[Tuple[str, str, str]]:
    """Return list of (title, content, url) for unseen RSS entries."""
    new_items: List[Tuple[str, str, str]] = []
    for src in config.get("sources", []):
        if src.get("type") != "rss":
            continue
        url = src.get("url")
        if not url:
            continue
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            logger.warning("Failed to parse feed %s: %s", url, e)
            continue
        for entry in getattr(feed, "entries", []):
            eid = entry.get("id") or entry.get("link") or _stable_id(
                entry.get("title", "") + entry.get("summary", "")
            )
            if not eid or eid in state.seen_ids:
                continue
            state.seen_ids.add(eid)
            title = entry.get("title", "Untitled")
            link = entry.get("link", "")
            content = (
                entry.get("summary")
                or entry.get("description")
                or entry.get("content", [{}])[0].get("value", "")
                or ""
            )
            new_items.append((title, content, link))
    return new_items


def is_novel_article(title: str, content: str, threshold: float = 0.8) -> bool:
    """Simple embedding-distance novelty filter using the KB search."""
    text = f"{title} {content}".strip()
    results = query_knowledge_base(text, top_k=1)
    if not results:
        return True
    dist = float(results[0].get("cosine_distance", 1.0))
    return dist > threshold


def summarize_article(title: str, content: str, source_url: str) -> str:
    """Summarize article via the same generator used by the KB module."""
    kb = _kb_singleton()  # Reuse initialized generator
    prompt = (
        f"Article Title: {title}\n"
        f"Article Content: {content}\n\n"
        "Summarize the key finding of this article in 3-5 sentences. "
        "If it introduces something novel or disruptive, highlight that. "
        f"Cite the source as [{source_url}] in the summary."
    )
    resp = kb._generator.generate_content(prompt)  # type: ignore[attr-defined]
    summary = (resp.text or "").strip()
    if source_url and source_url not in summary:
        summary += f" (Source: {source_url})"
    return summary


def update_knowledge_base_from_feeds(config_path: str) -> Dict[str, int]:
    """Process configured feeds and update KB. Returns stats."""
    cfg = load_radar_config(config_path)
    novelty_threshold = float(cfg.get("novelty_threshold", 0.8))
    state = RadarState()

    # Ensure KB is ready
    _kb_singleton().ensure_schema()

    added = 0
    skipped = 0
    items = fetch_new_articles(cfg, state)
    for title, content, url in items:
        try:
            if is_novel_article(title, content, threshold=novelty_threshold):
                summary = summarize_article(title, content, url)
                doc_id = url or _stable_id(title + content)
                add_document(doc_id, summary, source=url)
                added += 1
                logger.info("Added new summary for '%s'", title)
            else:
                skipped += 1
                logger.debug("Skipped (not novel): %s", title)
        except Exception as e:
            logger.warning("Failed processing article '%s': %s", title, e)
            skipped += 1

    return {"added": added, "skipped": skipped}

