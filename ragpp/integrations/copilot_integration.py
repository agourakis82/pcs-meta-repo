#!/usr/bin/env python3
"""
RAG++ Integration with GitHub Copilot
Enhanced code suggestions with research context.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from tools.mcp_rag_integration import MCPRAGIntegration
except ImportError:
    # Try alternative import path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from ragpp.tools.mcp_rag_integration import MCPRAGIntegration


class CopilotRAGEnhancer:
    """
    Enhance GitHub Copilot with RAG++ research context.
    """

    def __init__(self):
        self.rag_system = MCPRAGIntegration()
        self.workspace_root = Path.cwd()

    def setup_copilot_workspace(
        self, project_description: str, research_areas: List[str] = None
    ) -> Dict[str, str]:
        """
        Setup complete Copilot integration for workspace.

        Args:
            project_description: Description of the project
            research_areas: Relevant research areas to include

        Returns:
            Paths to created files
        """
        print("🚀 Setting up GitHub Copilot + RAG++ integration...")

        created_files = {}

        # 1. Create .copilot-context.md
        context_file = self.create_context_file(project_description, research_areas)
        created_files["context"] = context_file

        # 2. Create .github/copilot-instructions.md
        instructions_file = self.create_instructions_file()
        created_files["instructions"] = instructions_file

        # 3. Create research-enhanced docstring templates
        templates_file = self.create_docstring_templates()
        created_files["templates"] = templates_file

        # 4. Create VS Code settings for enhanced Copilot
        vscode_settings = self.create_vscode_settings()
        created_files["vscode_settings"] = vscode_settings

        print("✅ Copilot + RAG++ integration complete!")
        return created_files

    def create_context_file(
        self, project_description: str, research_areas: List[str] = None
    ) -> str:
        """
        Create .copilot-context.md with RAG++ knowledge.
        """
        # Get relevant research for project
        if research_areas:
            research_queries = research_areas
        else:
            research_queries = [
                f"computational methods {project_description}",
                f"machine learning {project_description}",
                "recent research methodology",
            ]

        context_content = f"""# GitHub Copilot Context - RAG++ Enhanced

## Project Overview
{project_description}

## Research-Enhanced Development Context

This project leverages recent scientific research through a RAG++ system that combines:
- Recent scientific literature (2020-2025)
- Project-specific research insights
- Computational methodology best practices

"""

        # Add research context for each area
        for area in research_queries:
            try:
                response = self.rag_system.hybrid_search(query=area, max_rag_results=3)

                if response and "rag_results" in response:
                    context_content += f"\n### {area.title()}:\n"
                    for result in response["rag_results"][:3]:
                        title = result.get("content", "")[:100] + "..."
                        context_content += f"- {title}\n"

            except Exception as e:
                context_content += (
                    f"\n### {area.title()}:\n- Research context loading error: {e}\n"
                )

        context_content += """
## Development Guidelines

### Code Quality Standards
- Follow scientific computing best practices
- Include comprehensive docstrings with research references
- Implement robust error handling and validation
- Use type hints and clear variable names
- Include unit tests for computational functions

### Preferred Libraries and Patterns
- **Numerical Computing**: NumPy, SciPy, pandas
- **Machine Learning**: scikit-learn, PyTorch, TensorFlow
- **Data Visualization**: matplotlib, seaborn, plotly
- **Statistical Analysis**: statsmodels, pingouin
- **Research Workflows**: Jupyter notebooks, papermill

### Documentation Patterns
```python
def research_function(data, method="default"):
    \"\"\"
    Brief description based on research methodology.
    
    This implementation follows best practices from:
    - Author et al. (2023). "Research Paper Title"
    - Method validated in recent literature
    
    Args:
        data: Input data description
        method: Computational approach to use
        
    Returns:
        Processed results with validation metrics
        
    Raises:
        ValueError: When input validation fails
    \"\"\"
    pass
```

### Research Integration Patterns
- Always validate computational methods against literature
- Include confidence intervals and statistical measures
- Document assumptions and limitations
- Provide alternative implementation approaches
- Reference specific research papers when relevant

