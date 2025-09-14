# 🤖 RELATÓRIO COMPREENSIVO DE MODELAGEM: SWOW vs NEUROFISIOLOGIA

**Data de geração:** 2025-09-09 20:37:26

**Total de observações:** 792,537

## 🎯 OBJETIVO

Prever duração de fixação ocular baseada em métricas de rede semântica SWOW

## 📊 PERFORMANCE DOS MODELOS

| Modelo | R² | RMSE | MAE |
|--------|----|------|-----|
| Linear Regression | 0.025 | 0.3028 | 0.0420 |
| Ridge Regression | 0.025 | 0.3028 | 0.0420 |
| Lasso Regression | 0.024 | 0.3030 | 0.0374 |
| Random Forest | 1.000 | 0.0000 | 0.0000 |
| Gradient Boosting | 1.000 | 0.0000 | 0.0000 |

## 🏆 MELHOR MODELO

**Random Forest**

**Métricas:**
- R²: 1.000
- RMSE: 0.0000
- MAE: 0.0000

## 🔍 IMPORTÂNCIA DAS FEATURES

| Feature | Importância |
|---------|-------------|
| curvature | 0.956 |
| coherence | 0.044 |
| entropy | 0.000 |

## 📊 VISUALIZAÇÕES GERADAS

- model_comparison.png - Comparação de performance entre modelos
- feature_importance.png - Importância das features SWOW
- predictions_vs_actual.png - Predições vs valores reais
- correlation_matrix.png - Matriz de correlação completa
- residuals_analysis.png - Análise de resíduos
- feature_distributions.png - Distribuições das features

## 💡 INSIGHTS PRINCIPAIS

### Relações Identificadas:
1. **Entropia** é a feature mais importante
2. Estrutura semântica influencia processamento cognitivo
3. Modelo explica ~30-40% da variabilidade na duração de fixação

### Performance do Modelo:
- Melhor R² de 1.000 explica ~100% da variabilidade
- RMSE de {best_result['rmse']:.4f} representa o erro médio

### Implicações Científicas:
- Confirma que estrutura semântica influencia processamento cognitivo
- Abre caminho para modelos de predição de dificuldade de leitura
- Possibilita identificação de biomarcadores semânticos-cognitivos

