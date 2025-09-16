#!/usr/bin/env python3
"""
Gerador de Dataset SWOW-EN Completo com Métricas Semânticas
Cria dados SWOW-EN completos com entropy, curvature e coherence
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# Importar toolbox PCS
sys.path.append(str(Path(__file__).parent.parent / "src"))
from pcs_toolbox.swow import load_swow_graph
from pcs_toolbox.kec import compute_kec_metrics


def generate_complete_swow_dataset(sample_size=50000):
    """Gera dataset SWOW-EN completo com métricas semânticas"""
    print("🔬 Gerando dataset SWOW-EN completo com métricas semânticas...")

    # Caminhos
    base_path = Path(__file__).parent.parent
    swow_complete = (
        base_path
        / "data"
        / "raw_public"
        / "swow"
        / "en"
        / "SWOW-EN.complete.20180827.csv"
    )
    output_csv = base_path / "data" / "processed" / "swow_en_semantic_complete.csv"

    try:
        # Carregar dados SWOW completos
        print("  📊 Carregando dados SWOW-EN completos...")
        df = pd.read_csv(swow_complete, low_memory=True)
        print(f"  📊 Dados carregados: {len(df):,} associações")

        # Extrair pares cue-response únicos com pesos
        print("  🔄 Processando pares cue-response...")
        pairs_df = df[["cue", "R1", "R2", "R3"]].copy()

        # Criar lista de pares com pesos
        pairs = []
        for _, row in pairs_df.iterrows():
            cue = str(row["cue"]).lower().strip()
            for i, response_col in enumerate(["R1", "R2", "R3"], 1):
                response = str(row[response_col]).lower().strip()
                if response and response != "nan":
                    # Peso maior para R1, menor para R3
                    weight = 4 - i  # R1=3, R2=2, R3=1
                    pairs.append((cue, response, weight))

        # Criar DataFrame de pares
        pairs_df = pd.DataFrame(pairs, columns=["cue", "response", "weight"])
        print(f"  📊 Pares extraídos: {len(pairs_df):,}")

        # Amostrar se necessário
        if len(pairs_df) > sample_size:
            print(f"  📊 Amostrando {sample_size:,} pares...")
            pairs_df = pairs_df.sample(n=sample_size, random_state=42)

        # Salvar pares para construir grafo
        temp_pairs = base_path / "data" / "processed" / "temp_swow_pairs.csv"
        pairs_df.to_csv(temp_pairs, index=False)

        # Construir grafo usando a função existente
        print("  🏗️  Construindo grafo SWOW...")
        g = load_swow_graph(temp_pairs)

        print(f"  📊 Grafo construído: {g.vcount()} nós, {g.ecount()} arestas")

        # Calcular métricas KEC
        print("  🔬 Calculando métricas semânticas (entropy, curvature, coherence)...")
        kec_df = compute_kec_metrics(g)

        print("  📊 Métricas calculadas:")
        print(f"    - Entropy: {kec_df['entropy'].notna().sum()} valores")
        print(f"    - Curvature: {kec_df['curvature'].notna().sum()} valores")
        print(f"    - Coherence: {kec_df['coherence'].notna().sum()} valores")

        # Adicionar dados simulados de neurociência
        print("  🧠 Adicionando dados neurocientíficos simulados...")

        np.random.seed(42)
        n_samples = len(kec_df)

        # Fixation duration correlacionado com entropy
        base_duration = 200  # ms
        entropy_factor = kec_df["entropy"] * 50
        noise = np.random.normal(0, 30, n_samples)
        fixation_duration = base_duration + entropy_factor + noise
        fixation_duration = np.clip(fixation_duration, 100, 800)

        kec_df["fixation_duration"] = fixation_duration

        # Salvar dataset
        print(f"  💾 Salvando dataset em: {output_csv}")
        kec_df.to_csv(output_csv, index=False)

        print("  ✅ Dataset SWOW-EN completo gerado!")
        print(f"  📊 Shape final: {kec_df.shape}")
        print(f"  📊 Colunas: {list(kec_df.columns)}")

        # Estatísticas básicas
        print("\n📈 Estatísticas das métricas:")
        for col in ["entropy", "curvature", "coherence", "fixation_duration"]:
            if col in kec_df.columns:
                values = kec_df[col].dropna()
                print(f"  {col}:")
                print(f"    Média: {values.mean():.3f}")
                print(f"    Desvio: {values.std():.3f}")
                print(f"    Mediana: {values.median():.3f}")

        # Limpar arquivo temporário
        if temp_pairs.exists():
            temp_pairs.unlink()

        return kec_df

    except Exception as e:
        print(f"❌ Erro ao gerar dataset completo: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("🚀 Gerador de Dataset SWOW-EN Completo")
    print("=" * 60)

    # Gerar dataset completo
    df = generate_complete_swow_dataset()

    if df is not None:
        print("\n🎉 Dataset SWOW-EN completo pronto para análise semântica!")
        print(f"📊 Dataset salvo em: data/processed/swow_en_semantic_complete.csv")
    else:
        print("\n❌ Falha ao gerar dataset completo")
        sys.exit(1)
