#!/usr/bin/env python3
"""
Análise Avançada: Clustering Semântico e PCA
Semantic clustering and principal component analysis of SWOW metrics
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
import warnings

warnings.filterwarnings("ignore")


class AdvancedSemanticAnalysis:
    """Advanced semantic analysis with PCA, clustering, and cross-validation"""

    def __init__(self):
        output_path = (
            Path(__file__).parent.parent / "reports" / "advanced_semantic_analysis"
        )
        self.output_dir = output_path
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize data containers
        self.df = None
        self.X = None
        self.X_scaled = None
        self.X_sample = None
        self.X_sample_scaled = None
        self.y = None
        self.y_sample = None
        self.scaler = None
        self.pca = None
        self.clustering_results = {}

    def load_data(self):
        """Load integrated neuro-SWOW data"""
        print("🔍 Carregando dados integrados...")

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
            self.df = pd.read_csv(data_path)
            print(f"  📊 Dados carregados: {len(self.df):,} observações")

            # Basic data cleaning
            self.df = self.df.dropna(
                subset=["entropy", "curvature", "coherence"], how="all"
            )
            print(f"  📊 Após limpeza: {len(self.df):,} observações válidas")

        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            sys.exit(1)

    def prepare_features_for_analysis(self):
        """Prepare features for PCA and clustering"""
        print("🎯 Preparando features para análise avançada...")

        # Select SWOW metrics
        feature_cols = ["entropy", "curvature", "coherence"]
        self.X = self.df[feature_cols].copy()

        # Sample data for clustering to reduce memory usage
        sample_size = min(50000, len(self.X))  # Limit to 50k samples
        if len(self.X) > sample_size:
            print(f"  📊 Amostrando {sample_size:,} observações para clustering")
            self.X_sample = self.X.sample(n=sample_size, random_state=42)
            self.sample_indices = self.X_sample.index
        else:
            self.X_sample = self.X.copy()
            self.sample_indices = self.X.index

        # Scale features
        self.scaler = StandardScaler()
        self.X_scaled = self.scaler.fit_transform(self.X)
        self.X_sample_scaled = self.scaler.transform(self.X_sample)

        # Target variable
        self.y = self.df["fixation_duration"].copy()
        self.y_sample = self.y.loc[self.sample_indices]

        print(f"  📊 Features completas shape: {self.X.shape}")
        print(f"  📊 Amostra para clustering shape: {self.X_sample.shape}")
        print("  ✅ Features escalonadas prontas para análise")

    def perform_pca_analysis(self):
        """Perform PCA analysis on SWOW metrics"""
        print("🔬 Executando análise PCA...")

        # Perform PCA
        self.pca = PCA()
        self.pca.fit(self.X_scaled)

        # Calculate explained variance
        explained_variance = self.pca.explained_variance_ratio_
        cumulative_variance = np.cumsum(explained_variance)

        print("  📊 Variância explicada por componente:")
        for i, var in enumerate(explained_variance[:5]):
            print(".3f")

        # Plot variance analysis
        self.plot_pca_variance(explained_variance, cumulative_variance)

        # Plot component analysis
        self.plot_pca_components()

        print("  ✅ Análise PCA concluída")

    def plot_pca_variance(self, explained_variance, cumulative_variance):
        """Plot PCA variance analysis"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Individual variance
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

        # Cumulative variance
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

        plt.tight_layout()
        plt.savefig(
            self.output_dir / "pca_variance_analysis.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def plot_pca_components(self):
        """Plot PCA component analysis"""
        # Get PCA components
        components = self.pca.components_
        feature_names = ["entropy", "curvature", "coherence"]
        explained_variance = self.pca.explained_variance_ratio_

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        for i in range(3):
            ax = axes[i]
            component = components[i]
            ax.barh(feature_names, component, color="lightcoral", alpha=0.7)
            ax.set_xlabel("Peso do Componente")
            ax.set_title(f"PC{i+1} - {explained_variance[i]:.3f} variância")
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(
            self.output_dir / "pca_components_analysis.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

    def perform_clustering_analysis(self):
        """Perform clustering analysis with memory-efficient algorithms"""
        print("🎯 Executando análise de clustering...")

        # Define clustering algorithms with memory-efficient parameters
        algorithms = {
            "K-Means": KMeans(n_clusters=4, random_state=42, n_init=10),
            "DBSCAN": DBSCAN(eps=0.5, min_samples=10, n_jobs=-1),
            "Hierarchical": AgglomerativeClustering(n_clusters=4, linkage="ward"),
        }

        results = {}

        for name, algorithm in algorithms.items():
            print(f"  🔄 Executando {name} clustering...")
            try:
                # Fit algorithm
                labels = algorithm.fit_predict(self.X_sample_scaled)

                # Calculate metrics
                if len(np.unique(labels)) > 1:
                    silhouette = silhouette_score(self.X_sample_scaled, labels)
                    calinski = calinski_harabasz_score(self.X_sample_scaled, labels)
                else:
                    silhouette = 0.0
                    calinski = 0.0

                results[name] = {
                    "labels": labels,
                    "silhouette_score": silhouette,
                    "calinski_harabasz_score": calinski,
                    "n_clusters": len(np.unique(labels)),
                }

                print(
                    f"    Silhouette: {silhouette:.3f}, Calinski-Harabasz: {calinski:.2f}"
                )

            except Exception as e:
                print(f"    ❌ Erro em {name}: {e}")
                continue

        self.clustering_results = results

        # Plot clustering comparison
        self.plot_clustering_comparison()

        # Plot cluster characteristics
        self.plot_cluster_characteristics()

        print("  ✅ Análise de clustering concluída")

    def plot_clustering_comparison(self):
        """Plot clustering algorithm comparison"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))

        for i, (name, result) in enumerate(self.clustering_results.items()):
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
                f'{name} Clustering\nSilhouette: {result["silhouette_score"]:.3f}',
                fontweight="bold",
            )
            plt.colorbar(scatter, ax=axes[0, i])

            # Cluster distribution
            unique_labels, counts = np.unique(labels, return_counts=True)
            axes[1, i].bar(unique_labels, counts, color="skyblue", alpha=0.7)
            axes[1, i].set_xlabel("Cluster")
            axes[1, i].set_ylabel("Número de Observações")
            axes[1, i].set_title(
                f"Distribuição de Clusters - {name}", fontweight="bold"
            )
            axes[1, i].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(
            self.output_dir / "clustering_comparison.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def plot_cluster_characteristics(self):
        """Plot cluster characteristics analysis"""
        # Use best clustering result (highest silhouette score)
        best_algorithm = max(
            self.clustering_results.items(), key=lambda x: x[1]["silhouette_score"]
        )
        best_name, best_result = best_algorithm

        labels = best_result["labels"]
        sample_df = self.X_sample.copy()
        sample_df["cluster"] = labels
        sample_df["fixation_duration"] = self.y_sample

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))

        metrics = ["entropy", "curvature", "coherence", "fixation_duration"]

        for i, metric in enumerate(metrics):
            row = i // 3
            col = i % 3

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
            f"Características dos Clusters - {best_name}",
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

    def perform_cross_validation_analysis(self):
        """Perform cross-validation analysis to assess overfitting"""
        print("🔍 Executando análise de validação cruzada...")

        # Prepare data for modeling
        X_train, X_test, y_train, y_test = train_test_split(
            self.X_scaled, self.y, test_size=0.2, random_state=42
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

            # Cross-validation scores
            cv_scores = cross_val_score(
                model, X_train, y_train, cv=5, scoring="r2", n_jobs=-1
            )

            # Train and test on holdout set
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

            print(f"    CV R²: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
            print(f"    Train R²: {train_score:.3f}, Test R²: {test_score:.3f}")

        self.cv_results = results

        # Plot cross-validation results
        self.plot_cross_validation_analysis()

        print("  ✅ Análise de validação cruzada concluída")

    def plot_cross_validation_analysis(self):
        """Plot cross-validation analysis results"""
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))

        model_names = list(self.cv_results.keys())
        cv_means = [self.cv_results[name]["cv_mean"] for name in model_names]
        cv_stds = [self.cv_results[name]["cv_std"] for name in model_names]
        train_scores = [self.cv_results[name]["train_score"] for name in model_names]
        test_scores = [self.cv_results[name]["test_score"] for name in model_names]

        # CV scores comparison
        x = np.arange(len(model_names))
        axes[0].bar(
            x - 0.2,
            cv_means,
            0.4,
            label="CV Mean",
            alpha=0.7,
            color="skyblue",
            yerr=cv_stds,
            capsize=5,
        )
        axes[0].bar(
            x + 0.2, test_scores, 0.4, label="Test Score", alpha=0.7, color="lightcoral"
        )
        axes[0].set_xlabel("Modelo")
        axes[0].set_ylabel("R² Score")
        axes[0].set_title("Comparação de Scores de Validação", fontweight="bold")
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(model_names)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Overfitting analysis
        overfitting = np.array(train_scores) - np.array(test_scores)
        axes[1].bar(model_names, overfitting, color="salmon", alpha=0.7)
        axes[1].set_xlabel("Modelo")
        axes[1].set_ylabel("Diferença (Train - Test)")
        axes[1].set_title("Análise de Overfitting", fontweight="bold")
        axes[1].axhline(y=0, color="red", linestyle="--", alpha=0.7)
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(
            self.output_dir / "cross_validation_analysis.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

    def generate_comprehensive_report(self):
        """Generate comprehensive analysis report"""
        print("📝 Gerando relatório abrangente...")

        report_path = self.output_dir / "advanced_semantic_analysis_report.txt"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("ANÁLISE AVANÇADA: CLUSTERING SEMÂNTICO E PCA\n")
            f.write("=" * 60 + "\n\n")

            # Dataset overview
            f.write("VISÃO GERAL DO DATASET\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total de observações: {len(self.df):,}\n")
            f.write(f"Features analisadas: {list(self.X.columns)}\n")
            f.write(f"Amostra para clustering: {len(self.X_sample):,}\n\n")

            # PCA results
            f.write("RESULTADOS DA ANÁLISE PCA\n")
            f.write("-" * 30 + "\n")
            explained_var = self.pca.explained_variance_ratio_
            for i, var in enumerate(explained_var[:3]):
                f.write(".3f")
            f.write(f"Variância acumulada (3 PCs): {explained_var[:3].sum():.3f}\n\n")

            # Clustering results
            f.write("RESULTADOS DO CLUSTERING\n")
            f.write("-" * 30 + "\n")
            for name, result in self.clustering_results.items():
                f.write(f"{name}:\n")
                f.write(f"  Clusters encontrados: {result['n_clusters']}\n")
                f.write(f"  Silhouette Score: {result['silhouette_score']:.3f}\n")
                f.write(
                    f"  Calinski-Harabasz Score: {result['calinski_harabasz_score']:.2f}\n"
                )
                f.write("\n")

            # Cross-validation results
            f.write("RESULTADOS DA VALIDAÇÃO CRUZADA\n")
            f.write("-" * 35 + "\n")
            for name, result in self.cv_results.items():
                f.write(f"{name}:\n")
                f.write(
                    f"  CV R² médio: {result['cv_mean']:.3f} ± {result['cv_std']:.3f}\n"
                )
                f.write(f"  Score de treino: {result['train_score']:.3f}\n")
                f.write(f"  Score de teste: {result['test_score']:.3f}\n")
                f.write(
                    f"  Overfitting (Train-Test): {result['train_score'] - result['test_score']:.3f}\n"
                )
                f.write("\n")

            # Conclusions
            f.write("CONCLUSÕES\n")
            f.write("-" * 15 + "\n")
            best_cluster = max(
                self.clustering_results.items(), key=lambda x: x[1]["silhouette_score"]
            )
            f.write(f"Melhor algoritmo de clustering: {best_cluster[0]} ")
            f.write(f"(Silhouette: {best_cluster[1]['silhouette_score']:.3f})\n")

            best_model = max(self.cv_results.items(), key=lambda x: x[1]["test_score"])
            f.write(f"Melhor modelo preditivo: {best_model[0]} ")
            f.write(f"(Test R²: {best_model[1]['test_score']:.3f})\n")

            # Check for overfitting
            overfitting_detected = any(
                result["train_score"] - result["test_score"] > 0.1
                for result in self.cv_results.values()
            )
            if overfitting_detected:
                f.write("⚠️  Possível overfitting detectado - ")
                f.write("diferença significativa entre treino e teste\n")
            else:
                f.write("✅ Não há evidências significativas de overfitting\n")

        print(f"  📄 Relatório salvo em: {report_path}")

    def run_complete_analysis(self):
        """Run complete advanced semantic analysis"""
        print("🚀 Iniciando Análise Semântica Avançada")
        print("=" * 50)

        # Load and prepare data
        self.load_data()
        self.prepare_features_for_analysis()

        # Perform analyses
        self.perform_pca_analysis()
        self.perform_clustering_analysis()
        self.perform_cross_validation_analysis()

        # Generate report
        self.generate_comprehensive_report()

        print("\n🎉 Análise semântica avançada concluída!")
        print(f"📁 Resultados salvos em: {self.output_dir}")


def main():
    """Main execution function"""
    try:
        analyzer = AdvancedSemanticAnalysis()
        analyzer.run_complete_analysis()
    except KeyboardInterrupt:
        print("\n⚠️  Análise interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante a análise: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
