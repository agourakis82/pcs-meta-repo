#!/usr/bin/env python3
"""
RAG++ Integration with OpenAI (ChatGPT, GPT-4, Codex)
Integra o sistema RAG++ com APIs da OpenAI para enhanced context.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from tools.mcp_rag_integration import MCPRAGIntegration
    from ragpp.lm_cache import get_lm_cache, make_key, fingerprint_context
    from ragpp.semantic_cache import SemanticLMCache
except ImportError:
    # Try alternative import path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from ragpp.tools.mcp_rag_integration import MCPRAGIntegration
    from ragpp.lm_cache import get_lm_cache, make_key, fingerprint_context
    from ragpp.semantic_cache import SemanticLMCache


class OpenAIRAGIntegration:
    """
    Integração do RAG++ com OpenAI APIs (ChatGPT, GPT-4, Codex).
    Fornece contexto enriquecido com literatura científica + memórias do projeto.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        max_context_tokens: int = 8000,
    ):
        """
        Initialize OpenAI RAG++ integration.

        Args:
            api_key: OpenAI API key (if None, loads from environment)
            model: OpenAI model to use
            max_context_tokens: Maximum tokens for context
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.max_context_tokens = max_context_tokens

        # Initialize RAG++ system
        self.rag_system = MCPRAGIntegration()
        self._sem_cache = None
        try:
            self._sem_cache = SemanticLMCache()
        except Exception:
            self._sem_cache = None

        # Import OpenAI after checking API key
        if self.api_key:
            try:
                import openai

                self.openai = openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                print("⚠️ OpenAI package not installed. Run: pip install openai")
                self.client = None
        else:
            print(
                "⚠️ OpenAI API key not found. Set OPENAI_API_KEY environment variable."
            )
            self.client = None

    def create_enhanced_prompt(
        self,
        user_query: str,
        system_prompt: Optional[str] = None,
        include_recent_research: bool = True,
        max_context_results: int = 10,
    ) -> Dict[str, Any]:
        """
        Create enhanced prompt with RAG++ context for OpenAI.

        Args:
            user_query: User's question/request
            system_prompt: Optional system prompt
            include_recent_research: Whether to include recent research findings
            max_context_results: Max results from RAG++

        Returns:
            Enhanced prompt structure for OpenAI
        """
        print(f"🔍 Enhancing prompt with RAG++ context...")

        # Get RAG++ enhanced context
        rag_response = self.rag_system.enhanced_qa(question=user_query)

        # Build context sections
        context_sections = []

        # Literature context
        if rag_response.get("literature_results"):
            lit_context = "📚 **Recent Scientific Literature:**\n"
            for i, result in enumerate(rag_response["literature_results"][:5], 1):
                title = result.get("title", "Unknown")
                authors = result.get("authors", "Unknown authors")
                content = result.get("content", "")[:200] + "..."
                lit_context += f"{i}. **{title}** ({authors})\n   {content}\n\n"
            context_sections.append(lit_context)

        # Project memory context
        if rag_response.get("memory_results"):
            mem_context = "🧠 **Project Knowledge & Memory:**\n"
            for i, result in enumerate(rag_response["memory_results"][:3], 1):
                content = result.get("content", "")[:300] + "..."
                category = result.get("category", "general")
                mem_context += f"{i}. [{category}] {content}\n\n"
            context_sections.append(mem_context)

        # Recommendations context
        if rag_response.get("recommendations"):
            rec_context = "💡 **Recommendations:**\n"
            for rec in rag_response["recommendations"][:3]:
                rec_context += f"• {rec}\n"
            context_sections.append(rec_context)

        # Build enhanced system prompt
        enhanced_system = (
            system_prompt
            or "You are an expert AI assistant with access to recent scientific literature and project-specific knowledge."
        )

        if context_sections:
            enhanced_system += "\n\n" + "=" * 50 + "\n"
            enhanced_system += "📖 **ENHANCED CONTEXT FROM RAG++ SYSTEM:**\n\n"
            enhanced_system += "\n".join(context_sections)
            enhanced_system += "=" * 50 + "\n\n"
            enhanced_system += "Use this context to provide more informed, accurate, and up-to-date responses. Reference specific sources when relevant."

        return {
            "enhanced_system_prompt": enhanced_system,
            "user_query": user_query,
            "rag_context": rag_response,
            "context_summary": {
                "literature_sources": len(rag_response.get("literature_results", [])),
                "memory_entries": len(rag_response.get("memory_results", [])),
                "total_confidence": rag_response.get("confidence", 0),
            },
        }

    async def chat_with_rag(
        self,
        user_message: str,
        conversation_history: List[Dict] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Chat with OpenAI using RAG++ enhanced context.

        Args:
            user_message: User's message
            conversation_history: Previous conversation
            system_prompt: Optional system prompt
            temperature: Response randomness

        Returns:
            Enhanced response with sources
        """
        if not self.client:
            return {"error": "OpenAI client not initialized"}

        # Create enhanced prompt
        enhanced_prompt = self.create_enhanced_prompt(
            user_query=user_message, system_prompt=system_prompt
        )

        # Build conversation messages
        messages = []

        # System message with RAG++ context
        messages.append(
            {"role": "system", "content": enhanced_prompt["enhanced_system_prompt"]}
        )

        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        try:
            # LM cache lookup (best-effort)
            key = None
            try:
                cache = get_lm_cache()
                ctx_fp = fingerprint_context(enhanced_prompt.get("rag_context", {}))
                key = make_key(
                    provider="openai",
                    model=self.model,
                    temperature=temperature,
                    top_p=1.0,
                    system_prompt=messages[0]["content"],
                    user_prompt=user_message,
                    context_fingerprint=ctx_fp,
                )
                cached_text = cache.get(key)
                if cached_text:
                    assistant_response = cached_text
                    return {
                        "response": assistant_response,
                        "model": self.model,
                        "rag_context": enhanced_prompt["rag_context"],
                        "context_summary": enhanced_prompt["context_summary"],
                        "tokens_used": None,
                        "cached": True,
                        "timestamp": datetime.now().isoformat(),
                    }
            except Exception:
                pass

            # Semantic cache lookup (optional)
            try:
                if self._sem_cache and self._sem_cache.is_available():
                    hit = self._sem_cache.find(
                        provider="openai",
                        model=self.model,
                        system_prompt=messages[0]["content"],
                        user_prompt=user_message,
                        context_fp=ctx_fp,
                        temperature=temperature,
                        top_p=1.0,
                    )
                    if hit:
                        return {
                            "response": hit.text,
                            "model": self.model,
                            "rag_context": enhanced_prompt["rag_context"],
                            "context_summary": enhanced_prompt["context_summary"],
                            "tokens_used": None,
                            "cached": True,
                            "semantic": True,
                            "timestamp": datetime.now().isoformat(),
                        }
            except Exception:
                pass

            # Call OpenAI API
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=1500,
            )

            assistant_response = response.choices[0].message.content

            # Store in cache (best-effort)
            try:
                if key is not None:
                    cache.set(key, assistant_response)
            except Exception:
                pass

            # Store semantically (optional)
            try:
                if self._sem_cache and self._sem_cache.is_available():
                    self._sem_cache.store(
                        provider="openai",
                        model=self.model,
                        system_prompt=messages[0]["content"],
                        user_prompt=user_message,
                        context_fp=ctx_fp,
                        response_text=assistant_response,
                        temperature=temperature,
                        top_p=1.0,
                    )
            except Exception:
                pass

            return {
                "response": assistant_response,
                "model": self.model,
                "rag_context": enhanced_prompt["rag_context"],
                "context_summary": enhanced_prompt["context_summary"],
                "tokens_used": response.usage.total_tokens
                if hasattr(response, "usage")
                else None,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"error": f"OpenAI API error: {str(e)}"}

    def code_with_rag(
        self, code_request: str, language: str = "python", include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Generate code using Codex/GPT-4 with RAG++ context.

        Args:
            code_request: Description of code to generate
            language: Programming language
            include_context: Whether to include RAG++ context

        Returns:
            Generated code with context
        """
        if not self.client:
            return {"error": "OpenAI client not initialized"}

        # Create code-focused system prompt
        system_prompt = f"""You are an expert {language} developer with access to recent research and project knowledge.
Generate clean, well-documented, production-ready code that follows best practices.
Include relevant comments and explanations."""

        if include_context:
            enhanced_prompt = self.create_enhanced_prompt(
                user_query=code_request, system_prompt=system_prompt
            )
            final_system_prompt = enhanced_prompt["enhanced_system_prompt"]
            rag_context = enhanced_prompt["rag_context"]
        else:
            final_system_prompt = system_prompt
            rag_context = None

        # Format code request
        code_prompt = f"""Generate {language} code for: {code_request}

Requirements:
- Write clean, readable code
- Include docstrings and comments
- Follow best practices for {language}
- Include error handling where appropriate
- Provide usage examples if relevant"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": final_system_prompt},
                    {"role": "user", "content": code_prompt},
                ],
                temperature=0.3,  # Lower temperature for code generation
                max_tokens=2000,
            )

            return {
                "code": response.choices[0].message.content,
                "language": language,
                "model": self.model,
                "rag_context": rag_context,
                "request": code_request,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"error": f"Code generation error: {str(e)}"}

    def create_openai_plugin_manifest(self) -> Dict[str, Any]:
        """
        Create OpenAI plugin manifest for RAG++ integration.
        """
        return {
            "schema_version": "v1",
            "name_for_human": "RAG++ Scientific Research Assistant",
            "name_for_model": "ragpp_research",
            "description_for_human": "Access recent scientific literature and project knowledge to enhance responses with up-to-date research findings.",
            "description_for_model": "This plugin provides access to recent scientific literature (2020-2025) and project-specific knowledge through a hybrid RAG++ system. Use it to enhance responses with current research findings, especially in psychiatry, computational methods, and neuroimaging.",
            "auth": {"type": "none"},
            "api": {"type": "openapi", "url": "http://localhost:8000/openapi.json"},
            "logo_url": "http://localhost:8000/logo.png",
            "contact_email": "support@ragpp.local",
            "legal_info_url": "http://localhost:8000/legal",
        }

    def export_for_custom_gpt(
        self, output_file: str = "ragpp/outputs/custom_gpt_instructions.md"
    ) -> str:
        """
        Export RAG++ context for Custom GPT creation.
        """
        # Get sample of available knowledge
        sample_queries = [
            "recent psychiatric research",
            "computational methods in psychiatry",
            "digital phenotyping mental health",
        ]

        instructions = """# RAG++ Scientific Research Assistant

## Description
This GPT has access to recent scientific literature (2020-2025) and project-specific knowledge through a hybrid RAG++ system, specializing in psychiatry, computational methods, and neuroimaging research.

## Instructions
You are an expert research assistant with access to:
1. **Recent Scientific Literature**: Up-to-date research papers from PubMed (2020-2025)
2. **Project Knowledge**: Specific insights and developments from ongoing research
3. **Hybrid Search**: Intelligent routing between literature and project-specific queries

### Available Knowledge Areas:
- Computational psychiatry and machine learning approaches
- Digital phenotyping and wearable sensors
- Neuroimaging and brain connectivity analysis  
- Language analysis and semantic processing
- Therapeutic innovations (psilocybin, ketamine, VR therapy)
- Genomic and epigenetic research findings

### Response Guidelines:
1. Always reference specific sources when citing research
2. Distinguish between published literature and project insights
3. Provide confidence levels for research claims
4. Suggest related areas for exploration
5. Highlight recent developments and emerging trends

### Sample Knowledge Available:
"""

        # Add sample context
        for query in sample_queries:
            try:
                response = self.rag_system.enhanced_qa(query)
                instructions += f"\n#### {query.title()}:\n"

                if response.get("literature_results"):
                    for result in response["literature_results"][:2]:
                        title = result.get("title", "Unknown")
                        authors = result.get("authors", "Unknown")
                        instructions += f"- {title} ({authors})\n"

            except Exception as e:
                instructions += f"- Error accessing knowledge for '{query}': {e}\n"

        instructions += """
## Usage Notes
- Ask about recent developments in psychiatric research
- Request specific methodological approaches  
- Inquire about computational tools and techniques
- Explore connections between different research areas
- Get recommendations for further investigation

## Data Sources
- PubMed scientific literature (2020-2025)
- Project-specific research memories and insights
- Curated knowledge in computational psychiatry
- Real-time synthesis of multiple information sources
"""

        # Save instructions
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(instructions)

        print(f"📄 Custom GPT instructions exported to: {output_path}")
        return str(output_path)


