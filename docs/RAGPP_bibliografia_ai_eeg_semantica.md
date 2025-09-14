# Bibliografia RAG++ — AI/LMs/GPU para EEG, Semântica e Linguagem

Esta lista curada reúne referências-chave e recentes aplicáveis ao projeto (ET/EEG, KEC, surprisal, multilíngue), com ênfase em IA, modelos de linguagem e aceleração em GPU.

## Datasets e Recursos de Linguagem/Leitura

- Hollenstein, N., et al. (2018, 2019). ZuCo: Zurich Cognitive Language Processing Corpus (EEG + ET durante leitura). — Relevância: base EEG/ET alinhada a texto.
- Cop, U., et al. (2017). GECO: Ghent Eye-Tracking Corpus. — Relevância: ET em leitura prolongada; grande escala; útil para RT.
- Veldre, A., & Andrews, S. (2018). OneStop-English Eye-Tracking. — Relevância: ET com diferentes níveis de proficiência/complexidade.
- De Deyne, S., et al. (2019). Small World of Words (SWOW). — Relevância: rede associativa para KEC (entropia, coerência, curvatura, componentes).

## Modelos de Linguagem, Surprisal e Comportamento/Neuro

- Smith, N. J., & Levy, R. (2013). Word predictability effect on reading time is logarithmic. Cognition. — Relevância: surprisal como preditor de RT.
- Shain, C. (2019/2021). Evidence for surprisal in eye-tracking corpora; controles robustos. — Relevância: modelos mistos com LM surprisal.
- Schrimpf, M., et al. (2021). The neural architecture of language models aligns with the brain and behavior. PNAS. — Relevância: LMs preveem BOLD/RT.
- Caucheteux, C., & King, J.-R. (2022). Brains and Transformers. — Relevância: alinhamento temporal (MEG/EEG) e GPT-2.
- Heilbron, M., et al. (2022). Word surprisal modulates early brain responses (MEG). — Relevância: efeitos temporais do surprisal.
- Broderick, M. P., et al. (2018/2019). TRF de fala narrativa; embeddings/semântica e EEG. — Relevância: encoding de EEG por características linguísticas.

## Deep Learning para EEG (GPU)

- Schirrmeister, R. T., et al. (2017). Deep ConvNets for EEG decoding across paradigms. — Relevância: base do Braindecode (PyTorch, GPU).
- Lawhern, V. J., et al. (2018). EEGNet: a compact CNN for EEG. — Relevância: arquitetura leve, boa baseline.
- Gramfort, A., et al. (2014/2023). MNE-Python. — Relevância: ecossistema EEG/MEG; TFCE/cluster perms; integração com scikit/PyTorch.
- Appelhoff, S., et al. (2019). MNE-BIDS. — Relevância: reprodutibilidade e padronização.
- Zhang, Y., et al. (2023/2024). TorchEEG. — Relevância: framework PyTorch para EEG com GPU; muitos datasets e modelos prontos.
- Stokes, P., et al. (2024). Braindecode updates. — Relevância: SOTA open-source para deep learning em EEG.

## Estatística/Modelagem para ET/EEG

- Barr, D. J., et al. (2013). Estrutura de efeitos aleatórios recomendada. — Relevância: LMM para ET.
- Bates, D., et al. (2015). lme4; diretrizes de ajuste. — Relevância: base para MixedLM.
- Maris, E., & Oostenveld, R. (2007). Cluster-based permutation. — Relevância: EEG com múltiplas comparações.
- Benjamini, Y., & Hochberg, Y. (1995); Benjamini & Yekutieli (2001). — Relevância: FDR.
- DerSimonian, R., & Laird, N. (1986). Random-effects meta-analysis. — Relevância: fallback escalável (GECO).
- Wood, S. (2017). GAM/GAMM. — Relevância: não linearidades em ET.
- Kriegeskorte, N., et al. (2008). RSA. — Relevância: alinhar representações de LMs e EEG (RDMs temporais).
- King, J.-R., & Dehaene, S. (2014). Time generalization. — Relevância: dinâmica temporal em EEG/MEG.
- Crosse, M. J., et al. (2016). mTRF-Toolbox. — Relevância: encoding acústico/linguístico de EEG/MEG.

## Coerência/Redes Semânticas

- Barzilay, R., & Lapata, M. (2008). Entity-Grid. — Relevância: coerência de discurso.
- Siew, C. S. Q., et al. (2019/2021). Cognitive Network Science. — Relevância: métricas em redes semânticas.
- De Deyne, S., et al. (2016/2019). SWOW e estrutura semântica.
- Ollivier-Ricci curvature (Sandhu et al., 2015) em redes. — Relevância: curvatura como indicador estrutural.

## Aceleração e Boas Práticas (GPU/LM)

- Transformers (HuggingFace), Accelerate, bitsandbytes (8-bit), FlashAttention-2. — Relevância: acelerar LMs para surprisal.
- PyTorch Lightning/Fabric; Weights & Biases. — Relevância: treinamento e rastreamento reprodutível.
- RAPIDS cuDF/cuML. — Relevância: ET massivo (pré-processamento) em GPU.

> Observação: onde possível, preferir código e modelos locais (privacidade), logs detalhados, validação cruzada e publicação na memória MCP do RAG++ para facilitar reuso.
