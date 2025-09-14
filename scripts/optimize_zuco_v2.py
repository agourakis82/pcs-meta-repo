#!/usr/bin/env python3
"""
ZuCo v2 EEG Processing Optimization Script
Enhanced EEG processing with improved memory management and parallel processing
"""

import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import psutil
import yaml
from typing import Dict, List, Optional, Tuple
import gc
import time

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from pipeline.zuco_real_loader import ZuCoRealLoader

class ZuCoV2Optimizer:
    """Optimized processor for ZuCo v2 EEG data"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.loader = ZuCoRealLoader()
        self._setup_logging()
        self._setup_performance_monitoring()

    def _load_config(self, config_path: str) -> Dict:
        """Load performance configuration"""
        if config_path is None:
            config_path = Path(__file__).parent / 'zuco_performance.yaml'

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)['zuco_processing']

    def _setup_logging(self):
        """Configure logging with performance metrics"""
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config['logging']['log_file']),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _setup_performance_monitoring(self):
        """Initialize performance monitoring"""
        self.start_time = time.time()
        self.processed_files = 0
        self.total_memory_usage = []
        self.processing_times = []

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    def _log_progress(self, file_count: int):
        """Log processing progress and performance metrics"""
        if file_count % self.config['logging']['progress_interval'] == 0:
            elapsed = time.time() - self.start_time
            avg_time = np.mean(self.processing_times) if self.processing_times else 0
            avg_memory = np.mean(self.total_memory_usage) if self.total_memory_usage else 0

            self.logger.info(
                f"Processed {file_count} files | "
                f"Elapsed: {elapsed:.2f}s | "
                f"Avg time/file: {avg_time:.3f}s | "
                f"Avg memory: {avg_memory:.1f}MB"
            )

    def _process_single_file_optimized(self, file_path: str) -> Tuple[str, bool, Dict]:
        """
        Optimized processing for single ZuCo v2 file
        Returns: (file_path, success, metrics)
        """
        start_time = time.time()
        metrics = {}

        try:
            # Load data with memory optimization
            data = self.loader.load_mat_file_scipy(file_path)

            if data is None:
                return file_path, False, {"error": "Failed to load file"}

            # Process EEG data with chunking
            eeg_data = self._process_eeg_data_chunked(data)

            # Validate processed data
            validation_result = self._validate_processed_data(eeg_data)

            # Calculate processing metrics
            processing_time = time.time() - start_time
            memory_usage = self._get_memory_usage()

            metrics.update({
                "processing_time": processing_time,
                "memory_usage": memory_usage,
                "data_shape": eeg_data.shape if hasattr(eeg_data, 'shape') else None,
                "validation_passed": validation_result['passed'],
                "validation_errors": validation_result.get('errors', [])
            })

            # Clean up memory
            del data, eeg_data
            gc.collect()

            return file_path, True, metrics

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Error processing {file_path}: {str(e)}")
            return file_path, False, {
                "error": str(e),
                "processing_time": processing_time
            }

    def _process_eeg_data_chunked(self, data: Dict) -> Optional[pd.DataFrame]:
        """Process EEG data in chunks to optimize memory usage"""
        try:
            # Extract EEG data
            if 'eegData' not in data:
                self.logger.warning("No EEG data found in file")
                return None

            eeg_raw = data['eegData']

            # Process in chunks
            chunk_size = self.config['memory']['chunk_size']
            processed_chunks = []

            for i in range(0, len(eeg_raw), chunk_size):
                chunk = eeg_raw[i:i + chunk_size]

                # Apply EEG processing (band filtering, artifact removal, etc.)
                processed_chunk = self._apply_eeg_processing(chunk)

                if processed_chunk is not None:
                    processed_chunks.append(processed_chunk)

                # Memory cleanup
                del chunk
                gc.collect()

            # Combine chunks
            if processed_chunks:
                return pd.concat(processed_chunks, ignore_index=True)
            else:
                return None

        except Exception as e:
            self.logger.error(f"Error in chunked EEG processing: {str(e)}")
            return None

    def _apply_eeg_processing(self, eeg_chunk: np.ndarray) -> Optional[pd.DataFrame]:
        """Apply EEG signal processing to chunk"""
        try:
            # Basic EEG processing pipeline
            # 1. Band-pass filtering (0.5-40 Hz typical for cognitive studies)
            # 2. Artifact removal (basic thresholding)
            # 3. Band power calculation (theta, alpha, beta, gamma)

            # For now, return basic structure - extend with actual EEG processing
            processed_data = {
                'timestamp': np.arange(len(eeg_chunk)),
                'eeg_channels': eeg_chunk.tolist() if len(eeg_chunk.shape) > 1 else [eeg_chunk],
                'band_powers': {
                    'theta': np.mean(eeg_chunk, axis=0) if len(eeg_chunk.shape) > 1 else eeg_chunk.mean(),
                    'alpha': np.mean(eeg_chunk, axis=0) if len(eeg_chunk.shape) > 1 else eeg_chunk.mean(),
                    'beta': np.mean(eeg_chunk, axis=0) if len(eeg_chunk.shape) > 1 else eeg_chunk.mean(),
                    'gamma': np.mean(eeg_chunk, axis=0) if len(eeg_chunk.shape) > 1 else eeg_chunk.mean()
                }
            }

            return pd.DataFrame(processed_data)

        except Exception as e:
            self.logger.error(f"Error in EEG processing: {str(e)}")
            return None

    def _validate_processed_data(self, data: pd.DataFrame) -> Dict:
        """Validate processed EEG data"""
        validation = {"passed": True, "errors": []}

        if data is None:
            validation["passed"] = False
            validation["errors"].append("No data to validate")
            return validation

        # Check for required columns/structure
        required_fields = ['timestamp', 'eeg_channels', 'band_powers']
        for field in required_fields:
            if field not in data.columns:
                validation["passed"] = False
                validation["errors"].append(f"Missing required field: {field}")

        # Check for data quality
        if len(data) == 0:
            validation["passed"] = False
            validation["errors"].append("Empty dataset")

        # Check for null values
        if self.config['validation']['check_nulls']:
            null_counts = data.isnull().sum()
            if null_counts.any():
                validation["passed"] = False
                validation["errors"].append(f"Null values found: {null_counts.to_dict()}")

        return validation

    def process_zuco_v2_optimized(self, data_dir: str, output_dir: str) -> Dict:
        """
        Main optimized processing function for ZuCo v2
        """
        self.logger.info("Starting optimized ZuCo v2 processing")

        # Find all .mat files
        data_path = Path(data_dir)
        mat_files = list(data_path.glob("**/*.mat"))

        if not mat_files:
            self.logger.warning(f"No .mat files found in {data_dir}")
            return {"status": "no_files", "processed": 0, "errors": 0}

        self.logger.info(f"Found {len(mat_files)} .mat files to process")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Process files with parallel execution
        results = []
        successful = 0
        errors = 0

        with ProcessPoolExecutor(max_workers=self.config['memory']['max_workers']) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self._process_single_file_optimized, str(file)): file
                for file in mat_files
            }

            # Process completed tasks
            for future in as_completed(future_to_file):
                file_path, success, metrics = future.result()

                results.append({
                    "file": str(file_path),
                    "success": success,
                    "metrics": metrics
                })

                if success:
                    successful += 1
                else:
                    errors += 1

                self.processed_files += 1
                self.processing_times.append(metrics.get("processing_time", 0))
                self.total_memory_usage.append(metrics.get("memory_usage", 0))

                self._log_progress(self.processed_files)

        # Save processing results
        results_df = pd.DataFrame(results)
        results_file = output_path / "zuco_v2_processing_results.csv"
        results_df.to_csv(results_file, index=False)

        # Generate summary report
        summary = {
            "status": "completed",
            "total_files": len(mat_files),
            "successful": successful,
            "errors": errors,
            "success_rate": successful / len(mat_files) if mat_files else 0,
            "total_time": time.time() - self.start_time,
            "avg_processing_time": np.mean(self.processing_times) if self.processing_times else 0,
            "avg_memory_usage": np.mean(self.total_memory_usage) if self.total_memory_usage else 0,
            "results_file": str(results_file)
        }

        self.logger.info(f"Processing completed: {summary}")

        return summary

def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="ZuCo v2 EEG Processing Optimizer")
    parser.add_argument("--data-dir", required=True, help="Directory containing ZuCo v2 .mat files")
    parser.add_argument("--output-dir", required=True, help="Output directory for processed data")
    parser.add_argument("--config", help="Path to configuration file")

    args = parser.parse_args()

    # Initialize optimizer
    optimizer = ZuCoV2Optimizer(args.config)

    # Run optimized processing
    summary = optimizer.process_zuco_v2_optimized(args.data_dir, args.output_dir)

    # Print final summary
    print("\n=== ZuCo v2 Processing Summary ===")
    print(f"Total files: {summary['total_files']}")
    print(f"Successful: {summary['successful']}")
    print(f"Errors: {summary['errors']}")
    print(".1f")
    print(".2f")
    print(".1f")
    print(f"Results saved to: {summary['results_file']}")

if __name__ == "__main__":
    main()
