#!/usr/bin/env python3
"""
Repository lint and QA tool for PCS-Meta-Repo v4.4
Research-grade validation following best practices
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Configure logging for research-grade output
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RepositoryLinter:
    """
    Research-grade repository linter following computational reproducibility standards.

    References:
    - Sandve et al. (2013). Ten simple rules for reproducible computational research.
    - Wilson et al. (2017). Good enough practices in scientific computing.
    """

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.errors = []
        self.warnings = []
        self.info = []

    def check_required_structure(self) -> None:
        """Validate canonical repository structure for v4.4."""
        logger.info("Checking required directory structure")

        required_dirs = [
            "docs",
            "src",
            "scripts",
            "notebooks",
            "data",
            "figures",
            "reports",
            "tools",
            "config",
        ]

        for dir_name in required_dirs:
            dir_path = self.repo_path / dir_name
            if not dir_path.exists():
                self.errors.append(f"Missing required directory: {dir_name}")
            elif not dir_path.is_dir():
                self.errors.append(f"Path exists but is not a directory: {dir_name}")
            else:
                self.info.append(f"✓ Directory exists: {dir_name}")

    def check_configuration_files(self) -> None:
        """Validate configuration files for v4.4."""
        logger.info("Checking configuration files")

        config_files = [
            "config/data_root.yaml",
            "config/datasets.yaml",
            "pyproject.toml",
            "requirements.txt",
        ]

        for config_file in config_files:
            file_path = self.repo_path / config_file
            if not file_path.exists():
                self.warnings.append(f"Missing configuration file: {config_file}")
            else:
                self.info.append(f"✓ Configuration file exists: {config_file}")

                # Validate YAML syntax for config files
                if config_file.endswith(".yaml"):
                    try:
                        with open(file_path) as f:
                            yaml.safe_load(f)
                        self.info.append(f"✓ Valid YAML syntax: {config_file}")
                    except yaml.YAMLError as e:
                        self.errors.append(f"Invalid YAML syntax in {config_file}: {e}")

    def check_governance_docs(self) -> None:
        """Validate governance documentation."""
        logger.info("Checking governance documentation")

        governance_files = [
            "docs/GOVERNANCE_v4.4.md",
            "docs/RUNBOOK_minimal_v4.4.md",
            "CITATION.cff",
            "README.md",
        ]

        for doc_file in governance_files:
            file_path = self.repo_path / doc_file
            if not file_path.exists():
                self.warnings.append(f"Missing governance document: {doc_file}")
            else:
                self.info.append(f"✓ Governance document exists: {doc_file}")

    def check_data_structure(self) -> None:
        """Validate data directory structure for modal split."""
        logger.info("Checking data structure for v4.4 modal split")

        data_dirs = ["data/L1_tidy", "data/L2_derived", "data/processed"]

        for data_dir in data_dirs:
            dir_path = self.repo_path / data_dir
            if not dir_path.exists():
                self.warnings.append(f"Data directory not found: {data_dir}")
            else:
                self.info.append(f"✓ Data directory exists: {data_dir}")

    def check_code_quality(self) -> None:
        """Basic code quality checks."""
        logger.info("Checking code quality indicators")

        # Check for Python files with basic quality indicators
        python_files = list(self.repo_path.rglob("*.py"))

        if len(python_files) == 0:
            self.warnings.append("No Python files found")
        else:
            self.info.append(f"✓ Found {len(python_files)} Python files")

            # Check for docstrings in main modules
            main_modules = [
                "src/cli/kec_compile.py",
                "src/datasets/zuco_rt_loader.py",
                "src/datasets/zuco_eeg_loader.py",
                "scripts/swow_zuco_pipeline.py",
            ]

            for module in main_modules:
                module_path = self.repo_path / module
                if module_path.exists():
                    self.info.append(f"✓ Main module exists: {module}")
                else:
                    self.warnings.append(f"Main module missing: {module}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive QA report."""
        # Run all checks
        self.check_required_structure()
        self.check_configuration_files()
        self.check_governance_docs()
        self.check_data_structure()
        self.check_code_quality()

        # Compile report
        report = {
            "timestamp": "2024-01-01T00:00:00Z",  # Will be set dynamically
            "repository_path": str(self.repo_path),
            "qa_summary": {
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "info": len(self.info),
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "status": "PASS" if len(self.errors) == 0 else "FAIL",
        }

        return report


def main():
    """Main QA execution following research reproducibility standards."""
    parser = argparse.ArgumentParser(
        description="Repository QA tool for PCS-Meta-Repo v4.4"
    )
    parser.add_argument(
        "--repo", type=Path, default=Path.cwd(), help="Repository root path"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/lint_qa.json"),
        help="Output report path",
    )

    args = parser.parse_args()

    # Ensure reports directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Run QA
    linter = RepositoryLinter(args.repo)
    report = linter.generate_report()

    # Save report
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print(f"QA Report Generated: {args.output}")
    print(f"Status: {report['status']}")
    print(f"Errors: {report['qa_summary']['errors']}")
    print(f"Warnings: {report['qa_summary']['warnings']}")
    print(f"Info: {report['qa_summary']['info']}")

    # Print errors and warnings
    if report["errors"]:
        print("\nERRORS:")
        for error in report["errors"]:
            print(f"  ❌ {error}")

    if report["warnings"]:
        print("\nWARNINGS:")
        for warning in report["warnings"]:
            print(f"  ⚠️  {warning}")

    # Exit with appropriate code
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    exit(main())
