#!/usr/bin/env python3
"""
Advanced MCP-Academic Integration Hub
Centralizes all academic research workflows with MCP.
"""

import asyncio
import json
import subprocess
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
import time
from datetime import datetime, timedelta
from pathlib import Path
import webbrowser
import urllib.parse
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ResearchPaper:
    """Structured representation of a research paper."""

    title: str
    authors: List[str]
    abstract: str
    journal: str
    publication_date: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    arxiv_id: Optional[str] = None
    keywords: List[str] = None
    url: str = ""
    relevance_score: float = 0.0
    pcs_tags: List[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.pcs_tags is None:
            self.pcs_tags = []


@dataclass
class SearchSession:
    """Research search session tracking."""

    query: str
    engines: List[str]
    timestamp: datetime
    papers_found: List[ResearchPaper]
    total_results: int
    session_id: str
    notes: str = ""


class AdvancedAcademicMCP:
    """Advanced academic research integration with MCP."""

    def __init__(self):
        self.base_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
        self.memory_manager = self.base_path / "scripts" / "memory_manager.py"
        self.sessions_file = self.base_path / "data" / "research_sessions.json"
        self.citations_file = self.base_path / "data" / "citations_database.json"

        # Ensure data directory exists
        (self.base_path / "data").mkdir(exist_ok=True)

        # PCS-specific research areas
        self.pcs_research_areas = {
            "semantic_networks": {
                "keywords": [
                    "semantic network",
                    "conceptual graph",
                    "word association",
                ],
                "priority": 5,
                "datasets": ["SWOW"],
            },
            "neural_reading": {
                "keywords": ["EEG reading", "eye tracking", "neural correlates"],
                "priority": 5,
                "datasets": ["ZuCo"],
            },
            "information_theory": {
                "keywords": ["entropy", "information theory", "complexity"],
                "priority": 4,
                "datasets": ["general"],
            },
            "graph_geometry": {
                "keywords": ["graph curvature", "ricci curvature", "manifold"],
                "priority": 4,
                "datasets": ["general"],
            },
            "computational_psychiatry": {
                "keywords": ["computational psychiatry", "cognitive modeling"],
                "priority": 5,
                "datasets": ["clinical"],
            },
        }

        # Search engine configurations
        self.search_engines = {
            "pubmed": {
                "api_base": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
                "web_url": "https://pubmed.ncbi.nlm.nih.gov/?term={}",
                "rate_limit": 0.34,
            },
            "arxiv": {
                "api_base": "http://export.arxiv.org/api/query",
                "web_url": "https://arxiv.org/search/?query={}&searchtype=all",
                "rate_limit": 3.0,
            },
            "semantic_scholar": {
                "api_base": "https://api.semanticscholar.org/graph/v1/paper/search",
                "web_url": "https://www.semanticscholar.org/search?q={}",
                "rate_limit": 1.0,
            },
        }

    async def comprehensive_research_pipeline(
        self, topic: str, max_papers: int = 20
    ) -> SearchSession:
        """Execute comprehensive research pipeline for a topic."""
        logger.info(f"🔬 Starting comprehensive research pipeline for: {topic}")

        session_id = f"research_{int(time.time())}"
        session = SearchSession(
            query=topic,
            engines=list(self.search_engines.keys()),
            timestamp=datetime.now(),
            papers_found=[],
            total_results=0,
            session_id=session_id,
        )

        # Phase 1: Multi-engine search
        logger.info("📖 Phase 1: Multi-engine literature search")
        all_papers = await self._multi_engine_search(topic, max_papers)

        # Phase 2: Deduplication and ranking
        logger.info("🔍 Phase 2: Deduplication and relevance ranking")
        unique_papers = self._deduplicate_papers(all_papers)
        ranked_papers = self._rank_papers_by_relevance(unique_papers, topic)

        # Phase 3: PCS relevance analysis
        logger.info("🧠 Phase 3: PCS relevance analysis")
        pcs_analyzed = self._analyze_pcs_relevance(ranked_papers)

        # Phase 4: MCP integration
        logger.info("💾 Phase 4: MCP memory integration")
        await self._store_papers_in_mcp(pcs_analyzed[:10], topic)  # Top 10

        # Phase 5: Citation network analysis
        logger.info("🕸️ Phase 5: Citation network mapping")
        citation_network = await self._build_citation_network(pcs_analyzed[:5])

        session.papers_found = pcs_analyzed
        session.total_results = len(pcs_analyzed)

        # Save session
        await self._save_research_session(session)

        # Generate research report
        report = await self._generate_research_report(session, citation_network)
        await self._store_report_in_mcp(report, topic)

        logger.info(
            f"✅ Research pipeline complete: {len(pcs_analyzed)} papers analyzed"
        )
        return session

    async def _multi_engine_search(
        self, query: str, max_papers: int
    ) -> List[ResearchPaper]:
        """Search across multiple academic engines."""
        all_papers = []
        per_engine = max_papers // len(self.search_engines)

        # PubMed search
        pubmed_papers = await self._search_pubmed(query, per_engine)
        all_papers.extend(pubmed_papers)

        # arXiv search
        arxiv_papers = await self._search_arxiv(query, per_engine)
        all_papers.extend(arxiv_papers)

        # Semantic Scholar search
        semantic_papers = await self._search_semantic_scholar(query, per_engine)
        all_papers.extend(semantic_papers)

        return all_papers

    async def _search_pubmed(self, query: str, max_results: int) -> List[ResearchPaper]:
        """Advanced PubMed search with metadata extraction."""
        papers = []

        try:
            # Search phase
            search_url = f"{self.search_engines['pubmed']['api_base']}esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
                "tool": "pcs-academic-hub",
                "email": "agourakis82@gmail.com",
            }

            response = requests.get(search_url, params=search_params)
            response.raise_for_status()
            search_data = response.json()

            pmids = search_data.get("esearchresult", {}).get("idlist", [])
            if not pmids:
                return papers

            await asyncio.sleep(self.search_engines["pubmed"]["rate_limit"])

            # Fetch details
            fetch_url = f"{self.search_engines['pubmed']['api_base']}efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "tool": "pcs-academic-hub",
                "email": "agourakis82@gmail.com",
            }

            fetch_response = requests.get(fetch_url, params=fetch_params)
            fetch_response.raise_for_status()

            papers = self._parse_pubmed_xml_advanced(fetch_response.text)

        except Exception as e:
            logger.error(f"PubMed search error: {e}")

        return papers

    def _parse_pubmed_xml_advanced(self, xml_content: str) -> List[ResearchPaper]:
        """Advanced PubMed XML parsing with enhanced metadata."""
        papers = []

        try:
            root = ET.fromstring(xml_content)

            for article in root.findall(".//PubmedArticle"):
                try:
                    # Basic info
                    pmid_elem = article.find(".//PMID")
                    pmid = pmid_elem.text if pmid_elem is not None else None

                    title_elem = article.find(".//ArticleTitle")
                    title = title_elem.text if title_elem is not None else "No title"

                    # Enhanced abstract parsing
                    abstract_parts = []
                    for abstract_text in article.findall(".//AbstractText"):
                        if abstract_text.text:
                            label = abstract_text.get("Label", "")
                            text = abstract_text.text
                            if label:
                                abstract_parts.append(f"{label}: {text}")
                            else:
                                abstract_parts.append(text)

                    abstract = (
                        "\n".join(abstract_parts) if abstract_parts else "No abstract"
                    )

                    # Authors with affiliations
                    authors = []
                    for author in article.findall(".//Author"):
                        last_name = author.find("LastName")
                        first_name = author.find("ForeName")
                        if last_name is not None and first_name is not None:
                            authors.append(f"{last_name.text}, {first_name.text}")

                    # Journal info
                    journal_elem = article.find(".//Journal/Title")
                    journal = (
                        journal_elem.text if journal_elem is not None else "Unknown"
                    )

                    # Publication date
                    pub_date = self._extract_publication_date(article)

                    # DOI
                    doi_elem = article.find('.//ELocationID[@EIdType="doi"]')
                    doi = doi_elem.text if doi_elem is not None else None

                    # Keywords/MeSH
                    keywords = []
                    for mesh in article.findall(".//MeshHeading/DescriptorName"):
                        if mesh.text:
                            keywords.append(mesh.text)

                    # Chemical list
                    for chemical in article.findall(".//Chemical/NameOfSubstance"):
                        if chemical.text:
                            keywords.append(f"Chemical: {chemical.text}")

                    paper = ResearchPaper(
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        journal=journal,
                        publication_date=pub_date,
                        doi=doi,
                        pmid=pmid,
                        keywords=keywords,
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                    )

                    papers.append(paper)

                except Exception as e:
                    logger.error(f"Error parsing PubMed article: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing PubMed XML: {e}")

        return papers

    def _extract_publication_date(self, article) -> str:
        """Extract publication date with fallbacks."""
        try:
            # Try PubDate first
            pub_date = article.find(".//PubDate")
            if pub_date is not None:
                year = pub_date.find("Year")
                month = pub_date.find("Month")
                day = pub_date.find("Day")

                if year is not None:
                    date_str = year.text
                    if month is not None:
                        month_num = self._month_to_number(month.text)
                        date_str += f"-{month_num:02d}"
                        if day is not None:
                            date_str += f"-{day.text.zfill(2)}"
                    return date_str

            # Fallback to MedlineDate
            medline_date = article.find(".//MedlineDate")
            if medline_date is not None:
                return medline_date.text

        except Exception:
            pass

        return "Unknown"

    def _month_to_number(self, month_str: str) -> int:
        """Convert month name to number."""
        months = {
            "Jan": 1,
            "Feb": 2,
            "Mar": 3,
            "Apr": 4,
            "May": 5,
            "Jun": 6,
            "Jul": 7,
            "Aug": 8,
            "Sep": 9,
            "Oct": 10,
            "Nov": 11,
            "Dec": 12,
        }
        return months.get(month_str[:3], 1)

    async def _search_arxiv(self, query: str, max_results: int) -> List[ResearchPaper]:
        """Search arXiv with API."""
        papers = []

        try:
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }

            response = requests.get(
                self.search_engines["arxiv"]["api_base"], params=params
            )
            response.raise_for_status()

            # Parse Atom feed
            root = ET.fromstring(response.content)
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom",
            }

            for entry in root.findall("atom:entry", ns):
                try:
                    title = entry.find("atom:title", ns).text.strip()

                    # Authors
                    authors = []
                    for author in entry.findall("atom:author", ns):
                        name = author.find("atom:name", ns).text
                        authors.append(name)

                    # Abstract
                    abstract = entry.find("atom:summary", ns).text.strip()

                    # arXiv ID
                    arxiv_id = entry.find("atom:id", ns).text.split("/")[-1]

                    # Published date
                    published = entry.find("atom:published", ns).text[:10]  # YYYY-MM-DD

                    # Categories as keywords
                    keywords = []
                    for category in entry.findall("atom:category", ns):
                        keywords.append(category.get("term"))

                    paper = ResearchPaper(
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        journal="arXiv",
                        publication_date=published,
                        arxiv_id=arxiv_id,
                        keywords=keywords,
                        url=f"https://arxiv.org/abs/{arxiv_id}",
                    )

                    papers.append(paper)

                except Exception as e:
                    logger.error(f"Error parsing arXiv entry: {e}")
                    continue

            await asyncio.sleep(self.search_engines["arxiv"]["rate_limit"])

        except Exception as e:
            logger.error(f"arXiv search error: {e}")

        return papers

    async def _search_semantic_scholar(
        self, query: str, max_results: int
    ) -> List[ResearchPaper]:
        """Search Semantic Scholar API."""
        papers = []

        try:
            params = {
                "query": query,
                "limit": min(max_results, 100),  # API limit
                "fields": "title,authors,abstract,venue,year,externalIds,url",
            }

            response = requests.get(
                self.search_engines["semantic_scholar"]["api_base"], params=params
            )
            response.raise_for_status()

            data = response.json()

            for item in data.get("data", []):
                try:
                    title = item.get("title", "No title")
                    abstract = item.get("abstract", "No abstract")
                    venue = item.get("venue", "Unknown venue")
                    year = str(item.get("year", "Unknown"))

                    # Authors
                    authors = []
                    for author in item.get("authors", []):
                        authors.append(author.get("name", "Unknown"))

                    # External IDs
                    external_ids = item.get("externalIds", {})
                    doi = external_ids.get("DOI")
                    pmid = external_ids.get("PubMed")
                    arxiv_id = external_ids.get("ArXiv")

                    url = item.get("url", "")

                    paper = ResearchPaper(
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        journal=venue,
                        publication_date=year,
                        doi=doi,
                        pmid=pmid,
                        arxiv_id=arxiv_id,
                        url=url,
                    )

                    papers.append(paper)

                except Exception as e:
                    logger.error(f"Error parsing Semantic Scholar result: {e}")
                    continue

            await asyncio.sleep(self.search_engines["semantic_scholar"]["rate_limit"])

        except Exception as e:
            logger.error(f"Semantic Scholar search error: {e}")

        return papers

    def _deduplicate_papers(self, papers: List[ResearchPaper]) -> List[ResearchPaper]:
        """Remove duplicate papers based on title similarity."""
        unique_papers = []
        seen_titles = set()

        for paper in papers:
            # Normalize title for comparison
            normalized_title = paper.title.lower().strip()
            normalized_title = "".join(
                c for c in normalized_title if c.isalnum() or c.isspace()
            )

            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_papers.append(paper)

        logger.info(f"Deduplication: {len(papers)} -> {len(unique_papers)} papers")
        return unique_papers

    def _rank_papers_by_relevance(
        self, papers: List[ResearchPaper], query: str
    ) -> List[ResearchPaper]:
        """Rank papers by relevance to query and PCS project."""
        query_terms = set(query.lower().split())

        for paper in papers:
            score = 0.0

            # Title relevance (highest weight)
            title_terms = set(paper.title.lower().split())
            title_overlap = len(query_terms.intersection(title_terms)) / len(
                query_terms
            )
            score += title_overlap * 3.0

            # Abstract relevance
            abstract_terms = set(paper.abstract.lower().split())
            abstract_overlap = len(query_terms.intersection(abstract_terms)) / len(
                query_terms
            )
            score += abstract_overlap * 2.0

            # Keywords relevance
            keyword_terms = set(" ".join(paper.keywords).lower().split())
            keyword_overlap = len(query_terms.intersection(keyword_terms)) / len(
                query_terms
            )
            score += keyword_overlap * 1.5

            # Recent publication bonus
            try:
                if paper.publication_date and paper.publication_date != "Unknown":
                    year = int(paper.publication_date.split("-")[0])
                    if year >= 2020:
                        score += 0.5
                    elif year >= 2015:
                        score += 0.2
            except:
                pass

            paper.relevance_score = score

        # Sort by relevance score
        papers.sort(key=lambda p: p.relevance_score, reverse=True)
        return papers

    def _analyze_pcs_relevance(
        self, papers: List[ResearchPaper]
    ) -> List[ResearchPaper]:
        """Analyze papers for PCS project relevance."""
        for paper in papers:
            pcs_tags = []
            pcs_score = 0.0

            # Check against PCS research areas
            text_content = (
                f"{paper.title} {paper.abstract} {' '.join(paper.keywords)}".lower()
            )

            for area, config in self.pcs_research_areas.items():
                area_relevance = 0
                for keyword in config["keywords"]:
                    if keyword.lower() in text_content:
                        area_relevance += 1

                if area_relevance > 0:
                    pcs_tags.append(area)
                    pcs_score += (
                        area_relevance * config["priority"] / len(config["keywords"])
                    )

            # Add specific PCS tags
            pcs_keywords = {
                "semantic_networks": ["semantic", "network", "graph", "association"],
                "eeg": ["eeg", "electroencephalography", "brain"],
                "eye_tracking": ["eye", "tracking", "saccade", "fixation"],
                "entropy": ["entropy", "information", "complexity"],
                "curvature": ["curvature", "ricci", "manifold"],
                "multilingual": ["multilingual", "cross-linguistic"],
                "swow": ["word", "association"],
                "zuco": ["reading", "comprehension"],
            }

            for tag, keywords in pcs_keywords.items():
                if any(kw in text_content for kw in keywords):
                    if tag not in pcs_tags:
                        pcs_tags.append(tag)

            paper.pcs_tags = pcs_tags
            paper.relevance_score += pcs_score * 0.1  # Boost for PCS relevance

        return papers

    async def _store_papers_in_mcp(self, papers: List[ResearchPaper], topic: str):
        """Store papers in MCP memory system."""
        for i, paper in enumerate(papers):
            try:
                # Create structured content
                authors_str = ", ".join(paper.authors[:3])
                if len(paper.authors) > 3:
                    authors_str += " et al."

                content = f"""
Research Paper: {paper.title}

Authors: {authors_str}
Journal: {paper.journal} ({paper.publication_date})
Relevance Score: {paper.relevance_score:.2f}

Abstract: {paper.abstract[:500]}{'...' if len(paper.abstract) > 500 else ''}

Keywords: {', '.join(paper.keywords[:10])}
PCS Tags: {', '.join(paper.pcs_tags)}

URLs:
{paper.url}
""".strip()

                if paper.doi:
                    content += f"\nDOI: {paper.doi}"
                if paper.pmid:
                    content += f"\nPMID: {paper.pmid}"
                if paper.arxiv_id:
                    content += f"\narXiv: {paper.arxiv_id}"

                # Determine importance based on relevance
                importance = min(5, max(1, int(paper.relevance_score * 2) + 1))

                # Create tags
                tags = ["literature", "research_paper", topic.replace(" ", "_")]
                tags.extend(paper.pcs_tags)

                # Store in MCP
                cmd = (
                    [
                        "python",
                        str(self.memory_manager),
                        "add",
                        content,
                        "--category",
                        "publications",
                        "--tags",
                    ]
                    + tags
                    + ["--importance", str(importance)]
                )

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    logger.info(f"✅ Stored paper {i+1}: {paper.title[:50]}...")
                else:
                    logger.error(f"❌ Failed to store paper: {result.stderr}")

                await asyncio.sleep(0.1)  # Rate limiting

            except Exception as e:
                logger.error(f"Error storing paper in MCP: {e}")

    async def _build_citation_network(self, papers: List[ResearchPaper]) -> Dict:
        """Build citation network for top papers."""
        # This would integrate with citation APIs
        # For now, return structure for future implementation
        network = {
            "nodes": [],
            "edges": [],
            "stats": {
                "total_papers": len(papers),
                "avg_relevance": sum(p.relevance_score for p in papers) / len(papers)
                if papers
                else 0,
            },
        }

        for paper in papers:
            network["nodes"].append(
                {
                    "id": paper.pmid or paper.arxiv_id or paper.title[:20],
                    "title": paper.title,
                    "relevance": paper.relevance_score,
                    "pcs_tags": paper.pcs_tags,
                }
            )

        return network

    async def _save_research_session(self, session: SearchSession):
        """Save research session to file."""
        try:
            sessions_data = []
            if self.sessions_file.exists():
                with open(self.sessions_file, "r") as f:
                    sessions_data = json.load(f)

            session_dict = asdict(session)
            session_dict["timestamp"] = session.timestamp.isoformat()

            # Convert papers to dict
            session_dict["papers_found"] = [
                asdict(paper) for paper in session.papers_found
            ]

            sessions_data.append(session_dict)

            with open(self.sessions_file, "w") as f:
                json.dump(sessions_data, f, indent=2)

            logger.info(f"✅ Research session saved: {session.session_id}")

        except Exception as e:
            logger.error(f"Error saving research session: {e}")

    async def _generate_research_report(
        self, session: SearchSession, citation_network: Dict
    ) -> str:
        """Generate comprehensive research report."""
        top_papers = session.papers_found[:5]

        report = f"""
# Research Report: {session.query}

**Session ID:** {session.session_id}
**Date:** {session.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Search Engines:** {', '.join(session.engines)}

## Executive Summary

Found {session.total_results} papers across {len(session.engines)} academic databases.
Average relevance score: {citation_network['stats']['avg_relevance']:.2f}

## Top 5 Papers

"""

        for i, paper in enumerate(top_papers, 1):
            authors_str = ", ".join(paper.authors[:2])
            if len(paper.authors) > 2:
                authors_str += " et al."

            report += f"""
### {i}. {paper.title}

**Authors:** {authors_str}
**Journal:** {paper.journal} ({paper.publication_date})
**Relevance Score:** {paper.relevance_score:.2f}
**PCS Tags:** {', '.join(paper.pcs_tags)}

**Abstract:** {paper.abstract[:200]}...

**URL:** {paper.url}
"""
            if paper.doi:
                report += f"**DOI:** {paper.doi}\n"

            report += "\n---\n"

        report += f"""
## PCS Relevance Analysis

**Research Areas Covered:**
"""

        # Analyze coverage of PCS areas
        area_coverage = {}
        for paper in session.papers_found:
            for tag in paper.pcs_tags:
                area_coverage[tag] = area_coverage.get(tag, 0) + 1

        for area, count in sorted(
            area_coverage.items(), key=lambda x: x[1], reverse=True
        ):
            report += f"- {area}: {count} papers\n"

        report += f"""
## Recommendations

1. **High Priority Papers:** Focus on papers with relevance score > 2.0
2. **PCS Integration:** Papers tagged with 'semantic_networks' and 'neural_reading' align with core datasets
3. **Citation Analysis:** Build forward/backward citation network for top papers
4. **Future Searches:** Consider expanding queries for underrepresented areas

## Next Steps

1. Download and organize top papers in Zotero
2. Create detailed notes for high-priority papers
3. Identify potential collaboration opportunities
4. Plan follow-up searches for specific gaps

---
*Report generated by PCS Academic Research Hub*
"""

        return report

    async def _store_report_in_mcp(self, report: str, topic: str):
        """Store research report in MCP."""
        try:
            cmd = [
                "python",
                str(self.memory_manager),
                "add",
                report,
                "--category",
                "research_progress",
                "--tags",
                "research_report",
                "literature_review",
                topic.replace(" ", "_"),
                "--importance",
                "4",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("✅ Research report stored in MCP")
            else:
                logger.error(f"❌ Failed to store report: {result.stderr}")

        except Exception as e:
            logger.error(f"Error storing report: {e}")


async def main():
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Advanced MCP-Academic Integration Hub"
    )
    parser.add_argument(
        "action",
        choices=["research", "pipeline", "sessions", "areas"],
        help="Action to perform",
    )
    parser.add_argument("--topic", help="Research topic")
    parser.add_argument("--max-papers", type=int, default=20, help="Maximum papers")

    args = parser.parse_args()

    hub = AdvancedAcademicMCP()

    if args.action == "research":
        if not args.topic:
            print("Error: --topic required for research action")
            return

        session = await hub.comprehensive_research_pipeline(args.topic, args.max_papers)

        print(f"\n🎯 Research Pipeline Complete!")
        print(f"Topic: {session.query}")
        print(f"Papers Found: {session.total_results}")
        print(f"Session ID: {session.session_id}")
        print(
            f"Top paper: {session.papers_found[0].title if session.papers_found else 'None'}"
        )

    elif args.action == "pipeline":
        # Run comprehensive PCS research pipeline
        pcs_topics = [
            "semantic networks cognitive neuroscience",
            "EEG eye tracking reading comprehension",
            "information entropy brain networks",
            "graph curvature brain connectivity",
            "computational psychiatry semantic processing",
        ]

        print("🧠 Starting Comprehensive PCS Research Pipeline")
        print("=" * 60)

        for topic in pcs_topics:
            print(f"\n🔬 Processing: {topic}")
            session = await hub.comprehensive_research_pipeline(topic, 15)
            print(f"✅ Completed: {session.total_results} papers processed")
            await asyncio.sleep(2)  # Rate limiting between topics

        print("\n🎯 PCS Research Pipeline Complete!")

    elif args.action == "areas":
        print("PCS Research Areas:")
        print("=" * 30)

        for area, config in hub.pcs_research_areas.items():
            print(f"\n{area}:")
            print(f"  Keywords: {', '.join(config['keywords'])}")
            print(f"  Priority: {config['priority']}/5")
            print(f"  Datasets: {', '.join(config['datasets'])}")


if __name__ == "__main__":
    asyncio.run(main())
