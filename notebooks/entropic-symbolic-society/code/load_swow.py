import pickle
from pathlib import Path

import networkx as nx  # noqa: E402  # noqa: E402
import pandas as pd

# Caminho para o CSV
csv_path = "NHB_Symbolic_Mainfold/data/SWOW-EN.complete.20180827.csv"
out_path = "NHB_Symbolic_Mainfold/data/swow_graph.pkl"

# Carrega os dados
df = pd.read_csv(csv_path)

# Normaliza nomes de colunas
df.columns = [col.strip().lower() for col in df.columns]

# Usa 'cue' e ['r1', 'r2', 'r3'] como respostas
cue_col = "cue"
response_cols = ["r1", "r2", "r3"]

# Cria o grafo direcionado
G = nx.DiGraph()

for _, row in df.iterrows():
    cue = str(row[cue_col]).strip().lower()
    for r_col in response_cols:
        response = str(row[r_col]).strip().lower()
        if cue and response and cue != response and response != "nan":
            G.add_edge(cue, response, weight=1)

# Cria diretório de saída se necessário
Path(out_path).parent.mkdir(parents=True, exist_ok=True)


with open(out_path, "wb") as f:
    pickle.dump(G, f)

print("✅ Grafo criado!")
print(f"Nós: {G.number_of_nodes()}, Arestas: {G.number_of_edges()}")
