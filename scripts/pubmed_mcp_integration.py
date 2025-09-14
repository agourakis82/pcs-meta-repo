#!/usr/bin/env python3
"""
PubMed-MCP Integration for PCS Project
Integrates PubMed search with MCP memory system for academic research.
"""

import requests
import json
import subprocess
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import urllib.parse


class PubMedMCPIntegration:
    """Integrates PubMed API with MCP memory system for PCS research."""

    def __init__(self, email: str = "agourakis82@gmail.com"):
        self.email = email
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.tool = "pcs-pubmed-mcp"
        self.rate_limit = 0.34  # NCBI rate limit: 3 requests per second

    def search_pubmed(
        self, query: str, max_results: int = 10, sort: str = "relevance"
    ) -> List[Dict]:
        """Search PubMed and return article information."""

        # Step 1: Search for PMIDs
        search_url = f"{self.base_url}esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": sort,
            "tool": self.tool,
            "email": self.email,
        }

        try:
            search_response = requests.get(search_url, params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()

            pmids = search_data.get("esearchresult", {}).get("idlist", [])
            if not pmids:
                return []

            time.sleep(self.rate_limit)

            # Step 2: Fetch detailed information
            fetch_url = f"{self.base_url}efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "tool": self.tool,
                "email": self.email,
            }

            fetch_response = requests.get(fetch_url, params=fetch_params)
            fetch_response.raise_for_status()

            return self._parse_pubmed_xml(fetch_response.text)

        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []

    def _parse_pubmed_xml(self, xml_content: str) -> List[Dict]:
        """Parse PubMed XML response into structured data."""
        articles = []

        try:
            root = ET.fromstring(xml_content)

            for article in root.findall(".//PubmedArticle"):
                try:
                    # Basic article info
                    pmid_elem = article.find(".//PMID")
                    pmid = pmid_elem.text if pmid_elem is not None else "Unknown"

                    # Title
                    title_elem = article.find(".//ArticleTitle")
                    title = title_elem.text if title_elem is not None else "No title"

                    # Abstract
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
                        "\n".join(abstract_parts)
                        if abstract_parts
                        else "No abstract available"
                    )

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

                    # Keywords/MeSH terms
                    keywords = []
                    for mesh in article.findall(".//MeshHeading/DescriptorName"):
                        if mesh.text:
                            keywords.append(mesh.text)

                    article_data = {
                        "pmid": pmid,
                        "title": title,
                        "abstract": abstract,
                        "authors": authors,
                        "journal": journal,
                        "publication_date": pub_date,
                        "doi": doi,
                        "keywords": keywords,
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
            # Try different date fields
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

            # Fallback to MedlineDate
            medline_date = article.find(".//MedlineDate")
            if medline_date is not None:
                return medline_date.text

        except Exception:
            pass

        return "Unknown date"

    def add_to_mcp_memory(
        self, article: Dict, importance: int = 3, additional_tags: List[str] = None
    ) -> bool:
        """Add a PubMed article to MCP memory system."""
        try:
            # Prepare memory content
            authors_str = ", ".join(article["authors"][:3])  # First 3 authors
            if len(article["authors"]) > 3:
                authors_str += " et al."

            content = f"""
Title: {article['title']}

Authors: {authors_str}

Journal: {article['journal']} ({article['publication_date']})

Abstract: {article['abstract'][:500]}{'...' if len(article['abstract']) > 500 else ''}

PMID: {article['pmid']}
URL: {article['pubmed_url']}
""".strip()

            if article["doi"]:
                content += f"\nDOI: {article['doi']}"

            # Prepare tags
            tags = ["pubmed", "literature", "research"]
            if additional_tags:
                tags.extend(additional_tags)

            # Add relevant PCS tags based on keywords and content
            pcs_keywords = {
                "semantic": ["semantic", "semantics", "meaning"],
                "network": ["network", "graph", "connectivity"],
                "eeg": ["eeg", "electroencephalography", "brain"],
                "eye_tracking": ["eye tracking", "saccade", "fixation"],
                "entropy": ["entropy", "information theory"],
                "curvature": ["curvature", "ricci", "geometry"],
                "cognition": ["cognitive", "cognition", "mental"],
                "language": ["language", "linguistic", "word"],
                "multilingual": ["multilingual", "cross-linguistic"],
            }

            content_lower = content.lower()
            keywords_lower = [k.lower() for k in article["keywords"]]

            for pcs_tag, search_terms in pcs_keywords.items():
                if any(
                    term in content_lower or term in keywords_lower
                    for term in search_terms
                ):
                    tags.append(pcs_tag)

            # Call MCP memory creation
            mcp_command = (
                [
                    "python",
                    "/home/agourakis82/workspace/pcs-meta-repo/scripts/memory_manager.py",
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
                print(f"✅ Added to MCP: {article['title'][:50]}...")
                return True
            else:
                print(f"❌ Failed to add to MCP: {result.stderr}")
                return False

        except Exception as e:
            print(f"Error adding to MCP: {e}")
            return False

    def search_and_store(
        self,
        query: str,
        max_results: int = 5,
        importance: int = 3,
        tags: List[str] = None,
    ) -> Dict:
        """Search PubMed and store relevant articles in MCP."""
        print(f"🔍 Searching PubMed for: {query}")

        articles = self.search_pubmed(query, max_results)
        stored_count = 0

        for article in articles:
            if self.add_to_mcp_memory(article, importance, tags):
                stored_count += 1
            time.sleep(0.5)  # Rate limiting

        result = {
            "query": query,
            "total_found": len(articles),
            "stored_count": stored_count,
            "articles": articles,
        }

        print(f"📚 Found {len(articles)} articles, stored {stored_count} in MCP")
        return result

    def get_pcs_relevant_searches(self) -> List[Dict]:
        """Get predefined search queries relevant to PCS project."""
        return [
            {
                "query": "semantic networks cognitive neuroscience",
                "tags": ["semantic", "network", "cognition"],
                "importance": 4,
            },
            {
                "query": "EEG eye tracking reading comprehension",
                "tags": ["eeg", "eye_tracking", "language"],
                "importance": 4,
            },
            {
                "query": "information entropy brain networks",
                "tags": ["entropy", "network", "brain"],
                "importance": 4,
            },
            {
                "query": "graph curvature brain connectivity",
                "tags": ["curvature", "network", "brain"],
                "importance": 4,
            },
            {
                "query": "multilingual semantic processing",
                "tags": ["multilingual", "semantic", "language"],
                "importance": 3,
            },
            {
                "query": "computational psychiatry semantic",
                "tags": ["psychiatry", "semantic", "computation"],
                "importance": 5,
            },
            {
                "query": "word association semantic networks",
                "tags": ["semantic", "network", "swow"],
                "importance": 4,
            },
            {
                "query": "fractal analysis cognitive networks",
                "tags": ["fractal", "cognition", "network"],
                "importance": 4,
            },
        ]


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="PubMed-MCP Integration for PCS")
    parser.add_argument(
        "action", choices=["search", "batch", "pcs-relevant"], help="Action to perform"
    )
    parser.add_argument("--query", help="Search query for PubMed")
    parser.add_argument(
        "--max-results", type=int, default=5, help="Maximum results to fetch"
    )
    parser.add_argument(
        "--importance",
        type=int,
        default=3,
        help="Importance level for MCP memory (1-5)",
    )
    parser.add_argument(
        "--tags", nargs="*", default=[], help="Additional tags for MCP memory"
    )

    args = parser.parse_args()

    integration = PubMedMCPIntegration()

    if args.action == "search":
        if not args.query:
            print("Error: --query required for search action")
            return

        result = integration.search_and_store(
            args.query, args.max_results, args.importance, args.tags
        )

        print(f"\n📊 Results Summary:")
        print(f"Query: {result['query']}")
        print(f"Found: {result['total_found']} articles")
        print(f"Stored: {result['stored_count']} in MCP")

    elif args.action == "pcs-relevant":
        searches = integration.get_pcs_relevant_searches()

        print(f"🧠 Running {len(searches)} PCS-relevant searches...")

        total_stored = 0
        for search_config in searches:
            print(f"\n🔍 {search_config['query']}")
            result = integration.search_and_store(
                search_config["query"],
                max_results=3,  # Smaller batches for comprehensive coverage
                importance=search_config["importance"],
                tags=search_config["tags"],
            )
            total_stored += result["stored_count"]
            time.sleep(1)  # Rate limiting between searches

        print(f"\n🎯 PCS Literature Review Complete!")
        print(f"Total articles stored in MCP: {total_stored}")


if __name__ == "__main__":
    main()
