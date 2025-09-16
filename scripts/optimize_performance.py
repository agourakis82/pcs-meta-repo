#!/usr/bin/env python3
"""
ZuCo Performance Optimization Script
Implements performance improvements and memory optimizations
"""

import os
import sys
import logging
import psutil
import gc
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import yaml
import time

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

class ZuCoPerformanceOptimizer:
    """Performance optimizer for ZuCo data processing"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.optimization_results = {}

    def _load_config(self, config_path: str) -> Dict:
        """Load performance configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'zuco_performance.yaml'

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)['zuco_processing']

    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def optimize_memory_usage(self) -> Dict:
        """Implement memory optimization strategies"""
        self.logger.info("Starting memory optimization...")

        results = {
            "before_optimization": self._get_memory_stats(),
            "optimizations_applied": [],
            "after_optimization": {},
            "performance_gains": {}
        }

        # Clear any existing large objects
        gc.collect()

        # Optimize pandas settings
        pd.set_option('mode.chained_assignment', None)  # Disable chained assignment warnings
        pd.set_option('compute.use_bottleneck', True)   # Use bottleneck for aggregations
        pd.set_option('compute.use_numexpr', True)      # Use numexpr for numerical operations

        results["optimizations_applied"].append("pandas_settings_optimized")

        # Optimize data types
        self._optimize_data_types()

        results["optimizations_applied"].append("data_types_optimized")

        # Implement chunked processing
        self._implement_chunked_processing()

        results["optimizations_applied"].append("chunked_processing_implemented")

        # Memory stats after optimization
        results["after_optimization"] = self._get_memory_stats()

        # Calculate performance gains
        before_mem = results["before_optimization"]["memory_mb"]
        after_mem = results["after_optimization"]["memory_mb"]
        memory_savings = before_mem - after_mem
        memory_savings_pct = (memory_savings / before_mem) * 100 if before_mem > 0 else 0

        results["performance_gains"] = {
            "memory_savings_mb": memory_savings,
            "memory_savings_percentage": memory_savings_pct
        }

        self.logger.info(".1f")
        return results

    def _get_memory_stats(self) -> Dict:
        """Get current memory statistics"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        return {
            "memory_mb": memory_info.rss / 1024 / 1024,
            "memory_percent": process.memory_percent(),
            "cpu_percent": process.cpu_percent(interval=0.1)
        }

    def _optimize_data_types(self):
        """Optimize data types for memory efficiency"""
        self.logger.info("Optimizing data types...")

        # Optimize ZuCo v1
        v1_path = Path('data/processed/zuco_v1/word_events.parquet')
        if v1_path.exists():
            df = pd.read_parquet(v1_path)

            # Convert to more efficient data types
            dtype_optimizations = {
                'sent_id': 'int32',
                'word_id': 'int32',
                'length': 'int16',
                'position': 'int16',
                'FFD': 'float32',
                'GD': 'float32',
                'TRT': 'float32'
            }

            for col, dtype in dtype_optimizations.items():
                if col in df.columns:
                    df[col] = df[col].astype(dtype)

            # Save optimized version
            df.to_parquet(v1_path, index=False)
            self.logger.info(f"ZuCo v1 optimized: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")

        # Optimize ZuCo v2
        v2_path = Path('data/processed/zuco_v2/word_events.parquet')
        if v2_path.exists():
            df = pd.read_parquet(v2_path)

            # Similar optimizations for v2
            for col, dtype in dtype_optimizations.items():
                if col in df.columns:
                    df[col] = df[col].astype(dtype)

            # Additional EEG optimizations
            eeg_cols = ['theta_power', 'alpha_power', 'beta_power', 'gamma_power', 'eeg_metric']
            for col in eeg_cols:
                if col in df.columns:
                    df[col] = df[col].astype('float32')

            df.to_parquet(v2_path, index=False)
            self.logger.info(f"ZuCo v2 optimized: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")

    def _implement_chunked_processing(self):
        """Implement chunked processing for large datasets"""
        self.logger.info("Implementing chunked processing strategies...")

        # Create chunked processing configuration
        chunk_config = {
            "chunk_size": self.config['memory']['chunk_size'],
            "max_workers": self.config['memory']['max_workers'],
            "memory_limit": self.config['gpu']['memory_limit']  # Use GPU memory limit as reference
        }

        # Save chunk configuration
        config_path = Path('config/chunk_processing.yaml')
        with open(config_path, 'w') as f:
            yaml.dump({"chunk_processing": chunk_config}, f)

        self.logger.info(f"Chunked processing configured: {chunk_config}")

    def optimize_io_operations(self) -> Dict:
        """Optimize I/O operations"""
        self.logger.info("Optimizing I/O operations...")

        results = {
            "compression_optimized": False,
            "caching_implemented": False,
            "parallel_io_enabled": False
        }

        # Optimize parquet compression
        compression_settings = {
            "compression": self.config['pipeline']['compression'],
            "use_dictionary": True,
            "row_group_size": 100000
        }

        # Apply to existing files
        for version in ['v1', 'v2']:
            path = Path(f'data/processed/zuco_{version}/word_events.parquet')
            if path.exists():
                df = pd.read_parquet(path)
                df.to_parquet(path, **compression_settings)
                self.logger.info(f"Recompressed ZuCo {version} with {compression_settings['compression']}")

        results["compression_optimized"] = True

        # Implement caching strategy
        cache_config = {
            "cache_dir": "data/cache",
            "max_cache_size_gb": 5,
            "cache_ttl_hours": 24
        }

        cache_dir = Path(cache_config["cache_dir"])
        cache_dir.mkdir(exist_ok=True)

        cache_config_path = Path('config/cache_config.yaml')
        with open(cache_config_path, 'w') as f:
            yaml.dump({"caching": cache_config}, f)

        results["caching_implemented"] = True

        return results

    def create_performance_report(self) -> Dict:
        """Create comprehensive performance report"""
        self.logger.info("Creating performance report...")

        report = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "system_info": self._get_system_info(),
            "data_stats": self._get_data_stats(),
            "performance_metrics": {},
            "recommendations": []
        }

        # Memory optimization
        memory_results = self.optimize_memory_usage()
        report["performance_metrics"]["memory_optimization"] = memory_results

        # I/O optimization
        io_results = self.optimize_io_operations()
        report["performance_metrics"]["io_optimization"] = io_results

        # Generate recommendations
        report["recommendations"] = self._generate_performance_recommendations(report)

        # Save report
        report_path = Path('reports/performance_optimization_report.json')
        with open(report_path, 'w') as f:
            # Convert numpy types to native Python types for JSON serialization
            json_report = self._make_json_serializable(report)
            import json
            json.dump(json_report, f, indent=2)

        self.logger.info(f"Performance report saved to {report_path}")

        return report

    def _get_system_info(self) -> Dict:
        """Get system information"""
        return {
            "cpu_count": os.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
            "memory_available_gb": psutil.virtual_memory().available / 1024 / 1024 / 1024,
            "python_version": sys.version.split()[0]
        }

    def _get_data_stats(self) -> Dict:
        """Get data statistics"""
        stats = {}

        for version in ['v1', 'v2']:
            path = Path(f'data/processed/zuco_{version}/word_events.parquet')
            if path.exists():
                df = pd.read_parquet(path)
                stats[f'zuco_{version}'] = {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "memory_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
                    "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
                }

        return stats

    def _generate_performance_recommendations(self, report: Dict) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        # Memory recommendations
        memory_gains = report["performance_metrics"]["memory_optimization"]["performance_gains"]
        if memory_gains["memory_savings_percentage"] > 10:
            recommendations.append(".1f")

        # System recommendations
        system_info = report["system_info"]
        if system_info["cpu_count"] >= 8:
            recommendations.append("Consider enabling parallel processing for multi-core CPU")

        if system_info["memory_total_gb"] >= 16:
            recommendations.append("System has sufficient memory for larger batch processing")

        # Data recommendations
        data_stats = report["data_stats"]
        for dataset, stats in data_stats.items():
            if stats["rows"] > 10000:
                recommendations.append(f"Consider partitioning {dataset} for better query performance")

        return recommendations

    def _make_json_serializable(self, obj):
        """Convert numpy types to JSON serializable types"""
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

def main():
    """Main execution function"""
    print("🚀 ZuCo Performance Optimization")
    print("=" * 40)

    optimizer = ZuCoPerformanceOptimizer()

    # Create performance report
    report = optimizer.create_performance_report()

    # Print summary
    print("\n📊 OPTIMIZATION SUMMARY")
    print("-" * 30)

    memory_gains = report["performance_metrics"]["memory_optimization"]["performance_gains"]
    print(".1f")
    print(".1f")

    print(f"\n📋 RECOMMENDAÇÕES ({len(report['recommendations'])})")
    print("-" * 20)
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"{i}. {rec}")

    print("\n✅ Optimization complete! Check reports/performance_optimization_report.json for details.")
    print(f"📈 Memory optimization: {memory_gains['memory_savings_percentage']:.1f}% savings")

if __name__ == "__main__":
    main()