## Current Research Context
The RAG++ system has indexed recent research in:
- Computational psychiatry and neuroscience
- Machine learning applications in mental health
- Digital phenotyping and behavioral analysis
- Neuroimaging and brain connectivity
- Language analysis and semantic processing

## VS Code Integration
This workspace is configured with enhanced Copilot settings in `.vscode/settings.json`.
The settings enable research-aware code suggestions and documentation.
"""

        # Write context file
        context_path = self.workspace_root / ".copilot-context.md"
        with open(context_path, "w", encoding="utf-8") as f:
            f.write(context_content)

        print(f"📄 Created Copilot context: {context_path}")
        return str(context_path)

    def create_instructions_file(self) -> str:
        """
        Create GitHub-specific Copilot instructions.
        """
        github_dir = self.workspace_root / ".github"
        github_dir.mkdir(exist_ok=True)

        instructions_content = """# GitHub Copilot Instructions - RAG++ Enhanced

## Code Generation Guidelines

### Research-Informed Development
When generating code for this repository:
1. **Reference recent research**: Include citations in docstrings when implementing methods from literature
2. **Validate computational approaches**: Ensure algorithms follow established best practices
3. **Include error handling**: Robust validation for research-grade code
4. **Document assumptions**: Clear documentation of methodological choices

### Specific Areas of Focus

#### Computational Methods
- Implement validated statistical and ML approaches
- Include confidence measures and uncertainty quantification
- Follow reproducible research practices
- Provide multiple implementation strategies when relevant

#### Data Processing
- Use established preprocessing pipelines
- Include data validation and quality checks
- Handle missing data appropriately
- Document data transformations clearly

#### Analysis Functions
- Include statistical significance testing
- Provide effect size calculations
- Implement proper multiple comparison corrections
- Document limitations and assumptions

### Code Review Priorities
1. Scientific accuracy and validation
2. Reproducibility and documentation
3. Error handling and edge cases
4. Performance optimization
5. Code maintainability

### Testing Standards
- Unit tests for all computational functions
- Integration tests for analysis pipelines
- Validation against published benchmarks
- Edge case and error condition testing

## Research Context Integration
This repository uses a RAG++ system that provides:
- Recent scientific literature context
- Validated computational methodologies
- Best practices from peer-reviewed research
- Cross-domain insights and approaches

Use this context to enhance code suggestions with research-backed implementations.
"""

        instructions_path = github_dir / "copilot-instructions.md"
        with open(instructions_path, "w", encoding="utf-8") as f:
            f.write(instructions_content)

        print(f"📄 Created GitHub Copilot instructions: {instructions_path}")
        return str(instructions_path)

    def create_docstring_templates(self) -> str:
        """
        Create enhanced docstring templates with research context.
        """
        templates_content = '''"""
Enhanced Docstring Templates for Research-Informed Code
======================================================

