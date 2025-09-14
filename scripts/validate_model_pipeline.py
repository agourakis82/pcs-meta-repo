#!/usr/bin/env python3
"""
🔍 VALIDAÇÃO AUTOMÁTICA DE PIPELINE DE MODELOS
Previne problemas de overfitting e qualidade de dados
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from datetime import datetime
import json

warnings.filterwarnings("ignore")


class ModelPipelineValidator:
    """Validador automático para pipeline de modelos ML"""

    def __init__(self):
        self.results = {}
        self.issues = []
        self.warnings = []

    def _clean_numeric_column(self, series, column_name):
        """Limpa uma coluna numérica convertendo valores problemáticos"""

        def convert_value(val):
            if pd.isna(val):
                return np.nan

            val_str = str(val).lower().strip()

            # Converter valores booleanos e problemáticos
            if val_str in ["false", "nan", "none", "null", ""]:
                return np.nan
            elif val_str == "true":
                return 1.0

            # Tentar converter para float
            try:
                return float(val)
            except (ValueError, TypeError):
                return np.nan

        cleaned_series = series.apply(convert_value)

        # Log de limpeza se necessário
        problematic_count = (
            series.astype(str).isin(["False", "True", "false", "true"]).sum()
        )
        if problematic_count > 0:
            print(
                f"  🔧 Coluna '{column_name}': {problematic_count} valores problemáticos convertidos"
            )

        return cleaned_series

    def validate_data_quality(self, df, target_col, feature_cols):
        """Valida qualidade dos dados antes do treinamento"""
        print("🔍 VALIDANDO QUALIDADE DOS DADOS...")

        # Verificar se as colunas existem
        missing_cols = []
        if target_col not in df.columns:
            missing_cols.append(target_col)

        for col in feature_cols:
            if col not in df.columns:
                missing_cols.append(col)

        if missing_cols:
            print(f"  ❌ COLUNAS FALTANTES: {missing_cols}")
            return False

        # Limpar e extrair target e features
        print("  🔧 Limpando dados numéricos...")
        y = self._clean_numeric_column(df[target_col], target_col)

        X = df[feature_cols].copy()
        for col in feature_cols:
            X[col] = self._clean_numeric_column(df[col], col)

        # Validações do target
        target_issues = self._validate_target(y, target_col)

        # Validações das features
        feature_issues = self._validate_features(X, feature_cols)

        # Validações gerais
        general_issues = self._validate_general(df)

        all_issues = target_issues + feature_issues + general_issues

        if all_issues:
            print("  ❌ PROBLEMAS ENCONTRADOS:")
            for issue in all_issues:
                print(f"    • {issue}")
            return False
        else:
            print("  ✅ Dados aprovados na validação")
            return True

    def _validate_target(self, y, target_col):
        """Valida variável target"""
        issues = []

        # Verificar se há dados válidos
        valid_data = y.dropna()
        if len(valid_data) == 0:
            issues.append(f"Target '{target_col}' não tem dados válidos")
            return issues

        if len(valid_data) < len(y) * 0.5:
            issues.append(
                f"Target '{target_col}' tem muitos valores faltantes ({len(valid_data)}/{len(y)})"
            )

        # Verificar valores únicos
        unique_ratio = valid_data.nunique() / len(valid_data)
        if unique_ratio < 0.01:
            issues.append(
                f"Target '{target_col}' tem poucos valores únicos ({unique_ratio:.3%})"
            )

        # Verificar variabilidade
        try:
            std_val = valid_data.std()
            if pd.isna(std_val) or std_val == 0:
                issues.append(f"Target '{target_col}' tem variabilidade zero (std=0)")
        except Exception:
            issues.append(f"Target '{target_col}' não pode calcular desvio padrão")

        # Verificar valores realistas
        try:
            min_val = valid_data.min()
            max_val = valid_data.max()
            if pd.notna(min_val) and pd.notna(max_val) and min_val == max_val:
                issues.append(f"Target '{target_col}' tem valor constante ({min_val})")
        except Exception:
            pass

        # Verificar valores negativos (se aplicável)
        if target_col in ["duration", "time", "fixation_duration"]:
            try:
                if (valid_data < 0).any():
                    issues.append(
                        f"Target '{target_col}' tem valores negativos impossíveis"
                    )
            except Exception:
                pass

        # Verificar outliers extremos
        try:
            mean_val = valid_data.mean()
            std_val = valid_data.std()
            max_val = valid_data.max()
            if pd.notna(mean_val) and pd.notna(std_val) and pd.notna(max_val):
                if max_val > mean_val + 10 * std_val:
                    issues.append(f"Target '{target_col}' tem outliers extremos")
        except Exception:
            pass

        return issues

    def _validate_features(self, X, feature_cols):
        """Valida features"""
        issues = []

        for col in feature_cols:
            # Verificar valores faltantes
            missing_pct = X[col].isnull().sum() / len(X)
            if missing_pct > 0.5:
                issues.append(
                    f"Feature '{col}' tem {missing_pct:.1%} valores faltantes"
                )

            # Verificar variabilidade
            try:
                valid_data = X[col].dropna()
                if len(valid_data) > 0:
                    std_val = valid_data.std()
                    if pd.isna(std_val) or std_val == 0:
                        issues.append(f"Feature '{col}' tem variabilidade zero")
                else:
                    issues.append(f"Feature '{col}' não tem dados válidos")
            except Exception:
                issues.append(f"Feature '{col}' não pode calcular variabilidade")

            # Verificar valores infinitos
            try:
                if np.isinf(X[col]).any():
                    issues.append(f"Feature '{col}' tem valores infinitos")
            except Exception:
                pass

        # Verificar correlações perfeitas entre features
        try:
            # Usar apenas colunas com dados válidos para correlação
            valid_cols = []
            for col in feature_cols:
                if X[col].dropna().nunique() > 1:  # Precisa ter variabilidade
                    valid_cols.append(col)

            if len(valid_cols) > 1:
                corr_matrix = X[valid_cols].corr()
                for i in range(len(corr_matrix.columns)):
                    for j in range(i + 1, len(corr_matrix.columns)):
                        corr_val = corr_matrix.iloc[i, j]
                        if pd.notna(corr_val) and abs(corr_val) > 0.99:
                            col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                            issues.append(
                                f"Correlação perfeita entre '{col1}' e '{col2}' ({corr_val:.3f})"
                            )
        except Exception as e:
            # Se não conseguir calcular correlações, não é um erro crítico
            pass

        return issues

    def _validate_general(self, df):
        """Validações gerais do dataset"""
        issues = []

        # Verificar duplicatas
        duplicates = df.duplicated().sum()
        if duplicates > len(df) * 0.1:
            issues.append(f"Muitas linhas duplicadas ({duplicates:,})")

        # Verificar tamanho mínimo
        if len(df) < 1000:
            issues.append(f"Dataset muito pequeno ({len(df):,} linhas)")

        return issues

    def validate_model_performance(self, results):
        """Valida performance dos modelos para detectar overfitting"""
        print("\n🔍 VALIDANDO PERFORMANCE DOS MODELOS...")

        issues = []

        for model_name, result in results.items():
            # Verificar performance suspeita
            if result.get("test_r2", 0) > 0.95:
                issues.append(
                    f"Modelo '{model_name}' tem performance suspeita (R²={result['test_r2']:.3f})"
                )

            # Verificar gaps de overfitting
            gap = result.get("overfitting_gap", 0)
            if gap > 0.15:
                issues.append(
                    f"Modelo '{model_name}' tem overfitting severo (gap={gap:.3f})"
                )
            elif gap > 0.1:
                self.warnings.append(
                    f"Modelo '{model_name}' tem overfitting moderado (gap={gap:.3f})"
                )

            # Verificar estabilidade da validação cruzada
            cv_std = result.get("cv_std", 0)
            if cv_std > 0.2:
                issues.append(
                    f"Modelo '{model_name}' tem CV instável (std={cv_std:.3f})"
                )

        if issues:
            print("  ❌ PROBLEMAS DE PERFORMANCE:")
            for issue in issues:
                print(f"    • {issue}")
            return False
        else:
            print("  ✅ Performance dos modelos aprovada")
            if self.warnings:
                print("  ⚠️ AVISOS:")
                for warning in self.warnings:
                    print(f"    • {warning}")
            return True

    def generate_validation_report(self, output_dir):
        """Gera relatório de validação"""
        report_path = Path(output_dir) / "validation_report.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "validation_status": "PASSED" if not self.issues else "FAILED",
            "issues_found": len(self.issues),
            "warnings_found": len(self.warnings),
            "issues": self.issues,
            "warnings": self.warnings,
            "results": self.results,
        }

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Relatório salvo em: {report_path}")
        return report

    def run_full_validation(
        self, data_path, target_col, feature_cols, model_results=None
    ):
        """Executa validação completa"""
        print("🚀 EXECUTANDO VALIDAÇÃO COMPLETA DO PIPELINE")
        print("=" * 60)

        try:
            # Carregar dados
            print(f"\n📥 Carregando dados de: {data_path}")
            df = pd.read_csv(data_path)
            print(f"  📊 Shape: {df.shape}")

            # Validar qualidade dos dados
            data_valid = self.validate_data_quality(df, target_col, feature_cols)

            # Validar performance dos modelos (se fornecida)
            model_valid = True
            if model_results:
                model_valid = self.validate_model_performance(model_results)

            # Resultado final
            overall_valid = data_valid and model_valid

            print(f"\n🎯 RESULTADO FINAL:")
            print(f"  Dados: {'✅ VÁLIDOS' if data_valid else '❌ INVÁLIDOS'}")
            print(f"  Modelos: {'✅ VÁLIDOS' if model_valid else '❌ INVÁLIDOS'}")
            print(f"  Geral: {'✅ APROVADO' if overall_valid else '❌ REPROVADO'}")

            # Gerar relatório
            output_dir = (
                Path(__file__).parent.parent / "reports" / "overfitting_diagnostic"
            )
            self.generate_validation_report(output_dir)

            return overall_valid

        except Exception as e:
            print(f"❌ Erro durante validação: {e}")
            return False


def main():
    """Função principal"""
    print("🔍 VALIDADOR DE PIPELINE DE MODELOS")
    print("=" * 50)

    # Configuração
    data_path = (
        Path(__file__).parent.parent
        / "data"
        / "processed"
        / "integrated_neuro_swow.csv"
    )
    target_col = "fixation_duration"
    feature_cols = ["entropy", "curvature", "coherence"]

    # Executar validação
    validator = ModelPipelineValidator()

    # Exemplo de resultados de modelos (normalmente viria do treinamento)
    example_results = {
        "Linear Regression": {"test_r2": 0.25, "overfitting_gap": 0.05, "cv_std": 0.03},
        "Random Forest": {"test_r2": 0.35, "overfitting_gap": 0.08, "cv_std": 0.04},
    }

    success = validator.run_full_validation(
        data_path=data_path,
        target_col=target_col,
        feature_cols=feature_cols,
        model_results=example_results,
    )

    if success:
        print("\n✅ Validação concluída com sucesso!")
    else:
        print("\n❌ Validação falhou - verifique os problemas identificados")
        sys.exit(1)


if __name__ == "__main__":
    main()
