#!/usr/bin/env python3
"""
Script para extrair durações reais de fixação dos dados ZuCo
Parte do Plano de Recuperação PCS v1.0
"""

import os
import pandas as pd
import numpy as np
import logging
from pathlib import Path
import json
from scipy.io import loadmat
import warnings

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

# Helpers to safely coerce MAT arrays to numeric and avoid isnan on non-numeric arrays
SKIP_TEXT_KEYS = {
    "comments",
    "colheader",
    "messages",
    "eyeevent",
    "eyeEvent",
    "eye_event",
}


def _to_scalar(x):
    try:
        if isinstance(x, np.ndarray):
            if x.size == 1:
                return x.item()
    except Exception:
        pass
    return x


def to_coerced_numeric(arr):
    """
    Flatten and coerce an arbitrary array-like (including MATLAB cell/object arrays)
    into a finite float numpy array. Non-numeric entries become NaN and are dropped.
    """
    # Use object dtype to avoid numpy trying to upcast mixed arrays prematurely
    a = np.asarray(arr, dtype=object).ravel()
    flat = [_to_scalar(x) for x in a]
    # Convert elementwise with pandas, coercing failures to NaN
    series = pd.to_numeric(pd.Series(flat, dtype="object"), errors="coerce")
    numeric = series.to_numpy(dtype=float)
    if numeric.size == 0:
        return numeric
    # Keep only finite values
    finite_mask = np.isfinite(numeric)
    return numeric[finite_mask]


def load_zuco_csv_files():
    """Carrega arquivos CSV do ZuCo com dados de fixação"""

    print("📊 CARREGANDO ARQUIVOS CSV DO ZUCO")
    print("=" * 50)

    csv_files = []
    base_paths = [
        "data/raw_public/zuco/v1/preprocessed",
        "data/raw_public/zuco/v1/task1_SR/Preprocessed",
        "data/raw_public/zuco/v2/task2__TSR/Preprocessed",
    ]

    for base_path in base_paths:
        if not os.path.exists(base_path):
            continue

        print(f"\n📁 Processando: {base_path}")

        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith(".csv"):
                    file_path = os.path.join(root, file)
                    try:
                        df = pd.read_csv(file_path)
                        print(
                            f"  ✅ {file}: {df.shape[0]} linhas, {df.shape[1]} colunas"
                        )

                        # Verificar se tem colunas de fixação
                        fixation_cols = [
                            col
                            for col in df.columns
                            if any(
                                term in col.lower()
                                for term in ["fixation", "duration", "gaze", "dwell"]
                            )
                        ]

                        if fixation_cols:
                            print(f"    📊 Colunas de fixação: {fixation_cols}")
                            csv_files.append(
                                {
                                    "path": file_path,
                                    "data": df,
                                    "fixation_cols": fixation_cols,
                                    "source": os.path.relpath(
                                        root, "data/raw_public/zuco"
                                    ),
                                }
                            )
                        else:
                            print(f"    ⚠️  Sem colunas de fixação identificadas")

                    except Exception as e:
                        print(f"  ❌ Erro ao carregar {file}: {e}")

    return csv_files


def load_zuco_mat_files():
    """Carrega arquivos MAT do ZuCo com dados de EEG/ET"""

    print("\n🧠 CARREGANDO ARQUIVOS MAT DO ZUCO")
    print("=" * 50)

    mat_files = []
    base_paths = [
        "data/raw_public/zuco/v1/preprocessed",
        "data/raw_public/zuco/v1/task1_SR/Preprocessed",
        "data/raw_public/zuco/v2/task2__TSR/Preprocessed",
    ]

    for base_path in base_paths:
        if not os.path.exists(base_path):
            continue

        print(f"\n📁 Processando: {base_path}")

        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith(".mat"):
                    file_path = os.path.join(root, file)
                    try:
                        mat_data = loadmat(file_path)
                        print(f"  ✅ {file}: {len(mat_data.keys())} chaves")

                        # Verificar estrutura do arquivo MAT
                        relevant_keys = [
                            k for k in mat_data.keys() if not k.startswith("__")
                        ]

                        if relevant_keys:
                            print(f"    🔑 Chaves relevantes: {relevant_keys}")
                            mat_files.append(
                                {
                                    "path": file_path,
                                    "data": mat_data,
                                    "keys": relevant_keys,
                                    "source": os.path.relpath(
                                        root, "data/raw_public/zuco"
                                    ),
                                }
                            )

                    except Exception as e:
                        print(f"  ❌ Erro ao carregar {file}: {e}")

    return mat_files


