"""
Scientific Discovery Radar - Continuous Knowledge Updates
=========================================================

Monitoring system for scientific sources with novelty detection,
summarization, and automated knowledge base updates.

This module implements the "24/7 Scientific Discovery" component
of the RAG++ system, following the outlined strategy.
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import feedparser
import requests
from loguru import logger


@dataclass
class SourceConfig:
    """Configuration for a scientific source"""
    name: str
    type: str  # 'rss', 'api', 'web'
    url: str
    enabled: bool = True
    check_interval: int = 3600  # seconds

class ScientificDiscoveryRadar:
    """
    Continuous monitoring system for scientific literature and discoveries.
    
    Features:
    - RSS feed monitoring (arXiv, Nature, Science, etc.)
    - Novelty detection using embedding similarity
    - Automated summarization with citations
    - Knowledge base integration
    """
    
    def __init__(self, rag_agent, sources_config: List[SourceConfig]):
        self.rag_agent = rag_agent
        self.sources = sources_config
        self.seen_articles: set[str] = set()
        self.running = False
        
    def fetch_new_articles(self) -> List[Tuple[str, str, str]]:
        """
        Fetch latest articles from all configured RSS feeds.
        
        Returns:
            List of (title, content, link) tuples for new articles
        """
        new_items = []
        
        for source in self.sources:
            if not source.enabled:
                continue
                
            try:
                if source.type == "rss":
                    items = self._fetch_rss_feed(source)
                    new_items.extend(items)
                elif source.type == "api":
                    items = self._fetch_api_source(source)
                    new_items.extend(items)
                    
            except Exception as e:
                logger.error(f"Error fetching from {source.name}: {e}")
                continue
        
        logger.info(f"Fetched {len(new_items)} new articles")
        return new_items
    
    def _fetch_rss_feed(self, source: SourceConfig) -> List[Tuple[str, str, str]]:
        """Fetch articles from RSS feed"""
        items = []
        
        try:
            feed = feedparser.parse(source.url)
            
            for entry in feed.entries:
                # Create unique ID for the article
                entry_id = entry.get("id") or entry.get("link") or ""
                if not entry_id:
                    continue
                    
                # Hash the ID to create a consistent identifier
                article_hash = hashlib.md5(entry_id.encode()).hexdigest()
                
                if article_hash not in self.seen_articles:
                    self.seen_articles.add(article_hash)
                    
                    title = entry.get("title", "")
                    link = entry.get("link", "")
                    
                    # Extract content (try different fields)
                    content = (
                        entry.get("summary") or 
                        entry.get("description") or 
                        entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
                    )
                    
                    # Clean HTML tags if present
                    content = self._clean_html(content)
                    
                    if title and content:
                        items.append((title, content, link))
                        
        except Exception as e:
            logger.error(f"Error parsing RSS feed {source.url}: {e}")
            
        return items
    
    def _fetch_api_source(self, source: SourceConfig) -> List[Tuple[str, str, str]]:
        """Fetch articles from API source (placeholder for future implementation)"""
        # This could be extended to support specific APIs like:
        # - arXiv API
        # - PubMed API  
        # - CrossRef API
        # - etc.
        return []
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and clean text"""
        import re

        # Remove HTML tags
        clean_text = re.sub('<.*?>', '', text)
        # Clean whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text
    
    def is_novel_article(
        self, title: str, content: str, threshold: float = 0.8
    ) -> bool:
        """
        Determine if article is novel using embedding similarity.
        
        Args:
            title: Article title
            content: Article content/abstract
            threshold: Similarity threshold (higher = more strict)
            
        Returns:
            True if article appears novel
        """
        try:
            # Combine title and content for embedding
            full_text = f"{title} {content}"
            
            # Query knowledge base for similar content
            results = self.rag_agent.query_knowledge_base(full_text, top_k=1)
            
            if not results:
                return True  # No existing data, consider novel
                
            # Check similarity with closest match
            closest = results[0]
            distance = float(closest.get("cosine_distance", 1.0))
            
            # Novel if distance is above threshold
            is_novel = distance > threshold
            
            logger.info(
                f"Novelty check: {title[:50]}... "
                f"Distance: {distance:.3f}, Novel: {is_novel}"
            )
            
            return is_novel
            
        except Exception as e:
            logger.error(f"Error checking novelty: {e}")
            return False  # Conservative: don't add if we can't verify
    
    def summarize_article(self, title: str, content: str, source_url: str) -> str:
        """
        Generate summary with citations using LLM.
        
        Args:
            title: Article title
            content: Article content
            source_url: Original source URL
            
        Returns:
            Summary with citation
        """
        try:
            # Truncate content if too long (model token limits)
            max_content_length = 2000
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            prompt = (
                f"Título do Artigo: {title}\n"
                f"Conteúdo do Artigo: {content}\n\n"
                "Resuma os principais achados deste artigo em 3-5 frases. "
                "Se introduz algo novo ou disruptivo, destaque isso. "
                "Mantenha o foco em descobertas científicas e inovações. "
                f"Cite a fonte como [{source_url}] no resumo.\n\n"
                "Resumo:"
            )
            
            params = {"temperature": 0.25, "max_output_tokens": 256}
            response = self.rag_agent.generation_model.predict(prompt, **params)
            summary = response.text.strip()
            
            # Ensure source is cited
            if source_url not in summary:
                summary += f" (Fonte: {source_url})"
                
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing article: {e}")
            return f"Artigo: {title} - {content[:200]}... (Fonte: {source_url})"
    
    def update_knowledge_base_from_feeds(self) -> Dict[str, int]:
        """
        Main update loop: fetch articles, check novelty, summarize, and store.
        
        Returns:
            Statistics about the update process
        """
        stats = {
            "fetched": 0,
            "novel": 0,
            "added": 0,
            "errors": 0
        }
        
        try:
            # Fetch new articles
            new_articles = self.fetch_new_articles()
            stats["fetched"] = len(new_articles)
            
            for title, content, url in new_articles:
                try:
                    # Check if article is novel
                    if self.is_novel_article(
                        title, content, 
                        threshold=self.rag_agent.config.novelty_threshold
                    ):
                        stats["novel"] += 1
                        
                        # Generate summary with citations
                        summary = self.summarize_article(title, content, url)
                        
                        # Add to knowledge base
                        doc_id = hashlib.md5(url.encode()).hexdigest()
                        metadata = {
                            "original_title": title,
                            "discovery_date": datetime.now(timezone.utc).isoformat(),
                            "source_type": "scientific_radar"
                        }
                        
                        success = self.rag_agent.add_document(
                            doc_id=doc_id,
                            content=summary,
                            source=url,
                            metadata=metadata
                        )
                        
                        if success:
                            stats["added"] += 1
                            logger.info(f"Added novel article: {title[:50]}...")
                        else:
                            stats["errors"] += 1
                    else:
                        logger.debug(f"Skipped (not novel): {title[:50]}...")
                        
                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"Error processing article '{title}': {e}")
                    
        except Exception as e:
            logger.error(f"Error in knowledge base update: {e}")
            stats["errors"] += 1
            
        # Log summary
        logger.info(
            f"Update complete: {stats['fetched']} fetched, "
            f"{stats['novel']} novel, {stats['added']} added, "
            f"{stats['errors']} errors"
        )
        
        return stats
    
    async def run_continuous_monitoring(self, check_interval: int = 3600):
        """
        Run continuous monitoring loop.
        
        Args:
            check_interval: Seconds between checks (default: 1 hour)
        """
        self.running = True
        logger.info(f"Starting continuous monitoring (interval: {check_interval}s)")
        
        while self.running:
            try:
                # Update knowledge base
                stats = self.update_knowledge_base_from_feeds()
                
                # Log periodic summary
                if stats["added"] > 0:
                    logger.info(f"Discovery radar: added {stats['added']} new insights")
                
                # Wait for next cycle
                await asyncio.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
                
        self.running = False
        logger.info("Continuous monitoring stopped")
    
    def stop_monitoring(self):
        """Stop the continuous monitoring loop"""
        self.running = False


# Default scientific sources configuration
DEFAULT_SOURCES = [
    SourceConfig(
        name="arXiv_CS_AI",
        type="rss",
        url="http://export.arxiv.org/rss/cs.AI",
        check_interval=3600
    ),
    SourceConfig(
        name="arXiv_CS_LG", 
        type="rss",
        url="http://export.arxiv.org/rss/cs.LG",
        check_interval=3600
    ),
    SourceConfig(
        name="Nature_AI",
        type="rss", 
        url="https://www.nature.com/subjects/machine-learning.rss",
        check_interval=7200
    ),
    SourceConfig(
        name="ScienceDaily_AI",
        type="rss",
        url="https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml",
        check_interval=7200
    ),
    SourceConfig(
        name="MIT_Tech_Review",
        type="rss",
        url="https://www.technologyreview.com/feed/",
        check_interval=7200
    )
]    )
]