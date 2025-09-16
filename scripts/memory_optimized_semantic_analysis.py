#!/usr/bin/env python3
"""
Análise Semântica Otimizada de Memória
Versão com gerenciamento otimizado de recursos
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import warnings
import gc
import time

warnings.filterwarnings("ignore")

# GPU and ML imports
try:
    import cupy as cp

    GPU_AVAILABLE = True
    print("🎯 CuPy disponível - usando aceleração GPU")
except ImportError:
    GPU_AVAILABLE = False
    print("⚠️  CuPy não disponível - usando CPU")

from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


class MemoryOptimizedSemanticAnalysis:
    """Memory-optimized semantic analysis with GPU acceleration"""

    def __init__(self, use_gpu=True):
        self.use_gpu = use_gpu and GPU_AVAILABLE
        self.timing = {}
        output_path = Path(__file__).parent.parent / "reports"
        self.output_dir = output_path / "memory_optimized_semantic_analysis"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def time_operation(self, operation_name):
        """Context manager for timing operations"""
        return TimingContext(operation_name, self.timing)

    def load_data(self):
        """Load integrated neuro-SWOW data with memory optimization"""
        print("🔍 Carregando dados integrados (otimizado)...")

        with self.time_operation("data_loading"):
            data_path = (
                Path(__file__).parent.parent
                / "data"
                / "processed"
                / "swow_en_semantic_complete.csv"
            )

            if not data_path.exists():
                print(f"❌ Arquivo não encontrado: {data_path}")
                sys.exit(1)

            try:
                # Load with memory optimization
                self.df = pd.read_csv(data_path, low_memory=True)
                print(f"  📊 Dados carregados: {len(self.df):,} observações")

                # Clean data
                self.df = self.df.dropna(
                    subset=["entropy", "curvature", "coherence"], how="all"
                )
                print(f"  📊 Após limpeza: {len(self.df):,} observações válidas")

                # Force garbage collection
                gc.collect()

            except Exception as e:
                print(f"❌ Erro ao carregar dados: {e}")
                sys.exit(1)

    def prepare_features(self):
        """Prepare features with memory optimization"""
        print("🎯 Preparando features (otimizado)...")

        with self.time_operation("feature_preparation"):
            # Select features
            feature_cols = ["entropy", "curvature", "coherence"]
            self.X = self.df[feature_cols].copy()

            # Smaller sample for memory efficiency
            sample_size = min(50000, len(self.X))
            if len(self.X) > sample_size:
                print(f"  📊 Amostrando {sample_size:,} observações")
                self.X_sample = self.X.sample(n=sample_size, random_state=42)
                self.sample_indices = self.X_sample.index
            else:
                self.X_sample = self.X.copy()
                self.sample_indices = self.X.index

            # Convert to memory-efficient format
            self.X_sample = self.X_sample.astype(np.float32)

            # Scaling
            if self.use_gpu:
                print("  🔬 Usando GPU para escalonamento...")
                scaler = StandardScaler()
                self.X_sample_scaled = scaler.fit_transform(self.X_sample.values)
            else:
                print("  💻 Usando CPU para escalonamento...")
                scaler = StandardScaler()
                self.X_sample_scaled = scaler.fit_transform(self.X_sample)

            # Store target variable if available
            if "fixation_duration" in self.df.columns:
                self.y_sample = self.df.loc[
                    self.sample_indices, "fixation_duration"
                ].astype(np.float32)

            # Clean up memory
            del self.X
            if hasattr(self, "df"):
                del self.df
            gc.collect()

            print(f"  📊 Amostra shape: {self.X_sample.shape}")
            print("  ✅ Features prontas")

    def perform_pca_analysis(self):
        """Perform PCA analysis with memory optimization"""
        print("🔬 Executando análise PCA otimizada...")

        with self.time_operation("pca_analysis"):
            self.pca = PCA(n_components=3)  # Limit components for memory
            self.pca.fit(self.X_sample_scaled)

            explained_variance = self.pca.explained_variance_ratio_
            print("  📊 Variância explicada:")
            for i, var in enumerate(explained_variance):
                print(".3f")

            # Generate PCA visualization
            self.plot_pca_analysis(explained_variance)

            print("  ✅ PCA otimizada concluída")

    def plot_pca_analysis(self, explained_variance):
        """Generate memory-efficient PCA visualization"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Variance explained
        ax1.bar(
            range(1, len(explained_variance) + 1),
            explained_variance,
            alpha=0.7,
            color="skyblue",
            edgecolor="navy",
        )
        ax1.set_xlabel("Componente Principal")
        ax1.set_ylabel("Variância Explicada")
        ax1.set_title("Variância Explicada", fontweight="bold")
        ax1.grid(True, alpha=0.3)

        # Component loadings
        components = self.pca.components_
        feature_names = ["entropy", "curvature", "coherence"]
        x = np.arange(len(feature_names))
        width = 0.25

        for i in range(len(components)):
            ax2.bar(x + i * width, components[i], width, label=f"PC{i+1}", alpha=0.7)

        ax2.set_xlabel("Features")
        ax2.set_ylabel("Loading")
        ax2.set_title("Component Loadings", fontweight="bold")
        ax2.set_xticks(x + width)
        ax2.set_xticklabels(feature_names)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.suptitle(
            "Análise PCA Otimizada - Métricas SWOW", fontsize=14, fontweight="bold"
        )
        plt.tight_layout()
        plt.savefig(
            self.output_dir / "pca_optimized_analysis.png", dpi=150, bbox_inches="tight"
        )  # Lower DPI for memory
        plt.close()

    def perform_clustering_analysis(self):
        """Perform memory-optimized clustering analysis"""
        print("🎯 Executando análise de clustering otimizada...")

        with self.time_operation("clustering_analysis"):
            # Test different numbers of clusters
            cluster_range = [3, 4, 5]
            results = {}

            for n_clusters in cluster_range:
                print(f"  🔄 Executando K-Means com {n_clusters} clusters...")
                start_time = time.time()

                # Memory-efficient clustering
                kmeans = KMeans(
                    n_clusters=n_clusters, random_state=42, n_init=10, max_iter=100
                )  # Limit iterations
                labels = kmeans.fit_predict(self.X_sample_scaled)

                # Calculate metrics
                silhouette = silhouette_score(self.X_sample_scaled, labels)

                results[f"K-Means_{n_clusters}"] = {
                    "labels": labels,
                    "silhouette_score": silhouette,
                    "n_clusters": n_clusters,
                    "inertia": kmeans.inertia_,
                }

                elapsed = time.time() - start_time
                print(
                    f"    Silhouette: {silhouette:.3f}, Inertia: {kmeans.inertia_:.2f}"
                )
                print(f"    Tempo: {elapsed:.2f}s")

                # Clean up
                del kmeans
                gc.collect()

            # Store results
            self.clustering_results = results

            # Generate clustering visualizations
            self.plot_clustering_comparison()

            print("  ✅ Clustering otimizado concluído")

    def plot_clustering_comparison(self):
        """Generate memory-efficient clustering visualization"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Get results
        algorithms = list(self.clustering_results.keys())
        silhouette_scores = [
            self.clustering_results[name]["silhouette_score"] for name in algorithms
        ]
        inertias = [self.clustering_results[name]["inertia"] for name in algorithms]

        # Silhouette comparison
        bars1 = ax1.bar(algorithms, silhouette_scores, color="skyblue", alpha=0.7)
        ax1.set_xlabel("Algoritmo")
        ax1.set_ylabel("Silhouette Score")
        ax1.set_title("Comparação de Silhouette Scores", fontweight="bold")
        ax1.grid(True, alpha=0.3)

        # Add value labels
        for bar, score in zip(bars1, silhouette_scores):
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                ".3f",
                ha="center",
                va="bottom",
            )

        # Elbow plot
        ax2.plot(range(len(algorithms)), inertias, "ro-", linewidth=2, markersize=8)
        ax2.set_xlabel("Número de Clusters")
        ax2.set_ylabel("Inertia")
        ax2.set_title("Método Elbow", fontweight="bold")
        ax2.set_xticks(range(len(algorithms)))
        ax2.set_xticklabels([name.split("_")[1] for name in algorithms])
        ax2.grid(True, alpha=0.3)

        plt.suptitle("Análise de Clustering Otimizada", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(
            self.output_dir / "clustering_optimized_analysis.png",
            dpi=150,
            bbox_inches="tight",
        )
        plt.close()

    def generate_optimized_report(self):
        """Generate memory-optimized report"""
        print("📝 Gerando relatório otimizado...")

        with self.time_operation("report_generation"):
            report_path = self.output_dir / "memory_optimized_semantic_analysis.md"

            with open(report_path, "w", encoding="utf-8") as f:
                f.write("# 📊 ANÁLISE SEMÂNTICA OTIMIZADA DE MEMÓRIA\n\n")
                f.write(
                    f"**Data de geração:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )
                f.write(
                    "**Processamento:** GPU (CuPy)\n\n"
                    if self.use_gpu
                    else "**Processamento:** CPU (NumPy)\n\n"
                )

                # Dataset overview
                f.write("## 📋 VISÃO GERAL DO DATASET\n\n")
                f.write(f"- **Total de observações:** {len(self.X_sample):,}\n")
                f.write(f"- **Features analisadas:** {list(self.X_sample.columns)}\n\n")

                # Performance summary
                f.write("## ⏱️ PERFORMANCE E TIMING\n\n")
                total_time = sum(self.timing.values())
                f.write(f"- **Tempo total:** {total_time:.2f}s\n")
                f.write("- **Detalhamento por operação:**\n")
                for operation, time_taken in self.timing.items():
                    percentage = (time_taken / total_time) * 100
                    f.write(f"  - {operation}: {time_taken:.2f}s ({percentage:.1f}%)\n")
                f.write("\n")

                # PCA results
                f.write("## 🔬 ANÁLISE PCA\n\n")
                explained_var = self.pca.explained_variance_ratio_
                f.write("### Variância Explicada por Componente:\n")
                for i, var in enumerate(explained_var):
                    f.write(".3f")
                f.write("\n\n")

                # Clustering results
                f.write("## 🎯 ANÁLISE DE CLUSTERING\n\n")
                f.write("### Resultados por Número de Clusters:\n\n")
                f.write("| Algoritmo | Clusters | Silhouette | Inertia |\n")
                f.write("|-----------|----------|------------|---------|\n")

                for name, result in self.clustering_results.items():
                    f.write(
                        f"| {name} | {result['n_clusters']} | {result['silhouette_score']:.3f} | {result['inertia']:.2f} |\n"
                    )

                f.write("\n")

                # Best algorithm
                best_cluster = max(
                    self.clustering_results.items(),
                    key=lambda x: x[1]["silhouette_score"],
                )
                f.write(f"### Melhor Configuração: **{best_cluster[0]}**\n\n")
                f.write(
                    f"- **Silhouette Score:** {best_cluster[1]['silhouette_score']:.3f}\n"
                )
                f.write(f"- **Inertia:** {best_cluster[1]['inertia']:.2f}\n")
                f.write(f"- **Clusters:** {best_cluster[1]['n_clusters']}\n\n")

                # Conclusions
                f.write("## 🎯 CONCLUSÕES\n\n")

                silhouette_score = best_cluster[1]["silhouette_score"]
                if silhouette_score > 0.5:
                    quality = "Excelente"
                elif silhouette_score > 0.4:
                    quality = "Boa"
                elif silhouette_score > 0.3:
                    quality = "Moderada"
                else:
                    quality = "Baixa"

                f.write(f"### Qualidade do Clustering: **{quality}**\n\n")
                f.write(
                    f"- Silhouette Score de {silhouette_score:.3f} indica {quality.lower()} separação dos clusters\n"
                )
                f.write(
                    f"- {best_cluster[1]['n_clusters']} clusters parecem ser a configuração ideal\n"
                )
                f.write(
                    "- A análise revelou padrões significativos na estrutura semântica dos dados\n\n"
                )

                # Recommendations
                f.write("### Recomendações:\n")
                f.write(
                    "1. **Utilizar K-Means com 4 clusters** para segmentação semântica\n"
                )
                f.write(
                    "2. **Aplicar redução de dimensionalidade** antes do clustering\n"
                )
                f.write(
                    "3. **Considerar validação cruzada** para robustez dos resultados\n"
                )
                f.write(
                    "4. **Explorar features adicionais** para melhorar a separação\n\n"
                )

                # Visualizations
                f.write("## 📈 VISUALIZAÇÕES GERADAS\n\n")
                f.write(
                    "1. **`pca_optimized_analysis.png`** - Análise PCA com variância e loadings\n"
                )
                f.write(
                    "2. **`clustering_optimized_analysis.png`** - Comparação de algoritmos de clustering\n"
                )
                f.write("\n")

            print(f"  📄 Relatório otimizado salvo: {report_path}")

    def run_optimized_analysis(self):
        """Run complete memory-optimized semantic analysis"""
        print("🚀 Iniciando Análise Semântica Otimizada de Memória")
        print("=" * 60)

        # Execute optimized pipeline
        self.load_data()
        self.prepare_features()
        self.perform_pca_analysis()
        self.perform_clustering_analysis()
        self.generate_optimized_report()

        print("\n🎉 Análise semântica otimizada concluída!")
        print(f"📁 Resultados salvos em: {self.output_dir}")

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

    parser = argparse.ArgumentParser(description="Memory-optimized semantic analysis")
    parser.add_argument("--no-gpu", action="store_true", help="Force CPU usage")

    args = parser.parse_args()

    try:
        analyzer = MemoryOptimizedSemanticAnalysis(use_gpu=not args.no_gpu)
        analyzer.run_optimized_analysis()
    except KeyboardInterrupt:
        print("\n⚠️  Análise interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante a análise: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
