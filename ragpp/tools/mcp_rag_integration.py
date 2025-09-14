#!/usr/bin/env python3
"""
MCP-RAG++ Integration
Connects your MCP memory system with the RAG pipeline for enhanced retrieval.
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ragpp.tools.psychiatric_research_collector import PsychiatricResearchCollector
from ragpp.tools.router import pick_index


class MCPRAGIntegration:
    """Integrates MCP memory system with RAG++ for enhanced retrieval."""

    def __init__(
        self,
        rag_db_path: str = "ragpp/index/lit2025",
        memory_manager_path: str = "scripts/memory_manager.py",
    ):
        self.rag_db_path = rag_db_path
        self.memory_manager_path = memory_manager_path

        # Initialize Live Literature Collector
        try:
            self.literature_collector = PsychiatricResearchCollector()
            print("✅ Live literature collector (PubMed) initialized.")
        except Exception as e:
            self.literature_collector = None
            print(f"⚠️ Live literature collector could not be initialized: {e}")

        # Initialize ChromaDB for RAG
        self._init_rag_db()

        # MCP categories for different types of knowledge
        self.mcp_categories = {
            "research_findings": "Key research discoveries and insights",
            "methodology": "Experimental methods and protocols",
            "literature_review": "Academic literature analysis",
            "project_progress": "PCS project development updates",
            "computational_results": "Data analysis and computational outputs",
            "theoretical_insights": "Theoretical frameworks and concepts",
        }

    def _init_rag_db(self):
        """Initialize ChromaDB connection."""
        try:
            logging.getLogger("chromadb.telemetry.product.posthog").disabled = True
            self.client = chromadb.PersistentClient(
                path=self.rag_db_path,
                settings=Settings(allow_reset=False, anonymized_telemetry=False),
            )
            self.lit_collection = self.client.get_collection("lit2025")
            print(f"✅ Connected to RAG database: {self.rag_db_path}")
        except Exception as e:
            print(f"❌ Failed to connect to RAG database: {e}")
            self.client = None
            self.lit_collection = None

    def hybrid_search(
        self,
        query: str,
        max_rag_results: int = 5,
        max_mcp_results: int = 3,
        search_type: str = "hybrid",
        include_mcp_categories: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining RAG literature and MCP memories.

        Args:
            query: Search query
            max_rag_results: Max results from RAG literature database
            max_mcp_results: Max results from MCP memory system
            search_type: Type of search ('hybrid', 'live_literature')
            include_mcp_categories: MCP categories to search (default: all)

        Returns:
            Combined search results with sources
        """
        results = {
            "query": query,
            "rag_results": [],
            "mcp_results": [],
            "synthesis": "",
            "sources": {"literature": 0, "memory": 0, "live_literature": 0, "total": 0},
        }

        # 1. Live Literature Search (e.g., PubMed)
        if search_type == "live_literature" and self.literature_collector:
            try:
                print(f"🛰️ Performing live literature search for: '{query}'")
                live_articles = self.literature_collector.search_pubmed_recent(
                    query, years_back=5
                )
                for i, article in enumerate(live_articles):
                    results["rag_results"].append(
                        {
                            "rank": i + 1,
                            "content": article.get("abstract", ""),
                            "metadata": {
                                "title": article.get("title"),
                                "authors": ", ".join(article.get("authors", [])),
                                "journal": article.get("journal"),
                                "year": article.get("year"),
                                "pmid": article.get("pmid"),
                            },
                            "distance": 0.0,  # Not applicable for live search
                            "source_type": "live_literature",
                            "record_id": f"pubmed:{article.get('pmid', 'unknown')}",
                        }
                    )
                results["sources"]["live_literature"] = len(live_articles)
                print(f"📚 Found {len(live_articles)} live literature results")
            except Exception as e:
                print(f"⚠️ Live literature search failed: {e}")

        # 2. RAG Literature Search (ChromaDB)
        if self.lit_collection and search_type != "live_literature":
            try:
                # Determine which index to use based on query
                index_type = pick_index(query)

                rag_search = self.lit_collection.query(
                    query_texts=[query],
                    n_results=max_rag_results,
                    include=["documents", "metadatas", "distances"],
                )

                for i, (doc, meta, dist) in enumerate(
                    zip(
                        rag_search["documents"][0],
                        rag_search["metadatas"][0],
                        rag_search["distances"][0],
                    )
                ):
                    results["rag_results"].append(
                        {
                            "rank": i + 1,
                            "content": doc,
                            "metadata": meta,
                            "distance": dist,
                            "source_type": "literature",
                            "record_id": meta.get("record_id", "unknown"),
                        }
                    )

                results["sources"]["literature"] = len(results["rag_results"])
                print(f"📚 Found {len(results['rag_results'])} literature results")

            except Exception as e:
                print(f"⚠️ RAG search failed: {e}")

        # 3. MCP Memory Search
        if search_type != "live_literature":
            try:
                mcp_results = self._search_mcp_memories(
                    query, max_mcp_results, include_mcp_categories
                )
                results["mcp_results"] = mcp_results
                results["sources"]["memory"] = len(mcp_results)
                print(f"🧠 Found {len(mcp_results)} memory results")

            except Exception as e:
                print(f"⚠️ MCP search failed: {e}")

        # 4. Calculate totals
        results["sources"]["total"] = (
            results["sources"]["literature"]
            + results["sources"]["memory"]
            + results["sources"]["live_literature"]
        )

        # 5. Generate synthesis if we have results
        if results["sources"]["total"] > 0:
            results["synthesis"] = self._synthesize_results(results)

        return results

    def _search_mcp_memories(
        self, query: str, max_results: int = 3, categories: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Search MCP memory system."""
        try:
            # Build MCP search command - use --query parameter
            cmd = ["python", self.memory_manager_path, "search", "--query", query]

            # Add category filter if specified (only first one)
            if categories and categories[0] in self.mcp_categories:
                cmd.extend(["--category", categories[0]])

            # Execute search
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"MCP search error: {result.stderr}")
                return []

            # Parse results (assuming JSON output from memory_manager)
            try:
                mcp_data = json.loads(result.stdout)
                if isinstance(mcp_data, list):
                    return [
                        {
                            "rank": i + 1,
                            "content": mem.get("content", ""),
                            "category": mem.get("category", "unknown"),
                            "tags": mem.get("tags", []),
                            "importance": mem.get("importance", 1),
                            "timestamp": mem.get("timestamp", ""),
                            "source_type": "memory",
                            "memory_id": mem.get("id", f"mem_{i}"),
                        }
                        for i, mem in enumerate(mcp_data)
                    ]
                else:
                    return []

            except json.JSONDecodeError:
                # Fallback: parse simple text output
                lines = result.stdout.strip().split("\n")
                parsed_results = []

                for i, line in enumerate(lines[:max_results]):
                    if line.strip():
                        parsed_results.append(
                            {
                                "rank": i + 1,
                                "content": line.strip(),
                                "source_type": "memory",
                                "memory_id": f"text_{i}",
                            }
                        )

                return parsed_results

        except Exception as e:
            print(f"Error searching MCP memories: {e}")
            return []

    def _synthesize_results(self, results: Dict[str, Any]) -> str:
        """Generate synthesis of RAG and MCP results."""
        synthesis_parts = []

        # Literature synthesis
        if results["rag_results"]:
            source_type = (
                "Live Literature"
                if results["sources"]["live_literature"] > 0
                else "Literature Review"
            )
            lit_summary = f"{source_type} ({len(results['rag_results'])} sources):\n"
            for result in results["rag_results"][:3]:  # Top 3
                record_id = result.get("record_id", "unknown")
                content_preview = (
                    result["content"][:200] + "..."
                    if len(result["content"]) > 200
                    else result["content"]
                )
                lit_summary += f"• [{record_id}]: {content_preview}\n"
            synthesis_parts.append(lit_summary)

        # Memory synthesis
        if results["mcp_results"]:
            mem_summary = f"Project Memory ({len(results['mcp_results'])} entries):\n"
            for result in results["mcp_results"][:3]:  # Top 3
                category = result.get("category", "general")
                content_preview = (
                    result["content"][:200] + "..."
                    if len(result["content"]) > 200
                    else result["content"]
                )
                mem_summary += f"• [{category}]: {content_preview}\n"
            synthesis_parts.append(mem_summary)

        # Integration insight
        if len(synthesis_parts) > 1:
            synthesis_parts.append(
                "Integration: This query benefits from both published literature "
                "and project-specific insights. Consider cross-referencing findings "
                "with ongoing research developments."
            )

        return "\n\n".join(synthesis_parts)

    def store_research_finding(
        self,
        content: str,
        category: str = "research_findings",
        tags: List[str] = None,
        importance: int = 3,
        auto_index_to_rag: bool = True,
    ) -> bool:
        """
        Store a research finding in MCP and optionally index to RAG.

        Args:
            content: The research finding content
            category: MCP category
            tags: Tags for the memory
            importance: Importance level (1-5)
            auto_index_to_rag: Whether to also add to RAG index
        """
        try:
            # Ensure importance is an integer (round if it's a float)
            if isinstance(importance, float):
                importance = int(round(importance))

            # Store in MCP
            mcp_cmd = [
                "python",
                self.memory_manager_path,
                "add",
                content,
                "--category",
                category,
                "--importance",
                str(importance),
            ]

            if tags:
                mcp_cmd.extend(["--tags"] + tags)

            result = subprocess.run(mcp_cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"Failed to store in MCP: {result.stderr}")
                return False

            print(f"✅ Stored research finding in MCP ({category})")

            # Optionally add to RAG index for future retrieval
            if auto_index_to_rag and self.lit_collection:
                try:
                    memory_id = f"mcp_research_{hash(content) % 1000000}"
                    self.lit_collection.add(
                        ids=[memory_id],
                        documents=[content],
                        metadatas=[
                            {
                                "source": "mcp_research",
                                "category": category,
                                "tags": ",".join(tags) if tags else "",
                                "importance": importance,
                            }
                        ],
                    )
                    print(f"✅ Also indexed research finding in RAG")
                except Exception as e:
                    print(f"⚠️ Failed to index in RAG: {e}")

            return True

        except Exception as e:
            print(f"Error storing research finding: {e}")
            return False

    def enhanced_qa(self, question: str) -> Dict[str, Any]:
        """
        Enhanced Q&A using both RAG and MCP with intelligent routing.
        """
        print(f"🤔 Processing question: {question}")

        # Determine search strategy based on question type
        if any(
            keyword in question.lower()
            for keyword in [
                "our",
                "nosso",
                "nossa",
                "projeto",
                "pipeline",
                "método",
                "protocolo",
            ]
        ):
            # Project-specific question - prioritize MCP
            search_results = self.hybrid_search(
                question,
                max_rag_results=2,
                max_mcp_results=5,
                search_type="hybrid",
                include_mcp_categories=[
                    "project_progress",
                    "methodology",
                    "computational_results",
                ],
            )
        else:
            # General research question - prioritize literature
            search_results = self.hybrid_search(
                question,
                max_rag_results=5,
                max_mcp_results=2,
                search_type="hybrid",
                include_mcp_categories=["research_findings", "theoretical_insights"],
            )

        # Structure response
        response = {
            "question": question,
            "answer_type": "hybrid_rag_mcp",
            "sources_found": search_results["sources"],
            "literature_evidence": search_results["rag_results"],
            "project_memory": search_results["mcp_results"],
            "synthesis": search_results["synthesis"],
            "confidence": self._calculate_confidence(search_results),
            "recommendations": self._generate_recommendations(search_results),
        }

        return response

    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score based on result quality."""
        total_sources = results["sources"]["total"]
        if total_sources == 0:
            return 0.0

        # Base confidence from number of sources
        base_confidence = min(total_sources / 8.0, 1.0)  # Max at 8 sources

        # Boost if we have both literature and memory
        if (
            results["sources"]["literature"] > 0
            or results["sources"]["live_literature"] > 0
        ) and results["sources"]["memory"] > 0:
            base_confidence *= 1.2

        # Consider quality indicators (distance, importance)
        quality_boost = 0.0
        for rag_result in results["rag_results"]:
            if rag_result.get("distance", 1.0) < 0.5:  # High similarity
                quality_boost += 0.1

        for mcp_result in results["mcp_results"]:
            if mcp_result.get("importance", 1) >= 4:  # High importance
                quality_boost += 0.1

        final_confidence = min(base_confidence + quality_boost, 1.0)
        return round(final_confidence, 2)

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on results."""
        recommendations = []

        if results["sources"]["total"] == 0:
            recommendations.append(
                "Consider rephrasing your query or searching with broader terms"
            )
            recommendations.append(
                "Check if relevant data has been indexed in the system"
            )

        elif (
            results["sources"]["literature"] == 0
            and results["sources"]["live_literature"] == 0
        ):
            recommendations.append(
                "This appears to be project-specific - consider consulting recent MCP memories"
            )
            recommendations.append(
                "Look for related published work that might inform this area"
            )

        elif results["sources"]["memory"] == 0:
            recommendations.append(
                "Consider documenting project insights about this topic in MCP"
            )
            recommendations.append(
                "This might be a good area for new research investigation"
            )

        else:
            recommendations.append(
                "Strong evidence base found - consider synthesizing findings"
            )
            recommendations.append(
                "Look for connections between literature and project developments"
            )

        # Add specific recommendations based on content
        all_content = " ".join(
            [r["content"] for r in results["rag_results"] + results["mcp_results"]]
        ).lower()

        if "method" in all_content or "protocol" in all_content:
            recommendations.append(
                "Consider validating methods against current best practices"
            )

        if "result" in all_content or "finding" in all_content:
            recommendations.append("Consider statistical validation and replication")

        return recommendations[:4]  # Limit to 4 recommendations

    def export_knowledge_graph(
        self, output_path: str = "ragpp/outputs/knowledge_graph.json"
    ):
        """Export combined knowledge from RAG and MCP as structured graph."""
        try:
            knowledge_graph = {
                "metadata": {
                    "export_timestamp": str(pd.Timestamp.now()),
                    "sources": {
                        "rag_database": self.rag_db_path,
                        "mcp_memories": "active_memory_system",
                    },
                },
                "literature_nodes": [],
                "memory_nodes": [],
                "connections": [],
                "statistics": {},
            }

            # Export literature nodes
            if self.lit_collection:
                try:
                    all_lit = self.lit_collection.get(
                        include=["documents", "metadatas"]
                    )
                    for i, (doc, meta) in enumerate(
                        zip(all_lit["documents"], all_lit["metadatas"])
                    ):
                        knowledge_graph["literature_nodes"].append(
                            {
                                "id": f"lit_{i}",
                                "content": doc[:500] + "..." if len(doc) > 500 else doc,
                                "metadata": meta,
                                "type": "literature",
                            }
                        )
                except Exception as e:
                    print(f"Warning: Could not export literature nodes: {e}")

            # Export memory nodes (sample recent memories)
            try:
                mcp_cmd = [
                    "python",
                    self.memory_manager_path,
                    "search",
                    "",
                    "--limit",
                    "50",
                ]
                result = subprocess.run(mcp_cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    try:
                        mcp_data = json.loads(result.stdout)
                        for i, mem in enumerate(mcp_data):
                            knowledge_graph["memory_nodes"].append(
                                {
                                    "id": f"mem_{i}",
                                    "content": mem.get("content", "")[:500],
                                    "category": mem.get("category", "unknown"),
                                    "tags": mem.get("tags", []),
                                    "importance": mem.get("importance", 1),
                                    "type": "memory",
                                }
                            )
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                print(f"Warning: Could not export memory nodes: {e}")

            # Calculate statistics
            knowledge_graph["statistics"] = {
                "total_literature_nodes": len(knowledge_graph["literature_nodes"]),
                "total_memory_nodes": len(knowledge_graph["memory_nodes"]),
                "total_nodes": len(knowledge_graph["literature_nodes"])
                + len(knowledge_graph["memory_nodes"]),
                "export_status": "success",
            }

            # Save to file
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(knowledge_graph, f, indent=2, ensure_ascii=False)

            print(f"✅ Knowledge graph exported to {output_path}")
            print(
                f"📊 Stats: {knowledge_graph['statistics']['total_nodes']} total nodes"
            )

            return True

        except Exception as e:
            print(f"❌ Failed to export knowledge graph: {e}")
            return False


def main():
    """CLI for MCP-RAG integration."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP-RAG++ Integration Tool")
    parser.add_argument(
        "action", choices=["search", "qa", "store", "export"], help="Action to perform"
    )
    parser.add_argument("--query", help="Search query or question")
    parser.add_argument("--content", help="Content to store (for store action)")
    parser.add_argument(
        "--category", default="research_findings", help="Category for storing content"
    )
    parser.add_argument("--tags", nargs="+", help="Tags for stored content")
    parser.add_argument(
        "--importance", type=int, default=3, help="Importance level (1-5)"
    )
    parser.add_argument("--output", help="Output file path")

    args = parser.parse_args()

    # Initialize integration
    mcp_rag = MCPRAGIntegration()

    if args.action == "search":
        if not args.query:
            print("Error: --query required for search action")
            return

        results = mcp_rag.hybrid_search(args.query, search_type="hybrid")
        print(f"\n🔍 Hybrid Search Results for: '{args.query}'")
        print("=" * 60)
        print(f"📊 Sources found: {results['sources']}")
        print(f"\n📚 Literature Results ({len(results['rag_results'])}):")
        for r in results["rag_results"]:
            print(
                f"  {r['rank']}. [{r.get('record_id', 'unknown')}] {r['content'][:100]}..."
            )

        print(f"\n🧠 Memory Results ({len(results['mcp_results'])}):")
        for r in results["mcp_results"]:
            print(
                f"  {r['rank']}. [{r.get('category', 'unknown')}] {r['content'][:100]}..."
            )

        if results["synthesis"]:
            print(f"\n💡 Synthesis:\n{results['synthesis']}")

    elif args.action == "qa":
        if not args.query:
            print("Error: --query required for qa action")
            return

        response = mcp_rag.enhanced_qa(args.query)
        print(f"\n❓ Question: {response['question']}")
        print("=" * 60)
        print(f"🎯 Confidence: {response['confidence']}")
        print(f"📊 Sources: {response['sources_found']}")
        print(f"\n💡 Synthesis:\n{response['synthesis']}")
        print(f"\n📋 Recommendations:")
        for rec in response["recommendations"]:
            print(f"  • {rec}")

    elif args.action == "store":
        if not args.content:
            print("Error: --content required for store action")
            return

        success = mcp_rag.store_research_finding(
            args.content, args.category, args.tags, args.importance
        )
        if success:
            print("✅ Research finding stored successfully")
        else:
            print("❌ Failed to store research finding")

    elif args.action == "export":
        output_path = args.output or "ragpp/outputs/knowledge_graph.json"
        success = mcp_rag.export_knowledge_graph(output_path)
        if success:
            print(f"✅ Knowledge graph exported to {output_path}")
        else:
            print("❌ Failed to export knowledge graph")


if __name__ == "__main__":
    import pandas as pd  # Import here to avoid issues if not needed

    main()
