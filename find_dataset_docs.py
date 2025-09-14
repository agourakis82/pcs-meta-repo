#!/usr/bin/env python3
"""
Research-grade dataset documentation and processing instructions finder
Based on official sources and established methodologies

References:
- ZuCo OSF repository: https://osf.io/2urht/
- Hollenstein et al. (2018). ZuCo, a simultaneous EEG and eye-tracking corpus
- GECO corpus documentation
- OneStop corpus specifications
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetDocumentationFinder:
    """
    Find and extract processing instructions from official dataset sources
    Following research-grade documentation standards
    """

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.docs_dir = self.repo_root / "docs" / "dataset_docs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def find_zuco_documentation(self) -> Dict[str, str]:
        """
        Extract ZuCo processing instructions from OSF and local sources

        Returns:
            Dictionary with documentation findings
        """
        logger.info("Searching for ZuCo documentation...")

        docs = {
            "source": "ZuCo OSF + Local Files",
            "osf_url": "https://osf.io/2urht/",
            "local_scripts": [],
            "matlab_info": {},
            "python_info": {},
            "data_structure": {},
            "processing_notes": [],
        }

        # Check local ZuCo scripts directory
        zuco_scripts = (
            self.repo_root / "scripts/data/raw_public/zuco/v1/osfstorage/scripts"
        )

        if zuco_scripts.exists():
            logger.info(f"Found ZuCo scripts directory: {zuco_scripts}")

            # Look for README files
            readme_files = list(zuco_scripts.rglob("README*"))
            docs["readme_files"] = [
                str(f.relative_to(self.repo_root)) for f in readme_files
            ]

            # Look for Python scripts
            python_files = list(zuco_scripts.rglob("*.py"))
            docs["python_scripts"] = [
                str(f.relative_to(self.repo_root)) for f in python_files
            ]

            # Look for MATLAB files
            matlab_files = list(zuco_scripts.rglob("*.m"))
            docs["matlab_scripts"] = [
                str(f.relative_to(self.repo_root)) for f in matlab_files
            ]

            # Check for utils_ZuCo.py specifically
            utils_zuco = (
                zuco_scripts / "Load data into Python and beyond" / "utils_ZuCo.py"
            )
            if utils_zuco.exists():
                docs["official_python_loader"] = str(
                    utils_zuco.relative_to(self.repo_root)
                )
                logger.info(f"Found official ZuCo Python loader: {utils_zuco}")

                # Extract key information from utils_ZuCo.py
                try:
                    with open(utils_zuco, "r") as f:
                        content = f.read()
                        docs["python_loader_content"] = content

                        # Extract function signatures and key patterns
                        if "def " in content:
                            functions = [
                                line.strip()
                                for line in content.split("\n")
                                if line.strip().startswith("def ")
                            ]
                            docs["python_functions"] = functions

                        # Look for data structure hints
                        structure_hints = []
                        for line in content.split("\n"):
                            line = line.strip()
                            if any(
                                keyword in line.lower()
                                for keyword in [
                                    "sentence",
                                    "word",
                                    "fixation",
                                    "ffd",
                                    "gd",
                                    "trt",
                                ]
                            ):
                                structure_hints.append(line)
                        docs["structure_hints"] = structure_hints

                except Exception as e:
                    logger.warning(f"Could not read utils_ZuCo.py: {e}")

            # Check for requirements.txt
            requirements = (
                zuco_scripts / "Load data into Python and beyond" / "requirements.txt"
            )
            if requirements.exists():
                try:
                    with open(requirements, "r") as f:
                        docs["python_requirements"] = f.read().strip().split("\n")
                except Exception as e:
                    logger.warning(f"Could not read requirements.txt: {e}")

        # Check for task materials and documentation
        task_materials = (
            self.repo_root / "scripts/data/raw_public/zuco/v1/osfstorage/task_materials"
        )
        if task_materials.exists():
            csv_files = list(task_materials.glob("*.csv"))
            docs["task_materials"] = [
                str(f.relative_to(self.repo_root)) for f in csv_files
            ]

            # Look for label files that might indicate data structure
            for csv_file in csv_files:
                if csv_file.name.endswith("_labels.csv"):
                    try:
                        # Just check the header to understand structure
                        with open(csv_file, "r") as f:
                            header = f.readline().strip()
                            docs[f"{csv_file.stem}_header"] = header
                    except Exception:
                        pass

        return docs

    def find_geco_documentation(self) -> Dict[str, str]:
        """
        Find GECO corpus documentation and processing instructions

        References:
        - Cop, U., Dirix, N., Drieghe, D., & Duyck, W. (2017).
          Presenting GECO: An eyetracking corpus of monolingual and bilingual sentence reading
        """
        logger.info("Searching for GECO documentation...")

        docs = {
            "source": "GECO Corpus",
            "official_url": "http://expsy.ugent.be/downloads/geco/",
            "paper_ref": "Cop et al. (2017). Presenting GECO",
            "local_files": [],
            "data_format": "Tab-separated values",
            "processing_notes": [
                "GECO provides word-level eye-tracking measures",
                "Contains monolingual (English) and bilingual (Dutch-English) data",
                "Standard RT measures: FFD, SFD, GD, TRT, regression measures",
            ],
        }

        # Check if GECO data exists locally
        geco_path = self.repo_root / "scripts/data/raw_public/geco"
        if geco_path.exists():
            # Look for documentation files
            doc_files = (
                list(geco_path.rglob("*.txt"))
                + list(geco_path.rglob("*.pdf"))
                + list(geco_path.rglob("README*"))
            )
            docs["local_files"] = [
                str(f.relative_to(self.repo_root)) for f in doc_files
            ]

            # Look for data files to understand structure
            data_files = list(geco_path.rglob("*.csv")) + list(geco_path.rglob("*.tsv"))
            if data_files:
                docs["data_files"] = [
                    str(f.relative_to(self.repo_root)) for f in data_files[:5]
                ]  # Limit output

                # Check first data file for structure
                try:
                    with open(data_files[0], "r") as f:
                        header = f.readline().strip()
                        docs["sample_header"] = header
                except Exception:
                    pass

        return docs

    def find_onestop_documentation(self) -> Dict[str, str]:
        """
        Find OneStop corpus documentation

        References:
        - Vajjala & Meurers (2014). Readability assessment for text simplification
        """
        logger.info("Searching for OneStop documentation...")

        docs = {
            "source": "OneStop Corpus",
            "description": "Reading comprehension corpus with eye-tracking",
            "processing_notes": [
                "Contains texts at different complexity levels",
                "Eye-tracking data from reading comprehension tasks",
                "Typically includes fixation durations and reading patterns",
            ],
        }

        # Check if OneStop data exists locally
        onestop_path = self.repo_root / "scripts/data/raw_public/onestop"
        if onestop_path.exists():
            # Look for documentation and data files
            all_files = list(onestop_path.rglob("*"))
            docs["local_files"] = [
                str(f.relative_to(self.repo_root)) for f in all_files[:10]
            ]

            # Check for specific file types
            data_files = [
                f for f in all_files if f.suffix in [".csv", ".tsv", ".parquet", ".txt"]
            ]
            if data_files:
                docs["data_files"] = [
                    str(f.relative_to(self.repo_root)) for f in data_files[:5]
                ]

        return docs

    def create_processing_instructions(self, all_docs: Dict) -> str:
        """
        Create comprehensive processing instructions based on found documentation
        """
        instructions = """# Dataset Processing Instructions
