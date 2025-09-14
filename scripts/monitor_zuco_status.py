#!/usr/bin/env python3
"""
ZuCo Processing Status Monitor
Generates comprehensive reports on processing status and performance metrics
"""

import os
import sys
import logging
from pathlib import Path
import pandas as pd
import yaml
from datetime import datetime
import json
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

class ZuCoStatusMonitor:
    """Monitor and report on ZuCo processing status"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.reports_dir = Path("reports/zuco_monitoring")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'datasets.yaml'

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def generate_status_report(self) -> Dict:
        """Generate comprehensive status report"""
        self.logger.info("Generating ZuCo processing status report")

        report = {
            "timestamp": datetime.now().isoformat(),
            "datasets": {},
            "summary": {},
            "recommendations": []
        }

        # Analyze each dataset
        zuco_datasets = ["zuco_v1", "zuco_v2"]

        for dataset_name in zuco_datasets:
            if dataset_name in self.config:
                dataset_config = self.config[dataset_name]
                dataset_status = self._analyze_dataset_status(dataset_name, dataset_config)
                report["datasets"][dataset_name] = dataset_status

        # Generate summary
        report["summary"] = self._generate_summary(report["datasets"])

        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report["datasets"])

        # Save report
        self._save_report(report)

        # Generate visualizations
        self._generate_visualizations(report)

        return report

    def _analyze_dataset_status(self, dataset_name: str, config: Dict) -> Dict:
        """Analyze status of specific dataset"""
        status = {
            "name": dataset_name,
            "processing_status": config.get("processing_status", "unknown"),
            "raw_files_count": 0,
            "processed_files_count": 0,
            "data_quality": {},
            "performance_metrics": {},
            "issues": []
        }

        # Check raw data directory
        raw_dir = Path(config.get("raw_dir", "").replace("@data_root.", "data/"))
        if raw_dir.exists():
            mat_files = list(raw_dir.glob("**/*.mat"))
            status["raw_files_count"] = len(mat_files)

        # Check processed data directory
        processed_dir = Path(config.get("processed_dir", "").replace("@data_root.", "data/"))
        if processed_dir.exists():
            processed_files = list(processed_dir.glob("**/*.csv")) + list(processed_dir.glob("**/*.parquet"))
            status["processed_files_count"] = len(processed_files)

            # Analyze processed data quality
            if processed_files:
                status["data_quality"] = self._analyze_data_quality(processed_files[0])

        # Check for processing logs
        log_files = list(Path("reports/kec").glob(f"*{dataset_name}*.log"))
        if log_files:
            status["performance_metrics"] = self._extract_performance_metrics(log_files[-1])

        # Identify issues
        status["issues"] = self._identify_issues(status)

        return status

    def _analyze_data_quality(self, file_path: Path) -> Dict:
        """Analyze quality of processed data"""
        quality = {
            "total_rows": 0,
            "null_percentage_overall": 0,
            "null_percentage_critical": 0,
            "duplicate_rows": 0,
            "expected_columns_present": False
        }

        try:
            if file_path.suffix == '.csv':
                df = pd.read_csv(file_path, nrows=1000)  # Sample for quality check
            elif file_path.suffix == '.parquet':
                df = pd.read_parquet(file_path)

            quality["total_rows"] = len(df)

            # Check for nulls - overall
            null_counts = df.isnull().sum()
            quality["null_percentage_overall"] = (null_counts.sum() / (len(df) * len(df.columns))) * 100

            # Check for nulls - critical columns only
            critical_cols = ['FFD', 'GD', 'TRT', 'subject_id', 'word']
            critical_cols_present = [col for col in critical_cols if col in df.columns]
            if critical_cols_present:
                critical_nulls = df[critical_cols_present].isnull().sum().sum()
                quality["null_percentage_critical"] = (critical_nulls / (len(df) * len(critical_cols_present))) * 100

            # Check for duplicates
            quality["duplicate_rows"] = df.duplicated().sum()

            # Check expected columns
            expected_cols = ["FFD", "GD", "TRT", "subject_id"]
            quality["expected_columns_present"] = all(col in df.columns for col in expected_cols)

        except Exception as e:
            self.logger.error(f"Error analyzing data quality for {file_path}: {str(e)}")

        return quality

    def _extract_performance_metrics(self, log_file: Path) -> Dict:
        """Extract performance metrics from log files"""
        metrics = {
            "processing_time": 0,
            "memory_usage": 0,
            "error_count": 0
        }

        try:
            with open(log_file, 'r') as f:
                content = f.read()

            # Extract basic metrics (this would need to be adapted based on actual log format)
            # For now, return placeholder metrics
            metrics["processing_time"] = 0  # Would parse from logs
            metrics["memory_usage"] = 0     # Would parse from logs
            metrics["error_count"] = content.count("ERROR")

        except Exception as e:
            self.logger.error(f"Error extracting metrics from {log_file}: {str(e)}")

        return metrics

    def _identify_issues(self, status: Dict) -> List[str]:
        """Identify potential issues with dataset processing"""
        issues = []

        if status["processing_status"] == "not_started":
            issues.append("Processing not yet started")

        if status["raw_files_count"] == 0:
            issues.append("No raw data files found")

        if status["processed_files_count"] == 0 and status["processing_status"] != "not_started":
            issues.append("No processed files found despite processing status")

        quality = status.get("data_quality", {})
        if quality.get("null_percentage_critical", 0) > 1:  # Only flag if critical nulls > 1%
            issues.append(".1f")

        if not quality.get("expected_columns_present", False):
            issues.append("Expected columns missing from processed data")

        return issues

    def _generate_summary(self, datasets: Dict) -> Dict:
        """Generate overall summary"""
        summary = {
            "total_datasets": len(datasets),
            "completed_datasets": 0,
            "partial_datasets": 0,
            "not_started_datasets": 0,
            "total_raw_files": 0,
            "total_processed_files": 0,
            "overall_completion_rate": 0
        }

        for dataset_name, status in datasets.items():
            summary["total_raw_files"] += status["raw_files_count"]
            summary["total_processed_files"] += status["processed_files_count"]

            if status["processing_status"] == "completed":
                summary["completed_datasets"] += 1
            elif status["processing_status"] == "partial":
                summary["partial_datasets"] += 1
            else:
                summary["not_started_datasets"] += 1

        # Calculate completion rate
        if summary["total_raw_files"] > 0:
            summary["overall_completion_rate"] = (summary["total_processed_files"] / summary["total_raw_files"]) * 100

        return summary

    def _generate_recommendations(self, datasets: Dict) -> List[str]:
        """Generate recommendations based on current status"""
        recommendations = []

        for dataset_name, status in datasets.items():
            if status["processing_status"] == "not_started":
                recommendations.append(f"Start processing {dataset_name} dataset")

            if status["processing_status"] == "partial":
                recommendations.append(f"Complete processing of {dataset_name} dataset")

            issues = status.get("issues", [])
            for issue in issues:
                recommendations.append(f"Fix {dataset_name}: {issue}")

        # General recommendations
        if any(status["processing_status"] == "partial" for status in datasets.values()):
            recommendations.append("Optimize EEG processing pipeline for partial datasets")

        if all(status["processing_status"] == "completed" for status in datasets.values()):
            recommendations.append("All datasets processed - consider performance optimizations")

        return recommendations

    def _save_report(self, report: Dict):
        """Save report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"zuco_status_report_{timestamp}.json"

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"Status report saved to {report_file}")

    def _generate_visualizations(self, report: Dict):
        """Generate visualization charts"""
        try:
            # Set style
            sns.set_style("whitegrid")

            # Create figure with subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))

            # Processing status pie chart
            summary = report["summary"]
            statuses = [
                summary["completed_datasets"],
                summary["partial_datasets"],
                summary["not_started_datasets"]
            ]
            status_labels = ["Completed", "Partial", "Not Started"]
            colors = ['#2ecc71', '#f39c12', '#e74c3c']

            ax1.pie(statuses, labels=status_labels, colors=colors, autopct='%1.1f%%')
            ax1.set_title("Dataset Processing Status")

            # File counts bar chart
            datasets = list(report["datasets"].keys())
            raw_counts = [report["datasets"][d]["raw_files_count"] for d in datasets]
            processed_counts = [report["datasets"][d]["processed_files_count"] for d in datasets]

            x = range(len(datasets))
            ax2.bar(x, raw_counts, width=0.35, label='Raw Files', alpha=0.8)
            ax2.bar([i + 0.35 for i in x], processed_counts, width=0.35, label='Processed Files', alpha=0.8)
            ax2.set_xlabel("Dataset")
            ax2.set_ylabel("File Count")
            ax2.set_title("Raw vs Processed Files")
            ax2.set_xticks([i + 0.175 for i in x])
            ax2.set_xticklabels(datasets)
            ax2.legend()

            # Data quality metrics
            quality_data = []
            for dataset_name, status in report["datasets"].items():
                quality = status.get("data_quality", {})
                if quality:
                    quality_data.append({
                        "dataset": dataset_name,
                        "null_percentage": quality.get("null_percentage", 0),
                        "total_rows": quality.get("total_rows", 0)
                    })

            if quality_data:
                df_quality = pd.DataFrame(quality_data)
                ax3.bar(df_quality["dataset"], df_quality["null_percentage"])
                ax3.set_xlabel("Dataset")
                ax3.set_ylabel("Null Percentage (%)")
                ax3.set_title("Data Quality - Null Values")
            else:
                ax3.text(0.5, 0.5, "No quality data available", ha='center', va='center', transform=ax3.transAxes)
                ax3.set_title("Data Quality")

            # Completion timeline (placeholder)
            ax4.text(0.5, 0.5, "Completion Timeline\n(Feature in development)", ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title("Processing Timeline")

            plt.tight_layout()

            # Save plot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_file = self.reports_dir / f"zuco_status_visualization_{timestamp}.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"Visualization saved to {plot_file}")

        except Exception as e:
            self.logger.error(f"Error generating visualizations: {str(e)}")

def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="ZuCo Processing Status Monitor")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--output-dir", help="Output directory for reports")

    args = parser.parse_args()

    # Initialize monitor
    monitor = ZuCoStatusMonitor(args.config)

    if args.output_dir:
        monitor.reports_dir = Path(args.output_dir)

    # Generate report
    report = monitor.generate_status_report()

    # Print summary
    print("\n=== ZuCo Processing Status Report ===")
    print(f"Generated at: {report['timestamp']}")
    print(f"Total datasets: {report['summary']['total_datasets']}")
    print(f"Completed: {report['summary']['completed_datasets']}")
    print(f"Partial: {report['summary']['partial_datasets']}")
    print(f"Not started: {report['summary']['not_started_datasets']}")
    print(".1f")
    print(f"Total raw files: {report['summary']['total_raw_files']}")
    print(f"Total processed files: {report['summary']['total_processed_files']}")

    print("\n=== Recommendations ===")
    for rec in report["recommendations"]:
        print(f"• {rec}")

if __name__ == "__main__":
    main()
