#!/usr/bin/env python3
"""
Step-by-step execution script for PCS-Meta-Repo v4.4
Research-grade pipeline execution following reproducibility standards
"""

import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PipelineExecutor:
    """
    Execute v4.4 pipeline steps with proper error handling and validation.

    References:
    - Reproducible research workflow best practices
    - Scientific computing pipeline standards
    """

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.step_count = 0

    def run_command(
        self, cmd: List[str], description: str, cwd: Optional[Path] = None
    ) -> bool:
        """Execute command with proper logging and error handling."""
        self.step_count += 1
        logger.info(f"Step {self.step_count}: {description}")
        logger.info(f"Command: {' '.join(cmd)}")

        if cwd is None:
            cwd = self.repo_path

        try:
            start_time = time.time()
            result = subprocess.run(
                cmd, cwd=cwd, check=True, capture_output=True, text=True
            )

            duration = time.time() - start_time
            logger.info(f"✓ Step {self.step_count} completed in {duration:.2f}s")

            if result.stdout:
                logger.info(f"Output: {result.stdout.strip()}")

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Step {self.step_count} failed with code {e.returncode}")
            if e.stdout:
                logger.error(f"Stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"Stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"✗ Step {self.step_count} failed with exception: {e}")
            return False

    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        logger.info("Checking dependencies...")

        # Check Python
        if not self.run_command(["python", "--version"], "Check Python version"):
            return False

        # Check if we can import required packages
        import_checks = [
            "import pandas",
            "import numpy",
            "import yaml",
            "import matplotlib",
        ]

        for import_check in import_checks:
            if not self.run_command(
                ["python", "-c", import_check], f"Check import: {import_check}"
            ):
                logger.warning(f"Package not available: {import_check}")

        return True

    def step_0_environment_qa(self) -> bool:
        """Step 0: Environment setup and initial QA."""
        logger.info("=== STEP 0: Environment & Initial QA ===")

        # Check dependencies
        if not self.check_dependencies():
            logger.error("Dependency check failed")
            return False

        # Run repository linter
        if not self.run_command(
            ["python", "tools/repo_lint.py"], "Run repository QA linter"
        ):
            logger.warning("Repository linting failed, continuing...")

        # Compute initial checksums
        if not self.run_command(
            ["python", "-m", "scripts.compute_checksums", "--inventory", "repo"],
            "Compute repository checksums",
        ):
            logger.warning("Checksum computation failed, continuing...")

        # Verify structure
        if not self.run_command(
            ["bash", "tools/verify_v4.4_structure.sh"], "Verify v4.4 structure"
        ):
            logger.warning("Structure verification had warnings, continuing...")

        return True

    def step_1_fetch_data(self) -> bool:
        """Step 1: Fetch real datasets (placeholder - would run fetch script)."""
        logger.info("=== STEP 1: Fetch Real Datasets ===")

        # This would normally run the fetch script
        logger.info("Note: Data fetching is environment-specific")
        logger.info(
            "Please ensure datasets are available according to config/datasets.yaml"
        )

        # Check if basic data directories exist
        data_dirs = ["data/L0_raw", "data/raw_public"]
        for data_dir in data_dirs:
            dir_path = self.repo_path / data_dir
            if not dir_path.exists():
                logger.warning(f"Data directory not found: {data_dir}")
                logger.info(f"Creating placeholder: {data_dir}")
                dir_path.mkdir(parents=True, exist_ok=True)

        return True

    def step_2_tidy_rt(self) -> bool:
        """Step 2: L0→L1 tidy for RT/ET datasets."""
        logger.info("=== STEP 2: Tidy RT/ET Datasets ===")

        return self.run_command(
            [
                "python",
                "-m",
                "scripts.swow_zuco_pipeline",
                "--step",
                "tidy_rt",
                "--datasets",
                "zuco_rt,geco_et,onestop_et",
            ],
            "Process RT/ET datasets to L1 tidy format",
        )

    def step_2b_tidy_eeg(self) -> bool:
        """Step 2b: L0→L1 tidy for EEG datasets."""
        logger.info("=== STEP 2b: Tidy EEG Datasets ===")

        return self.run_command(
            [
                "python",
                "-m",
                "scripts.swow_zuco_pipeline",
                "--step",
                "tidy_eeg",
                "--datasets",
                "zuco_eeg,derco_eeg,lpp_eeg",
            ],
            "Process EEG datasets to L1 tidy format",
        )

    def step_3_kec_compile(self) -> bool:
        """Step 3: KEC compilation for all languages."""
        logger.info("=== STEP 3: KEC Compilation (Multilingual) ===")

        return self.run_command(
            [
                "python",
                "-m",
                "src.cli.kec_compile",
                "--lang",
                "en,es,nl,zh",
                "--step",
                "all",
                "--device",
                "auto",
                "--resume",
            ],
            "Compile KEC metrics for all languages",
        )

    def step_4_integration(self) -> bool:
        """Step 4: Integration SWOW↔(EEG/RT)."""
        logger.info("=== STEP 4: SWOW↔(EEG/RT) Integration ===")

        return self.run_command(
            ["python", "scripts/swow_zuco_pipeline.py", "--step", "integrate"],
            "Integrate SWOW KEC with EEG/RT datasets",
        )

    def step_5_models(self) -> bool:
        """Step 5: Run prediction models."""
        logger.info("=== STEP 5: Prediction Models ===")

        # RT models
        if not self.run_command(
            ["python", "scripts/swow_zuco_pipeline.py", "--step", "models_rt"],
            "Run RT prediction models",
        ):
            return False

        # EEG models
        if not self.run_command(
            ["python", "scripts/swow_zuco_pipeline.py", "--step", "models_eeg"],
            "Run EEG prediction models",
        ):
            return False

        # Optional R validation
        self.run_command(
            ["Rscript", "scripts/r_mixedlm_check.R"],
            "Run R mixed-effects validation (optional)",
        )

        return True

    def step_6_figures(self) -> bool:
        """Step 6: Generate figures."""
        logger.info("=== STEP 6: Generate Figures ===")

        return self.run_command(
            ["python", "-m", "src.figures.make_figures", "--version", "v4.4"],
            "Generate v4.4 figures",
        )

    def step_7_qa_final(self) -> bool:
        """Step 7: Final QA and release preparation."""
        logger.info("=== STEP 7: Final QA & Release ===")

        # Final linting
        if not self.run_command(
            ["python", "tools/repo_lint.py"], "Final repository QA"
        ):
            logger.warning("Final QA had issues")

        # Final checksums
        if not self.run_command(
            ["python", "-m", "scripts.compute_checksums", "--inventory", "repo"],
            "Final checksum computation",
        ):
            logger.warning("Final checksums failed")

        logger.info("Pipeline execution completed!")
        logger.info("Check reports/ directory for QA outputs")
        logger.info("Expected outputs:")
        logger.info("- data/L1_tidy/*/word_events_{rt,eeg}.parquet")
        logger.info("- data/L2_derived/kec/*/entropy.parquet")
        logger.info("- data/processed/v4.4/integration/*.parquet")
        logger.info("- figures/v4.4/*.png")
        logger.info("- reports/{inventory,provenance}/*")

        return True


