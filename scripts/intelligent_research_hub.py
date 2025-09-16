#!/usr/bin/env python3
"""
Intelligent Research Control Hub for PCS Project
Integrates AI assistant with research automation suite.
"""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntelligentResearchHub:
    """Master control for AI-enhanced academic research."""

    def __init__(self):
        self.base_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
        self.scripts_path = self.base_path / "scripts"

        # Component scripts
        self.ai_assistant = self.scripts_path / "ai_research_assistant.py"
        self.academic_hub = self.scripts_path / "advanced_academic_hub.py"
        self.research_suite = self.base_path / "pcs_research_suite.sh"
        self.memory_manager = self.scripts_path / "memory_manager.py"

        # Ensure all components exist
        self._verify_components()

    def _verify_components(self):
        """Verify all research components are available."""
        components = {
            "AI Assistant": self.ai_assistant,
            "Academic Hub": self.academic_hub,
            "Research Suite": self.research_suite,
            "Memory Manager": self.memory_manager,
        }

        missing = []
        for name, path in components.items():
            if not path.exists():
                missing.append(f"{name}: {path}")

        if missing:
            logger.warning(f"Missing components: {', '.join(missing)}")
            return False
        return True

    async def run_intelligent_search(self, query: str, ai_analyze: bool = True) -> Dict:
        """Run intelligent search with optional AI analysis."""
        logger.info(f"🔍 Running intelligent search for: {query}")

        # Step 1: Run comprehensive academic search
        search_cmd = [str(self.research_suite), "quick", query]

        try:
            result = subprocess.run(
                search_cmd, capture_output=True, text=True, timeout=300
            )

            if result.returncode != 0:
                return {"status": "error", "message": f"Search failed: {result.stderr}"}

            search_results = result.stdout
            logger.info("✅ Academic search completed")

            # Step 2: Optional AI analysis
            if ai_analyze:
                ai_cmd = [
                    "python",
                    str(self.ai_assistant),
                    "synthesize",
                    "--topic",
                    query,
                    "--limit",
                    "10",
                ]

                ai_result = subprocess.run(
                    ai_cmd, capture_output=True, text=True, timeout=180
                )

                if ai_result.returncode == 0:
                    logger.info("✅ AI synthesis completed")
                    ai_analysis = ai_result.stdout
                else:
                    logger.warning(f"AI analysis failed: {ai_result.stderr}")
                    ai_analysis = "AI analysis unavailable"
            else:
                ai_analysis = "AI analysis not requested"

            return {
                "status": "success",
                "query": query,
                "search_results": search_results,
                "ai_analysis": ai_analysis,
                "timestamp": datetime.now().isoformat(),
            }

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "message": "Search operation timed out"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def generate_research_strategy(self, goal: str) -> Dict:
        """Generate comprehensive research strategy using AI."""
        logger.info(f"🎯 Generating research strategy for: {goal}")

        try:
            cmd = ["python", str(self.ai_assistant), "strategy", "--topic", goal]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=240)

            if result.returncode == 0:
                logger.info("✅ Research strategy generated")
                return {
                    "status": "success",
                    "goal": goal,
                    "output": result.stdout,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "error",
                    "message": f"Strategy generation failed: {result.stderr}",
                }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def analyze_research_gaps(self) -> Dict:
        """Run AI-powered gap analysis on current research."""
        logger.info("🔍 Analyzing research gaps...")

        try:
            cmd = ["python", str(self.ai_assistant), "gaps"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                logger.info("✅ Gap analysis completed")
                return {
                    "status": "success",
                    "output": result.stdout,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "error",
                    "message": f"Gap analysis failed: {result.stderr}",
                }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def create_manuscript_outline(self, focus: str) -> Dict:
        """Generate AI-powered manuscript outline."""
        logger.info(f"📝 Creating manuscript outline for: {focus}")

        try:
            cmd = ["python", str(self.ai_assistant), "outline", "--topic", focus]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=240)

            if result.returncode == 0:
                logger.info("✅ Manuscript outline created")
                return {
                    "status": "success",
                    "focus": focus,
                    "output": result.stdout,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "error",
                    "message": f"Outline creation failed: {result.stderr}",
                }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def run_complete_research_pipeline(self, research_goal: str) -> Dict:
        """Run complete intelligent research pipeline."""
        logger.info(f"🚀 Starting complete research pipeline for: {research_goal}")

        pipeline_results = {
            "goal": research_goal,
            "started": datetime.now().isoformat(),
            "steps": {},
        }

        # Step 1: Intelligent literature search
        logger.info("Step 1: Intelligent literature search")
        search_result = await self.run_intelligent_search(
            research_goal, ai_analyze=True
        )
        pipeline_results["steps"]["literature_search"] = search_result

        if search_result["status"] != "success":
            pipeline_results["status"] = "failed_at_search"
            return pipeline_results

        # Step 2: Research strategy generation
        logger.info("Step 2: Research strategy generation")
        strategy_result = await self.generate_research_strategy(research_goal)
        pipeline_results["steps"]["strategy_generation"] = strategy_result

        # Step 3: Gap analysis
        logger.info("Step 3: Gap analysis")
        gap_result = await self.analyze_research_gaps()
        pipeline_results["steps"]["gap_analysis"] = gap_result

        # Step 4: Manuscript outline
        logger.info("Step 4: Manuscript outline")
        outline_result = await self.create_manuscript_outline(research_goal)
        pipeline_results["steps"]["manuscript_outline"] = outline_result

        # Step 5: Summary and recommendations
        logger.info("Step 5: Generating summary")
        summary = await self._generate_pipeline_summary(pipeline_results)
        pipeline_results["summary"] = summary

        pipeline_results["completed"] = datetime.now().isoformat()
        pipeline_results["status"] = "success"

        # Store complete pipeline results in MCP
        await self._store_pipeline_results(pipeline_results)

        logger.info("✅ Complete research pipeline finished")
        return pipeline_results

    async def get_research_status(self) -> Dict:
        """Get current research status from MCP."""
        try:
            cmd = ["python", str(self.memory_manager), "context"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return {
                    "status": "success",
                    "context": result.stdout,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to retrieve research status",
                }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _generate_pipeline_summary(self, results: Dict) -> str:
        """Generate summary of pipeline results."""
        summary_parts = []

        summary_parts.append(f"🎯 Research Goal: {results['goal']}")
        summary_parts.append(
            f"⏱️  Duration: {results['started']} to {results.get('completed', 'ongoing')}"
        )

        for step_name, step_result in results["steps"].items():
            status = step_result.get("status", "unknown")
            emoji = "✅" if status == "success" else "❌"
            summary_parts.append(
                f"{emoji} {step_name.replace('_', ' ').title()}: {status}"
            )

        summary_parts.append("\n📋 Next Actions:")
        summary_parts.append("1. Review generated strategy and outline")
        summary_parts.append("2. Address identified research gaps")
        summary_parts.append("3. Begin literature review and data collection")
        summary_parts.append("4. Set up collaboration networks")
        summary_parts.append("5. Draft manuscript sections")

        return "\n".join(summary_parts)

    async def _store_pipeline_results(self, results: Dict):
        """Store complete pipeline results in MCP."""
        try:
            content = f"""Complete Research Pipeline Results

Goal: {results['goal']}
Started: {results['started']}
Completed: {results.get('completed', 'In Progress')}
Status: {results.get('status', 'Unknown')}

{results.get('summary', 'No summary available')}

Detailed Results:
{json.dumps(results['steps'], indent=2)}
"""

            cmd = [
                "python",
                str(self.memory_manager),
                "add",
                content,
                "--category",
                "research_progress",
                "--tags",
                "ai_pipeline",
                "complete_analysis",
                "research_automation",
                "--importance",
                "5",
            ]

            subprocess.run(cmd, capture_output=True, text=True)
            logger.info("✅ Pipeline results stored in MCP")

        except Exception as e:
            logger.error(f"Error storing pipeline results: {e}")


async def main():
    """CLI interface for intelligent research hub."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Intelligent Research Control Hub for PCS"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Search command
    search_parser = subparsers.add_parser("search", help="Intelligent search")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--no-ai", action="store_true", help="Skip AI analysis")

    # Strategy command
    strategy_parser = subparsers.add_parser(
        "strategy", help="Generate research strategy"
    )
    strategy_parser.add_argument("goal", help="Research goal")

    # Pipeline command
    pipeline_parser = subparsers.add_parser("pipeline", help="Run complete pipeline")
    pipeline_parser.add_argument("goal", help="Research goal")

    # Analysis commands
    subparsers.add_parser("gaps", help="Analyze research gaps")
    subparsers.add_parser("status", help="Get research status")

    # Outline command
    outline_parser = subparsers.add_parser("outline", help="Create manuscript outline")
    outline_parser.add_argument("focus", help="Research focus")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    hub = IntelligentResearchHub()

    try:
        if args.command == "search":
            result = await hub.run_intelligent_search(
                args.query, ai_analyze=not args.no_ai
            )

            if result["status"] == "success":
                print("✅ Intelligent search completed!")
                print(f"Query: {result['query']}")
                print(f"Timestamp: {result['timestamp']}")
                if not args.no_ai:
                    print("🤖 AI analysis included")
            else:
                print(f"❌ Search failed: {result.get('message')}")

        elif args.command == "strategy":
            result = await hub.generate_research_strategy(args.goal)

            if result["status"] == "success":
                print("✅ Research strategy generated!")
                print(f"Goal: {result['goal']}")
                print(f"Timestamp: {result['timestamp']}")
            else:
                print(f"❌ Strategy generation failed: {result.get('message')}")

        elif args.command == "pipeline":
            print(f"🚀 Starting complete research pipeline for: {args.goal}")
            print("This will run multiple AI-enhanced research steps...")

            result = await hub.run_complete_research_pipeline(args.goal)

            if result["status"] == "success":
                print("\n✅ Complete research pipeline finished!")
                print("\n📋 Summary:")
                print(result.get("summary", "No summary available"))
            else:
                print(f"\n❌ Pipeline failed: {result.get('status')}")

        elif args.command == "gaps":
            result = await hub.analyze_research_gaps()

            if result["status"] == "success":
                print("✅ Gap analysis completed!")
                print(f"Timestamp: {result['timestamp']}")
            else:
                print(f"❌ Gap analysis failed: {result.get('message')}")

        elif args.command == "status":
            result = await hub.get_research_status()

            if result["status"] == "success":
                print("✅ Research status retrieved!")
                print(f"Timestamp: {result['timestamp']}")
                print("\n📊 Current Research Context:")
                print(
                    result["context"][:500] + "..."
                    if len(result["context"]) > 500
                    else result["context"]
                )
            else:
                print(f"❌ Status retrieval failed: {result.get('message')}")

        elif args.command == "outline":
            result = await hub.create_manuscript_outline(args.focus)

            if result["status"] == "success":
                print("✅ Manuscript outline created!")
                print(f"Focus: {result['focus']}")
                print(f"Timestamp: {result['timestamp']}")
            else:
                print(f"❌ Outline creation failed: {result.get('message')}")

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
