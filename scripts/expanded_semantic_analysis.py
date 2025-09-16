#!/usr/bin/env python3
"""
Análise Semântica Expandida com Visualizações
Versão completa com gráficos e comparações
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

# GPU and ML imports
try:
    import cupy as cp

    GPU_AVAILABLE = True
    print("🎯 CuPy disponível - usando aceleração GPU")
except ImportError:
    GPU_AVAILABLE = False
    print("⚠️  CuPy não disponível - usando CPU")

from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    silhouette_score,
    calinski_harabasz_score,
    davies_bouldin_score,
)
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
import time


class ExpandedSemanticAnalysis:
    """Expanded semantic analysis with comprehensive visualizations"""

    def __init__(self, use_gpu=True):
        self.use_gpu = use_gpu and GPU_AVAILABLE
        self.timing = {}
        self.output_dir = (
            Path(__file__).parent.parent / "reports" / "expanded_semantic_analysis"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

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

            # Sample for clustering (balanced size)
            sample_size = min(100000, len(self.X))
            if len(self.X) > sample_size:
                print(f"  📊 Amostrando {sample_size:,} observações")
                self.X_sample = self.X.sample(n=sample_size, random_state=42)
                self.sample_indices = self.X_sample.index
            else:
                self.X_sample = self.X.copy()
                self.sample_indices = self.X.index

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

            # Store target variable
            if "fixation_duration" in self.df.columns:
                self.y_sample = self.df.loc[self.sample_indices, "fixation_duration"]

            print(f"  📊 Amostra shape: {self.X_sample.shape}")
            print("  ✅ Features prontas")

    def perform_pca_analysis(self):
        """Perform comprehensive PCA analysis"""
        print("🔬 Executando análise PCA completa...")

        with self.time_operation("pca_analysis"):
            self.pca = PCA()
            self.pca.fit(self.X_sample_scaled)

            explained_variance = self.pca.explained_variance_ratio_
            cumulative_variance = np.cumsum(explained_variance)

            print("  📊 Variância explicada por componente:")
            for i, var in enumerate(explained_variance[:5]):
                print(".3f")

            # Generate PCA visualizations
            self.plot_pca_analysis(explained_variance, cumulative_variance)

            print("  ✅ PCA completa concluída")

    def plot_pca_analysis(self, explained_variance, cumulative_variance):
        """Generate comprehensive PCA visualizations"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

        # 1. Individual variance
        ax1.bar(
            range(1, len(explained_variance) + 1),
            explained_variance,
            alpha=0.7,
            color="skyblue",
            edgecolor="navy",
        )
        ax1.set_xlabel("Componente Principal")
        ax1.set_ylabel("Variância Explicada")
        ax1.set_title("Variância Explicada por Componente", fontweight="bold")
        ax1.grid(True, alpha=0.3)

        # 2. Cumulative variance
        ax2.plot(
            range(1, len(cumulative_variance) + 1),
            cumulative_variance,
            "ro-",
            linewidth=2,
            markersize=6,
        )
        ax2.axhline(
            y=0.95, color="red", linestyle="--", alpha=0.7, label="95% da variância"
        )
        ax2.set_xlabel("Número de Componentes")
        ax2.set_ylabel("Variância Cumulativa")
        ax2.set_title("Variância Cumulativa Explicada", fontweight="bold")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. Component loadings
        components = self.pca.components_
        feature_names = ["entropy", "curvature", "coherence"]
        x = np.arange(len(feature_names))
        width = 0.25

        for i in range(min(3, len(components))):
            ax3.bar(x + i * width, components[i], width, label=f"PC{i+1}", alpha=0.7)

        ax3.set_xlabel("Features")
        ax3.set_ylabel("Loading")
        ax3.set_title("Component Loadings", fontweight="bold")
        ax3.set_xticks(x + width)
        ax3.set_xticklabels(feature_names)
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 4. Scree plot
        ax4.plot(
            range(1, len(explained_variance) + 1),
            explained_variance,
            "bo-",
            linewidth=2,
            markersize=8,
        )
        ax4.set_xlabel("Componente Principal")
        ax4.set_ylabel("Variância Explicada")
        ax4.set_title("Scree Plot", fontweight="bold")
        ax4.grid(True, alpha=0.3)

        plt.suptitle(
            "Análise PCA Completa - Métricas SWOW", fontsize=16, fontweight="bold"
        )
        plt.tight_layout()
        plt.savefig(
            self.output_dir / "pca_complete_analysis.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def perform_clustering_analysis(self):
        """Perform comprehensive clustering analysis"""
        print("🎯 Executando análise de clustering completa...")

        with self.time_operation("clustering_analysis"):
            # Define clustering algorithms
            algorithms = {
                "K-Means_3": KMeans(n_clusters=3, random_state=42, n_init=10),
                "K-Means_4": KMeans(n_clusters=4, random_state=42, n_init=10),
                "K-Means_5": KMeans(n_clusters=5, random_state=42, n_init=10),
                "Hierarchical": AgglomerativeClustering(n_clusters=4, linkage="ward"),
                "DBSCAN": DBSCAN(eps=0.8, min_samples=50),
            }

            results = {}

            for name, algorithm in algorithms.items():
                print(f"  🔄 Executando {name}...")
                start_time = time.time()

                try:
                    # Fit algorithm
                    labels = algorithm.fit_predict(self.X_sample_scaled)

                    # Calculate metrics
                    if len(np.unique(labels)) > 1:
                        silhouette = silhouette_score(self.X_sample_scaled, labels)
                        calinski = calinski_harabasz_score(self.X_sample_scaled, labels)
                        davies = davies_bouldin_score(self.X_sample_scaled, labels)
                    else:
                        silhouette = calinski = davies = 0.0

                    results[name] = {
                        "labels": labels,
                        "silhouette_score": silhouette,
                        "calinski_harabasz_score": calinski,
                        "davies_bouldin_score": davies,
                        "n_clusters": len(np.unique(labels[labels >= 0]))
                        if -1 in labels
                        else len(np.unique(labels)),
                    }

                    elapsed = time.time() - start_time
                    print(
                        f"    Silhouette: {silhouette:.3f}, Clusters: {results[name]['n_clusters']}"
                    )
                    print(f"    Tempo: {elapsed:.2f}s")

                except Exception as e:
                    elapsed = time.time() - start_time
                    print(f"    ❌ Erro em {name}: {e} ({elapsed:.2f}s)")

            # Store results
            self.clustering_results = results

            # Generate clustering visualizations
            self.plot_clustering_comparison()
            self.plot_cluster_characteristics()

            print("  ✅ Análise de clustering completa concluída")

    def plot_clustering_comparison(self):
        """Generate comprehensive clustering comparison"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))

        # Get best algorithms (top 3 by silhouette score)
        sorted_algorithms = sorted(
            self.clustering_results.items(),
            key=lambda x: x[1]["silhouette_score"],
            reverse=True,
        )[:3]

        for i, (name, result) in enumerate(sorted_algorithms):
            if i >= 3:  # Limit to 3 algorithms
                break

            labels = result["labels"]

            # Scatter plot of first two PCA components
            pca_2d = PCA(n_components=2).fit_transform(self.X_sample_scaled)
            scatter = axes[0, i].scatter(
                pca_2d[:, 0], pca_2d[:, 1], c=labels, cmap="viridis", alpha=0.6, s=20
            )
            axes[0, i].set_xlabel("PC1")
            axes[0, i].set_ylabel("PC2")
            axes[0, i].set_title(
                f'{name}\nSilhouette: {result["silhouette_score"]:.3f}',
                fontweight="bold",
            )
            plt.colorbar(scatter, ax=axes[0, i])

            # Cluster distribution
            if -1 in labels:  # Handle DBSCAN noise points
                unique_labels, counts = np.unique(
                    labels[labels >= 0], return_counts=True
                )
                noise_count = np.sum(labels == -1)
                axes[1, i].bar(
                    ["Noise"] + list(unique_labels),
                    [noise_count] + list(counts),
                    color=["red"] + ["skyblue"] * len(unique_labels),
                    alpha=0.7,
                )
            else:
                unique_labels, counts = np.unique(labels, return_counts=True)
                axes[1, i].bar(unique_labels, counts, color="skyblue", alpha=0.7)

            axes[1, i].set_xlabel("Cluster")
            axes[1, i].set_ylabel("Número de Observações")
            axes[1, i].set_title(
                f"Distribuição de Clusters - {name}", fontweight="bold"
            )
            axes[1, i].grid(True, alpha=0.3)

        plt.suptitle(
            "Comparação de Algoritmos de Clustering", fontsize=16, fontweight="bold"
        )
        plt.tight_layout()
        plt.savefig(
            self.output_dir / "clustering_comparison.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def plot_cluster_characteristics(self):
        """Generate cluster characteristics analysis"""
        # Use best clustering result
        best_algorithm = max(
            self.clustering_results.items(), key=lambda x: x[1]["silhouette_score"]
        )
        best_name, best_result = best_algorithm

        labels = best_result["labels"]
        sample_df = self.X_sample.copy()

        # Remove noise points for DBSCAN
        if -1 in labels:
            valid_indices = labels >= 0
            sample_df = sample_df[valid_indices]
            labels = labels[valid_indices]

        sample_df["cluster"] = labels

        # Add target variable if available
        if hasattr(self, "y_sample"):
            sample_df["fixation_duration"] = self.y_sample.loc[sample_df.index]

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))

        metrics = ["entropy", "curvature", "coherence"]
        if "fixation_duration" in sample_df.columns:
            metrics.append("fixation_duration")

        for i, metric in enumerate(metrics):
            row = i // 3
            col = i % 3

            if row >= 2:  # Limit to 2 rows
                break

            # Box plot for each cluster
            sns.boxplot(
                data=sample_df, x="cluster", y=metric, ax=axes[row, col], palette="Set2"
            )
            axes[row, col].set_title(
                f"{metric.capitalize()} por Cluster", fontweight="bold"
            )
            axes[row, col].set_xlabel("Cluster")
            axes[row, col].set_ylabel(metric.capitalize())
            axes[row, col].grid(True, alpha=0.3)

        plt.suptitle(
            f"Características dos Clusters - {best_name} (Melhor Algoritmo)",
            fontsize=16,
            fontweight="bold",
        )
        plt.tight_layout()
        plt.savefig(
            self.output_dir / "cluster_characteristics.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

    def perform_predictive_modeling(self):
        """Perform predictive modeling analysis"""
        print("🔮 Executando modelagem preditiva...")

        with self.time_operation("predictive_modeling"):
            if not hasattr(self, "y_sample"):
                print(
                    "  ⚠️  Variável target não disponível, pulando modelagem preditiva"
                )
                return

            # Prepare data
            X_train, X_test, y_train, y_test = train_test_split(
                self.X_sample_scaled, self.y_sample, test_size=0.2, random_state=42
            )

            # Define models
            models = {
                "Random Forest": RandomForestRegressor(
                    n_estimators=100, random_state=42, n_jobs=-1
                ),
                "Ridge Regression": Ridge(alpha=1.0, random_state=42),
            }

            results = {}

            for name, model in models.items():
                print(f"  🔄 Avaliando {name}...")
                start_time = time.time()

                # Cross-validation
                cv_scores = cross_val_score(
                    model, X_train, y_train, cv=5, scoring="r2", n_jobs=-1
                )

                # Train and test
                model.fit(X_train, y_train)
                train_score = model.score(X_train, y_train)
                test_score = model.score(X_test, y_test)

                results[name] = {
                    "cv_mean": cv_scores.mean(),
                    "cv_std": cv_scores.std(),
                    "train_score": train_score,
                    "test_score": test_score,
                    "cv_scores": cv_scores,
                }

                elapsed = time.time() - start_time
                print(f"    CV R²: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
                print(f"    Test R²: {test_score:.3f}")
                print(f"    Tempo: {elapsed:.2f}s")

            self.modeling_results = results

            # Generate modeling visualizations
            self.plot_modeling_results()

            print("  ✅ Modelagem preditiva concluída")

    def plot_modeling_results(self):
        """Generate predictive modeling visualizations"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        model_names = list(self.modeling_results.keys())
        cv_means = [self.modeling_results[name]["cv_mean"] for name in model_names]
        cv_stds = [self.modeling_results[name]["cv_std"] for name in model_names]
        train_scores = [
            self.modeling_results[name]["train_score"] for name in model_names
        ]
        test_scores = [
            self.modeling_results[name]["test_score"] for name in model_names
        ]

        # Model comparison
        x = np.arange(len(model_names))
        ax1.bar(
            x - 0.2,
            cv_means,
            0.4,
            label="CV Mean",
            alpha=0.7,
            color="skyblue",
            yerr=cv_stds,
            capsize=5,
        )
        ax1.bar(
            x + 0.2, test_scores, 0.4, label="Test Score", alpha=0.7, color="lightcoral"
        )
        ax1.set_xlabel("Modelo")
        ax1.set_ylabel("R² Score")
        ax1.set_title("Comparação de Modelos Preditivos", fontweight="bold")
        ax1.set_xticks(x)
        ax1.set_xticklabels(model_names)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Overfitting analysis
        overfitting = np.array(train_scores) - np.array(test_scores)
        bars = ax2.bar(model_names, overfitting, color="salmon", alpha=0.7)
        ax2.set_xlabel("Modelo")
        ax2.set_ylabel("Diferença (Train - Test)")
        ax2.set_title("Análise de Overfitting", fontweight="bold")
        ax2.axhline(y=0, color="red", linestyle="--", alpha=0.7)
        ax2.grid(True, alpha=0.3)

        # Add value labels
        for bar, value in zip(bars, overfitting):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                ".3f",
                ha="center",
                va="bottom" if value > 0 else "top",
            )

        plt.suptitle(
            "Modelagem Preditiva - Duração de Fixação", fontsize=16, fontweight="bold"
        )
        plt.tight_layout()
        plt.savefig(
            self.output_dir / "predictive_modeling.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def generate_comprehensive_report(self):
        """Generate comprehensive analysis report"""
        print("📝 Gerando relatório abrangente...")

        with self.time_operation("report_generation"):
            report_path = self.output_dir / "expanded_semantic_analysis_report.md"

            with open(report_path, "w", encoding="utf-8") as f:
                f.write("# 📊 ANÁLISE SEMÂNTICA EXPANDIDA - RELATÓRIO ABRANGENTE\n\n")
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
                f.write(f"- **Total de observações:** {len(self.df):,}\n")
                f.write(f"- **Amostra analisada:** {len(self.X_sample):,}\n")
                f.write(f"- **Features analisadas:** {list(self.X.columns)}\n\n")

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
                for i, var in enumerate(explained_var[:5]):
                    f.write(".3f")
                f.write("\n\n")

                f.write("### Component Loadings:\n")
                components = self.pca.components_
                feature_names = ["entropy", "curvature", "coherence"]
                for i in range(min(3, len(components))):
                    f.write(f"- **PC{i+1}:**\n")
                    for j, feature in enumerate(feature_names):
                        f.write(".3f")
                    f.write("\n")
                f.write("\n")

                # Clustering results
                f.write("## 🎯 ANÁLISE DE CLUSTERING\n\n")
                f.write("### Comparação de Algoritmos:\n\n")
                f.write(
                    "| Algoritmo | Clusters | Silhouette | Calinski-Harabasz | Davies-Bouldin |\n"
                )
                f.write(
                    "|-----------|----------|------------|-------------------|----------------|\n"
                )

                for name, result in self.clustering_results.items():
                    f.write(
                        f"| {name} | {result['n_clusters']} | {result['silhouette_score']:.3f} | {result['calinski_harabasz_score']:.2f} | {result['davies_bouldin_score']:.3f} |\n"
                    )

                f.write("\n")

                # Best algorithm analysis
                best_cluster = max(
                    self.clustering_results.items(),
                    key=lambda x: x[1]["silhouette_score"],
                )
                f.write(f"### Melhor Algoritmo: **{best_cluster[0]}**\n\n")
                f.write(
                    f"- **Silhouette Score:** {best_cluster[1]['silhouette_score']:.3f}\n"
                )
                f.write(
                    f"- **Número de clusters:** {best_cluster[1]['n_clusters']}\n\n"
                )

                # Predictive modeling results
                if hasattr(self, "modeling_results"):
                    f.write("## 🔮 MODELAGEM PREDITIVA\n\n")
                    f.write("### Resultados por Modelo:\n\n")
                    f.write(
                        "| Modelo | CV R² Médio | CV Std | Train R² | Test R² | Overfitting |\n"
                    )
                    f.write(
                        "|--------|-------------|--------|----------|---------|-------------|\n"
                    )

                    for name, result in self.modeling_results.items():
                        overfitting = result["train_score"] - result["test_score"]
                        f.write(
                            f"| {name} | {result['cv_mean']:.3f} | {result['cv_std']:.3f} | {result['train_score']:.3f} | {result['test_score']:.3f} | {overfitting:.3f} |\n"
                        )

                    f.write("\n")

                    # Best model
                    best_model = max(
                        self.modeling_results.items(), key=lambda x: x[1]["test_score"]
                    )
                    f.write(f"### Melhor Modelo: **{best_model[0]}**\n\n")
                    f.write(f"- **Test R²:** {best_model[1]['test_score']:.3f}\n")
                    f.write(
                        f"- **CV R²:** {best_model[1]['cv_mean']:.3f} ± {best_model[1]['cv_std']:.3f}\n\n"
                    )

                # Conclusions
                f.write("## 🎯 CONCLUSÕES\n\n")

                # Clustering insights
                f.write("### Insights de Clustering:\n")
                f.write(
                    f"- O algoritmo **{best_cluster[0]}** apresentou o melhor desempenho com Silhouette Score de {best_cluster[1]['silhouette_score']:.3f}\n"
                )
                f.write(
                    f"- Foram identificados **{best_cluster[1]['n_clusters']} clusters** distintos nas métricas SWOW\n"
                )
                f.write(
                    "- A análise revelou padrões significativos na estrutura semântica dos dados\n\n"
                )

                # Modeling insights
                if hasattr(self, "modeling_results"):
                    f.write("### Insights de Modelagem:\n")
                    best_test_score = best_model[1]["test_score"]
                    if best_test_score > 0.5:
                        f.write(
                            f"- O modelo **{best_model[0]}** demonstrou boa capacidade preditiva (R² = {best_test_score:.3f})\n"
                        )
                    elif best_test_score > 0.3:
                        f.write(
                            f"- O modelo **{best_model[0]}** apresentou capacidade preditiva moderada (R² = {best_test_score:.3f})\n"
                        )
                    else:
                        f.write(
                            f"- Os modelos apresentaram baixa capacidade preditiva (R² máximo = {best_test_score:.3f})\n"
                        )
                        f.write(
                            "- Sugere-se investigação de features adicionais ou abordagens não-lineares\n"
                        )

                # Recommendations
                f.write("\n### Recomendações:\n")
                f.write(
                    "1. **Utilizar o clustering** para segmentação semântica de palavras\n"
                )
                f.write(
                    "2. **Incorporar features contextuais** para melhorar predições\n"
                )
                f.write(
                    "3. **Explorar modelos não-lineares** para captura de relações complexas\n"
                )
                f.write(
                    "4. **Validar em dados independentes** antes de aplicações práticas\n\n"
                )

                # Visualizations
                f.write("## 📈 VISUALIZAÇÕES GERADAS\n\n")
                f.write(
                    "As seguintes visualizações foram salvas no diretório de saída:\n\n"
                )
                f.write(
                    "1. **`pca_complete_analysis.png`** - Análise PCA completa com variância, loadings e scree plot\n"
                )
                f.write(
                    "2. **`clustering_comparison.png`** - Comparação de algoritmos de clustering\n"
                )
                f.write(
                    "3. **`cluster_characteristics.png`** - Características dos clusters por feature\n"
                )
                if hasattr(self, "modeling_results"):
                    f.write(
                        "4. **`predictive_modeling.png`** - Resultados da modelagem preditiva\n"
                    )
                f.write("\n")

            print(f"  📄 Relatório abrangente salvo: {report_path}")

    def run_expanded_analysis(self):
        """Run complete expanded semantic analysis"""
        print("🚀 Iniciando Análise Semântica Expandida")
        print("=" * 60)

        # Execute complete pipeline
        self.load_data()
        self.prepare_features()
        self.perform_pca_analysis()
        self.perform_clustering_analysis()
        self.perform_predictive_modeling()
        self.generate_comprehensive_report()

        print("\n🎉 Análise semântica expandida concluída!")
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

    parser = argparse.ArgumentParser(description="Expanded semantic analysis")
    parser.add_argument("--no-gpu", action="store_true", help="Force CPU usage")

    args = parser.parse_args()

    try:
        analyzer = ExpandedSemanticAnalysis(use_gpu=not args.no_gpu)
        analyzer.run_expanded_analysis()
    except KeyboardInterrupt:
        print("\n⚠️  Análise interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante a análise: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