# Research-grade data processing based on official documentation

## ZuCo Corpus Processing

### Official Source
- OSF Repository: https://osf.io/2urht/
- Paper: Hollenstein et al. (2018). ZuCo, a simultaneous EEG and eye-tracking corpus

### Data Structure (from official utils_ZuCo.py):
"""

        if "zuco" in all_docs:
            zuco_docs = all_docs["zuco"]

            if "python_functions" in zuco_docs:
                instructions += "\n### Official Python Functions:\n"
                for func in zuco_docs["python_functions"]:
                    instructions += f"- {func}\n"

            if "structure_hints" in zuco_docs:
                instructions += "\n### Data Structure Hints:\n"
                for hint in zuco_docs["structure_hints"][:10]:  # Limit output
                    instructions += f"- {hint}\n"

            instructions += f"""
### Processing Notes:
- Use official utils_ZuCo.py as reference
- Data stored in .mat files with MATLAB struct format
- Word-level measures: FFD, GD, TRT, nFixations
- Sentence-level organization with nested word structures
"""

        if "geco" in all_docs:
            instructions += f"""
## GECO Corpus Processing

### Official Source
- URL: http://expsy.ugent.be/downloads/geco/
- Paper: Cop et al. (2017). Presenting GECO

### Data Format:
- Tab-separated values (.tsv)
- Word-level eye-tracking measures
- Standard RT measures: FFD, SFD, GD, TRT

### Processing Notes:
- Bilingual (English/Dutch) and monolingual data
- Established eye-tracking measure definitions
- CSV/TSV format with headers
"""

        if "onestop" in all_docs:
            instructions += f"""
## OneStop Corpus Processing

### Source
- Reading comprehension corpus with eye-tracking
- Multi-level text complexity

### Processing Notes:
- Focus on comprehension-related measures
- Variable data formats (check local files)
- May require custom parsing logic
"""

        instructions += """
## Implementation Strategy

### 1. ZuCo Loader Priority
- Study official utils_ZuCo.py implementation
- Mirror official data access patterns
- Handle MATLAB struct hierarchy correctly

### 2. Validation Approach
- Compare extracted data with known benchmarks
- Validate RT measure distributions
- Cross-reference with published statistics

### 3. Error Handling
- Robust parsing for different ZuCo versions
- Graceful handling of missing measures
- Data quality validation