Use these templates for research-enhanced documentation.
"""

# Template 1: Research-Based Function
def computational_method(data, parameters=None):
    """
    Brief description of the computational method.
    
    This implementation is based on methodology from:
    - Author et al. (YEAR). "Paper Title". Journal Name.
    - Validated approach following best practices in [research area]
    
    The method implements [specific algorithm/approach] with the following
    enhancements:
    - [Enhancement 1]
    - [Enhancement 2]
    
    Args:
        data (array-like): Input data description
            Shape: (n_samples, n_features) for typical ML applications
        parameters (dict, optional): Method-specific parameters
            Default: Uses validated parameters from literature
            
    Returns:
        result (array-like): Processed output
            Shape and interpretation details
        metadata (dict): Processing metadata including:
            - validation_metrics: Quality measures
            - confidence_intervals: Statistical confidence bounds
            - method_info: Implementation details
            
    Raises:
        ValueError: When input validation fails
        ComputationError: When algorithm convergence fails
        
    Examples:
        >>> data = np.random.randn(100, 10)
        >>> result, metadata = computational_method(data)
        >>> print(f"Processing quality: {metadata['validation_metrics']}")
        
    Notes:
        - Method assumes [key assumptions]
        - Computational complexity: O([complexity])
        - Memory usage: [memory requirements]
        - Limitations: [known limitations]
        
    References:
        [1] Author, A. et al. (2023). "Paper Title". Journal, vol(issue), pages.
        [2] Author, B. et al. (2024). "Related Work". Conference Proceedings.
    """
    pass

# Template 2: Analysis Pipeline Function  
def analysis_pipeline(input_data, config=None):
    """
    Complete analysis pipeline following research best practices.
    
    Implements end-to-end analysis workflow validated in:
    - [Research paper 1]
    - [Research paper 2]
    
    Pipeline stages:
    1. Data validation and preprocessing
    2. Quality control and outlier detection  
    3. Statistical analysis with multiple comparison correction
    4. Effect size calculation and confidence intervals
    5. Results validation and interpretation
    
    Args:
        input_data: Raw input data
        config: Analysis configuration following validated parameters
        
    Returns:
        AnalysisResults: Complete analysis results with validation
        
    See Also:
        preprocess_data(): Data preprocessing utilities
        validate_results(): Result validation functions
    """
    pass

# Template 3: Machine Learning Implementation
def ml_research_method(X, y, validation_strategy="cross_validation"):
    """
    Machine learning method following recent research guidelines.
    
    Implementation based on best practices from:
    - ML methodology papers
    - Domain-specific validation studies
    - Reproducibility guidelines
    
    Features:
    - Automated hyperparameter tuning
    - Cross-validation with appropriate splits
    - Feature importance analysis  
    - Model interpretability measures
    - Performance validation against benchmarks
    
    Args:
        X: Feature matrix
        y: Target variable
        validation_strategy: Validation approach
        
    Returns:
        MLResults: Comprehensive ML results including:
            - trained_model: Optimized model
            - performance_metrics: Cross-validated performance
            - feature_importance: Feature contribution analysis
            - interpretability: Model explanation
            - validation_report: Statistical validation
    """
    pass

# Template 4: Data Processing Function
def process_research_data(raw_data, processing_config=None):
    """
    Research-grade data processing with validation.
    
    Follows data processing best practices from:
    - [Data science methodology papers]
    - [Domain-specific preprocessing studies]
    
    Processing steps:
    1. Data quality assessment
    2. Missing value handling (research-appropriate methods)
    3. Outlier detection and treatment
    4. Normalization/standardization
    5. Feature engineering
    6. Validation and quality metrics
    
    Args:
        raw_data: Input dataset
        processing_config: Processing configuration
        
    Returns:
        ProcessedData: Validated processed dataset
        QualityReport: Data quality metrics and validation
    """
    pass
'''

        templates_path = self.workspace_root / "copilot_research_templates.py"
        with open(templates_path, "w", encoding="utf-8") as f:
            f.write(templates_content)

        print(f"📄 Created docstring templates: {templates_path}")
        return str(templates_path)

    def create_vscode_settings(self) -> str:
        """
        Create VS Code settings for enhanced Copilot integration.
        """
        vscode_dir = self.workspace_root / ".vscode"
        vscode_dir.mkdir(exist_ok=True)

        settings = {
            "github.copilot.enable": {
                "*": True,
                "yaml": True,
                "plaintext": True,
                "markdown": True,
            },
            "github.copilot.advanced": {
                "length": 500,
                "temperature": 0.1,
                "top_p": 1.0,
            },
            "python.analysis.autoImportCompletions": True,
            "python.analysis.typeCheckingMode": "strict",
            "python.linting.enabled": True,
            "python.linting.pylintEnabled": True,
            "python.formatting.provider": "black",
            "python.formatting.blackArgs": ["--line-length", "88"],
            "files.associations": {
                ".copilot-context.md": "markdown",
                "copilot-instructions.md": "markdown",
            },
            "workbench.editorAssociations": {"*.ipynb": "jupyter-notebook"},
            "jupyter.askForKernelRestart": False,
            "editor.formatOnSave": True,
            "editor.codeActionsOnSave": {"source.organizeImports": True},
        }

        settings_path = vscode_dir / "settings.json"
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

        print(f"📄 Created VS Code settings: {settings_path}")
        return str(settings_path)

    def generate_research_comment(self, function_name: str, purpose: str) -> str:
        """
        Generate research-informed comment for function.
        """
        try:
            # Get research context
            response = self.rag_system.hybrid_search(
                query=f"methodology for {purpose}", max_rag_results=2
            )

            if response and "rag_results" in response:
                comment = f"# {function_name}: {purpose}\n"
                comment += "# Based on research methodology:\n"
                for result in response["rag_results"][:2]:
                    content = result.get("content", "")[:100] + "..."
                    comment += f"# - {content}\n"
                return comment
            else:
                return f"# {function_name}: {purpose}\n# Implementing best practices\n"

        except Exception:
            return f"# {function_name}: {purpose}\n"

    def create_copilot_chat_context(self) -> str:
        """
        Create context for Copilot Chat conversations.
        """
        context_content = """# Copilot Chat Context - RAG++ Enhanced

