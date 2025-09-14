#!/usr/bin/env python3
"""
Visualizações dos Dados Integrados Neuro-SWOW
Data visualizations for integrated neurophysiological and SWOW data
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

class NeuroSWOWVisualization:
    """Data visualizations for integrated neuro-SWOW data"""

    def __init__(self, data_path: str = None):
        if data_path is None:
            data_path = Path(__file__).parent.parent / 'data' / 'processed' / 'integrated_neuro_swow.csv'

        print("🔍 Carregando dados para visualização...")
        self.df = pd.read_csv(data_path, low_memory=False)

        # Clean data
        self._clean_data()
        print(f"✅ Dados carregados e limpos: {len(self.df):,} observações")

        # Create output directory
        self.output_dir = Path(__file__).parent.parent / 'reports' / 'neuro_swow_visualizations'
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set style
        plt.style.use('default')
        sns.set_palette("husl")

    def _clean_data(self):
        """Clean data for visualization"""
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
        for col in ['entropy', 'curvature', 'coherence', 'fixation_duration']:
            if col in self.df.columns:
                self.df[col] = self.df[col].apply(safe_numeric_convert)

    def plot_dataset_distribution(self):
        """Plot dataset distribution"""
        plt.figure(figsize=(10, 6))

        dataset_counts = self.df['dataset'].value_counts()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']

        plt.pie(dataset_counts.values, labels=dataset_counts.index,
                autopct='%1.1f%%', colors=colors, startangle=90)
        plt.title('Distribuição por Dataset', fontsize=14, fontweight='bold')
        plt.axis('equal')

        plt.savefig(self.output_dir / 'dataset_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("📊 Gráfico de distribuição por dataset salvo")

    def plot_swow_distributions(self):
        """Plot SWOW metrics distributions"""
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        swow_metrics = ['entropy', 'curvature', 'coherence']
        titles = ['Entropia (H)', 'Curvatura (κ)', 'Coerência (Q)']

        for i, (metric, title) in enumerate(zip(swow_metrics, titles)):
            if metric in self.df.columns:
                data = self.df[metric].dropna()
                if len(data) > 0:
                    # Plot histogram with KDE
                    sns.histplot(data, ax=axes[i], bins=50, alpha=0.7, color='#FF6B6B')
                    axes[i].set_title(f'Distribuição de {title}', fontweight='bold')
                    axes[i].set_xlabel(title)
                    axes[i].set_ylabel('Frequência')

                    # Add statistics
                    mean_val = data.mean()
                    median_val = data.median()
                    axes[i].axvline(mean_val, color='red', linestyle='--', alpha=0.7,
                                  label=f'Média: {mean_val:.2f}')
                    axes[i].axvline(median_val, color='blue', linestyle='--', alpha=0.7,
                                  label=f'Mediana: {median_val:.2f}')
                    axes[i].legend()

        plt.tight_layout()
        plt.savefig(self.output_dir / 'swow_distributions.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("📊 Distribuições SWOW salvas")

    def plot_correlation_heatmap(self):
        """Plot correlation heatmap between SWOW and neuro metrics"""
        # Select relevant columns
        corr_cols = ['entropy', 'curvature', 'coherence', 'fixation_duration']
        available_cols = [col for col in corr_cols if col in self.df.columns]

        if len(available_cols) > 1:
            # Get correlation data
            corr_data = self.df[available_cols].dropna()
            if len(corr_data) > 100:
                corr_matrix = corr_data.corr()

                plt.figure(figsize=(8, 6))
                mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
                sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm',
                           center=0, fmt='.2f', square=True)
                plt.title('Correlação entre Métricas SWOW e Neurofisiológicas',
                         fontweight='bold')

                plt.savefig(self.output_dir / 'correlation_heatmap.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("📊 Heatmap de correlação salvo")
            else:
                print("⚠️ Dados insuficientes para heatmap de correlação")

    def plot_top_words_analysis(self):
        """Plot analysis of top words by SWOW metrics"""
        if 'word_norm' in self.df.columns and 'entropy' in self.df.columns:
            # Get top 20 words by frequency
            word_freq = self.df['word_norm'].value_counts().head(20)
            top_words = word_freq.index.tolist()

            # Get average metrics for top words
            top_words_data = self.df[self.df['word_norm'].isin(top_words)].copy()
            metrics_by_word = top_words_data.groupby('word_norm')[['entropy', 'curvature', 'coherence']].mean().dropna()

            if len(metrics_by_word) > 0:
                fig, axes = plt.subplots(1, 3, figsize=(18, 6))

                metrics = ['entropy', 'curvature', 'coherence']
                titles = ['Entropia Média', 'Curvatura Média', 'Coerência Média']
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

                for i, (metric, title, color) in enumerate(zip(metrics, titles, colors)):
                    if metric in metrics_by_word.columns:
                        data = metrics_by_word[metric].sort_values()
                        data.plot(kind='barh', ax=axes[i], color=color, alpha=0.7)
                        axes[i].set_title(title, fontweight='bold')
                        axes[i].set_xlabel('Valor Médio')
                        axes[i].grid(True, alpha=0.3)

                plt.tight_layout()
                plt.savefig(self.output_dir / 'top_words_analysis.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("📊 Análise de palavras mais frequentes salva")

    def plot_dataset_comparison(self):
        """Plot comparison of SWOW metrics across datasets"""
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        swow_metrics = ['entropy', 'curvature', 'coherence']
        titles = ['Entropia por Dataset', 'Curvatura por Dataset', 'Coerência por Dataset']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

        for i, (metric, title, color) in enumerate(zip(swow_metrics, titles, colors)):
            if metric in self.df.columns:
                # Group by dataset and calculate means
                dataset_means = self.df.groupby('dataset')[metric].mean().dropna()

                if len(dataset_means) > 0:
                    dataset_means.plot(kind='bar', ax=axes[i], color=color, alpha=0.7)
                    axes[i].set_title(title, fontweight='bold')
                    axes[i].set_ylabel('Valor Médio')
                    axes[i].tick_params(axis='x', rotation=45)
                    axes[i].grid(True, alpha=0.3)

                    # Add value labels
                    for j, v in enumerate(dataset_means):
                        axes[i].text(j, v + 0.01, '.2f', ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig(self.output_dir / 'dataset_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("📊 Comparação entre datasets salva")

    def generate_visualization_report(self):
        """Generate visualization report"""
        report_path = self.output_dir / 'visualization_report.md'

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 📊 RELATÓRIO DE VISUALIZAÇÕES: DADOS NEURO-SWOW\n\n")
            f.write(f"**Data de geração:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Total de observações:** {len(self.df):,}\n\n")

            f.write("## 📈 VISUALIZAÇÕES GERADAS\n\n")
            f.write("### 1. Distribuição por Dataset\n")
            f.write("- **Arquivo:** `dataset_distribution.png`\n")
            f.write("- **Descrição:** Distribuição proporcional dos dados por dataset\n\n")

            f.write("### 2. Distribuições SWOW\n")
            f.write("- **Arquivo:** `swow_distributions.png`\n")
            f.write("- **Descrição:** Histogramas das métricas SWOW (Entropia, Curvatura, Coerência)\n\n")

            f.write("### 3. Heatmap de Correlação\n")
            f.write("- **Arquivo:** `correlation_heatmap.png`\n")
            f.write("- **Descrição:** Correlações entre métricas SWOW e neurofisiológicas\n\n")

            f.write("### 4. Análise de Palavras Frequentes\n")
            f.write("- **Arquivo:** `top_words_analysis.png`\n")
            f.write("- **Descrição:** Métricas SWOW médias para as 20 palavras mais frequentes\n\n")

            f.write("### 5. Comparação entre Datasets\n")
            f.write("- **Arquivo:** `dataset_comparison.png`\n")
            f.write("- **Descrição:** Comparação das métricas SWOW médias por dataset\n\n")

            f.write("## 🔍 INSIGHTS PRINCIPAIS\n\n")
            f.write("### Distribuição de Dados:\n")
            dataset_stats = self.df['dataset'].value_counts()
            for dataset, count in dataset_stats.items():
                pct = count / len(self.df) * 100
                f.write(f"- **{dataset}:** {count:,} observações ({pct:.1f}%)\n")
            f.write("\n")

            f.write("### Cobertura das Métricas:\n")
            for metric in ['entropy', 'curvature', 'coherence']:
                if metric in self.df.columns:
                    coverage = self.df[metric].notna().sum() / len(self.df) * 100
                    f.write(f"- **{metric}:** {coverage:.1f}% de cobertura\n")
            f.write("\n")

            f.write("## 📋 PRÓXIMOS PASSOS\n\n")
            f.write("1. **Modelagem Preditiva:**\n")
            f.write("   - Regressão: fixation_duration ~ entropy + curvature + coherence\n")
            f.write("   - Classificação: predição de dificuldade de leitura\n\n")

            f.write("2. **Análises Avançadas:**\n")
            f.write("   - Análise por sujeito/modalidade\n")
            f.write("   - Modelos mistos (mixed-effects)\n")
            f.write("   - Validação estatística\n\n")

            f.write("3. **Visualizações Interativas:**\n")
            f.write("   - Dashboards interativos\n")
            f.write("   - Análise temporal\n")
            f.write("   - Comparações dinâmicas\n\n")

        print(f"📄 Relatório de visualizações salvo em: {report_path}")

    def run_all_visualizations(self):
        """Run all visualizations"""
        print("🎨 GERANDO VISUALIZAÇÕES COMPLETAS")
        print("=" * 50)

        try:
            self.plot_dataset_distribution()
            self.plot_swow_distributions()
            self.plot_correlation_heatmap()
            self.plot_top_words_analysis()
            self.plot_dataset_comparison()
            self.generate_visualization_report()

            print("\n🎉 VISUALIZAÇÕES CONCLUÍDAS!")
            print(f"📁 Visualizações salvas em: {self.output_dir}")

        except Exception as e:
            print(f"❌ Erro durante visualizações: {str(e)}")
            return False

        return True

def main():
    """Main execution function"""
    print("🎨 NEURO-SWOW DATA VISUALIZATION")
    print("=" * 40)

    viz = NeuroSWOWVisualization()
    success = viz.run_all_visualizations()

    if success:
        print("\n✅ Visualizações geradas com sucesso!")
        print("📊 Verifique a pasta de relatórios para ver os gráficos.")
    else:
        print("\n❌ Falha na geração de visualizações.")
        sys.exit(1)

if __name__ == "__main__":
    main()