class GitHubCopilotRAGIntegration:
    """
    Integration with GitHub Copilot for enhanced code suggestions.
    """

    def __init__(self):
        self.rag_system = MCPRAGIntegration()

    def create_copilot_context_file(
        self, project_description: str, output_file: str = ".copilot-context.md"
    ) -> str:
        """
        Create context file for GitHub Copilot with RAG++ knowledge.
        """
        # Get relevant research context
        research_context = self.rag_system.enhanced_qa(
            question=f"computational methods research relevant to {project_description}"
        )

        context_content = f"""# Project Context for GitHub Copilot

## Project Description
{project_description}

## Available Research Context
This project has access to recent scientific literature and research findings through a RAG++ system.

### Recent Research Methods Available:
"""

        # Add literature context
        if research_context.get("literature_results"):
            context_content += "\n#### Scientific Literature:\n"
            for result in research_context["literature_results"][:5]:
                title = result.get("title", "Unknown")
                authors = result.get("authors", "Unknown")
                context_content += f"- **{title}** by {authors}\n"

        # Add project insights
        if research_context.get("memory_results"):
            context_content += "\n#### Project Insights:\n"
            for result in research_context["memory_results"][:3]:
                content = result.get("content", "")[:200] + "..."
                category = result.get("category", "general")
                context_content += f"- [{category}] {content}\n"

        context_content += """
## Code Guidelines
- Follow scientific computing best practices
- Include proper documentation and citations
- Implement robust error handling
- Use validated computational methods
- Consider recent research findings in implementation

## Preferred Libraries and Tools
- NumPy/SciPy for numerical computing
- Pandas for data manipulation  
- Scikit-learn for machine learning
- PyTorch for deep learning
- Matplotlib/Seaborn for visualization
- Jupyter notebooks for research workflows
"""

        # Save context file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(context_content)

        print(f"📄 GitHub Copilot context file created: {output_file}")
        return output_file

    def generate_docstring_with_research(
        self, function_name: str, function_purpose: str
    ) -> str:
        """
        Generate enhanced docstring with research context.
        """
        # Get relevant research
        research = self.rag_system.enhanced_qa(
            question=f"research methods for {function_purpose}"
        )

        docstring = f'''"""
{function_purpose}

This implementation follows best practices from recent research literature.
"""'''

        if research.get("literature_results"):
            references = []
            for result in research["literature_results"][:2]:
                title = result.get("title", "Unknown")
                authors = result.get("authors", "Unknown")
                references.append(f"{authors}. {title}")

            if references:
                docstring = f'''"""
{function_purpose}

This implementation follows best practices from recent research literature.

References:
{chr(10).join(f"- {ref}" for ref in references)}
"""'''

        return docstring


