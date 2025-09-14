#!/usr/bin/env python3
"""
MCP-PubMed Web Integration
Creates web search queries and stores results in MCP for PCS project.
"""

import webbrowser
import urllib.parse
import subprocess
from typing import List, Dict
import time


class MCPWebSearchIntegration:
    """Integrates web search with MCP memory for academic research."""

    def __init__(self):
        self.search_engines = {
            "pubmed": {
                "name": "PubMed",
                "url": "https://pubmed.ncbi.nlm.nih.gov/?term={}",
                "description": "NCBI PubMed biomedical literature",
            },
            "scholar": {
                "name": "Google Scholar",
                "url": "https://scholar.google.com/scholar?q={}",
                "description": "Academic papers across disciplines",
            },
            "arxiv": {
                "name": "arXiv",
                "url": "https://arxiv.org/search/?query={}&searchtype=all",
                "description": "Preprints in physics, math, CS",
            },
            "semantic": {
                "name": "Semantic Scholar",
                "url": "https://www.semanticscholar.org/search?q={}",
                "description": "AI-powered research tool",
            },
            "researchgate": {
                "name": "ResearchGate",
                "url": "https://www.researchgate.net/search?q={}",
                "description": "Academic social network",
            },
            "nature": {
                "name": "Nature",
                "url": "https://www.nature.com/search?q={}",
                "description": "Nature journal publications",
            },
            "sciencedirect": {
                "name": "ScienceDirect",
                "url": "https://www.sciencedirect.com/search?qs={}",
                "description": "Elsevier scientific database",
            },
        }

        self.pcs_queries = [
            "semantic networks cognitive neuroscience",
            "EEG eye tracking reading comprehension",
            "information entropy brain networks",
            "graph curvature brain connectivity",
            "computational psychiatry semantic processing",
            "word association semantic networks",
            "multilingual semantic representation",
            "fractal analysis cognitive networks",
            "ricci curvature brain networks",
            "transition entropy cognitive graphs",
        ]

    def create_search_url(self, query: str, engine: str) -> str:
        """Create search URL for given query and engine."""
        if engine not in self.search_engines:
            raise ValueError(f"Unknown search engine: {engine}")

        encoded_query = urllib.parse.quote_plus(query)
        return self.search_engines[engine]["url"].format(encoded_query)

    def open_search(self, query: str, engines: List[str] = None) -> Dict:
        """Open search queries in browser and create MCP memory."""
        if engines is None:
            engines = ["pubmed", "scholar"]

        results = {"query": query, "opened_urls": [], "engines_used": engines}

        print(f"🔍 Opening search for: {query}")

        for engine in engines:
            try:
                url = self.create_search_url(query, engine)
                webbrowser.open(url)
                results["opened_urls"].append(url)

                engine_info = self.search_engines[engine]
                print(f"  📖 {engine_info['name']}: {url}")

                time.sleep(1)  # Delay between browser tabs

            except Exception as e:
                print(f"  ❌ Error opening {engine}: {e}")

        # Create MCP memory for this search session
        self.create_search_memory(query, results)

        return results

    def create_search_memory(self, query: str, results: Dict) -> bool:
        """Create MCP memory entry for search session."""
        try:
            engines_text = ", ".join(results["engines_used"])
            urls_text = "\n".join(f"- {url}" for url in results["opened_urls"])

            content = f"""
Academic Search Session: {query}

Search Engines Used: {engines_text}
Search URLs:
{urls_text}

Search performed on: {time.strftime('%Y-%m-%d %H:%M:%S')}

Instructions for manual review:
1. Review search results in opened browser tabs
2. Identify relevant papers for PCS project
3. Save important papers to Zotero
4. Create individual MCP memories for key findings
""".strip()

            # Extract PCS-relevant tags
            tags = ["web_search", "literature_review", "manual_review"]
            pcs_tags = self._extract_pcs_tags(query)
            tags.extend(pcs_tags)

            # Add engine tags
            tags.extend(results["engines_used"])

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
                    "research_progress",
                    "--tags",
                ]
                + tags
                + ["--importance", "3"]
            )

            result = subprocess.run(mcp_command, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ Search session saved to MCP memory")
                return True
            else:
                print(f"❌ Failed to save search session: {result.stderr}")
                return False

        except Exception as e:
            print(f"Error creating search memory: {e}")
            return False

    def _extract_pcs_tags(self, text: str) -> List[str]:
        """Extract PCS-relevant tags from search query."""
        pcs_keywords = {
            "semantic": ["semantic", "meaning", "conceptual"],
            "network": ["network", "graph", "connectivity", "topology"],
            "eeg": ["eeg", "brain", "neural", "neuroimaging"],
            "eye_tracking": ["eye", "tracking", "saccade", "fixation", "gaze"],
            "entropy": ["entropy", "information", "complexity"],
            "curvature": ["curvature", "ricci", "geometry", "manifold"],
            "cognition": ["cognitive", "cognition", "mental"],
            "language": ["language", "linguistic", "word", "reading"],
            "multilingual": ["multilingual", "cross-linguistic"],
            "fractal": ["fractal", "scaling"],
            "psychiatry": ["psychiatry", "psychiatric", "mental health"],
        }

        text_lower = text.lower()
        found_tags = []

        for tag, keywords in pcs_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                found_tags.append(tag)

        return found_tags

    def run_pcs_search_session(self, engines: List[str] = None) -> Dict:
        """Run comprehensive PCS literature search session."""
        if engines is None:
            engines = ["pubmed", "scholar"]

        print("🧠 Starting PCS Literature Search Session")
        print("=" * 50)
        print(f"Search engines: {', '.join(engines)}")
        print(f"Total queries: {len(self.pcs_queries)}")
        print("\nThis will open multiple browser tabs for manual review.")

        input("Press Enter to continue...")

        session_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "engines": engines,
            "queries": [],
            "total_urls": 0,
        }

        for i, query in enumerate(self.pcs_queries, 1):
            print(f"\n[{i}/{len(self.pcs_queries)}] {query}")

            try:
                results = self.open_search(query, engines)
                session_results["queries"].append(results)
                session_results["total_urls"] += len(results["opened_urls"])

                # Pause between queries to avoid overwhelming
                if i < len(self.pcs_queries):
                    time.sleep(3)

            except Exception as e:
                print(f"Error with query '{query}': {e}")

        # Create session summary memory
        self.create_session_summary(session_results)

        print(f"\n✅ PCS Search Session Complete!")
        print(f"Opened {session_results['total_urls']} search URLs")
        print("All search sessions saved to MCP memory")
        print("\nNext steps:")
        print("1. Review opened browser tabs")
        print("2. Save relevant papers to Zotero")
        print("3. Create specific MCP memories for key findings")

        return session_results

    def create_session_summary(self, session_results: Dict) -> bool:
        """Create summary memory for entire search session."""
        try:
            queries_text = "\n".join(
                f"- {r['query']}" for r in session_results["queries"]
            )

            content = f"""
PCS Literature Search Session Summary

Session Date: {session_results['timestamp']}
Search Engines: {', '.join(session_results['engines'])}
Total Queries: {len(session_results['queries'])}
Total URLs Opened: {session_results['total_urls']}

Queries Executed:
{queries_text}

Session Status: Manual review in progress
Next Steps:
1. Review all opened browser tabs
2. Identify papers relevant to PCS project goals
3. Save important papers to Zotero for citation management
4. Create individual MCP memories for breakthrough findings
5. Note any gaps in literature for future investigation

PCS Focus Areas Covered:
- Semantic networks and cognitive neuroscience
- EEG and eye-tracking in reading comprehension  
- Information entropy in brain networks
- Graph curvature approaches to brain connectivity
- Computational psychiatry and semantic processing
- Word association networks (SWOW relevance)
- Multilingual semantic representation
- Fractal analysis in cognitive networks
""".strip()

            memory_manager_path = (
                "/home/agourakis82/workspace/pcs-meta-repo/scripts/memory_manager.py"
            )

            mcp_command = [
                "python",
                memory_manager_path,
                "add",
                content,
                "--category",
                "research_progress",
                "--tags",
                "literature_review",
                "session_summary",
                "pcs_research",
                "manual_review",
                "--importance",
                "4",
            ]

            result = subprocess.run(mcp_command, capture_output=True, text=True)

            return result.returncode == 0

        except Exception as e:
            print(f"Error creating session summary: {e}")
            return False

    def quick_search(self, query: str, engine: str = "pubmed") -> str:
        """Quick single search with MCP memory creation."""
        try:
            url = self.create_search_url(query, engine)
            webbrowser.open(url)

            # Create simple memory
            results = {"query": query, "opened_urls": [url], "engines_used": [engine]}

            self.create_search_memory(query, results)

            print(f"🔍 Opened {engine}: {query}")
            print(f"URL: {url}")
            print("✅ Search saved to MCP memory")

            return url

        except Exception as e:
            print(f"Error in quick search: {e}")
            return ""


def main():
    """Command-line interface for MCP web search integration."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MCP-PubMed Web Search Integration for PCS"
    )
    parser.add_argument(
        "action",
        choices=["quick", "pcs-session", "search", "engines"],
        help="Search action to perform",
    )
    parser.add_argument("--query", help="Search query for quick/search actions")
    parser.add_argument(
        "--engine", default="pubmed", help="Search engine for quick action"
    )
    parser.add_argument(
        "--engines",
        nargs="+",
        default=["pubmed", "scholar"],
        help="Search engines for search/pcs-session actions",
    )

    args = parser.parse_args()

    integration = MCPWebSearchIntegration()

    if args.action == "quick":
        if not args.query:
            print("Error: --query required for quick action")
            return

        integration.quick_search(args.query, args.engine)

    elif args.action == "search":
        if not args.query:
            print("Error: --query required for search action")
            return

        integration.open_search(args.query, args.engines)

    elif args.action == "pcs-session":
        integration.run_pcs_search_session(args.engines)

    elif args.action == "engines":
        print("Available Search Engines:")
        print("=" * 30)

        for key, engine in integration.search_engines.items():
            print(f"\n{key}: {engine['name']}")
            print(f"   {engine['description']}")


if __name__ == "__main__":
    main()
