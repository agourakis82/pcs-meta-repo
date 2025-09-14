# 🔄 VALIDAÇÃO CRUZADA ABRANGENTE

**Data de geração:** 2025-09-09 07:27:43

**Processamento:** GPU (CuPy)

## 📋 VISÃO GERAL DA VALIDAÇÃO

- **Idiomas validados:** EN, NL, ES, ZH
- **Folds de CV:** 5
- **Range de clusters testado:** 2-7
- **Métricas:** Silhouette, Calinski-Harabasz, Davies-Bouldin

## ⏱️ PERFORMANCE DA VALIDAÇÃO

- **Tempo total:** 355.54s
- **Detalhamento por operação:**
  - data_loading: 228.28s (64.2%)
  - clustering_cv: 127.25s (35.8%)
  - statistical_comparison: 0.02s (0.0%)

## 🎯 RESULTADOS DE CLUSTERING - VALIDAÇÃO CRUZADA

### EN

| k | Silhouette (média ± std) | CH (média ± std) | DB (média ± std) |
|---|--------------------------|-------------------|-------------------|
| 2 | 0.934 ± 0.002 | 18856.9 ± 578.1 | 0.223 ± 0.008 |
| 3 | 0.960 ± 0.002 | 70140.3 ± 4598.0 | 0.231 ± 0.002 |
| 4 | 0.963 ± 0.002 | 112670.9 ± 6287.7 | 0.237 ± 0.012 |
| 5 | 0.951 ± 0.002 | 198990.7 ± 23771.7 | 0.217 ± 0.014 |
| 6 | 0.948 ± 0.005 | 216606.6 ± 33630.3 | 0.228 ± 0.040 |
| 7 | 0.948 ± 0.011 | 298422.9 ± 26370.3 | 0.275 ± 0.055 |

### NL

| k | Silhouette (média ± std) | CH (média ± std) | DB (média ± std) |
|---|--------------------------|-------------------|-------------------|
| 2 | 0.942 ± 0.002 | 21617.4 ± 1093.3 | 0.212 ± 0.007 |
| 3 | 0.965 ± 0.001 | 81380.9 ± 9760.2 | 0.221 ± 0.015 |
| 4 | 0.967 ± 0.001 | 123400.6 ± 15939.8 | 0.249 ± 0.046 |
| 5 | 0.954 ± 0.001 | 223531.7 ± 49071.3 | 0.230 ± 0.037 |
| 6 | 0.956 ± 0.005 | 234805.3 ± 59918.9 | 0.206 ± 0.041 |
| 7 | 0.961 ± 0.009 | 312133.7 ± 97570.1 | 0.224 ± 0.058 |

### ES

| k | Silhouette (média ± std) | CH (média ± std) | DB (média ± std) |
|---|--------------------------|-------------------|-------------------|
| 2 | 0.939 ± 0.003 | 19325.4 ± 544.2 | 0.215 ± 0.006 |
| 3 | 0.963 ± 0.001 | 72226.0 ± 4132.5 | 0.246 ± 0.015 |
| 4 | 0.965 ± 0.001 | 117601.2 ± 4446.5 | 0.229 ± 0.014 |
| 5 | 0.954 ± 0.002 | 228395.0 ± 25223.6 | 0.207 ± 0.015 |
| 6 | 0.966 ± 0.003 | 253314.3 ± 37162.0 | 0.192 ± 0.012 |
| 7 | 0.959 ± 0.004 | 336895.0 ± 71207.3 | 0.263 ± 0.010 |

### ZH

| k | Silhouette (média ± std) | CH (média ± std) | DB (média ± std) |
|---|--------------------------|-------------------|-------------------|
| 2 | 0.921 ± 0.002 | 15551.6 ± 578.6 | 0.252 ± 0.005 |
| 3 | 0.953 ± 0.002 | 48357.1 ± 4978.7 | 0.270 ± 0.011 |
| 4 | 0.958 ± 0.001 | 90726.8 ± 14474.4 | 0.283 ± 0.030 |
| 5 | 0.944 ± 0.003 | 112231.7 ± 29695.7 | 0.256 ± 0.026 |
| 6 | 0.945 ± 0.003 | 163754.7 ± 27130.1 | 0.273 ± 0.035 |
| 7 | 0.936 ± 0.003 | 201411.4 ± 46468.9 | 0.330 ± 0.014 |

## 📊 COMPARAÇÕES ESTATÍSTICAS

### Distribuições Semânticas

| Métrica | Teste | Estatística | p-valor | Significativo |
|---------|-------|-------------|---------|---------------|
| entropy | ANOVA | 21.308 | 0.000 | ✅ |
| curvature | ANOVA | nan | nan | ❌ |
| coherence | ANOVA | inf | 0.000 | ✅ |

### Performance de Clustering

- **Teste:** ANOVA
- **Estatística:** nan
- **p-valor:** nan
- **Significativo:** ❌

**Scores de Silhouette por idioma:**
- EN: 0.963
- NL: 0.967
- ES: 0.966
- ZH: 0.958

### Dados Neurocientíficos

| Métrica | Teste | Estatística | p-valor | Significativo |
|---------|-------|-------------|---------|---------------|
| fixation_duration | ANOVA | 5.598 | 0.001 | ✅ |
| theta | ANOVA | 7.053 | 0.000 | ✅ |
| alpha | ANOVA | 0.081 | 0.970 | ❌ |
| beta | ANOVA | nan | nan | ❌ |

## 🎯 CONCLUSÕES DA VALIDAÇÃO

### Melhor Configuração Geral:

1. **Idioma com melhor performance:** NL
2. **Melhor k:** 4
3. **Melhor Silhouette:** 0.967

### Robustez da Análise:

1. **Consistência:** Alta
2. **Estabilidade:** Alta
3. **Significância geral:** Média

### Recomendações:

1. Usar NL como idioma de referência para futuras análises
2. Configurar clustering com k=4 clusters para otimização geral
3. A análise demonstra alta consistência - resultados confiáveis
4. Algumas diferenças podem não ser estatisticamente robustas
5. Implementar validação cruzada em todas as futuras análises multilíngues

## 📈 VISUALIZAÇÕES GERADAS

1. **`cv_clustering_comparison.png`** - Comparação de clustering CV
2. **`cv_semantic_distributions.png`** - Distribuições semânticas
3. **`cv_performance_stability.png`** - Estabilidade da performance
4. **`cv_statistical_comparison.png`** - Comparações estatísticas

