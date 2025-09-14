#!/usr/bin/env python3
"""
Academic Search MCP Integration for PCS Project
Integrates multiple academic databases with MCP memory system.
"""

import requests
import subprocess
import xml.etree.ElementTree as ET
from typing import Dict, List
import time
import os
from dataclasses import dataclass


@dataclass
class SearchEngine:
    """Configuration for academic search engines."""

    name: str
    base_url: str
    search_template: str
    description: str


class AcademicSearchMCP:
    """Integrates multiple academic search engines with MCP memory."""

    def __init__(self):
        self.search_engines = {
            "pubmed": SearchEngine(
                name="PubMed",
                base_url="https://pubmed.ncbi.nlm.nih.gov",
                search_template="https://pubmed.ncbi.nlm.nih.gov/?term={}",
                description="Biomedical literature database",
            ),
            "scholar": SearchEngine(
                name="Google Scholar",
                base_url="https://scholar.google.com",
                search_template="https://scholar.google.com/scholar?q={}",
                description="Academic search across disciplines",
            ),
            "arxiv": SearchEngine(
                name="arXiv",
                base_url="https://arxiv.org",
                search_template="https://arxiv.org/search/?query={}&searchtype=all",
                description="Physics, math, CS, and related preprints",
            ),
            "semantic": SearchEngine(
                name="Semantic Scholar",
                base_url="https://www.semanticscholar.org",
                search_template="https://www.semanticscholar.org/search?q={}",
                description="AI-powered research tool",
            ),
            "researchgate": SearchEngine(
                name="ResearchGate",
                base_url="https://www.researchgate.net",
                search_template="https://www.researchgate.net/search?q={}",
                description="Academic social network",
            ),
        }

        # PubMed API configuration
        self.pubmed_api_base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.email = "agourakis82@gmail.com"
        self.tool = "pcs-academic-mcp"
        self.rate_limit = 0.34

    def create_search_memory(
        self, query: str, engine: str, results_summary: str, importance: int = 3
    ) -> bool:
        """Create a memory entry for an academic search."""
        try:
            engine_info = self.search_engines.get(engine, {})

            content = f"""
Academic Search Query: {query}
Search Engine: {engine_info.name if engine_info else engine}
Search URL: {engine_info.search_template.format(query) if engine_info else 'N/A'}

Results Summary:
{results_summary}

Search performed on: {time.strftime('%Y-%m-%d %H:%M:%S')}
""".strip()

            tags = ["academic_search", "literature", engine, "research"]

            # Add PCS-relevant tags based on query
            pcs_tags = self._extract_pcs_tags(query)
            tags.extend(pcs_tags)

            # Call MCP memory creation
            memory_manager_path = (
                "/home/agourakis82/workspace/pcs-meta-repo/scripts/memory_manager.py"
            )

            mcp_command = (
                [
                    "python",
                    memory_manager_path,
                    "add",
                    content,
                    "--category",
                    "publications",
                    "--tags",
                ]
                + tags
                + ["--importance", str(importance)]
            )

            result = subprocess.run(mcp_command, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ Search memory created for: {query}")
                return True
            else:
                print(f"❌ Failed to create search memory: {result.stderr}")
                return False

        except Exception as e:
            print(f"Error creating search memory: {e}")
            return False

    def _extract_pcs_tags(self, text: str) -> List[str]:
        """Extract PCS-relevant tags from text."""
        pcs_keywords = {
            "semantic": ["semantic", "semantics", "meaning", "conceptual"],
            "network": ["network", "graph", "connectivity", "topology"],
            "eeg": ["eeg", "electroencephalography", "brain", "neural"],
            "eye_tracking": ["eye", "tracking", "saccade", "fixation", "gaze"],
            "entropy": ["entropy", "information", "complexity"],
            "curvature": ["curvature", "ricci", "geometry", "manifold"],
            "cognition": ["cognitive", "cognition", "mental", "thinking"],
            "language": ["language", "linguistic", "word", "text"],
            "multilingual": ["multilingual", "cross-linguistic", "bilingual"],
            "fractal": ["fractal", "scaling", "self-similar"],
            "swow": ["word", "association", "swow"],
            "zuco": ["reading", "comprehension", "zuco"],
        }

        text_lower = text.lower()
        found_tags = []

        for tag, keywords in pcs_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                found_tags.append(tag)

        return found_tags

    def pubmed_detailed_search(self, query: str, max_results: int = 5) -> Dict:
        """Perform detailed PubMed search with API."""
        try:
            # Search for PMIDs
            search_url = f"{self.pubmed_api_base}esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
                "tool": self.tool,
                "email": self.email,
            }

            search_response = requests.get(search_url, params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()

            pmids = search_data.get("esearchresult", {}).get("idlist", [])
            if not pmids:
                return {"articles": [], "summary": "No results found"}

            time.sleep(self.rate_limit)

            # Fetch article details
            fetch_url = f"{self.pubmed_api_base}efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "tool": self.tool,
                "email": self.email,
            }

            fetch_response = requests.get(fetch_url, params=fetch_params)
            fetch_response.raise_for_status()

            articles = self._parse_pubmed_xml(fetch_response.text)

            # Create summary
            summary = f"Found {len(articles)} relevant articles:\n"
            for i, article in enumerate(articles[:3], 1):
                authors = ", ".join(article["authors"][:2])
                if len(article["authors"]) > 2:
                    authors += " et al."
                summary += (
                    f"{i}. {article['title']}\n"
                    f"   {authors} - {article['journal']} "
                    f"({article['publication_date']})\n"
                    f"   PMID: {article['pmid']}\n"
                )

            if len(articles) > 3:
                summary += f"... and {len(articles) - 3} more articles"

            return {"articles": articles, "summary": summary}

        except Exception as e:
            error_msg = f"PubMed search error: {e}"
            print(error_msg)
            return {"articles": [], "summary": error_msg}

    def _parse_pubmed_xml(self, xml_content: str) -> List[Dict]:
        """Parse PubMed XML response."""
        articles = []

        try:
            root = ET.fromstring(xml_content)

            for article in root.findall(".//PubmedArticle"):
                try:
                    pmid_elem = article.find(".//PMID")
                    pmid = pmid_elem.text if pmid_elem is not None else "Unknown"

                    title_elem = article.find(".//ArticleTitle")
                    title = title_elem.text if title_elem is not None else "No title"

                    # Authors
                    authors = []
                    for author in article.findall(".//Author"):
                        last_name = author.find("LastName")
                        first_name = author.find("ForeName")
                        if last_name is not None and first_name is not None:
                            authors.append(f"{last_name.text}, {first_name.text}")
                        elif last_name is not None:
                            authors.append(last_name.text)

                    # Journal
                    journal_elem = article.find(".//Journal/Title")
                    journal = (
                        journal_elem.text
                        if journal_elem is not None
                        else "Unknown Journal"
                    )

                    # Publication date
                    pub_date = self._extract_pub_date(article)

                    # DOI
                    doi_elem = article.find('.//ELocationID[@EIdType="doi"]')
                    doi = doi_elem.text if doi_elem is not None else None

                    article_data = {
                        "pmid": pmid,
                        "title": title,
                        "authors": authors,
                        "journal": journal,
                        "publication_date": pub_date,
                        "doi": doi,
                        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    }

                    articles.append(article_data)

                except Exception as e:
                    print(f"Error parsing article: {e}")
                    continue

        except Exception as e:
            print(f"Error parsing XML: {e}")

        return articles

    def _extract_pub_date(self, article) -> str:
        """Extract publication date from article XML."""
        try:
            pub_date = article.find(".//PubDate")
            if pub_date is not None:
                year = pub_date.find("Year")
                month = pub_date.find("Month")
                day = pub_date.find("Day")

                if year is not None:
                    date_str = year.text
                    if month is not None:
                        date_str += f"-{month.text}"
                        if day is not None:
                            date_str += f"-{day.text}"
                    return date_str

            medline_date = article.find(".//MedlineDate")
            if medline_date is not None:
                return medline_date.text

        except Exception:
            pass

        return "Unknown date"

    def store_article_in_mcp(self, article: Dict, importance: int = 3) -> bool:
        """Store a single article in MCP memory."""
        try:
            authors_str = ", ".join(article["authors"][:3])
            if len(article["authors"]) > 3:
                authors_str += " et al."

            content = f"""
Research Article: {article['title']}

Authors: {authors_str}
Journal: {article['journal']} ({article['publication_date']})
PMID: {article['pmid']}
URL: {article['pubmed_url']}
""".strip()

            if article.get("doi"):
                content += f"\nDOI: {article['doi']}"

            tags = ["pubmed", "literature", "research_article"]
            pcs_tags = self._extract_pcs_tags(article["title"])
            tags.extend(pcs_tags)

            memory_manager_path = (
                "/home/agourakis82/workspace/pcs-meta-repo/scripts/memory_manager.py"
            )

            mcp_command = (
                [
                    "python",
                    memory_manager_path,
                    "add",
                    content,
                    "--category",
                    "publications",
                    "--tags",
                ]
                + tags
                + ["--importance", str(importance)]
            )

            result = subprocess.run(mcp_command, capture_output=True, text=True)

            if result.returncode == 0:
                return True
            else:
                print(f"Failed to store article: {result.stderr}")
                return False

        except Exception as e:
            print(f"Error storing article: {e}")
            return False

    def comprehensive_search(
        self, query: str, engines: List[str] = None, store_articles: bool = True
    ) -> Dict:
        """Perform comprehensive search across multiple engines."""
        if engines is None:
            engines = ["pubmed"]

        results = {}

        for engine in engines:
            print(f"\n🔍 Searching {engine.upper()}: {query}")

            if engine == "pubmed":
                # Detailed PubMed search with API
                pubmed_results = self.pubmed_detailed_search(query)
                results[engine] = pubmed_results

                # Store search summary
                self.create_search_memory(
                    query, engine, pubmed_results["summary"], importance=3
                )

                # Store individual articles if requested
                if store_articles and pubmed_results["articles"]:
                    stored_count = 0
                    for article in pubmed_results["articles"]:
                        if self.store_article_in_mcp(article):
                            stored_count += 1
                        time.sleep(0.5)

                    print(f"📚 Stored {stored_count} articles in MCP")

            else:
                # For other engines, create search memory with URL
                engine_info = self.search_engines.get(engine)
                if engine_info:
                    search_url = engine_info.search_template.format(query)
                    summary = (
                        f"Search URL: {search_url}\n"
                        f"Engine: {engine_info.description}\n"
                        f"Manual verification required."
                    )

                    self.create_search_memory(query, engine, summary)
                    results[engine] = {"summary": summary, "url": search_url}

        return results

    def get_pcs_search_plan(self) -> List[Dict]:
        """Get comprehensive search plan for PCS project."""
        return [
            {
                "query": "semantic networks cognitive neuroscience",
                "engines": ["pubmed", "scholar"],
                "importance": 4,
                "description": "Core semantic network research",
            },
            {
                "query": "EEG eye tracking reading comprehension",
                "engines": ["pubmed"],
                "importance": 4,
                "description": "Multimodal reading research (ZuCo relevance)",
            },
            {
                "query": "information entropy brain networks",
                "engines": ["pubmed", "arxiv"],
                "importance": 4,
                "description": "Entropy in neuroscience",
            },
            {
                "query": "graph curvature brain connectivity",
                "engines": ["pubmed", "arxiv"],
                "importance": 4,
                "description": "Geometric approaches to brain networks",
            },
            {
                "query": "computational psychiatry semantic processing",
                "engines": ["pubmed"],
                "importance": 5,
                "description": "Direct PCS field relevance",
            },
            {
                "query": "word association semantic networks",
                "engines": ["pubmed", "scholar"],
                "importance": 4,
                "description": "SWOW-related research",
            },
            {
                "query": "multilingual semantic representation",
                "engines": ["pubmed", "scholar"],
                "importance": 3,
                "description": "Cross-linguistic semantics",
            },
            {
                "query": "fractal analysis cognitive networks",
                "engines": ["pubmed", "arxiv"],
                "importance": 4,
                "description": "Fractal approaches in cognition",
            },
        ]


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Academic Search MCP Integration for PCS"
    )
    parser.add_argument(
        "action", choices=["search", "pcs-plan", "engines"], help="Action to perform"
    )
    parser.add_argument("--query", help="Search query")
    parser.add_argument(
        "--engines", nargs="+", default=["pubmed"], help="Search engines to use"
    )
    parser.add_argument(
        "--no-store", action="store_true", help="Do not store articles in MCP"
    )

    args = parser.parse_args()

    integration = AcademicSearchMCP()

    if args.action == "search":
        if not args.query:
            print("Error: --query required for search action")
            return

        results = integration.comprehensive_search(
            args.query, args.engines, not args.no_store
        )

        print("\n" + "=" * 60)
        print("SEARCH RESULTS SUMMARY")
        print("=" * 60)

        for engine, result in results.items():
            print(f"\n{engine.upper()}:")
            print(result.get("summary", "No summary available"))

    elif args.action == "pcs-plan":
        search_plan = integration.get_pcs_search_plan()

        print("🧠 PCS Literature Review Plan")
        print("=" * 60)

        total_searches = 0
        for search_config in search_plan:
            print(f"\n📖 {search_config['description']}")
            print(f"Query: {search_config['query']}")
            print(f"Engines: {', '.join(search_config['engines'])}")
            print(f"Importance: {search_config['importance']}/5")

            # Execute the search
            results = integration.comprehensive_search(
                search_config["query"], search_config["engines"], store_articles=True
            )

            total_searches += len(search_config["engines"])
            time.sleep(1)  # Rate limiting

        print(f"\n✅ Completed {total_searches} academic searches")
        print("All results stored in MCP memory system")

    elif args.action == "engines":
        print("Available Academic Search Engines:")
        print("=" * 40)

        for key, engine in integration.search_engines.items():
            print(f"\n{key}: {engine.name}")
            print(f"   {engine.description}")
            print(f"   Base URL: {engine.base_url}")


if __name__ == "__main__":
    main()
