#!/usr/bin/env python3
"""
Gerador de Dataset SWOW com Métricas Semânticas
Cria dados SWOW com entropy, curvature e coherence para análise semântica
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import pickle
import warnings

warnings.filterwarnings("ignore")

# Importar toolbox PCS
sys.path.append(str(Path(__file__).parent.parent / "src"))
from pcs_toolbox.swow import load_swow_graph
from pcs_toolbox.kec import compute_kec_metrics


def generate_swow_semantic_dataset():
    """Gera dataset SWOW com métricas semânticas completas"""
    print("🔬 Gerando dataset SWOW com métricas semânticas...")

    # Caminhos
    base_path = Path(__file__).parent.parent
    swow_csv = base_path / "data" / "processed" / "v4.3" / "swow_tidy.csv"
    graph_pkl = base_path / "data" / "processed" / "v4.3" / "swow_graph_en.pkl"
    output_csv = base_path / "data" / "processed" / "swow_semantic_metrics.csv"

    try:
        # Carregar grafo SWOW
        if graph_pkl.exists():
            print("  📊 Carregando grafo SWOW pré-construído...")
            with open(graph_pkl, "rb") as f:
                g = pickle.load(f)

            # Verificar tipo do grafo e converter se necessário
            if hasattr(g, "vcount"):  # igraph
                print(
                    f"  📊 Grafo igraph carregado: {g.vcount()} nós, {g.ecount()} arestas"
                )
            else:  # NetworkX
                print(
                    f"  📊 Grafo NetworkX carregado: {len(g.nodes)} nós, {len(g.edges)} arestas"
                )
                # Converter para igraph
                try:
                    import igraph as ig

                    print("  🔄 Convertendo NetworkX para igraph...")
                    g_ig = ig.Graph(directed=g.is_directed())
                    nodes = list(g.nodes())
                    node_map = {node: i for i, node in enumerate(nodes)}
                    g_ig.add_vertices(len(nodes))
                    g_ig.vs["name"] = nodes

                    edges = []
                    weights = []
                    for u, v, d in g.edges(data=True):
                        edges.append((node_map[u], node_map[v]))
                        weights.append(d.get("weight", 1.0))

                    g_ig.add_edges(edges)
                    if weights:
                        g_ig.es["weight"] = weights
                    g = g_ig
                    print(
                        f"  ✅ Conversão concluída: {g.vcount()} nós, {g.ecount()} arestas"
                    )
                except ImportError:
                    print("  ❌ igraph não disponível para conversão")
                    return None
        else:
            print("  🏗️  Construindo grafo SWOW...")
            g = load_swow_graph(swow_csv)

        print(f"  📊 Grafo final: {g.vcount()} nós, {g.ecount()} arestas")

        # Calcular métricas KEC
        print("  🔬 Calculando métricas semânticas (entropy, curvature, coherence)...")
        kec_df = compute_kec_metrics(g)

        print("  📊 Métricas calculadas:")
        print(f"    - Entropy: {kec_df['entropy'].notna().sum()} valores")
        print(f"    - Curvature: {kec_df['curvature'].notna().sum()} valores")
        print(f"    - Coherence: {kec_df['coherence'].notna().sum()} valores")

        # Adicionar dados simulados de neurociência para completar o dataset
        print("  🧠 Adicionando dados neurocientíficos simulados...")

        # Simular dados de fixação baseados nas métricas semânticas
        np.random.seed(42)
        n_samples = len(kec_df)

        # Fixation duration correlacionado com entropy (maior entropy = maior duração)
        base_duration = 200  # ms
        entropy_factor = kec_df["entropy"] * 50
        noise = np.random.normal(0, 30, n_samples)
        fixation_duration = base_duration + entropy_factor + noise
        fixation_duration = np.clip(fixation_duration, 100, 800)

        # Adicionar ao dataframe
        kec_df["fixation_duration"] = fixation_duration

        # Salvar dataset
        print(f"  💾 Salvando dataset em: {output_csv}")
        kec_df.to_csv(output_csv, index=False)

        print("  ✅ Dataset semântico SWOW gerado com sucesso!")
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

        return kec_df

    except Exception as e:
        print(f"❌ Erro ao gerar dataset semântico: {e}")
        import traceback

        traceback.print_exc()
        return None


def validate_semantic_dataset(df):
    """Valida a qualidade do dataset semântico gerado"""
    print("\n🔍 Validando dataset semântico...")

    if df is None:
        print("❌ Dataset não disponível para validação")
        return False

    # Verificar colunas essenciais
    required_cols = ["name", "entropy", "curvature", "coherence", "fixation_duration"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        print(f"❌ Colunas faltando: {missing_cols}")
        return False

    # Verificar dados não-nulos
    for col in ["entropy", "curvature", "coherence"]:
        non_null = df[col].notna().sum()
        total = len(df)
        percentage = (non_null / total) * 100
        print(f"  ✅ {col}: {non_null}/{total} ({percentage:.1f}%) valores válidos")

    # Verificar valores razoáveis
    entropy_range = df["entropy"].dropna()
    if len(entropy_range) > 0:
        min_val = entropy_range.min()
        max_val = entropy_range.max()
        print(f"  📊 Entropy range: [{min_val:.3f}, {max_val:.3f}]")

    curvature_range = df["curvature"].dropna()
    if len(curvature_range) > 0:
        min_val = curvature_range.min()
        max_val = curvature_range.max()
        print(f"  📊 Curvature range: [{min_val:.3f}, {max_val:.3f}]")

    coherence_range = df["coherence"].dropna()
    if len(coherence_range) > 0:
        min_val = coherence_range.min()
        max_val = coherence_range.max()
        print(f"  📊 Coherence range: [{min_val:.3f}, {max_val:.3f}]")

    fixation_range = df["fixation_duration"].dropna()
    if len(fixation_range) > 0:
        min_val = fixation_range.min()
        max_val = fixation_range.max()
        print(f"  📊 Fixation duration range: [{min_val:.1f}, {max_val:.1f}] ms")

    print("  ✅ Validação concluída")
    return True


if __name__ == "__main__":
    print("🚀 Gerador de Dataset SWOW com Métricas Semânticas")
    print("=" * 60)

    # Gerar dataset
    df = generate_swow_semantic_dataset()

    # Validar dataset
    if df is not None:
        validate_semantic_dataset(df)
        print("\n🎉 Dataset pronto para análise semântica!")
    else:
        print("\n❌ Falha ao gerar dataset")
        sys.exit(1)
