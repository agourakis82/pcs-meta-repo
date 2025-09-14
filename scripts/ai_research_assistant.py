#!/usr/bin/env python3
"""
AI-Enhanced Research Assistant for PCS Project
Integrates Gemini AI with MCP for intelligent research analysis.
"""

import asyncio
import json
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class GeminiMCPResearchAssistant:
    """AI-enhanced research assistant using Gemini and MCP."""

    def __init__(self):
        self.base_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
        self.memory_manager = self.base_path / "scripts" / "memory_manager.py"

        # Load Gemini API key
        self.gemini_config_path = Path.home() / ".gemini" / "settings.json"
        self.api_key = self._load_gemini_api_key()
        self.api_base = "https://generativelanguage.googleapis.com/v1beta"

        # PCS research context
        self.pcs_context = {
            "project_name": "Computational-Symbolic Psychiatry (PCS)",
            "version": "4.3",
            "datasets": ["SWOW", "ZuCo", "DERCo", "GECO", "OneStop", "LPP"],
            "methods": ["AG5/KEC metrics", "Ricci curvature", "Transition entropy"],
            "targets": ["Nature Human Behaviour", "Scientific Reports"],
            "focus_areas": [
                "semantic networks",
                "neural reading",
                "information entropy",
                "graph curvature",
                "computational psychiatry",
                "multilingual processing",
            ],
        }

    def _load_gemini_api_key(self) -> Optional[str]:
        """Load Gemini API key from config."""
        try:
            if self.gemini_config_path.exists():
                with open(self.gemini_config_path, "r") as f:
                    config = json.load(f)
                    return config.get("apiKey")
        except Exception as e:
            logger.error(f"Error loading Gemini config: {e}")
        return None

    async def analyze_research_paper(
        self, paper_content: str, paper_metadata: Dict = None
    ) -> Dict[str, Any]:
        """AI analysis of research paper for PCS relevance."""
        if not self.api_key:
            return {"error": "Gemini API key not configured"}

        prompt = f"""
Analyze this research paper for relevance to the Computational-Symbolic Psychiatry (PCS) project:

PROJECT CONTEXT:
- Focus: {', '.join(self.pcs_context['focus_areas'])}
- Datasets: {', '.join(self.pcs_context['datasets'])}
- Methods: {', '.join(self.pcs_context['methods'])}
- Target journals: {', '.join(self.pcs_context['targets'])}

PAPER CONTENT:
{paper_content[:2000]}...

Please provide:
1. PCS Relevance Score (0-10)
2. Key insights relevant to PCS
3. Potential applications in our research
4. Gaps this paper addresses
5. Citations we should explore
6. Methodological insights
7. Recommended follow-up actions

Format as JSON with clear sections.
"""

        try:
            analysis = await self._call_gemini_api(prompt)

            # Store analysis in MCP
            await self._store_ai_analysis(analysis, paper_metadata)

            return {
                "status": "success",
                "analysis": analysis,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error analyzing paper: {e}")
            return {"error": str(e)}

    async def generate_research_strategy(self, research_goal: str) -> Dict[str, Any]:
        """Generate AI-powered research strategy for PCS goals."""
        if not self.api_key:
            return {"error": "Gemini API key not configured"}

        # Get current research state from MCP
        current_state = await self._get_mcp_research_state()

        prompt = f"""
Create a comprehensive research strategy for this PCS project goal:

GOAL: {research_goal}

CURRENT PROJECT STATE:
{current_state}

PCS PROJECT CONTEXT:
- Version: {self.pcs_context['version']}
- Datasets: {', '.join(self.pcs_context['datasets'])}
- Methods: {', '.join(self.pcs_context['methods'])}
- Target Publications: {', '.join(self.pcs_context['targets'])}

Generate a detailed strategy including:
1. Literature Review Plan (specific search queries)
2. Methodology Roadmap (step-by-step approach)
3. Data Analysis Pipeline (tools and methods)
4. Timeline with Milestones
5. Risk Assessment & Mitigation
6. Collaboration Opportunities
7. Publication Strategy
8. Success Metrics

Format as structured JSON for easy parsing and implementation.
"""

        try:
            strategy = await self._call_gemini_api(prompt)

            # Store strategy in MCP
            await self._store_research_strategy(strategy, research_goal)

            return {
                "status": "success",
                "strategy": strategy,
                "goal": research_goal,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating strategy: {e}")
            return {"error": str(e)}

    async def intelligent_literature_synthesis(
        self, topic: str, papers_limit: int = 10
    ) -> Dict[str, Any]:
        """AI-powered synthesis of literature on a topic."""
        if not self.api_key:
            return {"error": "Gemini API key not configured"}

        # Get relevant papers from MCP
        papers = await self._get_mcp_papers_on_topic(topic, papers_limit)

        if not papers:
            return {"error": f"No papers found on topic: {topic}"}

        prompt = f"""
Synthesize the following research papers into a comprehensive literature review for the PCS project:

TOPIC: {topic}

PAPERS TO SYNTHESIZE:
{chr(10).join(f"{i+1}. {paper}" for i, paper in enumerate(papers[:10]))}

PCS PROJECT FOCUS:
- Computational-Symbolic Psychiatry
- Focus areas: {', '.join(self.pcs_context['focus_areas'])}
- Target: Nature Human Behaviour publication

Create a synthesis including:
1. Executive Summary
2. Current State of the Field
3. Key Findings & Trends
4. Methodological Approaches
5. Gaps & Limitations
6. Future Directions
7. PCS Project Implications
8. Recommended Citations
9. Research Questions for Investigation

Format as well-structured markdown suitable for academic writing.
"""

        try:
            synthesis = await self._call_gemini_api(prompt)

            # Store synthesis in MCP
            await self._store_literature_synthesis(synthesis, topic)

            return {
                "status": "success",
                "synthesis": synthesis,
                "topic": topic,
                "papers_analyzed": len(papers),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error synthesizing literature: {e}")
            return {"error": str(e)}

    async def generate_manuscript_outline(self, research_focus: str) -> Dict[str, Any]:
        """Generate AI-powered manuscript outline for Nature Human Behaviour."""
        if not self.api_key:
            return {"error": "Gemini API key not configured"}

        # Get project context from MCP
        project_context = await self._get_comprehensive_project_context()

        prompt = f"""
Generate a comprehensive manuscript outline for Nature Human Behaviour on:

RESEARCH FOCUS: {research_focus}

PROJECT CONTEXT:
{project_context}

NATURE HUMAN BEHAVIOUR REQUIREMENTS:
- High-impact computational neuroscience/psychology
- Novel methodological contributions
- Clear clinical/societal implications
- Rigorous statistical analysis
- Open science practices

Create detailed outline with:
1. Title (compelling and specific)
2. Abstract (structured: Background, Methods, Results, Conclusions)
3. Introduction (3-4 key points)
4. Methods (detailed methodology sections)
5. Results (anticipated findings structure)
6. Discussion (implications, limitations, future work)
7. Figures Plan (what visualizations needed)
8. Statistical Analysis Plan
9. Supplementary Materials outline
10. Timeline for completion

Format as structured markdown with clear sections and subsections.
"""

        try:
            outline = await self._call_gemini_api(prompt)

            # Store outline in MCP
            await self._store_manuscript_outline(outline, research_focus)

            return {
                "status": "success",
                "outline": outline,
                "focus": research_focus,
                "target_journal": "Nature Human Behaviour",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating outline: {e}")
            return {"error": str(e)}

    async def intelligent_gap_analysis(self) -> Dict[str, Any]:
        """AI-powered analysis of research gaps in current literature."""
        if not self.api_key:
            return {"error": "Gemini API key not configured"}

        # Get all research memories from MCP
        all_research = await self._get_all_mcp_research()

        prompt = f"""
Analyze the current state of research for the PCS project and identify critical gaps:

CURRENT RESEARCH COVERAGE:
{all_research[:3000]}

PCS PROJECT GOALS:
- Computational-Symbolic Psychiatry
- Nature Human Behaviour publication target
- Focus areas: {', '.join(self.pcs_context['focus_areas'])}
- Datasets: {', '.join(self.pcs_context['datasets'])}

Provide detailed gap analysis:
1. Theoretical Gaps (unexplored concepts)
2. Methodological Gaps (missing approaches)
3. Empirical Gaps (data/validation needs)
4. Technological Gaps (tools/software needs)
5. Collaboration Gaps (expertise needs)
6. Publication Gaps (underrepresented areas)
7. Priority Ranking (which gaps to address first)
8. Resource Requirements (time, funding, expertise)
9. Risk Assessment (difficulty, feasibility)
10. Action Plan (specific next steps)

Format as actionable JSON with clear priorities and timelines.
"""

        try:
            gap_analysis = await self._call_gemini_api(prompt)

            # Store analysis in MCP
            await self._store_gap_analysis(gap_analysis)

            return {
                "status": "success",
                "analysis": gap_analysis,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error analyzing gaps: {e}")
            return {"error": str(e)}

    async def _call_gemini_api(self, prompt: str, model: str = "gemini-1.5-pro") -> str:
        """Call Gemini API with given prompt."""
        url = f"{self.api_base}/models/{model}:generateContent"

        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}

        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192,
            },
        }

        # Try LM cache (best-effort)
        try:
            from ragpp.lm_cache import get_lm_cache, make_key
            from ragpp.semantic_cache import SemanticLMCache

            cache = get_lm_cache()
            key = make_key(
                provider="gemini",
                model=model,
                temperature=0.7,
                top_p=0.95,
                system_prompt="",
                user_prompt=prompt,
                context_fingerprint="",
            )
            cached = cache.get(key)
            if cached:
                return cached
            # Semantic cache
            try:
                sem = SemanticLMCache()
                if sem.is_available():
                    hit = sem.find(
                        provider="gemini",
                        model=model,
                        system_prompt="",
                        user_prompt=prompt,
                        context_fp="",
                        temperature=0.7,
                        top_p=0.95,
                    )
                    if hit:
                        return hit.text
            except Exception:
                pass
        except Exception:
            key = None  # type: ignore

        def _do_post():
            return requests.post(url, headers=headers, json=data)

        response = await asyncio.get_event_loop().run_in_executor(None, _do_post)
        response.raise_for_status()
        result = response.json()

        if "candidates" in result and result["candidates"]:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            try:
                if key:
                    cache.set(key, text)
            except Exception:
                pass
            # Semantic store
            try:
                sem = SemanticLMCache()
                if sem.is_available():
                    sem.store(
                        provider="gemini",
                        model=model,
                        system_prompt="",
                        user_prompt=prompt,
                        context_fp="",
                        response_text=text,
                        temperature=0.7,
                        top_p=0.95,
                    )
            except Exception:
                pass
            return text
        else:
            raise Exception(f"Unexpected API response: {result}")

    async def _get_mcp_research_state(self) -> str:
        """Get current research state from MCP."""
        try:
            cmd = ["python", str(self.memory_manager), "search", "--query", "research"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return result.stdout[:1000]  # Limit for API
            else:
                return "No research state available"

        except Exception as e:
            logger.error(f"Error getting MCP state: {e}")
            return "Error retrieving research state"

    async def _get_mcp_papers_on_topic(self, topic: str, limit: int) -> List[str]:
        """Get papers on specific topic from MCP."""
        try:
            cmd = ["python", str(self.memory_manager), "search", "--query", topic]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # Parse papers from output (simplified)
                lines = result.stdout.split("\n")
                papers = [line for line in lines if "research paper" in line.lower()]
                return papers[:limit]
            else:
                return []

        except Exception as e:
            logger.error(f"Error getting papers: {e}")
            return []

    async def _get_comprehensive_project_context(self) -> str:
        """Get comprehensive project context from MCP."""
        try:
            cmd = ["python", str(self.memory_manager), "context"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return result.stdout
            else:
                return json.dumps(self.pcs_context, indent=2)

        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return json.dumps(self.pcs_context, indent=2)

    async def _get_all_mcp_research(self) -> str:
        """Get all research-related memories from MCP."""
        try:
            cmd = ["python", str(self.memory_manager), "list"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return result.stdout
            else:
                return "No research memories available"

        except Exception as e:
            logger.error(f"Error getting all research: {e}")
            return "Error retrieving research memories"

    async def _store_ai_analysis(self, analysis: str, metadata: Dict = None):
        """Store AI analysis in MCP."""
        try:
            title = f"AI Analysis: {metadata.get('title', 'Research Paper')[:50]}..."
            content = f"AI-Generated Paper Analysis\n\n{analysis}"

            cmd = [
                "python",
                str(self.memory_manager),
                "add",
                content,
                "--category",
                "publications",
                "--tags",
                "ai_analysis",
                "gemini",
                "paper_analysis",
                "--importance",
                "4",
            ]

            subprocess.run(cmd, capture_output=True, text=True)
            logger.info("✅ AI analysis stored in MCP")

        except Exception as e:
            logger.error(f"Error storing analysis: {e}")

    async def _store_research_strategy(self, strategy: str, goal: str):
        """Store research strategy in MCP."""
        try:
            content = f"AI-Generated Research Strategy\n\nGoal: {goal}\n\n{strategy}"

            cmd = [
                "python",
                str(self.memory_manager),
                "add",
                content,
                "--category",
                "research_progress",
                "--tags",
                "ai_strategy",
                "gemini",
                "research_planning",
                "--importance",
                "5",
            ]

            subprocess.run(cmd, capture_output=True, text=True)
            logger.info("✅ Research strategy stored in MCP")

        except Exception as e:
            logger.error(f"Error storing strategy: {e}")

    async def _store_literature_synthesis(self, synthesis: str, topic: str):
        """Store literature synthesis in MCP."""
        try:
            content = f"AI Literature Synthesis: {topic}\n\n{synthesis}"

            cmd = [
                "python",
                str(self.memory_manager),
                "add",
                content,
                "--category",
                "publications",
                "--tags",
                "ai_synthesis",
                "gemini",
                "literature_review",
                topic.replace(" ", "_"),
                "--importance",
                "4",
            ]

            subprocess.run(cmd, capture_output=True, text=True)
            logger.info("✅ Literature synthesis stored in MCP")

        except Exception as e:
            logger.error(f"Error storing synthesis: {e}")

    async def _store_manuscript_outline(self, outline: str, focus: str):
        """Store manuscript outline in MCP."""
        try:
            content = f"AI-Generated Manuscript Outline: {focus}\n\n{outline}"

            cmd = [
                "python",
                str(self.memory_manager),
                "add",
                content,
                "--category",
                "publications",
                "--tags",
                "ai_outline",
                "gemini",
                "manuscript",
                "nature_hb",
                "--importance",
                "5",
            ]

            subprocess.run(cmd, capture_output=True, text=True)
            logger.info("✅ Manuscript outline stored in MCP")

        except Exception as e:
            logger.error(f"Error storing outline: {e}")

    async def _store_gap_analysis(self, analysis: str):
        """Store gap analysis in MCP."""
        try:
            content = f"AI Gap Analysis for PCS Project\n\n{analysis}"

            cmd = [
                "python",
                str(self.memory_manager),
                "add",
                content,
                "--category",
                "research_progress",
                "--tags",
                "ai_analysis",
                "gemini",
                "gap_analysis",
                "strategic_planning",
                "--importance",
                "5",
            ]

            subprocess.run(cmd, capture_output=True, text=True)
            logger.info("✅ Gap analysis stored in MCP")

        except Exception as e:
            logger.error(f"Error storing gap analysis: {e}")


async def main():
    """CLI interface for AI research assistant."""
    import argparse

    parser = argparse.ArgumentParser(
        description="AI-Enhanced Research Assistant for PCS"
    )
    parser.add_argument(
        "action",
        choices=["analyze", "strategy", "synthesize", "outline", "gaps"],
        help="AI analysis action to perform",
    )
    parser.add_argument("--topic", help="Research topic or goal")
    parser.add_argument("--paper", help="Paper content file for analysis")
    parser.add_argument(
        "--limit", type=int, default=10, help="Paper limit for synthesis"
    )

    args = parser.parse_args()

    assistant = GeminiMCPResearchAssistant()

    if not assistant.api_key:
        print(
            "❌ Gemini API key not found. Please configure in ~/.gemini/settings.json"
        )
        return

    if args.action == "analyze":
        if not args.paper:
            print("Error: --paper required for analyze action")
            return

        try:
            with open(args.paper, "r") as f:
                content = f.read()

            result = await assistant.analyze_research_paper(content)

            if result.get("status") == "success":
                print("✅ Paper analysis complete!")
                print(f"Analysis stored in MCP at {result['timestamp']}")
            else:
                print(f"❌ Error: {result.get('error')}")

        except FileNotFoundError:
            print(f"❌ Paper file not found: {args.paper}")

    elif args.action == "strategy":
        if not args.topic:
            print("Error: --topic required for strategy action")
            return

        result = await assistant.generate_research_strategy(args.topic)

        if result.get("status") == "success":
            print("✅ Research strategy generated!")
            print(f"Goal: {result['goal']}")
            print(f"Strategy stored in MCP at {result['timestamp']}")
        else:
            print(f"❌ Error: {result.get('error')}")

    elif args.action == "synthesize":
        if not args.topic:
            print("Error: --topic required for synthesize action")
            return

        result = await assistant.intelligent_literature_synthesis(
            args.topic, args.limit
        )

        if result.get("status") == "success":
            print("✅ Literature synthesis complete!")
            print(f"Topic: {result['topic']}")
            print(f"Papers analyzed: {result['papers_analyzed']}")
            print(f"Synthesis stored in MCP at {result['timestamp']}")
        else:
            print(f"❌ Error: {result.get('error')}")

    elif args.action == "outline":
        if not args.topic:
            print("Error: --topic required for outline action")
            return

        result = await assistant.generate_manuscript_outline(args.topic)

        if result.get("status") == "success":
            print("✅ Manuscript outline generated!")
            print(f"Focus: {result['focus']}")
            print(f"Target: {result['target_journal']}")
            print(f"Outline stored in MCP at {result['timestamp']}")
        else:
            print(f"❌ Error: {result.get('error')}")

    elif args.action == "gaps":
        result = await assistant.intelligent_gap_analysis()

        if result.get("status") == "success":
            print("✅ Gap analysis complete!")
            print(f"Analysis stored in MCP at {result['timestamp']}")
        else:
            print(f"❌ Error: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