### 4. Research Standards
- Document all processing decisions
- Maintain traceability to source data
- Include uncertainty quantification
"""

        return instructions

    def analyze_official_zuco_loader(self) -> Dict[str, str]:
        """
        Analyze the official ZuCo Python loader to understand correct data access
        """
        logger.info("Analyzing official ZuCo loader...")

        analysis = {}

        utils_zuco = (
            self.repo_root
            / "scripts/data/raw_public/zuco/v1/osfstorage/scripts/Load data into Python and beyond/utils_ZuCo.py"
        )

        if utils_zuco.exists():
            try:
                with open(utils_zuco, "r") as f:
                    content = f.read()

                # Extract key patterns
                patterns = {
                    "data_loading": [],
                    "struct_access": [],
                    "rt_measures": [],
                    "sentence_iteration": [],
                    "word_iteration": [],
                }

                lines = content.split("\n")
                for i, line in enumerate(lines):
                    line_clean = line.strip()

                    # Look for scipy.io.loadmat usage
                    if "loadmat" in line_clean:
                        patterns["data_loading"].append(f"Line {i+1}: {line_clean}")

                    # Look for struct field access
                    if any(
                        field in line_clean for field in ["sentence", "word", "content"]
                    ):
                        patterns["struct_access"].append(f"Line {i+1}: {line_clean}")

                    # Look for RT measure access
                    if any(
                        rt in line_clean for rt in ["FFD", "GD", "TRT", "nFixations"]
                    ):
                        patterns["rt_measures"].append(f"Line {i+1}: {line_clean}")

                    # Look for iteration patterns
                    if "for " in line_clean and (
                        "sentence" in line_clean or "word" in line_clean
                    ):
                        patterns["sentence_iteration"].append(
                            f"Line {i+1}: {line_clean}"
                        )

                analysis["patterns"] = patterns
                analysis["full_content"] = content

            except Exception as e:
                logger.error(f"Failed to analyze utils_ZuCo.py: {e}")
                analysis["error"] = str(e)
        else:
            analysis["error"] = "Official ZuCo loader not found"

        return analysis


def main():
    """Main documentation finder execution"""

    print("📚 DATASET DOCUMENTATION FINDER")
    print("Research-grade processing instructions from official sources")
    print("=" * 60)

    repo_root = Path("/home/agourakis82/workspace/pcs-meta-repo")
    finder = DatasetDocumentationFinder(repo_root)

    # Find documentation for all datasets
    all_docs = {}

    print("🔍 Searching ZuCo documentation...")
    all_docs["zuco"] = finder.find_zuco_documentation()

    print("🔍 Searching GECO documentation...")
    all_docs["geco"] = finder.find_geco_documentation()

    print("🔍 Searching OneStop documentation...")
    all_docs["onestop"] = finder.find_onestop_documentation()

    # Analyze official ZuCo loader
    print("🔍 Analyzing official ZuCo loader...")
    zuco_analysis = finder.analyze_official_zuco_loader()
    all_docs["zuco"]["official_analysis"] = zuco_analysis

    # Create comprehensive processing instructions
    print("📝 Creating processing instructions...")
    instructions = finder.create_processing_instructions(all_docs)

    # Save documentation
    docs_dir = finder.docs_dir

    # Save full documentation as JSON
    with open(docs_dir / "dataset_documentation.json", "w") as f:
        json.dump(all_docs, f, indent=2, default=str)

    # Save processing instructions
    with open(docs_dir / "processing_instructions.md", "w") as f:
        f.write(instructions)

    # Save ZuCo analysis separately
    if "official_analysis" in all_docs["zuco"]:
        with open(docs_dir / "zuco_official_analysis.json", "w") as f:
            json.dump(all_docs["zuco"]["official_analysis"], f, indent=2, default=str)

    # Print summary
    print(f"\n📊 DOCUMENTATION SUMMARY:")
    print("=" * 40)

    for dataset, docs in all_docs.items():
        print(f"\n{dataset.upper()}:")

        if "official_python_loader" in docs:
            print(f"  ✅ Official Python loader found")
        if "python_functions" in docs:
            print(f"  ✅ {len(docs['python_functions'])} Python functions")
        if "structure_hints" in docs:
            print(f"  ✅ {len(docs['structure_hints'])} structure hints")
        if "local_files" in docs:
            print(f"  ✅ {len(docs['local_files'])} local files")
        if "data_files" in docs:
            print(f"  ✅ {len(docs['data_files'])} data files")

    print(f"\n📁 Documentation saved to:")
    print(f"  - {docs_dir}/dataset_documentation.json")
    print(f"  - {docs_dir}/processing_instructions.md")
    print(f"  - {docs_dir}/zuco_official_analysis.json")

    print(f"\n🚀 Next Steps:")
    print("1. Review processing_instructions.md")
    print("2. Study official ZuCo loader patterns")
    print("3. Implement research-grade loaders based on official methods")
    print("4. Validate against known benchmarks")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
