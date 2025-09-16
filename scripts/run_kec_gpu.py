#!/usr/bin/env python3
"""
Run KEC GPU-enabled semantic analysis with multi-core support
"""

import argparse
import yaml
from scripts.advanced_semantic_analysis_optimized import OptimizedSemanticAnalysis


def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)["zuco_processing"]


def main():
    parser = argparse.ArgumentParser(
        description="Run KEC GPU-enabled semantic analysis"
    )
    parser.add_argument(
        "--config", default="config/zuco_performance.yaml", help="Path to config file"
    )
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU usage")
    parser.add_argument(
        "--jobs", type=int, default=-1, help="Number of parallel jobs (multi-core)"
    )

    args = parser.parse_args()

    config = load_config(args.config)

    use_gpu = config.get("gpu", {}).get("enabled", True) and not args.no_gpu
    n_jobs = (
        args.jobs if args.jobs != -1 else config.get("memory", {}).get("max_workers", 4)
    )

    analyzer = OptimizedSemanticAnalysis(use_gpu=use_gpu, n_jobs=n_jobs)
    analyzer.run_optimized_analysis()


if __name__ == "__main__":
    main()
