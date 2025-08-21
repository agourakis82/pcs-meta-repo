#!/bin/bash

# =============================================
# SCRIPT DE REGENERAÇÃO DOS NOTEBOOKS PRINCIPAIS
# Projeto: The Fractal Nature of an Entropically-Driven Society
# Última atualização: 2025-08-06 10:09
# Ambiente: clean_env
# =============================================

echo "🚀 Ativando ambiente virtual..."
source ../notebook/clean_env/bin/activate

echo "📁 Entrando no diretório de notebooks..."
cd NHB_Symbolic_Mainfold/notebook || exit 1

echo "🔄 Executando notebooks em ordem..."

for nb in 00_Overview_and_Readme 01_Load_and_Visualize_SWOW 01_SWOW_graph_analysis 02_Centrality_and_SymbolicMetrics 03_EntropicEmbeddings_and_CognitiveDistances 04_Map_Symbolic_Metrics_From_SWOW 05_Clustering_Symbolic_Manifold 06_Visualize_UMAP_Embeddings
do
    echo "▶️ Executando $nb.ipynb"
    jupyter nbconvert --to notebook --execute --inplace "$nb.ipynb"
done

echo "✅ Todos os notebooks foram regenerados com sucesso."