def extract_fixation_durations_from_csv(csv_files):
    """Extrai durações de fixação dos arquivos CSV"""

    print("\n📊 EXTRAINDO DURAÇÕES DE FIXAÇÃO DOS CSV")
    print("=" * 50)

    all_fixation_data = []

    for csv_info in csv_files:
        df = csv_info["data"]
        fixation_cols = csv_info["fixation_cols"]
        source = csv_info["source"]

        print(f"\n📁 Processando: {source}")

        for col in fixation_cols:
            if col in df.columns:
                # Verificar variabilidade
                values = df[col].dropna()
                if len(values) > 0:
                    std_val = values.std()
                    unique_ratio = values.nunique() / len(values)

                    print(f"  📊 {col}:")
                    print(f"    • Valores: {len(values)}")
                    print(f"    • Únicos: {values.nunique()} ({unique_ratio:.3f})")
                    print(f"    • Média: {values.mean():.3f}")
                    print(f"    • Desvio: {std_val:.3f}")
                    print(f"    • Range: {values.min():.3f} - {values.max():.3f}")

                    # Só incluir se tiver variabilidade adequada
                    if std_val > 0 and unique_ratio > 0.01:
                        fixation_df = pd.DataFrame(
                            {
                                "fixation_duration": values,
                                "source": source,
                                "column": col,
                                "subject_id": df.get("subject", "unknown"),
                                "word": df.get("word", ""),
                                "sentence_id": df.get("sentence_id", ""),
                                "word_id": df.get("word_id", ""),
                            }
                        )
                        all_fixation_data.append(fixation_df)
                        print(f"    ✅ Incluído: {len(values)} valores válidos")
                    else:
                        print(f"    ❌ Rejeitado: baixa variabilidade")

    return all_fixation_data


def extract_fixation_durations_from_mat(mat_files):
    """Extrai durações de fixação dos arquivos MAT"""

    print("\n🧠 EXTRAINDO DURAÇÕES DE FIXAÇÃO DOS MAT")
    print("=" * 50)

    all_fixation_data = []

    for mat_info in mat_files:
        mat_data = mat_info["data"]
        keys = mat_info["keys"]
        source = mat_info["source"]

        print(f"\n📁 Processando: {source}")

        for key in keys:
            try:
                # Ignorar chaves claramente textuais/mistas
                if key in SKIP_TEXT_KEYS:
                    print(f"  ⏭️  {key}: ignorado (conteúdo não numérico esperado)")
                    continue

                data = mat_data[key]

                # Tentar diferentes estruturas de dados MAT
                if hasattr(data, "dtype") and data.dtype.names:
                    # Structured array
                    for field_name in data.dtype.names:
                        # Pular campos textuais conhecidos
                        if field_name in SKIP_TEXT_KEYS:
                            print(f"  ⏭️  {key}.{field_name}: ignorado (campo textual)")
                            continue

                        if any(
                            term in field_name.lower()
                            for term in ["fixation", "duration", "gaze", "dwell"]
                        ):
                            numeric = to_coerced_numeric(data[field_name])

                            if numeric.size > 0:
                                std_val = float(np.std(numeric))
                                unique_vals = np.unique(numeric)
                                unique_ratio = len(unique_vals) / len(numeric)

                                print(f"  📊 {key}.{field_name}:")
                                print(f"    • Valores: {len(numeric)}")
                                print(
                                    f"    • Únicos: {len(unique_vals)} ({unique_ratio:.3f})"
                                )
                                print(f"    • Média: {np.mean(numeric):.3f}")
                                print(f"    • Desvio: {std_val:.3f}")

                                if std_val > 0 and unique_ratio > 0.01:
                                    fixation_df = pd.DataFrame(
                                        {
                                            "fixation_duration": numeric,
                                            "source": source,
                                            "column": f"{key}.{field_name}",
                                            "subject_id": "mat_file",
                                            "word": "",
                                            "sentence_id": "",
                                            "word_id": "",
                                        }
                                    )
                                    all_fixation_data.append(fixation_df)
                                    print(
                                        f"    ✅ Incluído: {len(numeric)} valores válidos"
                                    )
                                else:
                                    print("    ❌ Rejeitado: baixa variabilidade")
                            else:
                                print(
                                    f"    ❌ Sem dados numéricos válidos após coerção"
                                )

                elif isinstance(data, np.ndarray) and data.size > 0:
                    # Array simples
                    numeric = to_coerced_numeric(data)

                    if numeric.size > 10:  # Mínimo de valores
                        std_val = float(np.std(numeric))
                        unique_vals = np.unique(numeric)
                        unique_ratio = len(unique_vals) / len(numeric)

                        print(f"  📊 {key} (array):")
                        print(f"    • Valores: {len(numeric)}")
                        print(f"    • Únicos: {len(unique_vals)} ({unique_ratio:.3f})")
                        print(f"    • Média: {np.mean(numeric):.3f}")
                        print(f"    • Desvio: {std_val:.3f}")

                        if std_val > 0 and unique_ratio > 0.01:
                            fixation_df = pd.DataFrame(
                                {
                                    "fixation_duration": numeric,
                                    "source": source,
                                    "column": key,
                                    "subject_id": "mat_file",
                                    "word": "",
                                    "sentence_id": "",
                                    "word_id": "",
                                }
                            )
                            all_fixation_data.append(fixation_df)
                            print(f"    ✅ Incluído: {len(numeric)} valores válidos")
                        else:
                            print("    ❌ Rejeitado: baixa variabilidade")
                    else:
                        print("  ❌ Sem dados numéricos válidos após coerção")
                else:
                    print(f"  ⏭️  {key}: tipo/estrutura não suportado ou vazio")

            except Exception as e:
                print(f"  ❌ Erro ao processar {key}: {e}")

    return all_fixation_data