def main():
    """Main pipeline execution."""
    repo_path = Path.cwd()
    executor = PipelineExecutor(repo_path)

    print("🧠 PCS-Meta-Repo v4.4 Pipeline Execution")
    print("======================================")
    print(f"Repository: {repo_path}")
    print()

    # Define execution steps
    steps = [
        ("Environment & QA", executor.step_0_environment_qa),
        ("Fetch Data", executor.step_1_fetch_data),
        ("Tidy RT", executor.step_2_tidy_rt),
        ("Tidy EEG", executor.step_2b_tidy_eeg),
        ("KEC Compile", executor.step_3_kec_compile),
        ("Integration", executor.step_4_integration),
        ("Models", executor.step_5_models),
        ("Figures", executor.step_6_figures),
        ("Final QA", executor.step_7_qa_final),
    ]

    # Ask user which steps to run
    print("Available steps:")
    for i, (name, _) in enumerate(steps):
        print(f"  {i}: {name}")
    print()

    try:
        choice = input(
            "Enter step number to start from (0 for all, q to quit): "
        ).strip()

        if choice.lower() == "q":
            print("Exiting...")
            return 0

        start_step = 0 if choice == "" else int(choice)

        # Execute steps
        success = True
        for i, (name, step_func) in enumerate(steps[start_step:], start_step):
            print(f"\n{'='*50}")
            print(f"Executing Step {i}: {name}")
            print(f"{'='*50}")

            if not step_func():
                print(f"❌ Step {i} failed: {name}")
                choice = input("Continue anyway? (y/N): ").strip().lower()
                if choice != "y":
                    success = False
                    break
            else:
                print(f"✅ Step {i} completed: {name}")

        if success:
            print("\n🎉 Pipeline execution completed successfully!")
        else:
            print("\n⚠️  Pipeline execution incomplete due to errors")

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        return 1
    except Exception as e:
        print(f"\nPipeline failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
