#!/usr/bin/env python3
"""
Checksum computation and provenance tracking for PCS-Meta-Repo v4.4
Research-grade data integrity following FAIR principles
"""

import argparse
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProvenanceTracker:
    """
    Track data provenance and integrity following FAIR data principles.

    References:
    - Wilkinson et al. (2016). The FAIR Guiding Principles for scientific data management
    - Peng (2011). Reproducible research in computational science
    """

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.reports_dir = repo_path / "reports" / "provenance"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def compute_file_hash(self, file_path: Path) -> Optional[str]:
        """Compute SHA-256 hash for file integrity verification."""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files efficiently
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to compute hash for {file_path}: {e}")
            return None

    def scan_directory(self, directory: Path, pattern: str = "*") -> Dict[str, Any]:
        """
        Scan directory and compute checksums for all matching files.

        Args:
            directory: Directory to scan
            pattern: File pattern to match (e.g., "*.parquet", "*.csv")

        Returns:
            Dictionary with file metadata and checksums
        """
        logger.info(f"Scanning directory: {directory} with pattern: {pattern}")

        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return {}

        files_data = {}

        for file_path in directory.rglob(pattern):
            if file_path.is_file():
                # Skip hidden files and common non-data files
                if file_path.name.startswith("."):
                    continue

                rel_path = str(file_path.relative_to(self.repo_path))

                try:
                    stat = file_path.stat()
                    file_hash = self.compute_file_hash(file_path)

                    files_data[rel_path] = {
                        "path": rel_path,
                        "size_bytes": stat.st_size,
                        "modified_time": stat.st_mtime,
                        "sha256": file_hash,
                        "timestamp_scanned": datetime.now().isoformat(),
                    }

                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    files_data[rel_path] = {
                        "path": rel_path,
                        "error": str(e),
                        "timestamp_scanned": datetime.now().isoformat(),
                    }

        return files_data

    def generate_dataset_provenance(self, dataset_name: str) -> Dict[str, Any]:
        """Generate provenance report for a specific dataset."""
        logger.info(f"Generating provenance for dataset: {dataset_name}")

        # Try to load dataset configuration
        config_path = self.repo_path / "config" / "datasets.yaml"
        dataset_config = {}

        if config_path.exists():
            try:
                with open(config_path) as f:
                    all_configs = yaml.safe_load(f)

                # Find dataset in different sections
                for section in ["swow", "datasets_rt", "datasets_eeg"]:
                    if section in all_configs:
                        if dataset_name == "swow" and section == "swow":
                            dataset_config = all_configs[section]
                            break
                        elif dataset_name in all_configs.get(section, {}):
                            dataset_config = all_configs[section][dataset_name]
                            break

            except Exception as e:
                logger.warning(f"Could not load dataset config: {e}")

        # Scan relevant directories
        provenance_data = {
            "dataset_name": dataset_name,
            "timestamp": datetime.now().isoformat(),
            "configuration": dataset_config,
            "files": {},
        }

        # Scan different data levels
        data_dirs = [
            f"data/L1_tidy/{dataset_name}",
            f"data/L2_derived/{dataset_name}",
            f"data/processed/v4.4/integration",
        ]

        for data_dir in data_dirs:
            dir_path = self.repo_path / data_dir
            if dir_path.exists():
                files_data = self.scan_directory(dir_path)
                if files_data:
                    provenance_data["files"][data_dir] = files_data

        return provenance_data

    def save_provenance_report(self, dataset_name: str, data: Dict[str, Any]) -> Path:
        """Save provenance report to YAML file."""
        output_path = self.reports_dir / f"{dataset_name}_provenance.yaml"

        with open(output_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=True)

        logger.info(f"Saved provenance report: {output_path}")
        return output_path

    def generate_inventory_report(self) -> Dict[str, Any]:
        """Generate complete repository inventory with checksums."""
        logger.info("Generating complete repository inventory")

        inventory = {
            "repository": str(self.repo_path),
            "timestamp": datetime.now().isoformat(),
            "data_files": {},
            "code_files": {},
            "documentation": {},
            "configuration": {},
        }

        # Scan different file types
        scan_configs = [
            ("data_files", "data", ["*.parquet", "*.csv", "*.tsv", "*.h5", "*.mat"]),
            ("code_files", "src", ["*.py"]),
            ("code_files", "scripts", ["*.py", "*.sh", "*.R"]),
            ("documentation", "docs", ["*.md", "*.rst"]),
            ("configuration", "config", ["*.yaml", "*.yml", "*.json"]),
        ]

        for category, base_dir, patterns in scan_configs:
            dir_path = self.repo_path / base_dir
            if dir_path.exists():
                for pattern in patterns:
                    files_data = self.scan_directory(dir_path, pattern)
                    if files_data:
                        if category not in inventory:
                            inventory[category] = {}
                        inventory[category].update(files_data)

        return inventory


def main():
    """Main execution following research data management best practices."""
    parser = argparse.ArgumentParser(
        description="Compute checksums and track provenance for PCS-Meta-Repo v4.4"
    )
    parser.add_argument(
        "--repo", type=Path, default=Path.cwd(), help="Repository root path"
    )
    parser.add_argument("--dataset", help="Generate provenance for specific dataset")
    parser.add_argument(
        "--inventory", choices=["repo", "data"], help="Generate inventory report"
    )
    parser.add_argument(
        "--output-dir", type=Path, help="Output directory (default: reports/provenance)"
    )

    args = parser.parse_args()

    # Initialize tracker
    tracker = ProvenanceTracker(args.repo)

    if args.output_dir:
        tracker.reports_dir = args.output_dir
        tracker.reports_dir.mkdir(parents=True, exist_ok=True)

    try:
        if args.dataset:
            # Generate dataset-specific provenance
            provenance_data = tracker.generate_dataset_provenance(args.dataset)
            output_path = tracker.save_provenance_report(args.dataset, provenance_data)
            print(f"Dataset provenance generated: {output_path}")

        elif args.inventory:
            # Generate inventory report
            if args.inventory == "repo":
                inventory_data = tracker.generate_inventory_report()
                output_path = tracker.reports_dir.parent / "inventory.json"
            else:
                # Data-only inventory
                inventory_data = tracker.scan_directory(args.repo / "data")
                output_path = tracker.reports_dir.parent / "data_inventory.json"

            with open(output_path, "w") as f:
                json.dump(inventory_data, f, indent=2)

            print(f"Inventory report generated: {output_path}")

        else:
            # Default: generate provenance for common datasets
            datasets = ["swow", "zuco_rt", "zuco_eeg"]

            for dataset in datasets:
                try:
                    provenance_data = tracker.generate_dataset_provenance(dataset)
                    tracker.save_provenance_report(dataset, provenance_data)
                except Exception as e:
                    logger.error(f"Failed to generate provenance for {dataset}: {e}")

            # Also generate inventory
            inventory_data = tracker.generate_inventory_report()
            inventory_path = tracker.reports_dir.parent / "inventory.json"
            with open(inventory_path, "w") as f:
                json.dump(inventory_data, f, indent=2)

            print(f"Provenance reports generated in: {tracker.reports_dir}")
            print(f"Inventory report: {inventory_path}")

    except Exception as e:
        logger.error(f"Provenance tracking failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
