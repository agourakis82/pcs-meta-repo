#!/usr/bin/env python3
"""
🔍 DIAGNÓSTICO DE DEGENERAÇÃO DE TARGETS
Analisa problemas específicos de degeneração em variáveis target
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from datetime import datetime
import json

# Adicionar src ao path para importar contratos
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from contracts_v4_4 import validate_target_degeneracy
except ImportError:
    try:
        from contracts_v4 import validate_target_degeneracy
    except ImportError:
        print("⚠️ Não foi possível importar validate_target_degeneracy")
        validate_target_degeneracy = None

warnings.filterwarnings("ignore")


class TargetDegeneracyDiagnostic:
    """Diagnóstico especializado para degeneração de targets"""

    def __init__(self):
        self.results = {}
        self.issues = []
        self.recommendations = []

    def analyze_column_degeneracy(self, series, column_name):
        """Analisa degeneração em uma coluna específica"""
        print(f"\n🔍 Analisando '{column_name}'...")

        # Estatísticas básicas
        total_values = len(series)
        non_null_values = series.notna().sum()
        null_values = series.isna().sum()

        if non_null_values == 0:
            return {
                "column": column_name,
                "status": "EMPTY",
                "issue": "Coluna completamente vazia",
                "recommendation": "Remover coluna ou preencher com dados válidos",
            }

        # Análise de valores únicos
        unique_values = series.nunique()
        unique_ratio = unique_values / non_null_values if non_null_values > 0 else 0

        # Análise de variabilidade
        try:
            numeric_series = pd.to_numeric(series, errors="coerce")
            std_dev = numeric_series.std()
            mean_val = numeric_series.mean()
            cv = std_dev / mean_val if mean_val != 0 else float("inf")
        except:
            std_dev = None
            mean_val = None
            cv = None

        # Análise de valores problemáticos
        str_series = series.astype(str)
        problematic_values = []
        for val in str_series.unique():
            val_lower = val.lower()
            if val_lower in ["false", "true", "nan", "none", "null", ""]:
                count = (str_series.str.lower() == val_lower).sum()
                problematic_values.append(f"{val}({count})")

        # Determinar status
        status = "HEALTHY"
        issue = None
        recommendation = None

        if unique_values == 1:
            status = "CONSTANT"
            issue = f"Valor constante: {series.iloc[0]}"
            recommendation = "Substituir por dados com variabilidade"
        elif unique_ratio < 0.01:
            status = "DEGENERATE"
            issue = f"Baixa variabilidade: {unique_ratio:.4%} valores únicos"
            recommendation = "Aumentar variabilidade dos dados"
        elif std_dev is not None and std_dev == 0:
            status = "ZERO_VARIANCE"
            issue = "Variância zero"
            recommendation = "Adicionar ruído realístico aos dados"
        elif problematic_values:
            status = "PROBLEMATIC_VALUES"
            issue = f"Valores problemáticos: {', '.join(problematic_values)}"
            recommendation = "Limpar valores problemáticos"

        result = {
            "column": column_name,
            "status": status,
            "total_values": total_values,
            "non_null_values": non_null_values,
            "null_values": null_values,
            "unique_values": unique_values,
            "unique_ratio": unique_ratio,
            "std_dev": std_dev,
            "mean": mean_val,
            "cv": cv,
            "problematic_values": problematic_values,
            "issue": issue,
            "recommendation": recommendation,
        }

        # Imprimir resultados
        print(f"  📊 Status: {status}")
        print(f"  📈 Valores: {non_null_values}/{total_values} válidos")
        print(f"  🎯 Únicos: {unique_values} ({unique_ratio:.4%})")
        if std_dev is not None:
            print(f"  📏 Variabilidade: μ={mean_val:.3f}, σ={std_dev:.3f}")
        if problematic_values:
            print(f"  ⚠️ Problemáticos: {', '.join(problematic_values)}")
        if issue:
            print(f"  ❌ Problema: {issue}")
        if recommendation:
            print(f"  💡 Recomendação: {recommendation}")

        return result

    def diagnose_dataset(self, df_path):
        """Diagnóstica todo o dataset"""
        print("🔍 DIAGNÓSTICO DE DEGENERAÇÃO DE TARGETS")
        print("=" * 50)

        # Carregar dados
        print(f"\n📥 Carregando: {df_path}")
        df = pd.read_csv(df_path)
        print(f"  📊 Shape: {df.shape}")

        # Colunas target principais
        target_columns = [
            "fixation_duration",
            "ffd_ms",
            "gd_ms",
            "trt_ms",
            "theta",
            "alpha",
            "beta",
            "entropy",
            "curvature",
            "coherence",
        ]

        # Analisar cada coluna target
        available_targets = [col for col in target_columns if col in df.columns]
        print(f"\n🎯 Colunas target encontradas: {available_targets}")

        results = {}
        for col in available_targets:
            results[col] = self.analyze_column_degeneracy(df[col], col)

        # Análise usando validate_target_degeneracy se disponível
        if validate_target_degeneracy:
            print(f"\n🔬 VALIDAÇÃO OFICIAL DE DEGENERAÇÃO")
            validation_result = validate_target_degeneracy(df, available_targets)
            print(f"  ✅ Válido: {validation_result['valid']}")
            if validation_result["errors"]:
                print(f"  ❌ Erros: {validation_result['errors']}")
            if validation_result["warnings"]:
                print(f"  ⚠️ Avisos: {validation_result['warnings']}")

        # Resumo geral
        print(f"\n📋 RESUMO GERAL")
        healthy_count = sum(1 for r in results.values() if r["status"] == "HEALTHY")
        problem_count = len(results) - healthy_count

        print(f"  ✅ Colunas saudáveis: {healthy_count}")
        print(f"  ❌ Colunas problemáticas: {problem_count}")

        if problem_count > 0:
            print(f"\n🚨 PROBLEMAS IDENTIFICADOS:")
            for col, result in results.items():
                if result["status"] != "HEALTHY":
                    print(f"  • {col}: {result['status']} - {result['issue']}")

        # Salvar relatório
        report = {
            "timestamp": datetime.now().isoformat(),
            "dataset_path": str(df_path),
            "dataset_shape": df.shape,
            "target_columns_analyzed": available_targets,
            "results": results,
            "summary": {
                "healthy_columns": healthy_count,
                "problematic_columns": problem_count,
                "total_analyzed": len(results),
            },
        }

        if validate_target_degeneracy:
            report["official_validation"] = validation_result

        report_path = "reports/target_degeneracy_diagnostic.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n💾 Relatório salvo: {report_path}")

        return results

    def generate_fix_recommendations(self, results):
        """Gera recomendações específicas de correção"""
        print(f"\n💡 RECOMENDAÇÕES DE CORREÇÃO")
        print("=" * 40)

        recommendations = []

        for col, result in results.items():
            if result["status"] != "HEALTHY":
                rec = {
                    "column": col,
                    "problem": result["issue"],
                    "action": result["recommendation"],
                    "priority": self._get_priority(result["status"]),
                }
                recommendations.append(rec)

        # Ordenar por prioridade
        recommendations.sort(key=lambda x: x["priority"])

        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['column']}")
            print(f"   Problema: {rec['problem']}")
            print(f"   Ação: {rec['action']}")
            print(f"   Prioridade: {rec['priority']}")
            print()

        return recommendations

    def _get_priority(self, status):
        """Determina prioridade baseada no status"""
        priority_map = {
            "CONSTANT": 1,
            "ZERO_VARIANCE": 1,
            "DEGENERATE": 2,
            "PROBLEMATIC_VALUES": 3,
            "EMPTY": 4,
        }
        return priority_map.get(status, 5)


def main():
    """Função principal"""
    print("🔍 DIAGNÓSTICO DE DEGENERAÇÃO DE TARGETS")
    print("=" * 50)

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

    # Executar diagnóstico
    diagnostic = TargetDegeneracyDiagnostic()

    try:
        results = diagnostic.diagnose_dataset(data_path)
        recommendations = diagnostic.generate_fix_recommendations(results)

        print(f"\n🎯 DIAGNÓSTICO CONCLUÍDO")
        print(
            f"✅ {len([r for r in results.values() if r['status'] == 'HEALTHY'])} colunas saudáveis"
        )
        print(
            f"❌ {len([r for r in results.values() if r['status'] != 'HEALTHY'])} colunas problemáticas"
        )
        print(f"💡 {len(recommendations)} recomendações geradas")

    except Exception as e:
        print(f"\n❌ Erro durante diagnóstico: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
