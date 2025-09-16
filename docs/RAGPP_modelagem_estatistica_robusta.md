# Playbook RAG++ de Modelagem e Estatística (ET/EEG, KEC, Surprisal)

Este playbook consolida práticas robustas, algoritmos validados e recomendações metodológicas para análises com Eye-Tracking (ET), EEG e métricas lexicais (KEC, surprisal), com foco em reprodutibilidade e rigor estatístico.

> Escopo: ET/EEG por palavra, integração com KEC e surprisal, modelos mistos, meta-análise, correções de múltiplas comparações, pipelines reprodutíveis e multilíngues.

## Fundamentos de Reprodutibilidade

- Versão dos dados/artefatos e trilhas de proveniência (YAML/JSONL). Seeds fixos onde aplicável. Ambientes isolados (conda/venv) e manifestos de dependências.
- Logs de métodos e cobertura; publicação automática em memória MCP (RAG++).
- Pré-registro quando viável e relatórios consolidados com métricas, ICs e diagnósticos.

## Modelos Mistos e Alternativas

- LMM/GLMM (efeitos aleatórios por sujeito/itens; interceptos e, quando justificável, slopes) [Barr et al., 2013; Bates et al., 2015].
  - Controles recomendados para ET: length, posição no enunciado, frequência lexical; acrescentar surprisal (LM/transformer) quando disponível.
  - Detecção de colinearidade (VIF), padronização opcional de preditores; interpretação via efeitos marginais.
- Fallback escalável: meta-análise de efeitos por sujeito (OLS) com efeitos aleatórios (DerSimonian–Laird) quando LMM fica instável/oneroso em corpora grandes (e.g., GECO).
- Modelagem Bayesiana hierárquica (Stan/brms) para estimativas completas das incertezas e priors informativos fracos [Gelman et al., 2013].
- GAM/GAMM para relações não lineares em ET (p.ex., posição, comprimento) [Wood, 2017].

## EEG: Inferência Robusta

- Correções de múltiplas comparações no tempo/frequência: cluster-based permutation tests [Maris & Oostenveld, 2007].
- Ajustes por bandas (theta/alpha/beta/gamma) com FDR por família e por DV.
- Reamostragem/bootstrapping para ICs robustos em métricas agregadas.

## Correção de Múltiplas Comparações

- BH-FDR (Benjamini–Hochberg, 1995) por arquivo e por (arquivo,DV); BY (Benjamini–Yekutieli, 2001) sob dependência arbitrária.
- Holms/Bonferroni para cenários altamente confirmatórios.
- Reporte de p ajustado, q-value e tamanho de efeito com ICs.

## Surprisal e KEC

- Surprisal: preferir modelos com contexto (KenLM sentencial; transformers com offsets para agregação por palavra). Unidades em bits. Lidar com OOV (<unk>) e normalização de tokens.
- KEC: garantir uma linha por token na junção, deduplicando por chave normalizada; documentar componentes (comp_*).
- Comparabilidade multilíngue: normalização ASCII para línguas latinas, cuidados com morfologia e recursos de frequência por língua.

## Correlação e Associações

- Spearman (exato via SciPy quando disponível) para relações monotônicas; Kendall tau-b quando há muitos empates.
- Correlações parciais com controles quando apropriado; ICs por bootstrap.

## Meta-Análise e Síntese de Evidência

- DerSimonian–Laird para combinar coeficientes por sujeito (efeitos aleatórios); reporte de tau² e heterogeneidade (Q, I²).
- Forest plots e análises de sensibilidade (leave-one-out).

## Qualidade de Dados e Missing

- Checagens de consistência, ranges plausíveis, outliers influentes (Cook’s D).
- Missing: preferir modelos hierárquicos (MCAR/MAR); imputação múltipla quando necessário.

## Boas Práticas de Relato

- Efeitos padronizados, IC 95%, p e q; convergência (Hessian, singularidade); diag. de resíduos.
- Tabelas por DV e arquivo com FDR por família e por (arquivo,DV). Visualizações (coef. plots, forest plots, distribuições).

## Referências (seleção)

- Barr, D. J., Levy, R., Scheepers, C., & Tily, H. J. (2013). Random effects structure for confirmatory hypothesis testing. Journal of Memory and Language.
- Bates, D., Mächler, M., Bolker, B., & Walker, S. (2015). Fitting Linear Mixed-Effects Models Using lme4. Journal of Statistical Software.
- Benjamini, Y., & Hochberg, Y. (1995). Controlling the False Discovery Rate. JRSS-B.
- Benjamini, Y., & Yekutieli, D. (2001). The control of the FDR under dependency. Annals of Statistics.
- Gelman, A., Carlin, J., Stern, H., Dunson, D., Vehtari, A., & Rubin, D. (2013). Bayesian Data Analysis (3rd). CRC.
- Maris, E., & Oostenveld, R. (2007). Nonparametric statistical testing of EEG/MEG-data. Journal of Neuroscience Methods.
- Wood, S. N. (2017). Generalized Additive Models: An Introduction with R (2nd). CRC.