def main():
    """CLI for RAG++ integrations with OpenAI and Copilot."""
    import argparse

    parser = argparse.ArgumentParser(
        description="RAG++ integrations with ChatGPT, Codex, and Copilot"
    )
    parser.add_argument(
        "--action",
        choices=["chat", "code", "export-gpt", "copilot-context", "test"],
        default="test",
        help="Action to perform",
    )
    parser.add_argument("--query", help="Query for chat or code generation")
    parser.add_argument("--model", default="gpt-4", help="OpenAI model to use")
    parser.add_argument(
        "--language", default="python", help="Programming language for code generation"
    )

    args = parser.parse_args()

    if args.action == "test":
        print("🧪 Testing RAG++ integrations...")

        # Test OpenAI integration
        openai_integration = OpenAIRAGIntegration(model=args.model)

        if openai_integration.client:
            print("✅ OpenAI integration ready")
        else:
            print("⚠️ OpenAI integration not ready (check API key)")

        # Test Copilot integration
        copilot_integration = GitHubCopilotRAGIntegration()
        print("✅ GitHub Copilot integration ready")

        # Export Custom GPT instructions
        openai_integration.export_for_custom_gpt()

        # Create Copilot context
        copilot_integration.create_copilot_context_file(
            "PCS Meta-Repo: Computational psychiatry research with RAG++ system"
        )

        print("\n🎯 Integration setup complete!")
        print("Next steps:")
        print("1. Set OPENAI_API_KEY for ChatGPT/GPT-4 integration")
        print("2. Use generated .copilot-context.md for enhanced code suggestions")
        print("3. Import custom GPT instructions for specialized research assistant")

    elif args.action == "export-gpt":
        openai_integration = OpenAIRAGIntegration()
        output_file = openai_integration.export_for_custom_gpt()
        print(f"📄 Custom GPT instructions exported to: {output_file}")

    elif args.action == "copilot-context":
        copilot_integration = GitHubCopilotRAGIntegration()
        context_file = copilot_integration.create_copilot_context_file(
            args.query or "Research project with computational methods"
        )
        print(f"📄 Copilot context created: {context_file}")

    elif args.action == "chat" and args.query:
        openai_integration = OpenAIRAGIntegration(model=args.model)

        if not openai_integration.client:
            print("❌ OpenAI client not available. Set OPENAI_API_KEY.")
            return

        print(f"💬 Chatting with {args.model} + RAG++...")
        result = asyncio.run(openai_integration.chat_with_rag(args.query))

        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"\n🤖 Response:")
            print(result["response"])
            print(f"\n📊 Context: {result['context_summary']}")

    elif args.action == "code" and args.query:
        openai_integration = OpenAIRAGIntegration(model=args.model)

        if not openai_integration.client:
            print("❌ OpenAI client not available. Set OPENAI_API_KEY.")
            return

        print(f"⚡ Generating {args.language} code with {args.model} + RAG++...")
        result = openai_integration.code_with_rag(args.query, args.language)

        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"\n💻 Generated Code:")
            print(result["code"])


if __name__ == "__main__":
    main()
