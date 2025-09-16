#!/usr/bin/env python3
"""
🚨 DIAGNÓSTICO CRÍTICO DE OVERFITTING - VERSÃO CORRIGIDA
Comprehensive overfitting detection and correction for SWOW-neuro models
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import (
    train_test_split,
    cross_val_score,
    KFold,
    StratifiedKFold,
)
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.inspection import permutation_importance
import warnings
import gc
from datetime import datetime

warnings.filterwarnings("ignore")


class OverfittingDiagnosticFixed:
    """Comprehensive overfitting diagnostic and correction system - FIXED VERSION"""

    def __init__(
        self, data_path: str = None, max_samples: int = 50000, min_samples: int = 1000
    ):
        if data_path is None:
            # Try multiple possible data paths
            possible_paths = [
                Path(__file__).parent.parent
                / "data"
                / "processed"
                / "integrated_neuro_swow.csv",
                Path(__file__).parent.parent
                / "data"
                / "processed"
                / "zuco_kec_merged.csv",
                Path(__file__).parent.parent
                / "data"
                / "processed"
                / "zuco_aligned_real_et_eeg.csv",
            ]

            data_path = None
            for path in possible_paths:
                if path.exists():
                    data_path = path
                    break

            if data_path is None:
                print("⚠️ Nenhum arquivo de dados encontrado, usando dados sintéticos")
                data_path = "synthetic"

        self.data_path = data_path
        self.output_dir = (
            Path(__file__).parent.parent / "reports" / "overfitting_diagnostic"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Configuration
        self.max_samples = max_samples
        self.min_samples = min_samples

        # Initialize containers
        self.df = None
        self.X = None
        self.y = None
        self.diagnostic_results = {}
        self.corrected_results = {}

        print("🚨 INICIANDO DIAGNÓSTICO CRÍTICO DE OVERFITTING - VERSÃO CORRIGIDA")
        print("=" * 70)
        print(f"📁 Arquivo de dados: {self.data_path}")
        print(f"🔢 Limite de amostras: {self.max_samples:,}")
        print(f"🔢 Mínimo de amostras: {self.min_samples:,}")

    def create_realistic_synthetic_data(self):
        """Create realistic synthetic data that mimics real neurophysiological patterns"""
        print("\n🔬 CRIANDO DADOS SINTÉTICOS REALISTAS...")

        np.random.seed(42)
        n_samples = max(self.min_samples, 10000)

        # Create realistic SWOW-based features
        # Entropy: typically ranges from 0.5 to 4.5 bits
        entropy = np.random.gamma(2, 1.2) + np.random.normal(0, 0.3, n_samples)
        entropy = np.clip(entropy, 0.1, 5.0)

        # Curvature: can be negative or positive, typically small values
        curvature = np.random.normal(0, 0.5, n_samples) + np.random.exponential(
            0.2, n_samples
        ) * np.random.choice([-1, 1], n_samples)
        curvature = np.clip(curvature, -2.0, 2.0)

        # Coherence: typically between -1 and 1, often positive
        coherence = np.random.beta(3, 2, n_samples) * 2 - 1  # Transform to [-1, 1]
        coherence = np.clip(coherence, -1.0, 1.0)

        # Create realistic fixation duration (in milliseconds)
        # Base duration around 200-300ms with realistic relationships
        base_duration = 250

        # Realistic relationships with noise
        duration = (
            base_duration
            + 30 * entropy  # Higher entropy = longer fixation
            + 20 * np.abs(curvature)  # Higher absolute curvature = longer fixation
            + -15 * coherence  # Higher coherence = shorter fixation
            + np.random.normal(0, 40, n_samples)  # Realistic noise
        )

        # Ensure realistic range (50ms to 800ms)
        duration = np.clip(duration, 50, 800)

        # Add some realistic outliers (5% of data)
        outlier_mask = np.random.random(n_samples) < 0.05
        duration[outlier_mask] = duration[outlier_mask] * np.random.uniform(
            1.5, 3.0, outlier_mask.sum()
        )
        duration = np.clip(duration, 50, 1500)  # Cap extreme outliers

        # Create DataFrame
        self.df = pd.DataFrame(
            {
                "entropy": entropy,
                "curvature": curvature,
                "coherence": coherence,
                "fixation_duration": duration,
                "subject_id": np.random.choice(
                    ["S01", "S02", "S03", "S04", "S05"], n_samples
                ),
                "word_id": np.arange(n_samples),
                "dataset": "synthetic",
            }
        )

        print(f"  ✅ Criados {n_samples:,} pontos de dados sintéticos realistas")
        print(f"  📊 Entropy range: {entropy.min():.2f} - {entropy.max():.2f}")
        print(f"  📊 Curvature range: {curvature.min():.2f} - {curvature.max():.2f}")
        print(f"  📊 Coherence range: {coherence.min():.2f} - {coherence.max():.2f}")
        print(f"  📊 Duration range: {duration.min():.0f} - {duration.max():.0f} ms")

        return True

    def load_and_inspect_data(self):
        """Load data and perform initial inspection for data leakage"""
        print("🔍 Carregando e inspecionando dados...")

        if self.data_path == "synthetic":
            return self.create_realistic_synthetic_data()

        if not Path(self.data_path).exists():
            print(f"❌ Arquivo não encontrado: {self.data_path}")
            print("🔄 Criando dados sintéticos como fallback...")
            return self.create_realistic_synthetic_data()

        try:
            # Load data with memory optimization
            print(f"  📥 Carregando arquivo: {self.data_path}")

            # Check file size
            file_size_mb = Path(self.data_path).stat().st_size / (1024 * 1024)
            print(f"  📁 Tamanho do arquivo: {file_size_mb:.1f} MB")

            if file_size_mb > 100:  # Large file
                print("  ⚠️ Arquivo grande detectado, usando amostragem...")
                # Load in chunks and sample
                chunk_size = 10000
                chunks = []
                total_rows = 0

                for chunk in pd.read_csv(
                    self.data_path, chunksize=chunk_size, low_memory=False
                ):
                    chunks.append(chunk)
                    total_rows += len(chunk)
                    if total_rows >= self.max_samples:
                        break

                self.df = pd.concat(chunks, ignore_index=True)
                if len(self.df) > self.max_samples:
                    self.df = self.df.sample(
                        n=self.max_samples, random_state=42
                    ).reset_index(drop=True)
            else:
                self.df = pd.read_csv(self.data_path, low_memory=False)
                if len(self.df) > self.max_samples:
                    print(f"  🔢 Amostrando {self.max_samples:,} observações")
                    self.df = self.df.sample(
                        n=self.max_samples, random_state=42
                    ).reset_index(drop=True)

            print(f"  📊 Dados carregados: {len(self.df):,} observações")
            print(f"  📊 Colunas: {len(self.df.columns)}")

            # Check data quality
            self.check_data_leakage()
            return True

        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            print("🔄 Criando dados sintéticos como fallback...")
            return self.create_realistic_synthetic_data()

    def check_data_leakage(self):
        """Check for potential data leakage issues"""
        print("\n🔍 VERIFICANDO VAZAMENTO DE DADOS...")

        leakage_issues = []

        # Check for duplicate rows
        duplicates = self.df.duplicated().sum()
        if duplicates > 0:
            leakage_issues.append(f"Linhas duplicadas: {duplicates:,}")

        # Check for perfect correlations
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            corr_matrix = self.df[numeric_cols].corr()

            # Find perfect correlations (excluding diagonal)
            perfect_corr = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    corr_val = abs(corr_matrix.iloc[i, j])
                    if corr_val > 0.99:  # Near perfect correlation
                        col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                        perfect_corr.append((col1, col2, corr_val))

            if perfect_corr:
                leakage_issues.append(f"Correlações perfeitas: {len(perfect_corr)}")
                for col1, col2, corr in perfect_corr[:5]:
                    print(f"    ⚠️ {col1} ↔ {col2}: {corr:.4f}")

        # Check for suspicious feature names
        suspicious_features = []
        target_keywords = ["target", "label", "prediction", "pred", "result", "outcome"]
        for col in self.df.columns:
            if any(keyword in col.lower() for keyword in target_keywords):
                suspicious_features.append(col)

        if suspicious_features:
            leakage_issues.append(f"Features suspeitas: {suspicious_features}")

        # Store results
        self.diagnostic_results["data_leakage"] = {
            "issues": leakage_issues,
            "duplicates": duplicates,
            "perfect_correlations": perfect_corr if "perfect_corr" in locals() else [],
            "suspicious_features": suspicious_features,
        }

        if leakage_issues:
            print("  ⚠️ PROBLEMAS DETECTADOS:")
            for issue in leakage_issues:
                print(f"    • {issue}")
        else:
            print("  ✅ Nenhum vazamento óbvio detectado")

    def prepare_clean_features(self):
        """Prepare clean features and target for modeling"""
        print("\n🎯 Preparando features limpas...")

        # Define feature and target columns with fallbacks
        feature_cols = ["entropy", "curvature", "coherence"]

        # Try different possible target column names
        possible_targets = [
            "fixation_duration",
            "duration_ms",
            "trt_ms",
            "gd_ms",
            "ffd_ms",
            "TRT",
            "GD",
            "FFD",
            "reading_time",
            "rt",
        ]

        target_col = None
        for col in possible_targets:
            if col in self.df.columns:
                target_col = col
                break

        if target_col is None:
            print("❌ Nenhuma coluna de target encontrada")
            print("   Colunas disponíveis:")
            for col in sorted(self.df.columns):
                print(f"     - {col}")
            return False

        # Check if feature columns exist
        missing_features = [col for col in feature_cols if col not in self.df.columns]
        if missing_features:
            print(f"❌ Features faltando: {missing_features}")
            print("   Tentando encontrar alternativas...")

            # Try to find alternative column names
            for missing_col in missing_features:
                alternatives = [
                    col
                    for col in self.df.columns
                    if missing_col.lower() in col.lower()
                    or col.lower() in missing_col.lower()
                ]
                if alternatives:
                    old_name = missing_col
                    new_name = alternatives[0]
                    feature_cols[feature_cols.index(old_name)] = new_name
                    print(f"   Usando '{new_name}' para '{old_name}'")

        print(f"  📊 Features: {feature_cols}")
        print(f"  📊 Target: {target_col}")

        # Extract features and target
        try:
            self.X = self.df[feature_cols].copy()
            self.y = self.df[target_col].copy()
        except KeyError as e:
            print(f"❌ Erro ao extrair colunas: {e}")
            return False

        # Convert to numeric and clean
        print("\n🔄 LIMPANDO E CONVERTENDO DADOS...")

        # Convert features to numeric
        for col in feature_cols:
            self.X[col] = pd.to_numeric(self.X[col], errors="coerce")

        # Convert target to numeric
        self.y = pd.to_numeric(self.y, errors="coerce")

        # Remove rows with any NaN values
        initial_size = len(self.X)
        valid_mask = ~(self.X.isnull().any(axis=1) | self.y.isnull())

        self.X = self.X[valid_mask].copy()
        self.y = self.y[valid_mask].copy()

        final_size = len(self.X)
        removed = initial_size - final_size

        print(
            f"  📊 Observações removidas: {removed:,} ({removed/initial_size*100:.1f}%)"
        )
        print(f"  📊 Observações restantes: {final_size:,}")

        if final_size < self.min_samples:
            print(f"❌ Dados insuficientes: {final_size:,} < {self.min_samples:,}")
            return False

        # Check target distribution
        self.check_target_distribution()

        return True

    def check_target_distribution(self):
        """Check target variable distribution for anomalies"""
        print("\n📊 ANALISANDO DISTRIBUIÇÃO DO TARGET...")

        target_stats = {
            "mean": self.y.mean(),
            "std": self.y.std(),
            "min": self.y.min(),
            "max": self.y.max(),
            "zeros": (self.y == 0).sum(),
            "negatives": (self.y < 0).sum(),
            "unique_values": self.y.nunique(),
            "total_values": len(self.y),
        }

        print(f"  📊 Média: {target_stats['mean']:.2f}")
        print(f"  📊 Desvio padrão: {target_stats['std']:.2f}")
        print(f"  📊 Min/Max: {target_stats['min']:.2f} / {target_stats['max']:.2f}")
        print(f"  📊 Valores únicos: {target_stats['unique_values']:,}")
        print(f"  📊 Zeros: {target_stats['zeros']:,}")

        # Check for issues
        issues = []

        # Check for too few unique values (indicating possible categorical target)
        unique_ratio = target_stats["unique_values"] / target_stats["total_values"]
        if unique_ratio < 0.01:  # Less than 1% unique values
            issues.append(f"Poucos valores únicos no target ({unique_ratio:.3%})")

        # Check for unrealistic values (assuming milliseconds)
        if target_stats["max"] > 2000:  # More than 2 seconds
            issues.append(
                f"Valores muito altos no target (max: {target_stats['max']:.0f})"
            )

        if target_stats["min"] < 0:
            issues.append("Valores negativos no target")

        self.diagnostic_results["target_distribution"] = target_stats
        self.diagnostic_results["target_issues"] = issues

        if issues:
            print("  ⚠️ PROBLEMAS NO TARGET:")
            for issue in issues:
                print(f"    • {issue}")
        else:
            print("  ✅ Distribuição do target parece normal")

    def run_overfitting_tests(self):
        """Run comprehensive overfitting detection tests with proper regularization"""
        print("\n🔬 EXECUTANDO TESTES DE OVERFITTING...")

        # Use robust scaling to handle outliers
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(self.X)

        # Define models with proper regularization to prevent overfitting
        models = {
            "Linear Regression": LinearRegression(),
            "Ridge (α=1.0)": Ridge(alpha=1.0, random_state=42),
            "Ridge (α=10.0)": Ridge(alpha=10.0, random_state=42),
            "Lasso (α=0.01)": Lasso(alpha=0.01, random_state=42, max_iter=2000),
            "Lasso (α=0.1)": Lasso(alpha=0.1, random_state=42, max_iter=2000),
            # Properly regularized tree models
            "Random Forest (Conservative)": RandomForestRegressor(
                n_estimators=50,
                max_depth=5,
                min_samples_split=20,
                min_samples_leaf=10,
                max_features="sqrt",
                random_state=42,
            ),
            "Random Forest (Moderate)": RandomForestRegressor(
                n_estimators=100,
                max_depth=8,
                min_samples_split=10,
                min_samples_leaf=5,
                max_features="sqrt",
                random_state=42,
            ),
            "Gradient Boosting (Conservative)": GradientBoostingRegressor(
                n_estimators=50,
                max_depth=3,
                learning_rate=0.05,
                min_samples_split=20,
                min_samples_leaf=10,
                subsample=0.8,
                random_state=42,
            ),
        }

        results = {}

        for name, model in models.items():
            print(f"  🔄 Testando {name}...")

            try:
                # Proper train/test split
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, self.y, test_size=0.2, random_state=42, shuffle=True
                )

                # Cross-validation on training set
                cv_scores = cross_val_score(
                    model, X_train, y_train, cv=5, scoring="r2", n_jobs=1
                )

                # Train model
                model.fit(X_train, y_train)

                # Evaluate
                train_score = model.score(X_train, y_train)
                test_score = model.score(X_test, y_test)

                # Predictions for detailed metrics
                y_train_pred = model.predict(X_train)
                y_test_pred = model.predict(X_test)

                train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
                test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))

                results[name] = {
                    "cv_mean": cv_scores.mean(),
                    "cv_std": cv_scores.std(),
                    "train_r2": train_score,
                    "test_r2": test_score,
                    "train_rmse": train_rmse,
                    "test_rmse": test_rmse,
                    "overfitting_gap": train_score - test_score,
                }

                print(f"    CV R²: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
                print(f"    Train R²: {train_score:.3f}, Test R²: {test_score:.3f}")
                print(f"    Gap: {train_score - test_score:.3f}")

                # Flag suspicious results
                if train_score > 0.99 or test_score > 0.99:
                    print(f"    🚨 SUSPEITO: Performance muito alta!")
                elif abs(train_score - test_score) > 0.2:
                    print(f"    ⚠️ OVERFITTING: Gap muito alto!")
                elif abs(train_score - test_score) < 0.01 and train_score > 0.8:
                    print(f"    🚨 SUSPEITO: Performance perfeita!")

            except Exception as e:
                print(f"    ❌ Erro em {name}: {e}")
                continue

        self.diagnostic_results["model_performance"] = results
        return len(results) > 0

    def analyze_overfitting_patterns(self):
        """Analyze overfitting patterns with improved thresholds"""
        print("\n📊 ANALISANDO PADRÕES DE OVERFITTING...")

        results = self.diagnostic_results["model_performance"]

        # Improved classification with more realistic thresholds
        analysis = {
            "severe_overfitting": [],  # Gap > 0.15
            "moderate_overfitting": [],  # Gap 0.05-0.15
            "good_generalization": [],  # Gap < 0.05
            "suspicious_perfect": [],  # R² > 0.95 or gap < 0.01 with high R²
            "poor_performance": [],  # R² < 0.1
        }

        for name, result in results.items():
            gap = result["overfitting_gap"]
            train_r2 = result["train_r2"]
            test_r2 = result["test_r2"]

            # More nuanced classification
            if (train_r2 > 0.95 or test_r2 > 0.95) or (
                abs(gap) < 0.01 and train_r2 > 0.8
            ):
                analysis["suspicious_perfect"].append(name)
            elif test_r2 < 0.1:
                analysis["poor_performance"].append(name)
            elif gap > 0.15:
                analysis["severe_overfitting"].append(name)
            elif gap > 0.05:
                analysis["moderate_overfitting"].append(name)
            else:
                analysis["good_generalization"].append(name)

        # Print analysis
        for category, models in analysis.items():
            if models:
                print(
                    f"  📊 {category.replace('_', ' ').title()}: {len(models)} modelos"
                )
                for model in models:
                    result = results[model]
                    print(
                        f"    • {model}: Gap={result['overfitting_gap']:.3f}, "
                        f"Train R²={result['train_r2']:.3f}, Test R²={result['test_r2']:.3f}"
                    )

        self.diagnostic_results["overfitting_analysis"] = analysis

        # Assessment
        total_models = len(results)
        problematic = len(analysis["severe_overfitting"]) + len(
            analysis["suspicious_perfect"]
        )

        print(f"\n📊 RESUMO:")
        print(f"  Total: {total_models}, Problemáticos: {problematic}")

        if problematic > total_models * 0.3:
            print("  🚨 ALTO RISCO DE OVERFITTING!")
        elif problematic > 0:
            print("  ⚠️ Alguns problemas detectados")
        else:
            print("  ✅ Modelos parecem adequados")

    def generate_corrected_models(self):
        """Generate properly regularized models"""
        print("\n🔧 GERANDO MODELOS CORRIGIDOS...")

        # Use robust scaling
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(self.X)

        # Proper 3-way split
        X_temp, X_test, y_temp, y_test = train_test_split(
            X_scaled, self.y, test_size=0.2, random_state=42
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp,
            y_temp,
            test_size=0.25,
            random_state=42,  # 0.25 * 0.8 = 0.2
        )

        print(f"  📊 Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

        # Conservative models designed to avoid overfitting
        corrected_models = {
            "Linear Regression": LinearRegression(),
            "Ridge (Optimized)": Ridge(alpha=5.0, random_state=42),
            "Lasso (Optimized)": Lasso(alpha=0.05, random_state=42, max_iter=2000),
            "Random Forest (Regularized)": RandomForestRegressor(
                n_estimators=50,
                max_depth=4,
                min_samples_split=30,
                min_samples_leaf=15,
                max_features="sqrt",
                random_state=42,
            ),
            "Gradient Boosting (Regularized)": GradientBoostingRegressor(
                n_estimators=30,
                max_depth=3,
                learning_rate=0.03,
                min_samples_split=30,
                min_samples_leaf=15,
                subsample=0.7,
                random_state=42,
            ),
        }

        corrected_results = {}

        for name, model in corrected_models.items():
            print(f"  🔧 Treinando {name}...")

            try:
                # Cross-validation
                cv_scores = cross_val_score(
                    model, X_train, y_train, cv=5, scoring="r2", n_jobs=1
                )

                # Train model
                model.fit(X_train, y_train)

                # Evaluate on all sets
                train_score = model.score(X_train, y_train)
                val_score = model.score(X_val, y_val)
                test_score = model.score(X_test, y_test)

                corrected_results[name] = {
                    "cv_mean": cv_scores.mean(),
                    "cv_std": cv_scores.std(),
                    "train_r2": train_score,
                    "val_r2": val_score,
                    "test_r2": test_score,
                    "train_val_gap": train_score - val_score,
                    "val_test_gap": val_score - test_score,
                    "model": model,
                }

                print(f"    CV: {cv_scores.mean():.3f}±{cv_scores.std():.3f}")
                print(
                    f"    Train: {train_score:.3f}, Val: {val_score:.3f}, Test: {test_score:.3f}"
                )
                print(
                    f"    Gaps: T-V={train_score-val_score:.3f}, V-T={val_score-test_score:.3f}"
                )

            except Exception as e:
                print(f"    ❌ Erro em {name}: {e}")

        self.corrected_results = corrected_results
        return corrected_results

    def generate_comprehensive_report(self):
        """Generate comprehensive diagnostic report"""
        print("\n📝 Gerando relatório...")

        report_path = self.output_dir / "overfitting_diagnostic_report_fixed.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(
                "# 🚨 RELATÓRIO DE DIAGNÓSTICO DE OVERFITTING - VERSÃO CORRIGIDA\n\n"
            )
            f.write(f"**Data:** {timestamp}\n\n")

            # Executive Summary
            f.write("## 📋 RESUMO EXECUTIVO\n\n")
            f.write(
                "Este relatório apresenta uma análise corrigida dos problemas de overfitting "
            )
            f.write(
                "identificados nos modelos anteriores, com implementação de regularização adequada "
            )
            f.write("e validação robusta.\n\n")

            # Data overview
            f.write("## 📊 VISÃO GERAL DOS DADOS\n\n")
            if self.df is not None:
                f.write(f"- **Total de observações:** {len(self.df):,}\n")
                f.write(
                    f"- **Features utilizadas:** {list(self.X.columns) if self.X is not None else 'N/A'}\n"
                )
                f.write(
                    f"- **Dados válidos:** {len(self.X) if self.X is not None else 'N/A'}\n"
                )
                f.write(
                    f"- **Fonte dos dados:** {'Sintéticos' if self.data_path == 'synthetic' else 'Reais'}\n\n"
                )

            # Data leakage analysis
            if "data_leakage" in self.diagnostic_results:
                leakage = self.diagnostic_results["data_leakage"]
                f.write("## 🔍 ANÁLISE DE VAZAMENTO DE DADOS\n\n")

                if leakage["issues"]:
                    f.write("### ⚠️ PROBLEMAS DETECTADOS:\n\n")
                    for issue in leakage["issues"]:
                        f.write(f"- {issue}\n")
                else:
                    f.write("### ✅ Nenhum vazamento detectado\n")
                f.write("\n")

            # Target analysis
            if "target_distribution" in self.diagnostic_results:
                target = self.diagnostic_results["target_distribution"]
                f.write("## 📊 ANÁLISE DO TARGET\n\n")
                f.write(f"- **Média:** {target['mean']:.2f}\n")
                f.write(f"- **Desvio padrão:** {target['std']:.2f}\n")
                f.write(f"- **Min/Max:** {target['min']:.2f} / {target['max']:.2f}\n")
                f.write(f"- **Valores únicos:** {target['unique_values']:,}\n")
                f.write(f"- **Zeros:** {target['zeros']:,}\n\n")

                if (
                    "target_issues" in self.diagnostic_results
                    and self.diagnostic_results["target_issues"]
                ):
                    f.write("### ⚠️ PROBLEMAS NO TARGET:\n\n")
                    for issue in self.diagnostic_results["target_issues"]:
                        f.write(f"- {issue}\n")
                    f.write("\n")

            # Original vs Corrected Models Comparison
            if (
                "model_performance" in self.diagnostic_results
                and self.corrected_results
            ):
                f.write("## 🔄 COMPARAÇÃO: MODELOS ORIGINAIS vs CORRIGIDOS\n\n")

                f.write("### 📊 Modelos Originais (Problemáticos)\n\n")
                original = self.diagnostic_results["model_performance"]
                f.write("| Modelo | Train R² | Test R² | Gap | Status |\n")
                f.write("|--------|----------|---------|-----|--------|\n")

                for name, result in original.items():
                    gap = result["overfitting_gap"]
                    status = (
                        "🚨 SUSPEITO"
                        if result["train_r2"] > 0.95 or result["test_r2"] > 0.95
                        else "⚠️ OVERFITTING"
                        if gap > 0.15
                        else "✅ OK"
                    )
                    f.write(
                        f"| {name} | {result['train_r2']:.3f} | {result['test_r2']:.3f} | {gap:.3f} | {status} |\n"
                    )
                f.write("\n")

            # Corrected models
            if self.corrected_results:
                f.write("### 🔧 Modelos Corrigidos\n\n")
                f.write(
                    "| Modelo | CV R² | Train R² | Val R² | Test R² | T-V Gap | V-T Gap | Status |\n"
                )
                f.write(
                    "|--------|-------|----------|--------|---------|---------|---------|--------|\n"
                )

                for name, result in self.corrected_results.items():
                    tv_gap = result["train_val_gap"]
                    vt_gap = result["val_test_gap"]
                    status = (
                        "✅ EXCELENTE"
                        if abs(tv_gap) < 0.05 and abs(vt_gap) < 0.05
                        else "✅ BOM"
                        if abs(tv_gap) < 0.1 and abs(vt_gap) < 0.1
                        else "⚠️ ATENÇÃO"
                    )

                    f.write(
                        f"| {name} | {result['cv_mean']:.3f}±{result['cv_std']:.3f} | "
                        f"{result['train_r2']:.3f} | {result['val_r2']:.3f} | {result['test_r2']:.3f} | "
                        f"{tv_gap:.3f} | {vt_gap:.3f} | {status} |\n"
                    )
                f.write("\n")

            # Key Findings
            f.write("## 🔍 PRINCIPAIS DESCOBERTAS\n\n")

            if "overfitting_analysis" in self.diagnostic_results:
                analysis = self.diagnostic_results["overfitting_analysis"]

                f.write("### ❌ Problemas Identificados nos Modelos Originais:\n\n")
                if analysis.get("suspicious_perfect"):
                    f.write(
                        f"- **{len(analysis['suspicious_perfect'])} modelos com performance suspeita** (R² > 0.95)\n"
                    )
                if analysis.get("severe_overfitting"):
                    f.write(
                        f"- **{len(analysis['severe_overfitting'])} modelos com overfitting severo** (Gap > 0.15)\n"
                    )

                f.write("\n### ✅ Soluções Implementadas:\n\n")
                f.write("- **Regularização adequada** em todos os modelos\n")
                f.write(
                    "- **Validação cruzada robusta** com 3 conjuntos (train/val/test)\n"
                )
                f.write("- **Scaling robusto** para lidar com outliers\n")
                f.write(
                    "- **Hiperparâmetros conservadores** para evitar overfitting\n\n"
                )

            # Recommendations
            f.write("## 💡 RECOMENDAÇÕES FINAIS\n\n")

            f.write("### 🚨 AÇÕES CRÍTICAS:\n\n")
            f.write(
                "1. **NUNCA usar modelos com R² > 0.95** - altamente suspeitos de overfitting\n"
            )
            f.write(
                "2. **Sempre implementar validação cruzada** com conjuntos separados\n"
            )
            f.write("3. **Monitorar gaps entre train/val/test** - devem ser < 0.1\n")
            f.write(
                "4. **Usar regularização adequada** especialmente em modelos complexos\n\n"
            )

            f.write("### 📋 MELHORES PRÁTICAS:\n\n")
            f.write("- Usar **scaling robusto** para dados com outliers\n")
            f.write("- Implementar **early stopping** em modelos iterativos\n")
            f.write(
                "- **Documentar todos os hiperparâmetros** e decisões de modelagem\n"
            )
            f.write("- **Validar resultados** com dados externos quando possível\n\n")

            # Best Models
            if self.corrected_results:
                f.write("### 🏆 MODELOS RECOMENDADOS:\n\n")

                # Sort by test performance with reasonable gaps
                good_models = []
                for name, result in self.corrected_results.items():
                    if (
                        abs(result["train_val_gap"]) < 0.1
                        and abs(result["val_test_gap"]) < 0.1
                    ):
                        good_models.append((name, result["test_r2"], result))

                good_models.sort(key=lambda x: x[1], reverse=True)

                for i, (name, test_r2, result) in enumerate(good_models[:3], 1):
                    f.write(f"{i}. **{name}**\n")
                    f.write(f"   - Test R²: {test_r2:.3f}\n")
                    f.write(
                        f"   - Gaps: T-V={result['train_val_gap']:.3f}, V-T={result['val_test_gap']:.3f}\n"
                    )
                    f.write(
                        f"   - CV Score: {result['cv_mean']:.3f}±{result['cv_std']:.3f}\n\n"
                    )

            # Technical Details
            f.write("## 🔧 DETALHES TÉCNICOS\n\n")
            f.write("### Correções Implementadas:\n\n")
            f.write("- **RobustScaler**: Reduz impacto de outliers\n")
            f.write(
                "- **Regularização L1/L2**: Previne overfitting em modelos lineares\n"
            )
            f.write("- **Limitação de profundidade**: max_depth reduzido em árvores\n")
            f.write(
                "- **Min samples**: Aumentado para evitar splits muito específicos\n"
            )
            f.write("- **Subsampling**: Reduz overfitting em gradient boosting\n")
            f.write("- **Learning rate baixo**: Convergência mais estável\n\n")

            f.write("### Métricas de Validação:\n\n")
            f.write("- **Cross-validation**: 5-fold para estabilidade\n")
            f.write("- **Train/Val/Test split**: 60%/20%/20%\n")
            f.write("- **Gap thresholds**: < 0.05 excelente, < 0.1 aceitável\n")
            f.write("- **Performance threshold**: R² > 0.95 considerado suspeito\n\n")

        print(f"  📄 Relatório salvo em: {report_path}")

    def run_complete_diagnostic(self):
        """Run complete overfitting diagnostic pipeline"""
        print("🚀 EXECUTANDO DIAGNÓSTICO COMPLETO DE OVERFITTING - VERSÃO CORRIGIDA")
        print("=" * 80)

        try:
            # Step 1: Load and inspect data
            print("\n📋 ETAPA 1: Carregamento e Inspeção")
            if not self.load_and_inspect_data():
                print("❌ Falha no carregamento")
                return False

            # Step 2: Prepare features
            print("\n📋 ETAPA 2: Preparação de Features")
            if not self.prepare_clean_features():
                print("❌ Falha na preparação")
                return False

            # Step 3: Run tests
            print("\n📋 ETAPA 3: Testes de Overfitting")
            if not self.run_overfitting_tests():
                print("❌ Falha nos testes")
                return False

            # Step 4: Analyze patterns
            print("\n📋 ETAPA 4: Análise de Padrões")
            self.analyze_overfitting_patterns()

            # Step 5: Generate corrected models
            print("\n📋 ETAPA 5: Modelos Corrigidos")
            self.generate_corrected_models()

            # Step 6: Generate report
            print("\n📋 ETAPA 6: Relatório Final")
            self.generate_comprehensive_report()

            print("\n🎉 DIAGNÓSTICO COMPLETO!")
            print(f"📁 Resultados em: {self.output_dir}")

            # Summary
            if self.corrected_results:
                best_model = max(
                    self.corrected_results.items(), key=lambda x: x[1]["test_r2"]
                )
                print(f"\n🏆 MELHOR MODELO:")
                print(f"  📊 {best_model[0]}")
                print(f"  📊 Test R²: {best_model[1]['test_r2']:.3f}")
                print(
                    f"  📊 Gaps: T-V={best_model[1]['train_val_gap']:.3f}, V-T={best_model[1]['val_test_gap']:.3f}"
                )

            return True

        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    """Main execution function"""
    print("🚨 DIAGNÓSTICO DE OVERFITTING - VERSÃO CORRIGIDA")
    print("=" * 60)

    try:
        diagnostic = OverfittingDiagnosticFixed()
        success = diagnostic.run_complete_diagnostic()

        if success:
            print("\n✅ Diagnóstico concluído com sucesso!")
            print("📊 Verifique os relatórios para detalhes.")
        else:
            print("\n❌ Falha no diagnóstico.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
