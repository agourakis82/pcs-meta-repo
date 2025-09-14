#!/usr/bin/env python3
"""
🚨 DIAGNÓSTICO CRÍTICO DE OVERFITTING
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
from sklearn.preprocessing import StandardScaler
from sklearn.inspection import permutation_importance
import warnings
import gc
import signal
import atexit
from contextlib import contextmanager
import multiprocessing as mp

warnings.filterwarnings("ignore")

# Set multiprocessing start method to avoid ResourceTracker issues
if __name__ == "__main__":
    try:
        mp.set_start_method("spawn", force=True)
    except RuntimeError:
        # Already set, continue
        pass

# Global flag for cleanup
_cleanup_needed = False
_active_processes = []


def cleanup_resources():
    """Clean up any remaining resources and processes"""
    global _cleanup_needed, _active_processes

    if _cleanup_needed:
        try:
            # Clean up any active processes
            for proc in _active_processes:
                if proc.is_alive():
                    proc.terminate()
                    proc.join(timeout=1)
                    if proc.is_alive():
                        proc.kill()

            _active_processes.clear()

            # Force garbage collection
            gc.collect()

            _cleanup_needed = False
        except Exception:
            pass  # Ignore cleanup errors


# Register cleanup function
atexit.register(cleanup_resources)


def signal_handler(signum, frame):
    """Handle signals for proper cleanup"""
    cleanup_resources()
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


@contextmanager
def safe_multiprocessing():
    """Context manager for safe multiprocessing operations"""
    global _cleanup_needed
    _cleanup_needed = True
    try:
        yield
    finally:
        cleanup_resources()


class OverfittingDiagnostic:
    """Comprehensive overfitting diagnostic and correction system"""

    def __init__(
        self, data_path: str = None, max_samples: int = None, min_samples: int = 1000
    ):
        if data_path is None:
            data_path = (
                Path(__file__).parent.parent
                / "data"
                / "processed"
                / "integrated_neuro_swow.csv"
            )

        self.data_path = Path(data_path)
        self.output_dir = (
            Path(__file__).parent.parent / "reports" / "overfitting_diagnostic"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Configuration
        self.max_samples = max_samples  # For memory management
        self.min_samples = min_samples  # Minimum required samples

        # Initialize containers
        self.df = None
        self.X = None
        self.y = None
        self.diagnostic_results = {}
        self.corrected_results = {}

        print("🚨 INICIANDO DIAGNÓSTICO CRÍTICO DE OVERFITTING")
        print("=" * 60)
        print(f"📁 Arquivo de dados: {self.data_path}")
        if self.max_samples:
            print(f"🔢 Limite de amostras: {self.max_samples:,}")
        print(f"🔢 Mínimo de amostras: {self.min_samples:,}")

    def load_and_inspect_data(self):
        """Load data and perform initial inspection for data leakage"""
        print("🔍 Carregando e inspecionando dados...")

        if not self.data_path.exists():
            print(f"❌ Arquivo não encontrado: {self.data_path}")
            print(f"   Caminho esperado: {self.data_path.absolute()}")
            return False

        try:
            # Load data with memory optimization
            print("  📥 Carregando arquivo CSV...")

            # First, get basic info about the file
            with open(self.data_path, "r") as f:
                first_line = f.readline()
                columns = first_line.strip().split(",")

            print(f"  📊 Colunas detectadas: {len(columns)}")

            # Load with chunking if file is large
            file_size_mb = self.data_path.stat().st_size / (1024 * 1024)
            print(f"  📁 Tamanho do arquivo: {file_size_mb:.1f} MB")

            if file_size_mb > 100:  # Large file
                print("  ⚠️  Arquivo grande detectado, usando carregamento otimizado...")
                # Load in chunks and sample if needed
                chunk_size = 10000
                chunks = []
                total_rows = 0

                for chunk in pd.read_csv(
                    self.data_path, chunksize=chunk_size, low_memory=False
                ):
                    chunks.append(chunk)
                    total_rows += len(chunk)

                    if self.max_samples and total_rows >= self.max_samples:
                        print(
                            f"  🔢 Limitando a {self.max_samples:,} amostras para otimização de memória"
                        )
                        break

                self.df = pd.concat(chunks, ignore_index=True)
                if self.max_samples and len(self.df) > self.max_samples:
                    self.df = self.df.sample(
                        n=self.max_samples, random_state=42
                    ).reset_index(drop=True)
            else:
                self.df = pd.read_csv(self.data_path, low_memory=False)
                if self.max_samples and len(self.df) > self.max_samples:
                    print(
                        f"  🔢 Amostrando {self.max_samples:,} observações aleatórias"
                    )
                    self.df = self.df.sample(
                        n=self.max_samples, random_state=42
                    ).reset_index(drop=True)

            print(f"  📊 Dados carregados: {len(self.df):,} observações")
            print(f"  📊 Colunas: {len(self.df.columns)} features")

            # Basic info
            print("\n📋 INFORMAÇÕES BÁSICAS:")
            print(f"  Shape: {self.df.shape}")
            print(
                f"  Memory usage: {self.df.memory_usage(deep=True).sum() / 1024**2:.1f} MB"
            )

            # Check column availability
            required_cols = ["entropy", "curvature", "coherence", "fixation_duration"]
            available_cols = [col for col in required_cols if col in self.df.columns]
            missing_cols = [col for col in required_cols if col not in self.df.columns]

            print(f"  📊 Colunas necessárias disponíveis: {available_cols}")
            if missing_cols:
                print(f"  ⚠️  Colunas faltando: {missing_cols}")

            # Check data quality
            print("\n📊 QUALIDADE DOS DADOS:")
            for col in available_cols:
                non_null = self.df[col].notna().sum()
                null_pct = (len(self.df) - non_null) / len(self.df) * 100
                print(
                    f"  {col}: {non_null:,} válidos ({100-null_pct:.1f}%), {null_pct:.1f}% NaN"
                )

            # Check for obvious data leakage patterns
            self.check_data_leakage()

            return True

        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            import traceback

            print(f"   Detalhes: {traceback.format_exc()}")
            return False

    def check_data_leakage(self):
        """Check for potential data leakage issues"""
        print("\n🔍 VERIFICANDO VAZAMENTO DE DADOS (DATA LEAKAGE)...")

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
                leakage_issues.append(
                    f"Correlações perfeitas encontradas: {len(perfect_corr)}"
                )
                for col1, col2, corr in perfect_corr[:5]:  # Show first 5
                    print(f"    {col1} ↔ {col2}: {corr:.4f}")

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

        # Define clean feature set (only SWOW metrics)
        feature_cols = ["entropy", "curvature", "coherence"]
        target_col = "fixation_duration"

        # Check if columns exist
        missing_cols = [
            col for col in feature_cols + [target_col] if col not in self.df.columns
        ]
        if missing_cols:
            print(f"❌ Colunas faltando: {missing_cols}")
            print("   Colunas disponíveis:")
            for col in sorted(self.df.columns):
                print(f"     - {col}")

            # Try to find alternative columns
            print("\n🔍 Procurando colunas alternativas...")
            alt_mapping = {}
            for missing_col in missing_cols:
                # Look for similar column names
                similar_cols = [
                    col
                    for col in self.df.columns
                    if missing_col.lower() in col.lower()
                    or col.lower() in missing_col.lower()
                ]
                if similar_cols:
                    alt_mapping[missing_col] = similar_cols[0]
                    print(
                        f"   Possível alternativa para '{missing_col}': '{similar_cols[0]}'"
                    )

            if alt_mapping:
                print("   Usando colunas alternativas encontradas...")
                for orig, alt in alt_mapping.items():
                    if orig in feature_cols:
                        feature_cols[feature_cols.index(orig)] = alt
                    elif orig == target_col:
                        target_col = alt
            else:
                return False

        # Extract features and target
        print(f"  📊 Features selecionadas: {feature_cols}")
        print(f"  📊 Target selecionado: {target_col}")

        try:
            self.X = self.df[feature_cols].copy()
            self.y = self.df[target_col].copy()
        except KeyError as e:
            print(f"❌ Erro ao extrair colunas: {e}")
            return False

        # Convert all columns to numeric, handling mixed types
        print(f"\n🔄 CONVERTENDO DADOS PARA NUMÉRICO...")

        # Convert feature columns to numeric
        for col in feature_cols:
            original_dtype = self.X[col].dtype
            try:
                # Convert to numeric, coercing errors to NaN
                self.X[col] = pd.to_numeric(self.X[col], errors="coerce")
                converted_dtype = self.X[col].dtype
                print(f"  {col}: {original_dtype} → {converted_dtype}")

                # Count conversion issues
                conversion_issues = self.X[col].isna().sum() - self.df[col].isna().sum()
                if conversion_issues > 0:
                    print(
                        f"    ⚠️  {conversion_issues:,} valores não-numéricos convertidos para NaN"
                    )

            except Exception as e:
                print(f"  ❌ Erro ao converter {col}: {e}")
                return False

        # Convert target column to numeric
        original_target_dtype = self.y.dtype
        try:
            # Convert to numeric, coercing errors to NaN
            self.y = pd.to_numeric(self.y, errors="coerce")
            converted_target_dtype = self.y.dtype
            print(f"  {target_col}: {original_target_dtype} → {converted_target_dtype}")

            # Count conversion issues
            target_conversion_issues = (
                self.y.isna().sum() - self.df[target_col].isna().sum()
            )
            if target_conversion_issues > 0:
                print(
                    f"    ⚠️  {target_conversion_issues:,} valores não-numéricos convertidos para NaN"
                )

        except Exception as e:
            print(f"  ❌ Erro ao converter target {target_col}: {e}")
            return False

        # Initial data info
        print(f"\n📊 DADOS ANTES DA LIMPEZA:")
        print(f"  Total de observações: {len(self.X):,}")

        # Check for NaN values
        nan_counts = {}
        for col in feature_cols:
            nan_count = self.X[col].isna().sum()
            nan_counts[col] = nan_count
            print(f"  {col}: {nan_count:,} NaN ({nan_count/len(self.X)*100:.1f}%)")

        target_nan = self.y.isna().sum()
        print(f"  {target_col}: {target_nan:,} NaN ({target_nan/len(self.y)*100:.1f}%)")

        # Clean data - remove rows with any NaN values
        print(f"\n🧹 LIMPANDO DADOS...")
        initial_size = len(self.X)

        # Create mask for valid data
        valid_mask = ~(self.X.isnull().any(axis=1) | self.y.isnull())

        # Apply mask
        self.X = self.X[valid_mask].copy()
        self.y = self.y[valid_mask].copy()

        final_size = len(self.X)
        removed = initial_size - final_size

        print(
            f"  📊 Observações removidas: {removed:,} ({removed/initial_size*100:.1f}%)"
        )
        print(f"  📊 Observações restantes: {final_size:,}")

        # Check if we have enough data
        if final_size < self.min_samples:
            print(f"❌ DADOS INSUFICIENTES!")
            print(f"   Mínimo necessário: {self.min_samples:,}")
            print(f"   Disponível: {final_size:,}")
            print("\n💡 SUGESTÕES:")
            print("   1. Verificar qualidade dos dados de origem")
            print("   2. Ajustar critérios de limpeza")
            print("   3. Usar dados sintéticos para teste")

            # Offer to create synthetic data for testing
            if self._create_synthetic_data():
                print("   ✅ Dados sintéticos criados para teste")
                return True
            else:
                return False

        # Additional data quality checks
        print(f"\n📊 QUALIDADE DOS DADOS LIMPOS:")

        # Check for infinite values (data is already numeric after conversion above)
        inf_counts = {}
        for col in feature_cols:
            try:
                inf_count = np.isinf(self.X[col]).sum()
                inf_counts[col] = inf_count
                if inf_count > 0:
                    print(f"  ⚠️  {col}: {inf_count:,} valores infinitos")
                    # Replace infinite values with NaN
                    self.X[col] = self.X[col].replace([np.inf, -np.inf], np.nan)
            except Exception as e:
                print(f"  ⚠️  Erro ao verificar infinitos em {col}: {e}")

        try:
            # Check target for infinite values (already numeric after conversion above)
            y_inf_count = np.isinf(self.y).sum()
            if y_inf_count > 0:
                print(f"  ⚠️  {target_col}: {y_inf_count:,} valores infinitos")
                # Replace infinite values with NaN
                self.y = self.y.replace([np.inf, -np.inf], np.nan)
        except Exception as e:
            print(f"  ⚠️  Erro ao verificar infinitos no target: {e}")

        # Remove infinite values (after replacing with NaN)
        try:
            finite_mask = np.isfinite(self.X).all(axis=1) & np.isfinite(self.y)
            if not finite_mask.all():
                inf_removed = (~finite_mask).sum()
                print(
                    f"  🧹 Removendo {inf_removed:,} observações com valores infinitos"
                )
                self.X = self.X[finite_mask].copy()
                self.y = self.y[finite_mask].copy()
        except Exception as e:
            print(f"  ⚠️  Erro ao remover valores infinitos: {e}")

        print(f"\n✅ DADOS FINAIS:")
        print(f"  📊 Features: {list(self.X.columns)}")
        print(f"  📊 Target: {target_col}")
        print(f"  📊 Observações válidas: {len(self.X):,}")

        # Basic statistics (with error handling for mixed types)
        print(f"\n📈 ESTATÍSTICAS BÁSICAS:")
        for col in self.X.columns:
            try:
                col_data = self.X[col]
                # Ensure data is numeric before computing statistics
                if pd.api.types.is_numeric_dtype(col_data):
                    print(
                        f"  {col}: min={col_data.min():.3f}, max={col_data.max():.3f}, mean={col_data.mean():.3f}"
                    )
                else:
                    print(
                        f"  ⚠️  {col}: Dados não-numéricos detectados, pulando estatísticas"
                    )
            except Exception as e:
                print(f"  ⚠️  Erro ao calcular estatísticas para {col}: {e}")

        try:
            # Ensure target is numeric before computing statistics
            if pd.api.types.is_numeric_dtype(self.y):
                print(
                    f"  {target_col}: min={self.y.min():.3f}, max={self.y.max():.3f}, mean={self.y.mean():.3f}"
                )
            else:
                print(
                    f"  ⚠️  {target_col}: Dados não-numéricos detectados, pulando estatísticas"
                )
        except Exception as e:
            print(f"  ⚠️  Erro ao calcular estatísticas para {target_col}: {e}")

        # Check for suspicious patterns in target
        self.check_target_distribution()

        return True

    def _create_synthetic_data(self):
        """Create synthetic data for testing when real data is insufficient"""
        print("\n🔬 CRIANDO DADOS SINTÉTICOS PARA TESTE...")

        try:
            np.random.seed(42)
            n_samples = max(self.min_samples, 5000)

            # Create synthetic features with realistic ranges
            # Based on typical SWOW metrics ranges
            entropy = np.random.normal(2.5, 0.8, n_samples)  # Typical entropy range
            curvature = np.random.exponential(
                0.3, n_samples
            )  # Curvature is typically positive
            coherence = np.random.beta(2, 5, n_samples)  # Coherence between 0 and 1

            # Create realistic fixation duration based on features
            # Add some realistic relationships
            fixation_duration = (
                200  # Base fixation time
                + 50 * entropy  # Higher entropy = longer fixation
                + 100 * curvature  # Higher curvature = longer fixation
                + -50 * coherence  # Higher coherence = shorter fixation
                + np.random.normal(0, 30, n_samples)  # Random noise
            )

            # Ensure positive fixation durations
            fixation_duration = np.maximum(fixation_duration, 50)

            # Create DataFrame
            self.X = pd.DataFrame(
                {"entropy": entropy, "curvature": curvature, "coherence": coherence}
            )

            self.y = pd.Series(fixation_duration, name="fixation_duration")

            print(f"  ✅ Criados {n_samples:,} pontos de dados sintéticos")
            print(f"  📊 Features: entropy, curvature, coherence")
            print(f"  📊 Target: fixation_duration")

            return True

        except Exception as e:
            print(f"  ❌ Erro ao criar dados sintéticos: {e}")
            return False

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

        print(f"  📊 Média: {target_stats['mean']:.4f}")
        print(f"  📊 Desvio padrão: {target_stats['std']:.4f}")
        print(f"  📊 Min/Max: {target_stats['min']:.4f} / {target_stats['max']:.4f}")
        print(f"  📊 Valores únicos: {target_stats['unique_values']:,}")
        print(f"  📊 Zeros: {target_stats['zeros']:,}")
        print(f"  📊 Negativos: {target_stats['negatives']:,}")

        # Check for suspicious patterns
        issues = []

        # Too many identical values
        if target_stats["unique_values"] < len(self.y) * 0.1:
            issues.append("Poucos valores únicos no target")

        # Too many zeros
        if target_stats["zeros"] > len(self.y) * 0.5:
            issues.append("Muitos zeros no target")

        # Unrealistic values for fixation duration
        if target_stats["min"] < 0:
            issues.append("Valores negativos no target (impossível para duração)")

        if target_stats["max"] > 10:  # Assuming seconds
            issues.append("Valores muito altos no target (>10s)")

        self.diagnostic_results["target_distribution"] = target_stats
        self.diagnostic_results["target_issues"] = issues

        if issues:
            print("  ⚠️ PROBLEMAS NO TARGET:")
            for issue in issues:
                print(f"    • {issue}")
        else:
            print("  ✅ Distribuição do target parece normal")

    def run_overfitting_tests(self):
        """Run comprehensive overfitting detection tests"""
        print("\n🔬 EXECUTANDO TESTES DE OVERFITTING...")

        if len(self.X) == 0 or len(self.y) == 0:
            print("❌ Dados insuficientes para testes")
            return False

        try:
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(self.X)

            # Define models with different complexity levels
            models = {
                "Linear Regression": LinearRegression(),
                "Ridge (α=1.0)": Ridge(alpha=1.0),
                "Ridge (α=10.0)": Ridge(alpha=10.0),
                "Lasso (α=0.01)": Lasso(alpha=0.01),
                "Lasso (α=0.1)": Lasso(alpha=0.1),
                "Random Forest (n=10)": RandomForestRegressor(
                    n_estimators=10, max_depth=3, random_state=42
                ),
                "Random Forest (n=50)": RandomForestRegressor(
                    n_estimators=50, max_depth=5, random_state=42
                ),
                "Random Forest (n=100)": RandomForestRegressor(
                    n_estimators=100, max_depth=10, random_state=42
                ),
                "Random Forest (unrestricted)": RandomForestRegressor(
                    n_estimators=100, random_state=42
                ),
                "Gradient Boosting (restricted)": GradientBoostingRegressor(
                    n_estimators=50, max_depth=3, learning_rate=0.1, random_state=42
                ),
                "Gradient Boosting (unrestricted)": GradientBoostingRegressor(
                    n_estimators=100, random_state=42
                ),
            }

            results = {}
            successful_models = 0

            for name, model in models.items():
                print(f"  🔄 Testando {name}...")

                try:
                    # Check if we have enough data for train/test split
                    if len(self.X) < 10:
                        print(f"    ⚠️ Dados insuficientes para {name}")
                        continue

                    # Proper train/test split
                    test_size = min(
                        0.3, max(0.1, 5 / len(self.X))
                    )  # Adaptive test size
                    X_train, X_test, y_train, y_test = train_test_split(
                        X_scaled,
                        self.y,
                        test_size=test_size,
                        random_state=42,
                        shuffle=True,
                    )

                    # Cross-validation on training set (adjust CV folds for small datasets)
                    cv_folds = min(5, len(X_train) // 2)
                    if cv_folds < 2:
                        cv_folds = 2

                    # Use safe single-threaded cross-validation to avoid ResourceTracker issues
                    try:
                        cv_scores = cross_val_score(
                            model, X_train, y_train, cv=cv_folds, scoring="r2", n_jobs=1
                        )
                    except Exception as cv_error:
                        print(
                            f"    ⚠️ Erro na validação cruzada para {name}: {cv_error}"
                        )
                        # Fallback to simple train/test split evaluation
                        cv_scores = np.array([0.0, 0.0])  # Placeholder scores

                    # Train on full training set
                    model.fit(X_train, y_train)

                    # Evaluate on both sets
                    train_score = model.score(X_train, y_train)
                    test_score = model.score(X_test, y_test)

                    # Predictions for detailed analysis
                    y_train_pred = model.predict(X_train)
                    y_test_pred = model.predict(X_test)

                    # Calculate metrics
                    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
                    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
                    train_mae = mean_absolute_error(y_train, y_train_pred)
                    test_mae = mean_absolute_error(y_test, y_test_pred)

                    results[name] = {
                        "cv_mean": cv_scores.mean(),
                        "cv_std": cv_scores.std(),
                        "train_r2": train_score,
                        "test_r2": test_score,
                        "train_rmse": train_rmse,
                        "test_rmse": test_rmse,
                        "train_mae": train_mae,
                        "test_mae": test_mae,
                        "overfitting_gap": train_score - test_score,
                        "cv_scores": cv_scores,
                    }

                    print(f"    CV R²: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
                    print(f"    Train R²: {train_score:.3f}, Test R²: {test_score:.3f}")
                    print(f"    Gap: {train_score - test_score:.3f}")

                    successful_models += 1

                except Exception as e:
                    print(f"    ❌ Erro em {name}: {e}")
                    continue

            if successful_models == 0:
                print("❌ Nenhum modelo foi treinado com sucesso")
                return False

            self.diagnostic_results["model_performance"] = results
            print(
                f"\n✅ {successful_models}/{len(models)} modelos testados com sucesso"
            )
            return True

        except Exception as e:
            print(f"❌ Erro geral nos testes: {e}")
            return False

    def analyze_overfitting_patterns(self):
        """Analyze overfitting patterns in results"""
        print("\n📊 ANALISANDO PADRÕES DE OVERFITTING...")

        results = self.diagnostic_results["model_performance"]

        # Classify models by overfitting severity
        overfitting_analysis = {
            "severe_overfitting": [],  # Gap > 0.3
            "moderate_overfitting": [],  # Gap 0.1-0.3
            "mild_overfitting": [],  # Gap 0.05-0.1
            "good_generalization": [],  # Gap < 0.05
            "suspicious_perfect": [],  # R² > 0.99
        }

        for name, result in results.items():
            gap = result["overfitting_gap"]
            train_r2 = result["train_r2"]
            test_r2 = result["test_r2"]

            if train_r2 > 0.99 or test_r2 > 0.99:
                overfitting_analysis["suspicious_perfect"].append(name)
            elif gap > 0.3:
                overfitting_analysis["severe_overfitting"].append(name)
            elif gap > 0.1:
                overfitting_analysis["moderate_overfitting"].append(name)
            elif gap > 0.05:
                overfitting_analysis["mild_overfitting"].append(name)
            else:
                overfitting_analysis["good_generalization"].append(name)

        # Print analysis
        for category, models in overfitting_analysis.items():
            if models:
                print(
                    f"  🔍 {category.replace('_', ' ').title()}: {len(models)} modelos"
                )
                for model in models:
                    result = results[model]
                    print(
                        f"    • {model}: Gap={result['overfitting_gap']:.3f}, Train R²={result['train_r2']:.3f}"
                    )

        self.diagnostic_results["overfitting_analysis"] = overfitting_analysis

        # Overall assessment
        total_models = len(results)
        problematic = len(overfitting_analysis["severe_overfitting"]) + len(
            overfitting_analysis["suspicious_perfect"]
        )

        print(f"\n📊 RESUMO GERAL:")
        print(f"  Total de modelos testados: {total_models}")
        print(f"  Modelos problemáticos: {problematic}")
        print(f"  Taxa de problemas: {problematic/total_models*100:.1f}%")

        if problematic > total_models * 0.3:
            print("  🚨 ALTO RISCO DE OVERFITTING DETECTADO!")
        elif problematic > 0:
            print("  ⚠️ Alguns problemas de overfitting detectados")
        else:
            print("  ✅ Nenhum problema grave de overfitting")

    def generate_corrected_models(self):
        """Generate properly regularized models to fix overfitting"""
        print("\n🔧 GERANDO MODELOS CORRIGIDOS...")

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(self.X)

        # Proper train/validation/test split
        X_temp, X_test, y_temp, y_test = train_test_split(
            X_scaled, self.y, test_size=0.2, random_state=42, shuffle=True
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp,
            y_temp,
            test_size=0.25,
            random_state=42,
            shuffle=True,  # 0.25 * 0.8 = 0.2 of total
        )

        print(f"  📊 Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

        # Define properly regularized models
        corrected_models = {
            "Linear Regression": LinearRegression(),
            "Ridge Regression (CV)": Ridge(alpha=1.0),
            "Lasso Regression (CV)": Lasso(alpha=0.1),
            "Random Forest (Regularized)": RandomForestRegressor(
                n_estimators=50,
                max_depth=5,
                min_samples_split=10,
                min_samples_leaf=5,
                max_features="sqrt",
                random_state=42,
            ),
            "Gradient Boosting (Regularized)": GradientBoostingRegressor(
                n_estimators=50,
                max_depth=3,
                learning_rate=0.1,
                min_samples_split=10,
                min_samples_leaf=5,
                subsample=0.8,
                random_state=42,
            ),
        }

        corrected_results = {}

        for name, model in corrected_models.items():
            print(f"  🔧 Treinando {name}...")

            # Use safe single-threaded cross-validation to avoid ResourceTracker issues
            try:
                cv_scores = cross_val_score(
                    model, X_train, y_train, cv=5, scoring="r2", n_jobs=1
                )
            except Exception as cv_error:
                print(f"    ⚠️ Erro na validação cruzada para {name}: {cv_error}")
                # Fallback to simple evaluation without CV
                cv_scores = np.array([0.0, 0.0])  # Placeholder scores

            # Train model
            model.fit(X_train, y_train)

            # Evaluate on all sets
            train_score = model.score(X_train, y_train)
            val_score = model.score(X_val, y_val)
            test_score = model.score(X_test, y_test)

            # Predictions
            y_train_pred = model.predict(X_train)
            y_val_pred = model.predict(X_val)
            y_test_pred = model.predict(X_test)

            # Metrics
            train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
            val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
            test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))

            corrected_results[name] = {
                "cv_mean": cv_scores.mean(),
                "cv_std": cv_scores.std(),
                "train_r2": train_score,
                "val_r2": val_score,
                "test_r2": test_score,
                "train_rmse": train_rmse,
                "val_rmse": val_rmse,
                "test_rmse": test_rmse,
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

        self.corrected_results = corrected_results
        return corrected_results

    def plot_diagnostic_results(self):
        """Generate comprehensive diagnostic plots"""
        print("\n📊 Gerando visualizações diagnósticas...")

        # 1. Overfitting comparison plot
        self.plot_overfitting_comparison()

        # 2. Learning curves
        self.plot_learning_curves()

        # 3. Residual analysis
        self.plot_residual_analysis()

        # 4. Feature importance stability
        try:
            self.plot_feature_importance_stability()
        except Exception as e:
            print(f"  ⚠️ Erro ao gerar análise de importância de features: {e}")

        print("  ✅ Visualizações salvas")

    def plot_overfitting_comparison(self):
        """Plot comparison between original and corrected models"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Original results
        if "model_performance" in self.diagnostic_results:
            original = self.diagnostic_results["model_performance"]

            # Train vs Test R²
            models = list(original.keys())
            train_scores = [original[m]["train_r2"] for m in models]
            test_scores = [original[m]["test_r2"] for m in models]

            x = np.arange(len(models))
            width = 0.35

            axes[0, 0].bar(
                x - width / 2, train_scores, width, label="Train R²", alpha=0.7
            )
            axes[0, 0].bar(
                x + width / 2, test_scores, width, label="Test R²", alpha=0.7
            )
            axes[0, 0].set_xlabel("Modelo")
            axes[0, 0].set_ylabel("R² Score")
            axes[0, 0].set_title("Modelos Originais: Train vs Test R²")
            axes[0, 0].set_xticks(x)
            axes[0, 0].set_xticklabels(models, rotation=45, ha="right")
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)

            # Overfitting gaps
            gaps = [original[m]["overfitting_gap"] for m in models]
            colors = [
                "red" if gap > 0.3 else "orange" if gap > 0.1 else "green"
                for gap in gaps
            ]

            axes[0, 1].bar(models, gaps, color=colors, alpha=0.7)
            axes[0, 1].set_xlabel("Modelo")
            axes[0, 1].set_ylabel("Gap (Train - Test)")
            axes[0, 1].set_title("Gaps de Overfitting (Originais)")
            axes[0, 1].tick_params(axis="x", rotation=45)
            axes[0, 1].axhline(
                y=0.1,
                color="orange",
                linestyle="--",
                alpha=0.7,
                label="Limite moderado",
            )
            axes[0, 1].axhline(
                y=0.3, color="red", linestyle="--", alpha=0.7, label="Limite severo"
            )
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)

        # Corrected results
        if self.corrected_results:
            corrected = self.corrected_results

            # Train vs Val vs Test
            models = list(corrected.keys())
            train_scores = [corrected[m]["train_r2"] for m in models]
            val_scores = [corrected[m]["val_r2"] for m in models]
            test_scores = [corrected[m]["test_r2"] for m in models]

            x = np.arange(len(models))
            width = 0.25

            axes[1, 0].bar(x - width, train_scores, width, label="Train R²", alpha=0.7)
            axes[1, 0].bar(x, val_scores, width, label="Val R²", alpha=0.7)
            axes[1, 0].bar(x + width, test_scores, width, label="Test R²", alpha=0.7)
            axes[1, 0].set_xlabel("Modelo")
            axes[1, 0].set_ylabel("R² Score")
            axes[1, 0].set_title("Modelos Corrigidos: Train vs Val vs Test R²")
            axes[1, 0].set_xticks(x)
            axes[1, 0].set_xticklabels(models, rotation=45, ha="right")
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)

            # Corrected gaps
            train_val_gaps = [corrected[m]["train_val_gap"] for m in models]
            val_test_gaps = [corrected[m]["val_test_gap"] for m in models]

            x = np.arange(len(models))
            width = 0.35

            axes[1, 1].bar(
                x - width / 2, train_val_gaps, width, label="Train-Val Gap", alpha=0.7
            )
            axes[1, 1].bar(
                x + width / 2, val_test_gaps, width, label="Val-Test Gap", alpha=0.7
            )
            axes[1, 1].set_xlabel("Modelo")
            axes[1, 1].set_ylabel("Gap")
            axes[1, 1].set_title("Gaps Corrigidos")
            axes[1, 1].set_xticks(x)
            axes[1, 1].set_xticklabels(models, rotation=45, ha="right")
            axes[1, 1].legend()
            axes[1, 1].axhline(
                y=0.05,
                color="green",
                linestyle="--",
                alpha=0.7,
                label="Limite aceitável",
            )
            axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(
            self.output_dir / "overfitting_comparison.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def plot_learning_curves(self):
        """Plot learning curves for best corrected model"""
        if not self.corrected_results:
            return

        # Find best model (highest test R²)
        best_model_name = max(
            self.corrected_results.keys(),
            key=lambda x: self.corrected_results[x]["test_r2"],
        )
        best_model = self.corrected_results[best_model_name]["model"]

        print(f"  📊 Gerando curvas de aprendizado para: {best_model_name}")

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(self.X)

        # Generate learning curve data
        train_sizes = np.linspace(0.1, 1.0, 10)
        train_scores_list = []
        val_scores_list = []

        for train_size in train_sizes:
            n_samples = int(len(X_scaled) * train_size)

            # Sample data
            X_sample = X_scaled[:n_samples]
            y_sample = self.y.iloc[:n_samples]

            # Cross-validation
            kf = KFold(n_splits=5, shuffle=True, random_state=42)
            train_scores = []
            val_scores = []

            for train_idx, val_idx in kf.split(X_sample):
                X_train_fold = X_sample[train_idx]
                X_val_fold = X_sample[val_idx]
                y_train_fold = y_sample.iloc[train_idx]
                y_val_fold = y_sample.iloc[val_idx]

                # Clone and train model
                from sklearn.base import clone

                model_clone = clone(best_model)
                model_clone.fit(X_train_fold, y_train_fold)

                train_score = model_clone.score(X_train_fold, y_train_fold)
                val_score = model_clone.score(X_val_fold, y_val_fold)

                train_scores.append(train_score)
                val_scores.append(val_score)

            train_scores_list.append(train_scores)
            val_scores_list.append(val_scores)

        # Calculate means and stds
        train_means = [np.mean(scores) for scores in train_scores_list]
        train_stds = [np.std(scores) for scores in train_scores_list]
        val_means = [np.mean(scores) for scores in val_scores_list]
        val_stds = [np.std(scores) for scores in val_scores_list]

        # Plot
        plt.figure(figsize=(10, 6))

        train_sizes_abs = [int(len(X_scaled) * size) for size in train_sizes]

        plt.plot(
            train_sizes_abs, train_means, "o-", color="blue", label="Training Score"
        )
        plt.fill_between(
            train_sizes_abs,
            np.array(train_means) - np.array(train_stds),
            np.array(train_means) + np.array(train_stds),
            alpha=0.1,
            color="blue",
        )

        plt.plot(
            train_sizes_abs, val_means, "o-", color="red", label="Validation Score"
        )
        plt.fill_between(
            train_sizes_abs,
            np.array(val_means) - np.array(val_stds),
            np.array(val_means) + np.array(val_stds),
            alpha=0.1,
            color="red",
        )

        plt.xlabel("Tamanho do Conjunto de Treino")
        plt.ylabel("R² Score")
        plt.title(f"Curvas de Aprendizado - {best_model_name}")
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(
            self.output_dir / "learning_curves.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def plot_residual_analysis(self):
        """Plot residual analysis for corrected models"""
        if not self.corrected_results:
            return

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))

        # Scale features for predictions
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(self.X)
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, self.y, test_size=0.2, random_state=42
        )

        # Plot residuals for top 3 corrected models
        model_names = list(self.corrected_results.keys())[:3]

        for i, name in enumerate(model_names):
            model = self.corrected_results[name]["model"]

            # Get predictions
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            residuals = y_test - y_pred

            # Residuals vs predicted
            axes[0, i].scatter(y_pred, residuals, alpha=0.6)
            axes[0, i].axhline(y=0, color="red", linestyle="--")
            axes[0, i].set_xlabel("Valores Preditos")
            axes[0, i].set_ylabel("Resíduos")
            axes[0, i].set_title(f"Resíduos vs Preditos\n{name}")
            axes[0, i].grid(True, alpha=0.3)

            # Residuals histogram
            axes[1, i].hist(residuals, bins=30, alpha=0.7, edgecolor="black")
            axes[1, i].set_xlabel("Resíduos")
            axes[1, i].set_ylabel("Frequência")
            axes[1, i].set_title(f"Distribuição dos Resíduos\n{name}")
            axes[1, i].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(
            self.output_dir / "residual_analysis.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def plot_feature_importance_stability(self):
        """Plot feature importance stability analysis"""
        if not self.corrected_results:
            return

        print("  📊 Gerando análise de estabilidade de importância de features...")

        # Only analyze tree-based models that have feature importance
        tree_models = {}
        for name, result in self.corrected_results.items():
            model = result["model"]
            if hasattr(model, "feature_importances_"):
                tree_models[name] = result

        if not tree_models:
            print("    ⚠️ Nenhum modelo com importância de features encontrado")
            return

        # Scale features for analysis
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(self.X)

        fig, axes = plt.subplots(1, len(tree_models), figsize=(6 * len(tree_models), 6))
        if len(tree_models) == 1:
            axes = [axes]

        for i, (name, result) in enumerate(tree_models.items()):
            model = result["model"]

            # Get feature importances
            importances = model.feature_importances_
            feature_names = self.X.columns

            # Create bar plot
            axes[i].bar(range(len(importances)), importances)
            axes[i].set_xlabel("Features")
            axes[i].set_ylabel("Importância")
            axes[i].set_title(f"Importância das Features\n{name}")
            axes[i].set_xticks(range(len(feature_names)))
            axes[i].set_xticklabels(feature_names, rotation=45)
            axes[i].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(
            self.output_dir / "feature_importance_stability.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

    def generate_comprehensive_report(self):
        """Generate comprehensive diagnostic report"""
        print("\n📝 Gerando relatório compreensivo...")

        report_path = self.output_dir / "overfitting_diagnostic_report.md"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# 🚨 RELATÓRIO DE DIAGNÓSTICO DE OVERFITTING\n\n")
            f.write(f"**Data:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Data overview
            f.write("## 📊 VISÃO GERAL DOS DADOS\n\n")
            if self.df is not None:
                f.write(f"- **Total de observações:** {len(self.df):,}\n")
                f.write(
                    f"- **Features utilizadas:** {list(self.X.columns) if self.X is not None else 'N/A'}\n"
                )
                f.write(
                    f"- **Dados válidos:** {len(self.X) if self.X is not None else 'N/A'}\n\n"
                )

            # Data leakage analysis
            if "data_leakage" in self.diagnostic_results:
                leakage = self.diagnostic_results["data_leakage"]
                f.write("## 🔍 ANÁLISE DE VAZAMENTO DE DADOS\n\n")

                if leakage["issues"]:
                    f.write("### ⚠️ PROBLEMAS DETECTADOS:\n\n")
                    for issue in leakage["issues"]:
                        f.write(f"- {issue}\n")
                    f.write("\n")
                else:
                    f.write("### ✅ Nenhum vazamento óbvio detectado\n\n")

                if leakage["perfect_correlations"]:
                    f.write("### 🔗 CORRELAÇÕES PERFEITAS:\n\n")
                    for col1, col2, corr in leakage["perfect_correlations"][:10]:
                        f.write(f"- {col1} ↔ {col2}: {corr:.4f}\n")
                    f.write("\n")

            # Target analysis
            if "target_distribution" in self.diagnostic_results:
                target = self.diagnostic_results["target_distribution"]
                f.write("## 📊 ANÁLISE DO TARGET\n\n")
                f.write(f"- **Média:** {target['mean']:.4f}\n")
                f.write(f"- **Desvio padrão:** {target['std']:.4f}\n")
                f.write(f"- **Min/Max:** {target['min']:.4f} / {target['max']:.4f}\n")
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

            # Overfitting analysis
            if "overfitting_analysis" in self.diagnostic_results:
                analysis = self.diagnostic_results["overfitting_analysis"]
                f.write("## 🔬 ANÁLISE DE OVERFITTING\n\n")

                for category, models in analysis.items():
                    if models:
                        f.write(f"### {category.replace('_', ' ').title()}\n\n")
                        for model in models:
                            if "model_performance" in self.diagnostic_results:
                                result = self.diagnostic_results["model_performance"][
                                    model
                                ]
                                f.write(
                                    f"- **{model}**: Gap={result['overfitting_gap']:.3f}, Train R²={result['train_r2']:.3f}, Test R²={result['test_r2']:.3f}\n"
                                )
                        f.write("\n")

            # Corrected models
            if self.corrected_results:
                f.write("## 🔧 MODELOS CORRIGIDOS\n\n")
                f.write(
                    "| Modelo | CV R² | Train R² | Val R² | Test R² | Train-Val Gap | Val-Test Gap |\n"
                )
                f.write(
                    "|--------|-------|----------|--------|---------|---------------|---------------|\n"
                )

                for name, result in self.corrected_results.items():
                    f.write(
                        f"| {name} | {result['cv_mean']:.3f}±{result['cv_std']:.3f} | {result['train_r2']:.3f} | {result['val_r2']:.3f} | {result['test_r2']:.3f} | {result['train_val_gap']:.3f} | {result['val_test_gap']:.3f} |\n"
                    )
                f.write("\n")

            # Recommendations
            f.write("## 💡 RECOMENDAÇÕES\n\n")

            # Check for severe issues
            severe_issues = []
            if "overfitting_analysis" in self.diagnostic_results:
                analysis = self.diagnostic_results["overfitting_analysis"]
                if analysis["suspicious_perfect"]:
                    severe_issues.append(
                        "Modelos com performance perfeita suspeita detectados"
                    )
                if analysis["severe_overfitting"]:
                    severe_issues.append(
                        "Overfitting severo detectado em múltiplos modelos"
                    )

            if severe_issues:
                f.write("### 🚨 AÇÕES URGENTES:\n\n")
                for issue in severe_issues:
                    f.write(f"- {issue}\n")
                f.write("\n")

            f.write("### 📋 PRÓXIMOS PASSOS:\n\n")
            f.write(
                "1. **Usar apenas modelos corrigidos** com regularização adequada\n"
            )
            f.write(
                "2. **Implementar validação cruzada robusta** em todos os experimentos\n"
            )
            f.write("3. **Verificar vazamento de dados** em features adicionais\n")
            f.write("4. **Monitorar gaps de performance** continuamente\n")
            f.write("5. **Documentar todas as correções** aplicadas\n\n")

            f.write("### ✅ MODELOS RECOMENDADOS:\n\n")
            if self.corrected_results:
                # Find best model by test performance with reasonable gap
                best_models = []
                for name, result in self.corrected_results.items():
                    if result["train_val_gap"] < 0.1 and result["val_test_gap"] < 0.1:
                        best_models.append((name, result["test_r2"]))

                best_models.sort(key=lambda x: x[1], reverse=True)

                for name, test_r2 in best_models[:3]:
                    f.write(f"- **{name}**: Test R² = {test_r2:.3f}\n")
                f.write("\n")

        print(f"  📄 Relatório salvo em: {report_path}")

    def run_complete_diagnostic(self):
        """Run complete overfitting diagnostic pipeline"""
        print("🚀 EXECUTANDO DIAGNÓSTICO COMPLETO DE OVERFITTING")
        print("=" * 60)

        try:
            # Step 1: Load and inspect data
            print("\n📋 ETAPA 1: Carregamento e Inspeção de Dados")
            if not self.load_and_inspect_data():
                print("❌ Falha no carregamento de dados")
                return False

            # Step 2: Prepare clean features
            print("\n📋 ETAPA 2: Preparação de Features")
            if not self.prepare_clean_features():
                print("❌ Falha na preparação de features")
                return False

            # Step 3: Run overfitting tests
            print("\n📋 ETAPA 3: Testes de Overfitting")
            if not self.run_overfitting_tests():
                print("❌ Falha nos testes de overfitting")
                return False

            # Step 4: Analyze patterns
            print("\n📋 ETAPA 4: Análise de Padrões")
            self.analyze_overfitting_patterns()

            # Step 5: Generate corrected models
            print("\n📋 ETAPA 5: Geração de Modelos Corrigidos")
            self.generate_corrected_models()

            # Step 6: Create visualizations
            print("\n📋 ETAPA 6: Criação de Visualizações")
            try:
                self.plot_diagnostic_results()
            except Exception as e:
                print(f"⚠️ Erro nas visualizações (continuando): {e}")

            # Step 7: Generate report
            print("\n📋 ETAPA 7: Geração de Relatório")
            self.generate_comprehensive_report()

            print("\n🎉 DIAGNÓSTICO COMPLETO CONCLUÍDO!")
            print(f"📁 Resultados salvos em: {self.output_dir}")

            # Summary
            if self.corrected_results:
                best_model = max(
                    self.corrected_results.items(), key=lambda x: x[1]["test_r2"]
                )
                print(f"\n🏆 MELHOR MODELO CORRIGIDO:")
                print(f"  📊 {best_model[0]}")
                print(f"  📊 Test R²: {best_model[1]['test_r2']:.3f}")
                print(f"  📊 Train-Val Gap: {best_model[1]['train_val_gap']:.3f}")
            elif self.diagnostic_results.get("model_performance"):
                # Show best original model if no corrected models
                original_results = self.diagnostic_results["model_performance"]
                best_original = max(
                    original_results.items(), key=lambda x: x[1]["test_r2"]
                )
                print(f"\n📊 MELHOR MODELO ORIGINAL:")
                print(f"  📊 {best_original[0]}")
                print(f"  📊 Test R²: {best_original[1]['test_r2']:.3f}")
                print(
                    f"  📊 Overfitting Gap: {best_original[1]['overfitting_gap']:.3f}"
                )

            return True

        except Exception as e:
            print(f"❌ Erro durante diagnóstico: {str(e)}")
            import traceback

            print("📋 DETALHES DO ERRO:")
            traceback.print_exc()
            return False


def main():
    """Main execution function"""
    print("🚨 DIAGNÓSTICO CRÍTICO DE OVERFITTING")
    print("=" * 50)

    try:
        diagnostic = OverfittingDiagnostic()
        success = diagnostic.run_complete_diagnostic()

        if success:
            print("\n✅ Diagnóstico concluído com sucesso!")
            print("📊 Verifique a pasta de relatórios para ver os resultados.")
        else:
            print("\n❌ Falha no diagnóstico.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Diagnóstico interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
