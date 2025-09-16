#!/usr/bin/env python3
"""
🔧 CORRETOR DE DATASET INTEGRADO
Corrige problemas de tipos de dados no dataset integrado neuro-swow
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")


class IntegratedDatasetFixer:
    """Corretor para problemas de tipos de dados no dataset integrado"""

    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []

    def clean_numeric_column(self, series, column_name):
        """Limpa uma coluna numérica convertendo valores problemáticos e validando consistência"""
        print(f"🔍 Limpando coluna '{column_name}'...")

        original_count = len(series)

        # Converter para string primeiro para identificar problemas
        str_series = series.astype(str)

        # Identificar valores problemáticos
        problematic_values = set()
        for val in str_series.unique():
            if column_name == "fixation_duration":
                if val.lower() in ["nan", "none", "null", "", "false", "true"]:
                    problematic_values.add(val)
            else:
                if val.lower() in ["false", "true", "nan", "none", "null", ""]:
                    problematic_values.add(val)

        if problematic_values:
            print(f"  📊 Valores problemáticos encontrados: {problematic_values}")
            self.issues_found.append(
                f"Coluna '{column_name}': {len(problematic_values)} tipos de valores problemáticos"
            )

        # Função para converter valores
        def convert_value(val):
            if pd.isna(val):
                return np.nan

            val_str = str(val).lower().strip()

            if column_name == "fixation_duration":
                # For fixation_duration, treat "false" and "true" as NaN
                if val_str in ["false", "true"]:
                    return np.nan
            else:
                if val_str == "false":
                    return np.nan  # Tratar False como missing data
                elif val_str == "true":
                    return 1.0  # Tratar True como 1

            if val_str in ["nan", "none", "null", ""]:
                return np.nan

            # Tentar converter para float
            try:
                fval = float(val)
                # Validar valores negativos ou zeros para colunas que não deveriam ter
                if column_name == "fixation_duration":
                    if fval <= 0:
                        return np.nan
                return fval
            except (ValueError, TypeError):
                return np.nan

        # Aplicar conversão
        cleaned_series = series.apply(convert_value)

        # Estatísticas de limpeza
        nan_count = cleaned_series.isna().sum()
        valid_count = original_count - nan_count

        # Estatísticas adicionais para validação
        mean_val = cleaned_series.mean()
        std_val = cleaned_series.std()
        unique_vals = cleaned_series.nunique(dropna=True)

        print(
            f"  ✅ Limpeza concluída: {valid_count}/{original_count} valores válidos ({nan_count} NaN)"
        )
        print(
            f"    • Média: {mean_val:.3f}, Desvio Padrão: {std_val:.3f}, Valores Únicos: {unique_vals}"
        )

        if problematic_values:
            self.fixes_applied.append(
                f"Coluna '{column_name}': convertidos {len(problematic_values)} tipos problemáticos para NaN"
            )

        return cleaned_series

    def fix_dataset(self, input_path, output_path=None):
        """Corrige o dataset integrado"""
        print("🚀 INICIANDO CORREÇÃO DO DATASET INTEGRADO")
        print("=" * 50)

        # Carregar dados
        print(f"\n📥 Carregando dados de: {input_path}")
        df = pd.read_csv(input_path)
        print(f"  📊 Shape original: {df.shape}")

        # Identificar colunas numéricas que precisam de limpeza
        numeric_columns = [
            "fixation_duration",
            "entropy",
            "curvature",
            "coherence",
            "theta",
            "alpha",
            "beta",
            "onset_ms",
            "offset_ms",
            "cloze_prob",
            "length",
            "logfreq",
            "position",
            "log_fixation_duration",
            "timestamp",
        ]

        # Verificar quais colunas existem
        existing_numeric_cols = [col for col in numeric_columns if col in df.columns]
        print(f"\n🔍 Colunas numéricas encontradas: {existing_numeric_cols}")

        # Limpar cada coluna numérica
        for col in existing_numeric_cols:
            df[col] = self.clean_numeric_column(df[col], col)

        # Verificar se há outras colunas com problemas
        print(f"\n🔍 Verificando outras colunas...")
        for col in df.columns:
            if col not in existing_numeric_cols:
                # Verificar se há valores 'False'/'True' em colunas não-numéricas
                if df[col].dtype == "object":
                    false_count = (df[col].astype(str) == "False").sum()
                    true_count = (df[col].astype(str) == "True").sum()
                    if false_count > 0 or true_count > 0:
                        print(
                            f"  ⚠️ Coluna '{col}': {false_count} 'False', {true_count} 'True'"
                        )
                        self.issues_found.append(
                            f"Coluna '{col}': valores booleanos como string"
                        )

        # Estatísticas finais
        print(f"\n📊 ESTATÍSTICAS DE CORREÇÃO:")
        print(f"  • Problemas encontrados: {len(self.issues_found)}")
        print(f"  • Correções aplicadas: {len(self.fixes_applied)}")

        if self.issues_found:
            print(f"\n🔍 PROBLEMAS ENCONTRADOS:")
            for issue in self.issues_found:
                print(f"    • {issue}")

        if self.fixes_applied:
            print(f"\n✅ CORREÇÕES APLICADAS:")
            for fix in self.fixes_applied:
                print(f"    • {fix}")

        # Salvar dataset corrigido
        if output_path is None:
            # Criar backup do original
            backup_path = str(input_path).replace(".csv", "_backup.csv")
            print(f"\n💾 Criando backup: {backup_path}")
            df_original = pd.read_csv(input_path)
            df_original.to_csv(backup_path, index=False)

            output_path = input_path

        print(f"\n💾 Salvando dataset corrigido: {output_path}")
        df.to_csv(output_path, index=False)

        print(f"\n✅ CORREÇÃO CONCLUÍDA!")
        print(f"  📊 Shape final: {df.shape}")

        return df

    def validate_fix(self, df):
        """Valida se a correção foi bem-sucedida"""
        print(f"\n🔍 VALIDANDO CORREÇÃO...")

        numeric_columns = ["fixation_duration", "entropy", "curvature", "coherence"]
        validation_results = {}

        for col in numeric_columns:
            if col in df.columns:
                try:
                    # Tentar operações numéricas
                    mean_val = df[col].mean()
                    std_val = df[col].std()
                    validation_results[col] = {
                        "mean": mean_val,
                        "std": std_val,
                        "valid_count": df[col].notna().sum(),
                        "total_count": len(df),
                    }
                    print(f"  ✅ {col}: média={mean_val:.3f}, std={std_val:.3f}")
                except Exception as e:
                    print(f"  ❌ {col}: erro na validação - {e}")
                    validation_results[col] = {"error": str(e)}

        return validation_results


def main():
    """Função principal"""
    print("🔧 CORRETOR DE DATASET INTEGRADO")
    print("=" * 40)

    # Configuração
    data_path = (
        Path(__file__).parent.parent
        / "data"
        / "processed"
        / "integrated_neuro_swow.csv"
    )

    if not data_path.exists():
        print(f"❌ Arquivo não encontrado: {data_path}")
        sys.exit(1)

    # Executar correção
    fixer = IntegratedDatasetFixer()

    try:
        # Corrigir dataset
        df_fixed = fixer.fix_dataset(data_path)

        # Validar correção
        validation_results = fixer.validate_fix(df_fixed)

        print(f"\n🎯 RESULTADO FINAL: ✅ SUCESSO")

    except Exception as e:
        print(f"\n❌ Erro durante correção: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
