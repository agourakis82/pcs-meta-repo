#!/usr/bin/env python3
"""
SWOW-Z                "pipeline": {
                    "name": "Neuro-SWOW Integration Pipeline",
                    "version": "2.1",
                    "description": "Integrates SWOW network metrics with multiple neurophysiological datasets (DERCo, GECO, OneStop, LPP)"
                },ntegration Pipeline Runner
Automated pipeline for integrating SWOW network metrics with ZuCo neurophysiological data
"""

import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import yaml
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

class SWOWZuCoPipeline:
    """Automated pipeline for neurophysiological-SWOW integration"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.results = {}

    def _load_config(self, config_path: str) -> dict:
        """Load pipeline configuration"""
        if config_path is None:
            config_path = Path(__file__).parent / 'config' / 'swow_zuco_pipeline.yaml'

        if not config_path.exists():
            # Create default configuration
            default_config = {
                "pipeline": {
                    "name": "SWOW-ZuCo Integration Pipeline",
                    "version": "2.0",
                    "description": "Integrates SWOW network metrics with ZuCo EEG+RT data"
                },
                "input_files": {
                    "processed_datasets": [
                        "/home/agourakis82/FASTDATA/processed/derco_eeg/word_events.parquet",
                        "/home/agourakis82/FASTDATA/processed/geco_et/word_events.parquet", 
                        "/home/agourakis82/FASTDATA/processed/onestop_et/word_events.parquet",
                        "/home/agourakis82/FASTDATA/processed/lpp_eeg/word_events.parquet"
                    ],
                    "swow_base_path": "data/L2_derived/kec/en"
                },
                "output_files": {
                    "integrated": "data/processed/integrated_neuro_swow.csv",
                    "validation_report": "reports/integration_validation.yaml"
                },
                "processing": {
                    "chunk_size": 1000,
                    "validate_integrity": True,
                    "generate_reports": True
                }
            }

            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/swow_zuco_pipeline.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def validate_inputs(self) -> bool:
        """Validate input files exist and are accessible"""
        self.logger.info("Validating input files...")

        # Check processed datasets
        processed_files = self.config['input_files']['processed_datasets']
        missing_datasets = []

        for file_path in processed_files:
            if not Path(file_path).exists():
                missing_datasets.append(file_path)

        if missing_datasets:
            self.logger.error("Missing processed dataset files:")
            for file in missing_datasets:
                self.logger.error(f"  - {file}")
            return False

        # Check SWOW data
        swow_base = Path(self.config['input_files']['swow_base_path'])
        required_swow = ['entropy.parquet', 'curvature.parquet', 'coherence.parquet']
        missing_swow = []

        for swow_file in required_swow:
            if not (swow_base / swow_file).exists():
                missing_swow.append(str(swow_base / swow_file))

        if missing_swow:
            self.logger.error("Missing SWOW data files:")
            for file in missing_swow:
                self.logger.error(f"  - {file}")
            return False

        self.logger.info("All input files validated successfully")
        return True

    def prepare_neuro_data(self) -> pd.DataFrame:
        """Prepare and align neurophysiological data from multiple sources"""
        self.logger.info("Preparing neurophysiological data...")

        processed_files = self.config['input_files']['processed_datasets']
        all_data = []

        for file_path in processed_files:
            if Path(file_path).exists():
                self.logger.info(f"Loading {file_path}")
                df = pd.read_parquet(file_path)

                # Extract dataset name from path
                dataset_name = Path(file_path).parent.name
                df['dataset'] = dataset_name

                # Normalize word column for merging
                import re
                def normalize_word(w):
                    if pd.isna(w):
                        return ''
                    w = str(w).lower()
                    # Remove punctuation and extra whitespace
                    w = re.sub(r'[^\w\s]', '', w)
                    w = re.sub(r'\s+', ' ', w).strip()
                    return w

                df['word_norm'] = df['word'].apply(normalize_word)

                # Keep only rows with valid words
                df = df[df['word_norm'] != ''].copy()

                all_data.append(df)
                self.logger.info(f"Processed {len(df)} rows from {dataset_name}")

        if not all_data:
            raise ValueError("No neurophysiological data files found")

        combined_data = pd.concat(all_data, ignore_index=True)
        self.logger.info(f"Combined neuro data: {len(combined_data)} rows from {len(all_data)} datasets")

        return combined_data

    def load_swow_data(self) -> pd.DataFrame:
        """Load SWOW KEC metrics from Parquet files"""
        self.logger.info("Loading SWOW data...")

        swow_base = Path(self.config['input_files']['swow_base_path'])

        # Load all SWOW metrics
        swow_data = {}

        # Load entropy
        entropy_df = pd.read_parquet(swow_base / 'entropy.parquet')
        entropy_df = entropy_df.rename(columns={'node': 'word_norm', 'H': 'entropy'})
        swow_data['entropy'] = entropy_df

        # Load curvature
        curvature_df = pd.read_parquet(swow_base / 'curvature.parquet')
        curvature_df = curvature_df.rename(columns={'node': 'word_norm', 'kappa': 'curvature'})
        # Take mean if multiple methods
        if 'method' in curvature_df.columns:
            curvature_df = curvature_df.groupby('word_norm')['curvature'].mean().reset_index()
        swow_data['curvature'] = curvature_df

        # Load coherence
        coherence_df = pd.read_parquet(swow_base / 'coherence.parquet')
        coherence_df = coherence_df.rename(columns={'node': 'word_norm', 'Q': 'coherence'})
        swow_data['coherence'] = coherence_df

        # Merge all SWOW metrics
        base_df = swow_data['entropy']
        for metric_name, df in swow_data.items():
            if metric_name != 'entropy':
                base_df = base_df.merge(df[['word_norm', metric_name]], on='word_norm', how='left')

        self.logger.info(f"Loaded SWOW data: {len(base_df)} nodes with {len(base_df.columns)-1} metrics")
        return base_df

    def integrate_datasets(self, neuro_df: pd.DataFrame, swow_df: pd.DataFrame) -> pd.DataFrame:
        """Integrate neurophysiological and SWOW datasets"""
        self.logger.info("Integrating datasets...")

        # Merge on normalized words
        merged = neuro_df.merge(swow_df, on='word_norm', how='left')

        # Add log transformations for timing data if available
        if 'fixation_duration' in merged.columns:
            merged['log_fixation_duration'] = merged['fixation_duration'].apply(
                lambda x: float(np.log1p(x)) if pd.notna(x) and x > 0 else pd.NA
            )

        self.logger.info(f"Integration complete: {len(merged)} rows")
        return merged

    def validate_integration(self, integrated_df: pd.DataFrame) -> dict:
        """Validate integration quality"""
        self.logger.info("Validating integration...")

        validation = {
            "total_rows": len(integrated_df),
            "columns": list(integrated_df.columns),
            "swow_coverage": {},
            "neuro_coverage": {},
            "integration_quality": {},
            "dataset_breakdown": {}
        }

        # SWOW metrics coverage
        swow_cols = ['entropy', 'curvature', 'coherence']
        for col in swow_cols:
            if col in integrated_df.columns:
                coverage = integrated_df[col].notna().sum() / len(integrated_df) * 100
                validation["swow_coverage"][col] = coverage

        # Neurophysiological metrics coverage
        neuro_cols = ['fixation_duration', 'timestamp']
        for col in neuro_cols:
            if col in integrated_df.columns:
                coverage = integrated_df[col].notna().sum() / len(integrated_df) * 100
                validation["neuro_coverage"][col] = coverage

        # Dataset breakdown
        if 'dataset' in integrated_df.columns:
            dataset_counts = integrated_df['dataset'].value_counts().to_dict()
            validation["dataset_breakdown"] = dataset_counts

        # Overall integration quality
        swow_present = integrated_df['entropy'].notna()
        neuro_present = integrated_df['word'].notna()
        both_present = (swow_present & neuro_present).sum()
        validation["integration_quality"]["both_metrics"] = both_present / len(integrated_df) * 100

        return validation

    def save_results(self, integrated_df: pd.DataFrame, validation: dict):
        """Save integrated data and validation results"""
        self.logger.info("Saving results...")

        # Save integrated data
        output_path = self.config['output_files']['integrated']
        integrated_df.to_csv(output_path, index=False)
        self.logger.info(f"Saved integrated data: {output_path}")

        # Save validation report
        validation_path = Path(output_path).parent / "integration_validation.yaml"
        with open(validation_path, 'w') as f:
            yaml.dump(validation, f, default_flow_style=False)
        self.logger.info(f"Saved validation report: {validation_path}")

    def run_pipeline(self) -> dict:
        """Run complete neuro-SWOW integration pipeline"""
        self.logger.info("Starting Neuro-SWOW Integration Pipeline")
        self.logger.info(f"Pipeline version: {self.config['pipeline']['version']}")

        try:
            # Step 1: Validate inputs
            if not self.validate_inputs():
                raise RuntimeError("Input validation failed")

            # Step 2: Prepare neurophysiological data
            neuro_data = self.prepare_neuro_data()

            # Step 3: Load SWOW data
            swow_data = self.load_swow_data()

            # Step 4: Integrate datasets
            integrated_data = self.integrate_datasets(neuro_data, swow_data)

            # Step 5: Validate integration
            validation = self.validate_integration(integrated_data)

            # Step 6: Save results
            self.save_results(integrated_data, validation)

            # Prepare final results
            results = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "integrated_rows": len(integrated_data),
                "validation": validation,
                "config": self.config
            }

            self.logger.info("Pipeline completed successfully!")
            return results

        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

def _ensure_dirs():
    for d in [
        'data/L1_tidy/zuco_rt','data/L1_tidy/geco_rt','data/L1_tidy/onestop_rt',
        'data/L1_tidy/zuco_eeg','data/L1_tidy/derco_eeg','data/L1_tidy/lpp_eeg',
        'data/processed/v4.4/integration','data/processed/v4.4/models']:
        Path(d).mkdir(parents=True, exist_ok=True)

def run_step(step: str, datasets: str | None = None):
    _ensure_dirs()
    if step == 'tidy_rt':
        # Placeholders — do not redistribute data; only create folders
        for ds in ['zuco_rt','geco_rt','onestop_rt']:
            Path(f'data/L1_tidy/{ds}/word_events_rt.parquet').touch()
        print('[pipeline] tidy_rt prepared (placeholders)')
    elif step == 'tidy_eeg':
        for ds in ['zuco_eeg','derco_eeg','lpp_eeg']:
            Path(f'data/L1_tidy/{ds}/word_events_eeg.parquet').touch()
        print('[pipeline] tidy_eeg prepared (placeholders)')
    elif step == 'integrate':
        for out in ['zuco_kec_rt.parquet','zuco_kec_eeg.parquet','zuco_kec_merged.parquet']:
            Path(f'data/processed/v4.4/integration/{out}').touch()
        print('[pipeline] integrate prepared (placeholders)')
    elif step == 'models_rt':
        Path('data/processed/v4.4/models/models_reading_coeffs.csv').touch()
        print('[pipeline] models_rt prepared (placeholders)')
    elif step == 'models_eeg':
        Path('data/processed/v4.4/models/models_eeg_coeffs.csv').touch()
        print('[pipeline] models_eeg prepared (placeholders)')
    elif step == 'models':
        run_step('models_rt')
        run_step('models_eeg')
    else:
        print(f"[pipeline] unknown step: {step}")

def main():
    import argparse
    ap = argparse.ArgumentParser(description='SWOW↔ZuCo pipeline')
    ap.add_argument('--step', default=None, help='tidy_rt|tidy_eeg|integrate|models_rt|models_eeg|models')
    ap.add_argument('--datasets', default=None)
    args = ap.parse_args()
    if args.step:
        run_step(args.step, args.datasets)
        return
    # Fallback to legacy end-to-end run
    print("🚀 Neuro-SWOW Integration Pipeline")
    print("=" * 40)
    pipeline = SWOWZuCoPipeline()
    results = pipeline.run_pipeline()

    if results["status"] == "success":
        print("\n✅ Pipeline completed successfully!")
        print(f"📊 Integrated {results['integrated_rows']:,} observations")
        print(f"🔬 SWOW coverage: {results['validation']['swow_coverage']}")
        print(f"🧠 Neuro coverage: {results['validation']['neuro_coverage']}")
        if 'dataset_breakdown' in results['validation']:
            print(f"📈 Dataset breakdown: {results['validation']['dataset_breakdown']}")
    else:
        print(f"\n❌ Pipeline failed: {results['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
