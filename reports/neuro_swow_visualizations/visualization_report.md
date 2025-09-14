# 📊 RELATÓRIO DE VISUALIZAÇÕES: DADOS NEURO-SWOW

**Data de geração:** 2025-09-08 20:44:08

**Total de observações:** 902,812

## 📈 VISUALIZAÇÕES GERADAS

### 1. Distribuição por Dataset
- **Arquivo:** `dataset_distribution.png`
- **Descrição:** Distribuição proporcional dos dados por dataset

### 2. Distribuições SWOW
- **Arquivo:** `swow_distributions.png`
- **Descrição:** Histogramas das métricas SWOW (Entropia, Curvatura, Coerência)

### 3. Heatmap de Correlação
- **Arquivo:** `correlation_heatmap.png`
- **Descrição:** Correlações entre métricas SWOW e neurofisiológicas

### 4. Análise de Palavras Frequentes
- **Arquivo:** `top_words_analysis.png`
- **Descrição:** Métricas SWOW médias para as 20 palavras mais frequentes

### 5. Comparação entre Datasets
- **Arquivo:** `dataset_comparison.png`
- **Descrição:** Comparação das métricas SWOW médias por dataset

## 🔍 INSIGHTS PRINCIPAIS

### Distribuição de Dados:
- **geco_et:** 827,966 observações (91.7%)
- **onestop_et:** 62,675 observações (6.9%)
- **derco_eeg:** 9,571 observações (1.1%)
- **lpp_eeg:** 2,600 observações (0.3%)

### Cobertura das Métricas:
- **entropy:** 87.8% de cobertura
- **curvature:** 87.8% de cobertura
- **coherence:** 87.8% de cobertura

## 📋 PRÓXIMOS PASSOS

1. **Modelagem Preditiva:**
   - Regressão: fixation_duration ~ entropy + curvature + coherence
   - Classificação: predição de dificuldade de leitura

2. **Análises Avançadas:**
   - Análise por sujeito/modalidade
   - Modelos mistos (mixed-effects)
   - Validação estatística

3. **Visualizações Interativas:**
   - Dashboards interativos
   - Análise temporal
   - Comparações dinâmicas