## Project Context
This is a research-oriented project with access to recent scientific literature and computational methodologies through a RAG++ system.

## Available Knowledge
- Recent psychiatric and neuroscience research (2020-2025)
- Computational methods and machine learning approaches
- Digital phenotyping and behavioral analysis techniques
- Neuroimaging and brain connectivity research
- Statistical and data analysis methodologies

## Chat Guidelines
When assisting with code:
1. Reference relevant research when suggesting implementations
2. Recommend validated computational approaches
3. Include error handling and validation strategies
4. Suggest appropriate testing methodologies
5. Consider reproducibility and documentation standards

## Research Areas Available
- Computational psychiatry
- Machine learning in healthcare
- Digital biomarkers and phenotyping
- Neuroimaging analysis
- Language and semantic processing
- Statistical methodology

Use "@workspace" to access project-specific context and research insights.
"""

        chat_context_path = self.workspace_root / ".copilot-chat-context.md"
        with open(chat_context_path, "w", encoding="utf-8") as f:
            f.write(context_content)

        print(f"📄 Created Copilot Chat context: {chat_context_path}")
        return str(chat_context_path)


def main():
    """CLI for Copilot RAG++ integration."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Setup GitHub Copilot + RAG++ integration"
    )
    parser.add_argument(
        "--action",
        choices=["setup", "context", "templates", "settings", "test"],
        default="setup",
        help="Action to perform",
    )
    parser.add_argument(
        "--description",
        default="Research project with computational methods and RAG++ integration",
        help="Project description",
    )
    parser.add_argument(
        "--research-areas", nargs="+", help="Specific research areas to include"
    )

    args = parser.parse_args()

    enhancer = CopilotRAGEnhancer()

    if args.action == "setup":
        print("🚀 Setting up complete Copilot + RAG++ integration...")
        created_files = enhancer.setup_copilot_workspace(
            project_description=args.description, research_areas=args.research_areas
        )

        print("\n✅ Integration complete! Created files:")
        for file_type, path in created_files.items():
            print(f"  - {file_type}: {path}")

        print("\n🎯 Next steps:")
        print("1. Restart VS Code to load new settings")
        print("2. GitHub Copilot will now use research context")
        print("3. Use templates in copilot_research_templates.py")
        print("4. Reference .copilot-context.md for project knowledge")

    elif args.action == "context":
        context_file = enhancer.create_context_file(
            args.description, args.research_areas
        )
        print(f"📄 Context file created: {context_file}")

    elif args.action == "templates":
        templates_file = enhancer.create_docstring_templates()
        print(f"📄 Templates created: {templates_file}")

    elif args.action == "settings":
        settings_file = enhancer.create_vscode_settings()
        print(f"📄 VS Code settings created: {settings_file}")

    elif args.action == "test":
        print("🧪 Testing Copilot RAG++ integration...")

        # Test basic functionality
        try:
            response = enhancer.rag_system.hybrid_search(
                query="machine learning methods", search_type="literature", limit=2
            )
            print(
                f"✅ RAG++ system working: {len(response) if response else 0} results"
            )
        except Exception as e:
            print(f"❌ RAG++ system error: {e}")

        # Test comment generation
        comment = enhancer.generate_research_comment(
            "analyze_data", "statistical analysis of experimental data"
        )
        print(f"\n📝 Sample research comment:")
        print(comment)

        print("\n🎯 Ready for enhanced Copilot development!")


if __name__ == "__main__":
    main()
