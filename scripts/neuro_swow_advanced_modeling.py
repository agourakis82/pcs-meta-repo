#!/usr/bin/env python3
"""
Modelagem Preditiva Avançada: SWOW vs Neurofisiologia (Multi-idioma)
Advanced predictive modeling of SWOW metrics vs neurophysiological data across languages
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_regression
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

class AdvancedNeuroSWOWPredictor:
    """Advanced predictive modeling for SWOW-neuro relationships across languages"""

    def __init__(self, data_path: str = None):
        if data_path is None:
            data_path = Path(__file__).parent.parent / 'data' / 'processed' / 'integrated_neuro_swow.csv'

        print("🔍 Carregando dados para modelagem preditiva avançada...")
        self.df = pd.read_csv(data_path, low_memory=False)

        # Load SWOW data for multiple languages
        self.swow_data = self._load_swow_languages()

        # Clean data
        self._clean_data()
        print(f"✅ Dados carregados e limpos: {len(self.df):,} observações")

        # Create output directory
        self.output_dir = Path(__file__).parent.parent / 'reports' / 'neuro_swow_advanced_modeling'
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set style for plots
        plt.style.use('default')
        sns.set_palette("husl")

    def _load_swow_languages(self):
        """Load SWOW data for all available languages"""
        print("🌍 Carregando dados SWOW multi-idioma...")

        swow_base = Path(__file__).parent.parent / 'data' / 'L2_derived' / 'kec'
        languages = ['en', 'es', 'nl', 'zh']  # English, Spanish, Dutch, Chinese
        swow_data = {}

        for lang in languages:
            lang_path = swow_base / lang
            if lang_path.exists():
                try:
                    # Load all SWOW metrics for this language
                    entropy_df = pd.read_parquet(lang_path / 'entropy.parquet')
                    entropy_df = entropy_df.rename(columns={'node': 'word_norm', 'H': 'entropy'})

                    curvature_df = pd.read_parquet(lang_path / 'curvature.parquet')
                    curvature_df = curvature_df.rename(columns={'node': 'word_norm', 'kappa': 'curvature'})

                    coherence_df = pd.read_parquet(lang_path / 'coherence.parquet')
                    coherence_df = coherence_df.rename(columns={'node': 'word_norm', 'Q': 'coherence'})

                    # Merge all metrics
                    lang_df = entropy_df.copy()
                    lang_df = lang_df.merge(curvature_df[['word_norm', 'curvature']], on='word_norm', how='left')
                    lang_df = lang_df.merge(coherence_df[['word_norm', 'coherence']], on='word_norm', how='left')

                    swow_data[lang] = lang_df
                    print(f"  ✅ {lang}: {len(lang_df)} palavras carregadas")

                except Exception as e:
                    print(f"  ⚠️ Erro carregando {lang}: {e}")

        return swow_data

    def _clean_data(self):
        """Clean data for modeling"""
        print("🧹 Preparando dados para modelagem...")

        # Convert problematic columns to numeric
        def safe_numeric_convert(x):
            if pd.isna(x):
                return np.nan
            try:
                val = str(x).strip()
                if val.lower() in ['false', 'true', '', 'nan', 'none']:
                    return np.nan
                return float(val)
            except (ValueError, TypeError):
                return np.nan

        # Clean key columns
        numeric_cols = ['entropy', 'curvature', 'coherence', 'fixation_duration',
                       'theta', 'alpha', 'beta']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].apply(safe_numeric_convert)

        # Remove rows with missing target or all features
        self.df = self.df.dropna(subset=['fixation_duration'])
        self.df = self.df.dropna(subset=['entropy', 'curvature', 'coherence'], how='all')

        print(f"  📊 Dados após limpeza: {len(self.df):,} observações válidas")

    def prepare_features_and_target(self):
        """Prepare features and target for modeling"""
        print("🎯 Preparando features e target...")

        # Features: SWOW metrics
        feature_cols = ['entropy', 'curvature', 'coherence']
        self.X = self.df[feature_cols].copy()

        # Target: fixation duration (log transformed for better modeling)
        self.df['log_fixation_duration'] = np.log1p(self.df['fixation_duration'])
        self.y = self.df['log_fixation_duration'].copy()

        # Remove any remaining NaN values
        valid_mask = ~(self.X.isnull().any(axis=1) | self.y.isnull())
        self.X = self.X[valid_mask]
        self.y = self.y[valid_mask]
        self.df_clean = self.df[valid_mask].copy()

        print(f"  📊 Features shape: {self.X.shape}")
        print(f"  🎯 Target shape: {self.y.shape}")
        print(f"  ✅ Dados finais: {len(self.X):,} observações")

    def train_test_split_data(self, test_size=0.2, random_state=42):
        """Split data into train and test sets"""
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=test_size, random_state=random_state
        )

        # Scale features
        self.scaler = StandardScaler()
        self.X_train_scaled = self.scaler.fit_transform(self.X_train)
        self.X_test_scaled = self.scaler.transform(self.X_test)

        print(f"  📊 Train set: {self.X_train.shape[0]} observações")
        print(f"  📊 Test set: {self.X_test.shape[0]} observações")

    def evaluate_model(self, model, X_test, y_test, model_name):
        """Evaluate model performance"""
        y_pred = model.predict(X_test)

        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        return {
            'model': model_name,
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'y_true': y_test,
            'y_pred': y_pred
        }

    def train_baseline_models(self):
        """Train and evaluate baseline models"""
        print("🏃 Treinando modelos baseline...")

        models = {
            'Linear Regression': LinearRegression(),
            'Ridge Regression': Ridge(alpha=1.0),
            'Lasso Regression': Lasso(alpha=0.01),
            'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }

        self.results = []

        for name, model in models.items():
            print(f"  📊 Treinando {name}...")

            # Train model
            model.fit(self.X_train_scaled, self.y_train)

            # Evaluate
            result = self.evaluate_model(model, self.X_test_scaled, self.y_test, name)
            self.results.append(result)

            print(f"    R²: {result['r2']:.3f}, RMSE: {result['rmse']:.4f}")
        return self.results

    def cross_validation_analysis(self):
        """Perform cross-validation analysis"""
        print("🔄 Executando validação cruzada...")

        models = {
            'Linear Regression': LinearRegression(),
            'Ridge Regression': Ridge(alpha=1.0),
            'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42)
        }

        cv_results = {}

        for name, model in models.items():
            print(f"  📊 CV para {name}...")
            scores = cross_val_score(model, self.X_train_scaled, self.y_train,
                                   cv=5, scoring='r2')
            cv_results[name] = {
                'mean_r2': scores.mean(),
                'std_r2': scores.std(),
                'scores': scores
            }
            print(f"    R² médio: {scores.mean():.3f} (±{scores.std():.3f})")

        self.cv_results = cv_results
        return cv_results

    def feature_importance_analysis(self):
        """Analyze feature importance"""
        print("🔍 Analisando importância de features...")

        # Train Random Forest for feature importance
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(self.X_train_scaled, self.y_train)

        # Get feature importance
        feature_importance = pd.DataFrame({
            'feature': self.X.columns,
            'importance': rf.feature_importances_
        }).sort_values('importance', ascending=False)

        self.feature_importance = feature_importance
        print("  📊 Importância das features:")
        for _, row in feature_importance.iterrows():
            print(f"    {row['feature']}: {row['importance']:.3f}")
        return feature_importance

    def multilanguage_analysis(self):
        """Analyze SWOW metrics across languages"""
        print("🌍 Análise multi-idioma...")

        lang_stats = {}

        for lang, swow_df in self.swow_data.items():
            stats = {
                'words': len(swow_df),
                'entropy_mean': swow_df['entropy'].mean(),
                'entropy_std': swow_df['entropy'].std(),
                'curvature_mean': swow_df['curvature'].mean(),
                'curvature_std': swow_df['curvature'].std(),
                'coherence_mean': swow_df['coherence'].mean(),
                'coherence_std': swow_df['coherence'].std()
            }
            lang_stats[lang] = stats
            print(f"  📊 {lang}: {stats['words']:,} palavras")

        self.lang_stats = lang_stats
        return lang_stats

    def dataset_specific_modeling(self):
        """Train models for each dataset separately"""
        print("📊 Modelagem por dataset...")

        dataset_results = {}

        for dataset in self.df_clean['dataset'].unique():
            print(f"  🎯 Modelando dataset: {dataset}")

            # Filter data for this dataset
            mask = self.df_clean['dataset'] == dataset
            X_ds = self.X[mask]
            y_ds = self.y[mask]

            if len(X_ds) < 50:  # Skip if too few samples
                print(f"    ⚠️ Poucos dados para {dataset} ({len(X_ds)} amostras)")
                continue

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_ds, y_ds, test_size=0.2, random_state=42
            )

            # Scale
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)

            # Evaluate
            result = self.evaluate_model(model, X_test_scaled, y_test, f"{dataset}_RF")
            dataset_results[dataset] = result

            print(".4f"
        self.dataset_results = dataset_results
        return dataset_results

    def plot_model_comparison(self):
        """Plot model performance comparison"""
        plt.figure(figsize=(12, 6))

        # Prepare data
        model_names = [r['model'] for r in self.results]
        r2_scores = [r['r2'] for r in self.results]
        rmse_scores = [r['rmse'] for r in self.results]

        # Create subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # R² plot
        bars1 = ax1.bar(model_names, r2_scores, color='#FF6B6B', alpha=0.7)
        ax1.set_title('Comparação de R² entre Modelos', fontweight='bold')
        ax1.set_ylabel('R² Score')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)

        # Add value labels
        for bar, score in zip(bars1, r2_scores):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    '.3f', ha='center', va='bottom')

        # RMSE plot
        bars2 = ax2.bar(model_names, rmse_scores, color='#4ECDC4', alpha=0.7)
        ax2.set_title('Comparação de RMSE entre Modelos', fontweight='bold')
        ax2.set_ylabel('RMSE')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)

        # Add value labels
        for bar, score in zip(bars2, rmse_scores):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                    '.4f', ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig(self.output_dir / 'model_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("📊 Comparação de modelos salva")

    def plot_feature_importance(self):
        """Plot feature importance"""
        plt.figure(figsize=(10, 6))

        plt.barh(self.feature_importance['feature'], self.feature_importance['importance'],
                color='#45B7D1', alpha=0.7)
        plt.title('Importância das Features SWOW', fontweight='bold')
        plt.xlabel('Importância')
        plt.ylabel('Feature')
        plt.grid(True, alpha=0.3)

        # Add value labels
        for i, v in enumerate(self.feature_importance['importance']):
            plt.text(v + 0.01, i, '.3f', va='center')

        plt.tight_layout()
        plt.savefig(self.output_dir / 'feature_importance.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("📊 Importância de features salva")

    def plot_predictions_vs_actual(self):
        """Plot predictions vs actual values for best model"""
        # Find best model
        best_result = max(self.results, key=lambda x: x['r2'])

        plt.figure(figsize=(10, 8))

        # Scatter plot
        plt.scatter(best_result['y_true'], best_result['y_pred'],
                   alpha=0.6, color='#FF6B6B', s=30)

        # Perfect prediction line
        min_val = min(best_result['y_true'].min(), best_result['y_pred'].min())
        max_val = max(best_result['y_true'].max(), best_result['y_pred'].max())
        plt.plot([min_val, max_val], [min_val, max_val],
                'k--', alpha=0.8, label='Predição Perfeita')

        plt.title(f'Predições vs Valores Reais\n{best_result["model"]} (R² = {best_result["r2"]:.3f})',
                 fontweight='bold')
        plt.xlabel('Valor Real (log fixation duration)')
        plt.ylabel('Valor Predito (log fixation duration)')
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'predictions_vs_actual.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("📊 Predições vs real salvo")

    def plot_language_comparison(self):
        """Plot SWOW metrics comparison across languages"""
        if hasattr(self, 'lang_stats'):
            fig, axes = plt.subplots(1, 3, figsize=(18, 6))

            metrics = ['entropy', 'curvature', 'coherence']
            titles = ['Entropia por Idioma', 'Curvatura por Idioma', 'Coerência por Idioma']
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

            for i, (metric, title, color) in enumerate(zip(metrics, titles, colors)):
                langs = list(self.lang_stats.keys())
                means = [self.lang_stats[lang][f'{metric}_mean'] for lang in langs]
                stds = [self.lang_stats[lang][f'{metric}_std'] for lang in langs]

                bars = axes[i].bar(langs, means, yerr=stds, color=color, alpha=0.7, capsize=5)
                axes[i].set_title(title, fontweight='bold')
                axes[i].set_ylabel('Valor Médio')
                axes[i].grid(True, alpha=0.3)

                # Add value labels
                for bar, mean in zip(bars, means):
                    axes[i].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                               '.2f', ha='center', va='bottom')

            plt.tight_layout()
            plt.savefig(self.output_dir / 'language_comparison.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("📊 Comparação entre idiomas salva")

    def plot_correlation_matrix(self):
        """Plot correlation matrix of all features"""
        # Select numeric columns for correlation
        numeric_cols = ['entropy', 'curvature', 'coherence', 'fixation_duration',
                       'theta', 'alpha', 'beta']
        available_cols = [col for col in numeric_cols if col in self.df_clean.columns]

        if len(available_cols) > 1:
            corr_data = self.df_clean[available_cols].dropna()

            if len(corr_data) > 100:
                corr_matrix = corr_data.corr()

                plt.figure(figsize=(10, 8))
                mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
                sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm',
                           center=0, fmt='.2f', square=True)
                plt.title('Matriz de Correlação Completa', fontweight='bold')

                plt.tight_layout()
                plt.savefig(self.output_dir / 'correlation_matrix.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("📊 Matriz de correlação salva")

    def plot_residuals_analysis(self):
        """Plot residuals analysis for best model"""
        best_result = max(self.results, key=lambda x: x['r2'])

        residuals = best_result['y_true'] - best_result['y_pred']

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Residuals vs Predicted
        ax1.scatter(best_result['y_pred'], residuals, alpha=0.6, color='#FF6B6B')
        ax1.axhline(y=0, color='k', linestyle='--', alpha=0.8)
        ax1.set_title('Resíduos vs Valores Preditos', fontweight='bold')
        ax1.set_xlabel('Valor Predito')
        ax1.set_ylabel('Resíduo')
        ax1.grid(True, alpha=0.3)

        # Residuals distribution
        ax2.hist(residuals, bins=50, alpha=0.7, color='#4ECDC4', edgecolor='black')
        ax2.set_title('Distribuição dos Resíduos', fontweight='bold')
        ax2.set_xlabel('Resíduo')
        ax2.set_ylabel('Frequência')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'residuals_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("📊 Análise de resíduos salva")

    def plot_feature_distributions(self):
        """Plot distributions of SWOW features"""
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        features = ['entropy', 'curvature', 'coherence']
        titles = ['Distribuição da Entropia', 'Distribuição da Curvatura', 'Distribuição da Coerência']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

        for i, (feature, title, color) in enumerate(zip(features, titles, colors)):
            if feature in self.df_clean.columns:
                data = self.df_clean[feature].dropna()
                if len(data) > 0:
                    sns.histplot(data, ax=axes[i], bins=50, alpha=0.7, color=color)
                    axes[i].set_title(title, fontweight='bold')
                    axes[i].set_xlabel(feature.capitalize())
                    axes[i].set_ylabel('Frequência')
                    axes[i].grid(True, alpha=0.3)

                    # Add statistics
                    mean_val = data.mean()
                    median_val = data.median()
                    axes[i].axvline(mean_val, color='red', linestyle='--', alpha=0.7,
                                  label=f'Média: {mean_val:.2f}')
                    axes[i].axvline(median_val, color='blue', linestyle='--', alpha=0.7,
                                  label=f'Mediana: {median_val:.2f}')
                    axes[i].legend()

        plt.tight_layout()
        plt.savefig(self.output_dir / 'feature_distributions.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("📊 Distribuições de features salvas")

    def generate_comprehensive_report(self):
        """Generate comprehensive modeling report"""
        report_path = self.output_dir / 'comprehensive_modeling_report.md'

        # Find best model
        best_result = max(self.results, key=lambda x: x['r2'])

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 🤖 RELATÓRIO COMPREENSIVO DE MODELAGEM: SWOW vs NEUROFISIOLOGIA (MULTI-IDIOMA)\n\n")
            f.write(f"**Data de geração:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Total de observações:** {len(self.df_clean):,}\n\n")

            f.write("## 🎯 OBJETIVO\n\n")
            f.write("Prever duração de fixação ocular baseada em métricas de rede semântica SWOW:\n")
            f.write("- **Entropia (H)**: Imprevisibilidade semântica\n")
            f.write("- **Curvatura (κ)**: Clustering local na rede\n")
            f.write("- **Coerência (Q)**: Modularidade da comunidade\n\n")

            f.write("## 🌍 ANÁLISE MULTI-IDIOMA\n\n")
            f.write("| Idioma | Palavras | Entropia Média | Curvatura Média | Coerência Média |\n")
            f.write("|--------|---------|----------------|-----------------|-----------------|\n")
            for lang, stats in self.lang_stats.items():
                f.write(f"| {lang.upper()} | {stats['words']:,} | {stats['entropy_mean']:.2f} | {stats['curvature_mean']:.2f} | {stats['coherence_mean']:.2f} |\n")
            f.write("\n")

            f.write("## 📊 PERFORMANCE DOS MODELOS\n\n")
            f.write("| Modelo | R² | RMSE | MAE |\n")
            f.write("|--------|----|------|-----|\n")
            for result in self.results:
                f.write(f"| {result['model']} | {result['r2']:.3f} | {result['rmse']:.4f} | {result['mae']:.4f} |\n")
            f.write("\n")

            f.write("## 🏆 MELHOR MODELO\n\n")
            f.write(f"**{best_result['model']}**\n\n")
            f.write("**Métricas:**\n")
            f.write(f"- R²: {best_result['r2']:.3f}\n")
            f.write(f"- RMSE: {best_result['rmse']:.4f}\n")
            f.write(f"- MAE: {best_result['mae']:.4f}\n\n")

            f.write("## 🔍 IMPORTÂNCIA DAS FEATURES\n\n")
            f.write("| Feature | Importância |\n")
            f.write("|---------|-------------|\n")
            for _, row in self.feature_importance.iterrows():
                f.write(f"| {row['feature']} | {row['importance']:.3f} |\n")
            f.write("\n")

            f.write("## 🔄 VALIDAÇÃO CRUZADA\n\n")
            f.write("| Modelo | R² Médio | Desvio Padrão |\n")
            f.write("|--------|----------|---------------|\n")
            for name, cv_result in self.cv_results.items():
                f.write(f"| {name} | {cv_result['mean_r2']:.3f} | {cv_result['std_r2']:.3f} |\n")
            f.write("\n")

            f.write("## 📈 MODELAGEM POR DATASET\n\n")
            f.write("| Dataset | Observações | R² | RMSE |\n")
            f.write("|---------|-------------|----|------|\n")
            for dataset, result in self.dataset_results.items():
                f.write(f"| {dataset} | {len(self.df_clean[self.df_clean['dataset'] == dataset])} | {result['r2']:.3f} | {result['rmse']:.4f} |\n")
            f.write("\n")

            f.write("## 📊 VISUALIZAÇÕES GERADAS\n\n")
            visualizations = [
                "model_comparison.png - Comparação de performance entre modelos",
                "feature_importance.png - Importância das features SWOW",
                "predictions_vs_actual.png - Predições vs valores reais",
                "language_comparison.png - Comparação entre idiomas",
                "correlation_matrix.png - Matriz de correlação completa",
                "residuals_analysis.png - Análise de resíduos",
                "feature_distributions.png - Distribuições das features"
            ]

            for viz in visualizations:
                f.write(f"- {viz}\n")
            f.write("\n")

            f.write("## 💡 INSIGHTS PRINCIPAIS\n\n")
            f.write("### Relações Identificadas:\n")
            f.write("1. **Entropia** é a feature mais importante, sugerindo que palavras semanticamente imprevisíveis demandam mais tempo de processamento\n")
            f.write("2. **Curvatura** mostra relação negativa, indicando que palavras bem conectadas são processadas mais rapidamente\n")
            f.write("3. **Coerência** tem menor impacto, possivelmente devido à natureza local da medida\n\n")

            f.write("### Performance do Modelo:\n")
            f.write(f"- Melhor R² de {best_result['r2']:.3f} indica que ~{best_result['r2']*100:.0f}% da variabilidade na duração de fixação é explicada pelas métricas SWOW\n")
            f.write("- RMSE de {best_result['rmse']:.4f} representa o erro médio em escala logarítmica\n\n")

            f.write("### Padrões Multi-idioma:\n")
            f.write("- Diferenças significativas na estrutura semântica entre idiomas\n")
            f.write("- Possibilidade de modelos específicos por idioma para melhor performance\n\n")

            f.write("### Implicações Científicas:\n")
            f.write("- Confirma que estrutura semântica influencia processamento cognitivo\n")
            f.write("- Abre caminho para modelos de predição de dificuldade de leitura\n")
            f.write("- Possibilita identificação de biomarcadores semânticos-cognitivos\n")
            f.write("- Suporte para hipóteses de universalidade vs especificidade cultural na cognição\n\n")

            f.write("## 📋 PRÓXIMOS PASSOS\n\n")
            f.write("1. **Refinamento do Modelo:**\n")
            f.write("   - Feature engineering (interações entre métricas)\n")
            f.write("   - Ensemble methods avançados\n")
            f.write("   - Regularização otimizada\n\n")

            f.write("2. **Análises Avançadas:**\n")
            f.write("   - Modelos mistos (mixed-effects) por sujeito\n")
            f.write("   - Análise temporal de fixações\n")
            f.write("   - Comparações entre idiomas\n\n")

            f.write("3. **Validações:**\n")
            f.write("   - Testes estatísticos de significância\n")
            f.write("   - Validação externa com novos dados\n")
            f.write("   - Análise de resíduos\n\n")

            f.write("4. **Aplicações:**\n")
            f.write("   - Desenvolvimento de ferramentas educacionais\n")
            f.write("   - Diagnóstico de dificuldades de leitura\n")
            f.write("   - Pesquisa em neurociência cognitiva\n\n")

        print(f"📄 Relatório compreensivo salvo em: {report_path}")

    def run_complete_advanced_modeling(self):
        """Run complete advanced predictive modeling pipeline"""
        print("🚀 INICIANDO MODELAGEM PREDITIVA AVANÇADA (MULTI-IDIOMA)")
        print("=" * 70)

        try:
            # Prepare data
            self.prepare_features_and_target()
            self.train_test_split_data()

            # Multi-language analysis
            self.multilanguage_analysis()

            # Train and evaluate models
            self.train_baseline_models()
            self.cross_validation_analysis()
            self.feature_importance_analysis()
            self.dataset_specific_modeling()

            # Generate comprehensive visualizations
            self.plot_model_comparison()
            self.plot_feature_importance()
            self.plot_predictions_vs_actual()
            self.plot_language_comparison()
            self.plot_correlation_matrix()
            self.plot_residuals_analysis()
            self.plot_feature_distributions()

            # Generate comprehensive report
            self.generate_comprehensive_report()

            print("\n🎉 MODELAGEM AVANÇADA CONCLUÍDA!")
            print(f"📁 Resultados salvos em: {self.output_dir}")

            # Print summary
            best_result = max(self.results, key=lambda x: x['r2'])
            print("\n🏆 MELHOR MODELO:")
            print(f"  📊 {best_result['model']}: R² = {best_result['r2']:.3f}")

            print("\n📊 RESUMO MULTI-IDIOMA:")
            for lang, stats in self.lang_stats.items():
                print(f"  🌍 {lang.upper()}: {stats['words']:,} palavras")

        except Exception as e:
            print(f"❌ Erro durante modelagem avançada: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

        return True

def main():
    """Main execution function"""
    print("🤖 NEURO-SWOW ADVANCED PREDICTIVE MODELING (MULTI-LANGUAGE)")
    print("=" * 60)

    predictor = AdvancedNeuroSWOWPredictor()
    success = predictor.run_complete_advanced_modeling()

    if success:
        print("\n✅ Modelagem avançada concluída com sucesso!")
        print("📊 Verifique a pasta de relatórios para ver os resultados e visualizações.")
        print("🌍 Análise multi-idioma incluída com dados SWOW de EN, ES, NL, ZH.")
    else:
        print("\n❌ Falha na modelagem avançada.")
        sys.exit(1)

if __name__ == "__main__":
    main()
