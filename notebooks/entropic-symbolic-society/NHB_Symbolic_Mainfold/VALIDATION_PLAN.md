# Plano de Validação — NHB_Symbolic_Mainfold

## 0) Escopo
Consolidar testes formais para: (H1) Distância simbólica ↔ entropia/RT/força; (H2) Centralidade/clustering ↔ ancoragem/curvatura; (H3) Métricas simbólicas ↔ medidas neurais (EEG/fMRI); (H4) Atratores/estabilidade.

## 1) Testes & Métricas
- H1 Distância ↔ RT/força/entropia
  - Regressões RT ~ distância + frequência + concreteness + polissêmia
  - Limiar: efeitos estáveis pós-controle; replicação split-half
- H2 Centralidade/clustering ↔ ancoragem
  - Correlações/mistos entre centralidades e atributos lexicais; ANOVA por comunidades
- H3 Semântico ↔ Neural (RSA)
  - fMRI narrativas: RSA (matriz SWOW vs. padrões por ROI/whole-brain)
  - EEG: N400 e RT em priming/decisão lexical vs. força/distância SWOW
  - Limiar: ρ_RSA ≥ 0.30 em ≥ 2 datasets; efeito N400 consistente
- H4 Atratores/Estabilidade
  - Estabilidade de rótulos: Jaccard/ARI sob variações (n_neighbors, min_dist, k)
  - Modelos nulos: redes configuracionais; comparação silhouette/CH/DB

## 2) Notebooks novos (07–10)
- 07_Validation_Semantic_Communities.ipynb
  - Comunidades (Louvain/Infomap); estabilidade; confundidores
- 08_RSA_fMRI_Narratives.ipynb
  - Pré-processamento BIDS; alinhamento texto→tempo; RSA; correções múltiplas
- 09_EEG_Priming_N400.ipynb
  - ERP N400 single-trial; regressões com preditores SWOW; controles
- 10_Robustness_and_Nulls.ipynb
  - Perturbações; subamostragem; redes nulas configuracionais; relatórios comparativos

## 3) Outputs esperados (salvos por código)
- Tabelas: coeficientes regressão, ρ_RSA por ROI, métricas de estabilidade
- Figuras: mapas de comunidades; curvas RT~distância; topoplots N400; mapas RSA
- Artefatos: CSV/NPY/PNG em `data/` e `results/`; logs de seeds e versões

## 4) Parâmetros & seeds (reprodutibilidade)
- random_state = 42 em UMAP/KMeans/SVD; registrar versões (requirements), datas, e DOIs

## 5) Pré-registro (OSF)
- Objetivos, hipóteses, métricas, thresholds, datasets-alvo, e planos de exclusão/controle
