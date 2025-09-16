#!/usr/bin/env python3
"""
Análise Semântica Simplificada - Versão Final
Apenas o essencial para completar a análise
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings("ignore")

# GPU and parallel processing imports
try:
    import cupy as cp

    GPU_AVAILABLE = True
    print("🎯 CuPy disponível - usando aceleração GPU")
except ImportError:
    GPU_AVAILABLE = False
    print("⚠️  CuPy não disponível - usando CPU")

# Machine Learning libraries
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import time


class SimpleSemanticAnalysis:
    """Simplified semantic analysis with GPU acceleration"""

    def __init__(self, use_gpu=True):
        self.use_gpu = use_gpu and GPU_AVAILABLE
        self.timing = {}

    def time_operation(self, operation_name):
        """Context manager for timing operations"""
        return TimingContext(operation_name, self.timing)

    def load_data(self):
        """Load integrated neuro-SWOW data"""
        print("🔍 Carregando dados integrados...")

        with self.time_operation("data_loading"):
            data_path = (
                Path(__file__).parent.parent
                / "data"
                / "processed"
                / "integrated_neuro_swow.csv"
            )

            if not data_path.exists():
                print(f"❌ Arquivo não encontrado: {data_path}")
                sys.exit(1)

            try:
                self.df = pd.read_csv(data_path, low_memory=False)
                print(f"  📊 Dados carregados: {len(self.df):,} observações")

                # Clean data
                self.df = self.df.dropna(
                    subset=["entropy", "curvature", "coherence"], how="all"
                )
                print(f"  📊 Após limpeza: {len(self.df):,} observações válidas")

            except Exception as e:
                print(f"❌ Erro ao carregar dados: {e}")
                sys.exit(1)

    def prepare_features(self):
        """Prepare features for analysis"""
        print("🎯 Preparando features...")

        with self.time_operation("feature_preparation"):
            # Select features
            feature_cols = ["entropy", "curvature", "coherence"]
            self.X = self.df[feature_cols].copy()

            # Sample for clustering
            sample_size = min(50000, len(self.X))  # Smaller sample for speed
            if len(self.X) > sample_size:
                print(f"  📊 Amostrando {sample_size:,} observações")
                self.X_sample = self.X.sample(n=sample_size, random_state=42)
            else:
                self.X_sample = self.X.copy()

            # Scaling
            if self.use_gpu:
                print("  🔬 Usando GPU para escalonamento...")
                X_np = self.X_sample.values.astype(np.float32)
                scaler = StandardScaler()
                self.X_sample_scaled = scaler.fit_transform(X_np)
            else:
                print("  💻 Usando CPU para escalonamento...")
                scaler = StandardScaler()
                self.X_sample_scaled = scaler.fit_transform(self.X_sample)

            print(f"  📊 Amostra shape: {self.X_sample.shape}")
            print("  ✅ Features prontas")

    def perform_pca(self):
        """Perform PCA analysis"""
        print("🔬 Executando análise PCA...")

        with self.time_operation("pca_analysis"):
            self.pca = PCA()
            self.pca.fit(self.X_sample_scaled)

            explained_variance = self.pca.explained_variance_ratio_
            print("  📊 Variância explicada:")
            for i, var in enumerate(explained_variance[:3]):
                print(".3f")

            print("  ✅ PCA concluída")

    def perform_clustering(self):
        """Perform simplified clustering analysis"""
        print("🎯 Executando clustering simplificado...")

        with self.time_operation("clustering"):
            # Simple K-Means only
            print("  🔄 Executando K-Means...")
            start_time = time.time()

            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            labels = kmeans.fit_predict(self.X_sample_scaled)

            # Calculate metrics
            silhouette = silhouette_score(self.X_sample_scaled, labels)

            elapsed = time.time() - start_time
            print(f"    Silhouette Score: {silhouette:.3f}")
            print(f"    Tempo: {elapsed:.2f}s")

            self.clustering_results = {
                "K-Means": {
                    "labels": labels,
                    "silhouette_score": silhouette,
                    "n_clusters": 3,
                }
            }

            print("  ✅ Clustering concluído")

    def generate_report(self):
        """Generate simple report"""
        print("📝 Gerando relatório...")

        with self.time_operation("report"):
            output_dir = Path(__file__).parent.parent / "reports" / "semantic_analysis"
            output_dir.mkdir(parents=True, exist_ok=True)

            report_path = output_dir / "simple_semantic_analysis_report.txt"

            with open(report_path, "w", encoding="utf-8") as f:
                f.write("ANÁLISE SEMÂNTICA SIMPLIFICADA\n")
                f.write("=" * 40 + "\n\n")

                f.write(f"Processamento: {'GPU (CuPy)' if self.use_gpu else 'CPU'}\n")
                f.write(f"Observações totais: {len(self.df):,}\n")
                f.write(f"Amostra analisada: {len(self.X_sample):,}\n\n")

                # Timing
                total_time = sum(self.timing.values())
                f.write("TIMING:\n")
                for operation, time_taken in self.timing.items():
                    f.write(f"  {operation}: {time_taken:.2f}s\n")
                f.write(f"  Total: {total_time:.2f}s\n\n")

                # PCA results
                explained_var = self.pca.explained_variance_ratio_
                f.write("PCA RESULTS:\n")
                for i, var in enumerate(explained_var[:3]):
                    f.write(".3f")
                f.write("\n")

                # Clustering results
                f.write("CLUSTERING RESULTS:\n")
                for name, result in self.clustering_results.items():
                    f.write(f"  {name}:\n")
                    f.write(f"    Clusters: {result['n_clusters']}\n")
                    f.write(f"    Silhouette: {result['silhouette_score']:.3f}\n")

            print(f"  📄 Relatório salvo: {report_path}")

    def run_analysis(self):
        """Run complete simplified analysis"""
        print("🚀 Iniciando Análise Semântica Simplificada")
        print("=" * 50)

        # Execute pipeline
        self.load_data()
        self.prepare_features()
        self.perform_pca()
        self.perform_clustering()
        self.generate_report()

        print("\n🎉 Análise semântica simplificada concluída!")
        print(
            f"📁 Resultados salvos em: {Path(__file__).parent.parent / 'reports' / 'semantic_analysis'}"
        )

        # Print timing summary
        print("\n⏱️  RESUMO DE PERFORMANCE:")
        total_time = sum(self.timing.values())
        print(f"   Tempo total: {total_time:.2f}s")
        for operation, time_taken in self.timing.items():
            percentage = (time_taken / total_time) * 100
            print(".1f")


class TimingContext:
    """Context manager for timing operations"""

    def __init__(self, name, timing_dict):
        self.name = name
        self.timing_dict = timing_dict
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
            self.timing_dict[self.name] = elapsed


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="Simple semantic analysis")
    parser.add_argument("--no-gpu", action="store_true", help="Force CPU usage")

    args = parser.parse_args()

    try:
        analyzer = SimpleSemanticAnalysis(use_gpu=not args.no_gpu)
        analyzer.run_analysis()
    except KeyboardInterrupt:
        print("\n⚠️  Análise interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante a análise: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
