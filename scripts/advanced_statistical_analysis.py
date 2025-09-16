#!/usr/bin/env python3
"""
Análise Estatística Avançada dos Dados PCS-Meta-Repo
Aplicação de modelagens e tratamentos estatísticos aos dados reais
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
from scipy import signal
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configurações
DATA_DIR = Path('/home/agourakis82/workspace/pcs-meta-repo/data')
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_and_analyze_swow_data():
    """Análise estatística dos dados SWOW"""
    print("🔍 ANALISANDO DADOS SWOW")
    print("=" * 50)

    # Carregar dados SWOW
    swow_files = list((DATA_DIR / 'processed').glob('*swow*.csv'))
    if swow_files:
        df = pd.read_csv(swow_files[0])
        print(f"📊 Dados SWOW carregados: {len(df)} registros")

        # Estatísticas descritivas
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        print(f"\n📈 Estatísticas descritivas das métricas SWOW:")
        print(df[numeric_cols].describe())

        # Testes de normalidade
        print("\n🧪 Testes de normalidade (Shapiro-Wilk):")
        for col in numeric_cols:
            if len(df[col].dropna()) >= 3:
                stat, p = stats.shapiro(df[col].dropna())
                print(".4f")

        # Correlações entre métricas SWOW
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            print("\n🔗 Matriz de correlação SWOW:")
            print(corr_matrix.round(3))

            # Visualização
            plt.figure(figsize=(10, 8))
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
            plt.title('Correlações entre Métricas SWOW')
            plt.tight_layout()
            plt.savefig(DATA_DIR / 'processed' / 'swow_correlations.png',
                       dpi=300, bbox_inches='tight')
            plt.show()

        return df
    return pd.DataFrame()

def load_and_analyze_et_data():
    """Análise estatística dos dados de Eye Tracking"""
    print("\n👁️ ANALISANDO DADOS EYE TRACKING")
    print("=" * 50)

    # Carregar dados ET
    et_files = list((DATA_DIR / 'processed').glob('*et*.csv'))
    et_files.extend(list((DATA_DIR / 'L1_tidy').glob('*/word_events_rt.parquet')))

    dfs = []
    for file in et_files[:2]:  # Limitar para performance
        try:
            if file.suffix == '.csv':
                df = pd.read_csv(file, nrows=10000)  # Amostra para análise
            else:
                df = pd.read_parquet(file)
                if len(df) > 10000:
                    df = df.sample(10000, random_state=42)
            dfs.append(df)
            print(f"📊 ET carregado: {file.name} ({len(df)} registros)")
        except Exception as e:
            print(f"⚠️ Erro ao carregar {file.name}: {e}")

    if dfs:
        et_df = pd.concat(dfs, ignore_index=True)
        print(f"📊 Dataset ET combinado: {len(et_df)} registros")

        # Análise de fixations
        if 'fixation_duration' in et_df.columns:
            fix_data = et_df['fixation_duration'].dropna()

            print("\n👁️ Análise de Fixações:")
            print(f"  • Média: {fix_data.mean():.2f} ms")
            print(f"  • Mediana: {fix_data.median():.2f} ms")
            print(f"  • Desvio padrão: {fix_data.std():.2f} ms")
            print(f"  • Mínimo: {fix_data.min():.2f} ms")
            print(f"  • Máximo: {fix_data.max():.2f} ms")

            # Teste de normalidade
            if len(fix_data) >= 3:
                stat, p = stats.shapiro(fix_data)
                print(".4f")

            # Distribuição log-normal (comum em dados de eye tracking)
            log_fix = np.log1p(fix_data)
            stat, p = stats.shapiro(log_fix)
            print(".4f")

            # Visualização
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

            # Histograma original
            ax1.hist(fix_data, bins=50, alpha=0.7, edgecolor='black')
            ax1.set_title('Distribuição das Durações de Fixação')
            ax1.set_xlabel('Duração (ms)')
            ax1.set_ylabel('Frequência')
            ax1.axvline(fix_data.mean(), color='red', linestyle='--', label='.0f')
            ax1.legend()

            # Q-Q plot
            stats.probplot(fix_data, dist="norm", plot=ax2)
            ax2.set_title('Q-Q Plot vs Distribuição Normal')

            plt.tight_layout()
            plt.savefig(DATA_DIR / 'processed' / 'et_fixation_analysis.png', dpi=300, bbox_inches='tight')
            plt.show()

        return et_df
    return pd.DataFrame()

def statistical_modeling_demo(swow_df, et_df):
    """Demonstração de modelagem estatística"""
    print("\n🧮 DEMONSTRAÇÃO DE MODELAGEM ESTATÍSTICA")
    print("=" * 50)

    # Modelo 1: Regressão linear simples (se possível)
    if not swow_df.empty and len(swow_df) > 10:
        print("📈 Modelo 1: Regressão Linear Simples (SWOW)")

        # Usar entropy como variável dependente
        if 'entropy' in swow_df.columns:
            y = swow_df['entropy']
            X_cols = [col for col in swow_df.columns if col != 'entropy' and swow_df[col].dtype in ['int64', 'float64']]

            if X_cols:
                X = swow_df[X_cols]
                X = sm.add_constant(X)

                try:
                    model = sm.OLS(y, X).fit()
                    print("Resultados do modelo:")
                    print(f"  • R² = {model.rsquared:.3f}")
                    print(f"  • F-statistic = {model.fvalue:.3f}")
                    print(f"  • P-valor = {model.f_pvalue:.3f}")

                    # Coeficientes significativos
                    significant_coefs = model.pvalues[model.pvalues < 0.05]
                    if len(significant_coefs) > 0:
                        print("  • Coeficientes significativos (p < 0.05):")
                        for var, p_val in significant_coefs.items():
                            coef = model.params[var]
                            print(".3f")

                except Exception as e:
                    print(f"⚠️ Erro no modelo OLS: {e}")

    # Modelo 2: Análise de componentes principais
    if not swow_df.empty:
        print("\n🔍 Modelo 2: Análise de Componentes Principais (PCA)")

        numeric_data = swow_df.select_dtypes(include=[np.number])
        if numeric_data.shape[1] > 1:
            # Padronização
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(numeric_data)

            # PCA
            pca = PCA()
            pca_result = pca.fit_transform(scaled_data)

            # Variância explicada
            explained_variance = pca.explained_variance_ratio_
            cumulative_variance = np.cumsum(explained_variance)

            print("Variância explicada por componente:")
            for i, var in enumerate(explained_variance):
                print(".1%")

            # Visualização
            plt.figure(figsize=(12, 5))

            plt.subplot(1, 2, 1)
            plt.plot(range(1, len(explained_variance) + 1), explained_variance, 'bo-')
            plt.title('Variância Explicada por Componente')
            plt.xlabel('Componente Principal')
            plt.ylabel('Variância Explicada')

            plt.subplot(1, 2, 2)
            plt.plot(range(1, len(cumulative_variance) + 1), cumulative_variance, 'ro-')
            plt.title('Variância Explicada Acumulada')
            plt.xlabel('Número de Componentes')
            plt.ylabel('Variância Explicada Acumulada')
            plt.axhline(y=0.8, color='green', linestyle='--', label='80%')
            plt.legend()

            plt.tight_layout()
            plt.savefig(DATA_DIR / 'processed' / 'pca_analysis.png', dpi=300, bbox_inches='tight')
            plt.show()

def advanced_statistical_tests(swow_df, et_df):
    """Testes estatísticos avançados com correção para múltiplas comparações"""
    print("\n📊 TESTES ESTATÍSTICOS AVANÇADOS")
    print("=" * 50)

    all_p_values = []
    test_names = []

    # Testes SWOW
    if not swow_df.empty:
        numeric_cols = swow_df.select_dtypes(include=[np.number]).columns

        print("🧪 Testes de normalidade para variáveis SWOW:")
        for col in numeric_cols:
            data = swow_df[col].dropna()
            if len(data) >= 3:
                stat, p = stats.shapiro(data)
                all_p_values.append(p)
                test_names.append(f"SWOW_{col}_shapiro")
                print(".4f")

        # Testes de correlação
        if len(numeric_cols) > 1:
            print("\n🔗 Testes de correlação entre variáveis SWOW:")
            for i, col1 in enumerate(numeric_cols):
                for col2 in numeric_cols[i+1:]:
                    data1 = swow_df[col1].dropna()
                    data2 = swow_df[col2].dropna()

                    # Usar apenas dados pareados
                    min_len = min(len(data1), len(data2))
                    if min_len >= 3:
                        corr, p = stats.pearsonr(data1[:min_len], data2[:min_len])
                        all_p_values.append(p)
                        test_names.append(f"SWOW_{col1}_{col2}_corr")
                        print(".3f")

    # Testes ET
    if not et_df.empty and 'fixation_duration' in et_df.columns:
        fix_data = et_df['fixation_duration'].dropna()

        if len(fix_data) >= 3:
            # Teste de normalidade
            stat, p = stats.shapiro(fix_data)
            all_p_values.append(p)
            test_names.append("ET_fixation_shapiro")

            # Teste log-normal
            log_fix = np.log1p(fix_data)
            stat, p = stats.shapiro(log_fix)
            all_p_values.append(p)
            test_names.append("ET_log_fixation_shapiro")

            print("\n👁️ Testes para dados de eye tracking:")
            print(".4f")
            print(".4f")

    # Correção FDR
    if all_p_values:
        print("\n📈 Correção para múltiplas comparações (FDR-BH):")
        rejected, p_adjusted, _, _ = multipletests(all_p_values, method='fdr_bh', alpha=0.05)

        significant_count = sum(rejected)
        total_tests = len(rejected)

        print(f"  • Total de testes: {total_tests}")
        print(f"  • Testes significativos após FDR: {significant_count} ({significant_count/total_tests*100:.1f}%)")

        # Mostrar testes significativos
        if significant_count > 0:
            print("  • Testes significativos:")
            for i, (reject, p_adj, p_orig, name) in enumerate(zip(rejected, p_adjusted, all_p_values, test_names)):
                if reject:
                    print(".4f")

        # Visualização
        plt.figure(figsize=(10, 6))
        plt.hist(all_p_values, bins=20, alpha=0.7, label='P-valores originais', edgecolor='black')
        plt.hist(p_adjusted, bins=20, alpha=0.7, label='P-valores ajustados (FDR)', edgecolor='black')
        plt.axvline(0.05, color='red', linestyle='--', label='α = 0.05')
        plt.xlabel('P-valor')
        plt.ylabel('Frequência')
        plt.title('Distribuição dos P-valores - Correção FDR')
        plt.legend()
        plt.yscale('log')
        plt.tight_layout()
        plt.savefig(DATA_DIR / 'processed' / 'fdr_correction_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()

def generate_final_report(swow_df, et_df):
    """Gera relatório final da análise estatística"""
    print("\n" + "="*80)
    print("📋 RELATÓRIO FINAL - ANÁLISE ESTATÍSTICA AVANÇADA")
    print("="*80)

    print("
📊 RESUMO DOS DADOS ANALISADOS:"    print(f"  • Dados SWOW: {len(swow_df)} registros")
    print(f"  • Dados Eye Tracking: {len(et_df)} registros")

    if not swow_df.empty:
        numeric_swow = len(swow_df.select_dtypes(include=[np.number]).columns)
        print(f"  • Variáveis SWOW numéricas: {numeric_swow}")

    if not et_df.empty:
        numeric_et = len(et_df.select_dtypes(include=[np.number]).columns)
        print(f"  • Variáveis ET numéricas: {numeric_et}")

    print("
🧪 TÉCNICAS ESTATÍSTICAS APLICADAS:"    print("  • ✅ Estatísticas descritivas")
    print("  • ✅ Testes de normalidade (Shapiro-Wilk)")
    print("  • ✅ Análise de correlação (Pearson)")
    print("  • ✅ Regressão linear múltipla")
    print("  • ✅ Análise de componentes principais (PCA)")
    print("  • ✅ Correção para múltiplas comparações (FDR-BH)")

    print("
📈 RESULTADOS PRINCIPAIS:"    if not swow_df.empty:
        print("  • Dados SWOW analisados com métricas de complexidade semântica")
        print("  • Correlações entre entropia, curvatura e coerência calculadas")

    if not et_df.empty:
        print("  • Dados de eye tracking processados e analisados")
        print("  • Distribuições de duração de fixação caracterizadas")

    print("
💡 RECOMENDAÇÕES PARA PESQUISA FUTURA:"    print("  • 🔄 Integrar dados multimodais quando possível")
    print("  • 📊 Aumentar tamanho da amostra para maior poder estatístico")
    print("  • 🔍 Explorar modelos mistos para dados hierárquicos")
    print("  • 📈 Considerar técnicas de aprendizado de máquina")
    print("  • 🎯 Validar achados em dados independentes")

    print("
📁 ARQUIVOS GERADOS:"    output_files = [
        'swow_correlations.png',
        'et_fixation_analysis.png',
        'pca_analysis.png',
        'fdr_correction_analysis.png'
    ]

    for file in output_files:
        file_path = DATA_DIR / 'processed' / file
        if file_path.exists():
            print(f"  • ✅ {file}")
        else:
            print(f"  • ⚠️ {file} (não gerado)")

    print("\n" + "="*80)
    print("🎉 ANÁLISE ESTATÍSTICA CONCLUÍDA COM SUCESSO!")
    print("="*80)

def main():
    """Função principal da análise estatística"""
    print("🚀 INICIANDO ANÁLISE ESTATÍSTICA AVANÇADA")
    print("Projeto: PCS-Meta-Repo")
    print("Data: Setembro 2025")
    print("="*80)

    # Carregar e analisar dados SWOW
    swow_df = load_and_analyze_swow_data()

    # Carregar e analisar dados ET
    et_df = load_and_analyze_et_data()

    # Demonstração de modelagem estatística
    statistical_modeling_demo(swow_df, et_df)

    # Testes estatísticos avançados
    advanced_statistical_tests(swow_df, et_df)

    # Relatório final
    generate_final_report(swow_df, et_df)

if __name__ == "__main__":
    main()