def combine_and_save_fixation_data(csv_data, mat_data):
    """Combina e salva os dados de fixação extraídos"""

    print("\n💾 COMBINANDO E SALVANDO DADOS")
    print("=" * 40)

    all_data = csv_data + mat_data

    if not all_data:
        print("❌ Nenhum dado válido encontrado!")
        return None

    # Combinar todos os DataFrames
    combined_df = pd.concat(all_data, ignore_index=True)

    print(f"📊 Dados combinados:")
    print(f"  • Total de registros: {len(combined_df)}")
    print(f"  • Fontes únicas: {combined_df['source'].nunique()}")
    print(f"  • Colunas únicas: {combined_df['column'].nunique()}")

    # Estatísticas finais
    fixation_values = combined_df["fixation_duration"]
    print(f"\n📈 Estatísticas finais:")
    print(f"  • Média: {fixation_values.mean():.3f}")
    print(f"  • Desvio padrão: {fixation_values.std():.3f}")
    print(f"  • Valores únicos: {fixation_values.nunique()}")
    print(f"  • Ratio únicos: {fixation_values.nunique() / len(fixation_values):.3f}")
    print(f"  • Range: {fixation_values.min():.3f} - {fixation_values.max():.3f}")

    # Salvar arquivo
    output_path = "data/processed/zuco_real_fixation_durations.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined_df.to_csv(output_path, index=False)

    print(f"\n💾 Arquivo salvo: {output_path}")

    # Criar relatório
    report = {
        "total_records": len(combined_df),
        "unique_sources": combined_df["source"].nunique(),
        "unique_columns": combined_df["column"].nunique(),
        "fixation_stats": {
            "mean": float(fixation_values.mean()),
            "std": float(fixation_values.std()),
            "min": float(fixation_values.min()),
            "max": float(fixation_values.max()),
            "unique_count": int(fixation_values.nunique()),
            "unique_ratio": float(fixation_values.nunique() / len(fixation_values)),
        },
        "sources": combined_df["source"].value_counts().to_dict(),
        "columns": combined_df["column"].value_counts().to_dict(),
    }

    report_path = "reports/zuco_fixation_extraction_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"📄 Relatório salvo: {report_path}")

    return combined_df


def main():
    """Função principal"""

    print("🚀 INICIANDO EXTRAÇÃO DE DADOS REAIS DE FIXAÇÃO")
    print("=" * 60)

    try:
        # Passo 1: Carregar arquivos CSV
        csv_files = load_zuco_csv_files()

        # Passo 2: Carregar arquivos MAT
        mat_files = load_zuco_mat_files()

        # Passo 3: Extrair dados de fixação dos CSV
        csv_fixation_data = extract_fixation_durations_from_csv(csv_files)

        # Passo 4: Extrair dados de fixação dos MAT
        mat_fixation_data = extract_fixation_durations_from_mat(mat_files)

        # Passo 5: Combinar e salvar
        final_df = combine_and_save_fixation_data(csv_fixation_data, mat_fixation_data)

        if final_df is not None:
            print("\n" + "=" * 60)
            print("🎯 EXTRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 60)
            print(f"✅ Dados extraídos: {len(final_df)} registros")
            print(
                f"✅ Variabilidade confirmada: {final_df['fixation_duration'].std():.3f}"
            )
            print(f"✅ Próximo passo: Reintegrar com dados SWOW")
            return True
        else:
            print("\n❌ EXTRAÇÃO FALHOU - Nenhum dado válido encontrado")
            return False

    except Exception as e:
        logger.error(f"Erro durante extração: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
