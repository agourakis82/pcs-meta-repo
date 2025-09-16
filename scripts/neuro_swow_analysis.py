#!/usr/bin/env python3
"""
Análise Exploratória dos Dados Integrados Neuro-SWOW
Exploratory analysis of integrated neurophysiological and SWOW data
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

class NeuroSWOWAnalysis:
    """Exploratory analysis of integrated neuro-SWOW data"""

    def __init__(self, data_path: str = None):
        if data_path is None:
            data_path = Path(__file__).parent.parent / 'data' / 'processed' / 'integrated_neuro_swow.csv'

        print("🔍 Carregando dados integrados...")
        self.df = pd.read_csv(data_path, low_memory=False)

        # Clean and convert data types
        self._clean_data()
        print(f"✅ Dados carregados e limpos: {len(self.df):,} observações")

        # Create output directory
        self.output_dir = Path(__file__).parent.parent / 'reports' / 'neuro_swow_analysis'
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _clean_data(self):
        """Clean and convert data types"""
        print("🧹 Limpando dados...")

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

        # Clean numeric columns that might have mixed types
        mixed_type_cols = ['fixation_duration', 'timestamp', 'theta', 'alpha', 'beta']
        for col in mixed_type_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].apply(safe_numeric_convert)
                print(f"  ✅ {col} convertido para numérico")

        # Convert other numeric columns
        numeric_cols = ['entropy', 'curvature', 'coherence', 'onset_ms', 'offset_ms',
                       'cloze_prob', 'length', 'logfreq', 'position', 'sentence_id']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        # Remove rows with all NaN values in key metrics
        key_cols = ['entropy', 'fixation_duration']
        available_key_cols = [col for col in key_cols if col in self.df.columns]
        if available_key_cols:
            before_clean = len(self.df)
            self.df = self.df.dropna(subset=available_key_cols, how='all')
            after_clean = len(self.df)
            removed = before_clean - after_clean
            print(f"  🗑️ Removidas {removed:,} linhas com dados faltantes")

        print(f"  📊 Dados após limpeza: {len(self.df):,} observações")

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

class NeuroSWOWAnalysis:
    """Exploratory analysis of integrated neuro-SWOW data"""

    def __init__(self, data_path: str = None):
        if data_path is None:
            data_path = Path(__file__).parent.parent / 'data' / 'processed' / 'integrated_neuro_swow.csv'

        print("🔍 Carregando dados integrados...")
        self.df = pd.read_csv(data_path, low_memory=False)
        print(f"✅ Dados carregados: {len(self.df):,} observações")

        # Create output directory
        self.output_dir = Path(__file__).parent / 'reports' / 'neuro_swow_analysis'
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def basic_statistics(self):
        """Generate basic statistics"""
        print("\n📊 ESTATÍSTICAS BÁSICAS")
        print("=" * 50)

        # Dataset breakdown
        print("\n🔢 DISTRIBUIÇÃO POR DATASET:")
        dataset_stats = self.df['dataset'].value_counts()
        for dataset, count in dataset_stats.items():
            pct = count / len(self.df) * 100
            print(f"  {dataset}: {count:,} ({pct:.1f}%)")

        # SWOW metrics coverage
        print("\n🔬 COBERTURA MÉTRICAS SWOW:")
        swow_cols = ['entropy', 'curvature', 'coherence']
        for col in swow_cols:
            if col in self.df.columns:
                coverage = self.df[col].notna().sum() / len(self.df) * 100
                print(".1f")

        # Neuro metrics coverage
        print("\n🧠 COBERTURA MÉTRICAS NEUROFISIOLÓGICAS:")
        neuro_cols = ['fixation_duration', 'theta', 'alpha', 'beta']
        for col in neuro_cols:
            if col in self.df.columns:
                coverage = self.df[col].notna().sum() / len(self.df) * 100
                print(".1f")

    def correlation_analysis(self):
        """Analyze correlations between SWOW and neuro metrics"""
        print("\n📈 ANÁLISE DE CORRELAÇÕES")
        print("=" * 50)

        # Prepare data for correlation - filter only numeric values
        corr_data = self.df.copy()

        # Select relevant columns
        swow_cols = ['entropy', 'curvature', 'coherence']
        neuro_cols = ['fixation_duration', 'theta', 'alpha', 'beta']

        available_swow = [col for col in swow_cols if col in corr_data.columns]
        available_neuro = [col for col in neuro_cols if col in corr_data.columns]

        if available_swow and available_neuro:
            # Filter to rows with valid numeric data
            corr_cols = available_swow + available_neuro
            corr_subset = corr_data[corr_cols].dropna()

            print(f"📊 Usando {len(corr_subset):,} observações com dados completos para correlação")

            if len(corr_subset) > 100:  # Need minimum sample size
                # Calculate correlations
                corr_matrix = corr_subset.corr()

                print("\n🔗 MATRIZ DE CORRELAÇÃO:")
                print(corr_matrix.round(3))

                # Focus on SWOW-neuro correlations
                print("\n🎯 CORRELAÇÕES SWOW vs NEURO:")
                for swow_metric in available_swow:
                    for neuro_metric in available_neuro:
                        if swow_metric in corr_matrix.columns and neuro_metric in corr_matrix.columns:
                            corr_val = corr_matrix.loc[swow_metric, neuro_metric]
                            if not pd.isna(corr_val):
                                print("+.3f")
            else:
                print("⚠️ Amostra muito pequena para análise de correlação confiável")
        else:
            print("⚠️ Colunas necessárias não encontradas para análise de correlação")

    def dataset_comparison(self):
        """Compare metrics across datasets"""
        print("\n🔍 COMPARAÇÃO ENTRE DATASETS")
        print("=" * 50)

        datasets = self.df['dataset'].unique()

        # Focus on SWOW metrics that we know work
        for metric in ['entropy', 'curvature', 'coherence']:
            if metric in self.df.columns:
                print(f"\n📊 {metric.upper()} POR DATASET:")
                # Filter out NaN values for this metric
                metric_data = self.df[[metric, 'dataset']].dropna()
                if len(metric_data) > 0:
                    metric_stats = metric_data.groupby('dataset')[metric].agg(['mean', 'std', 'count'])
                    print(metric_stats.round(3))
                else:
                    print("  ⚠️ Nenhum dado válido encontrado")

    def word_frequency_analysis(self):
        """Analyze most frequent words and their metrics"""
        print("\n📝 ANÁLISE DE FREQUÊNCIA DE PALAVRAS")
        print("=" * 50)

        # Most frequent words
        word_freq = self.df['word_norm'].value_counts().head(20)
        print("\n🔤 PALAVRAS MAIS FREQUENTES:")
        for word, freq in word_freq.items():
            print(f"  {word}: {freq:,}")

        # Average metrics for top words
        print("\n📊 MÉTRICAS MÉDIAS PARA PALAVRAS MAIS FREQUENTES:")
        top_words = word_freq.index.tolist()
        top_words_data = self.df[self.df['word_norm'].isin(top_words)]

        metrics_summary = top_words_data.groupby('word_norm')[['entropy', 'curvature', 'coherence']].mean()
        print(metrics_summary.round(3))

    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n📋 GERANDO RELATÓRIO FINAL")
        print("=" * 50)

        report_path = self.output_dir / 'neuro_swow_analysis_report.txt'

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("ANÁLISE EXPLORATÓRIA: DADOS INTEGRADOS NEURO-SWOW\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"Data de análise: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total de observações: {len(self.df):,}\n\n")

            # Dataset breakdown
            f.write("DISTRIBUIÇÃO POR DATASET:\n")
            f.write("-" * 30 + "\n")
            dataset_stats = self.df['dataset'].value_counts()
            for dataset, count in dataset_stats.items():
                pct = count / len(self.df) * 100
                f.write(".1f")
            f.write("\n")

            # Coverage statistics
            f.write("COBERTURA DAS MÉTRICAS:\n")
            f.write("-" * 30 + "\n")

            swow_cols = ['entropy', 'curvature', 'coherence']
            for col in swow_cols:
                if col in self.df.columns:
                    coverage = self.df[col].notna().sum() / len(self.df) * 100
                    f.write(".1f")

            neuro_cols = ['fixation_duration', 'theta', 'alpha', 'beta']
            for col in neuro_cols:
                if col in self.df.columns:
                    coverage = self.df[col].notna().sum() / len(self.df) * 100
                    f.write(".1f")

            f.write("\n")
            f.write("✅ ANÁLISE CONCLUÍDA COM SUCESSO!\n")

        print(f"📄 Relatório salvo em: {report_path}")

    def run_full_analysis(self):
        """Run complete exploratory analysis"""
        print("🚀 INICIANDO ANÁLISE EXPLORATÓRIA COMPLETA")
        print("=" * 60)

        try:
            self.basic_statistics()
            self.correlation_analysis()
            self.dataset_comparison()
            self.word_frequency_analysis()
            self.generate_report()

            print("\n🎉 ANÁLISE EXPLORATÓRIA CONCLUÍDA!")
            print("📊 Dados prontos para modelagem preditiva e visualizações avançadas.")

        except Exception as e:
            print(f"❌ Erro durante análise: {str(e)}")
            return False

        return True

def main():
    """Main execution function"""
    print("🧠 NEURO-SWOW EXPLORATORY ANALYSIS")
    print("=" * 40)

    analyzer = NeuroSWOWAnalysis()
    success = analyzer.run_full_analysis()

    if success:
        print("\n✅ Análise concluída com sucesso!")
        print("📈 Próximos passos sugeridos:")
        print("  1. Modelagem preditiva (regressão de fixation duration ~ entropy)")
        print("  2. Visualizações avançadas (scatter plots, heatmaps)")
        print("  3. Análise por sujeito/modalidade")
        print("  4. Validação estatística dos achados")
    else:
        print("\n❌ Análise falhou. Verifique os logs para detalhes.")
        sys.exit(1)

if __name__ == "__main__":
    main()
