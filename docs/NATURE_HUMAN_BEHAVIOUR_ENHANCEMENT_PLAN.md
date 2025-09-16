# Plano de Aprimoramento para Nature Human Behaviour
## Análises Causais Avançadas para Framework KEC

**Autor:** Análise baseada no projeto PCS Meta-Repo  
**Data:** Janeiro 2025  
**Objetivo:** Elevar o trabalho ao padrão Nature Human Behaviour com foco em análises causais  
**Timeline:** Implementação rápida (4-6 semanas)

---

## **RESUMO EXECUTIVO**

Este plano detalha análises causais avançadas específicas para transformar o atual framework KEC em uma contribuição de alto impacto para Nature Human Behaviour. Foca em três pilares estratégicos: **inferência causal rigorosa**, **mediação neural**, e **validação cross-linguística robusta** usando apenas datasets públicos existentes.

### **Diferencial para Nature Human Behaviour**
- **Inovação Metodológica**: Primeira aplicação de DAGs causais em redes semânticas + neuroimagem
- **Rigor Estatístico**: Framework causal robusto com múltiplas validações
- **Relevância Comportamental**: Conexão direta entre estrutura semântica e comportamento de leitura
- **Replicabilidade**: Análises em 5 idiomas com datasets públicos

---

## **1. ANÁLISES CAUSAIS PRIORITÁRIAS**

### **1.1 Inferência Causal com DAGs Estruturais**

#### **Objetivo Científico**
Estabelecer relações causais definitivas: **Estrutura Semântica → Atividade Neural → Comportamento de Leitura**

#### **Implementação Técnica Rápida**

**A. DAG Teórico Baseado em Literatura**
```python
# Estrutura causal fundamentada teoricamente
causal_dag = """
digraph {
    # Confundidores
    word_freq -> kec_entropy
    word_freq -> theta_power  
    word_freq -> reading_time
    
    word_length -> kec_curvature
    word_length -> alpha_power
    word_length -> fixation_duration
    
    # Cadeia causal principal
    kec_entropy -> theta_power -> reading_time
    kec_curvature -> alpha_power -> fixation_duration
    kec_coherence -> beta_power -> comprehension
    
    # Efeitos diretos residuais
    kec_entropy -> reading_time
    kec_curvature -> fixation_duration
}
"""
```

**B. Estimação Causal com DoWhy**
```python
import dowhy
from dowhy import CausalModel

# Modelo causal automatizado
def estimate_causal_effect(data, treatment, outcome, graph):
    model = CausalModel(
        data=data,
        treatment=treatment,
        outcome=outcome,
        graph=graph,
        instruments=['word_freq', 'word_length']  # Variáveis instrumentais
    )
    
    # Múltiplos estimadores para robustez
    estimates = {}
    
    # 1. Backdoor adjustment
    estimates['backdoor'] = model.estimate_effect(
        method_name="backdoor.linear_regression",
        control_value=0,
        treatment_value=1
    )
    
    # 2. Instrumental variables
    estimates['iv'] = model.estimate_effect(
        method_name="iv.instrumental_variable"
    )
    
    # 3. Propensity score matching
    estimates['psm'] = model.estimate_effect(
        method_name="backdoor.propensity_score_matching"
    )
    
    return estimates, model
```

**C. Validação de Robustez**
```python
# Análise de sensibilidade automatizada
def sensitivity_analysis(model, estimates):
    # Teste de confundidores não observados
    sensitivity_results = {}
    
    for method, estimate in estimates.items():
        # Refutation tests
        refute_random = model.refute_estimate(
            estimate, method_name="random_common_cause"
        )
        
        refute_placebo = model.refute_estimate(
            estimate, method_name="placebo_treatment_refuter"
        )
        
        sensitivity_results[method] = {
            'estimate': estimate.value,
            'random_refute_p': refute_random.new_effect,
            'placebo_refute_p': refute_placebo.new_effect
        }
    
    return sensitivity_results
```

#### **Produtos Esperados (Semana 1-2)**
- **Script**: `scripts/advanced_causal_inference.py`
- **Notebook**: `notebooks/11_causal_dag_analysis_complete.ipynb`
- **Figuras**: DAGs com coeficientes causais estimados
- **Métricas**: ATE, CATE com intervalos de confiança robustos

### **1.2 Análise de Mediação Neural Sequencial**

#### **Objetivo Científico**
Identificar mecanismos neurais específicos que mediam efeitos KEC→Comportamento com precisão temporal.

#### **Implementação Técnica**

**A. Mediação Temporal Multi-nível**
```python
from mediation_analysis import SequentialMediation
import numpy as np

def temporal_mediation_analysis(data):
    """
    Análise de mediação com resolução temporal
    KEC → EEG(t1) → EEG(t2) → Comportamento
    """
    
    # Definir janelas temporais baseadas em literatura N400/P600
    time_windows = {
        'early': (100, 200),    # Processamento lexical
        'n400': (300, 500),     # Integração semântica  
        'p600': (500, 700),     # Reprocessamento
        'late': (700, 1000)     # Integração final
    }
    
    mediation_results = {}
    
    for window_name, (t_start, t_end) in time_windows.items():
        # Extrair poder EEG na janela temporal
        eeg_window = f'eeg_power_{window_name}'
        
        # Modelo de mediação sequencial
        mediation = SequentialMediation(
            treatment='kec_entropy',
            mediators=[eeg_window, 'fixation_duration'],
            outcome='comprehension_accuracy',
            covariates=['word_frequency', 'word_length', 'sentence_position']
        )
        
        results = mediation.fit(
            data=data,
            bootstrap_samples=5000,
            confidence_level=0.95
        )
        
        mediation_results[window_name] = results
    
    return mediation_results
```

**B. Mediação Moderada por Proficiência**
```python
def moderated_mediation_analysis(data):
    """
    Efeitos condicionais por proficiência de leitura
    """
    
    # Dividir por proficiência (baseado em velocidade de leitura)
    data['reading_proficiency'] = pd.qcut(
        data.groupby('subject_id')['reading_time'].mean(),
        q=3, labels=['low', 'medium', 'high']
    )
    
    moderated_results = {}
    
    for proficiency in ['low', 'medium', 'high']:
        subset = data[data['reading_proficiency'] == proficiency]
        
        # Análise de mediação por grupo
        mediation = ConditionalMediation(
            treatment='kec_coherence',
            mediator='beta_power',
            outcome='total_reading_time',
            moderator='reading_proficiency',
            covariates=['word_frequency', 'word_length']
        )
        
        results = mediation.fit(subset)
        moderated_results[proficiency] = results
    
    return moderated_results
```

#### **Produtos Esperados (Semana 2-3)**
- **Análise**: Decomposição temporal de efeitos (direto/indireto/total)
- **Visualização**: Diagramas de mediação com path coefficients temporais
- **Validação**: Replicação em múltiplos datasets (ZuCo v1/v2, DERCo)

### **1.3 Inferência Causal Cross-Linguística**

#### **Objetivo Científico**
Demonstrar universalidade de relações causais KEC→Neural→Comportamental através de idiomas.

#### **Implementação Técnica**

**A. Meta-Análise Causal Multi-Idioma**
```python
def cross_linguistic_causal_meta_analysis():
    """
    Meta-análise de efeitos causais através de idiomas
    """
    
    languages = ['en', 'es', 'zh', 'nl', 'pt']
    causal_effects = {}
    
    for lang in languages:
        # Carregar dados específicos do idioma
        data = load_language_data(lang)
        
        # Estimar efeito causal padronizado
        effect = estimate_standardized_causal_effect(
            data=data,
            treatment='kec_entropy_standardized',
            outcome='reading_time_standardized',
            confounders=['word_freq_std', 'word_len_std']
        )
        
        causal_effects[lang] = {
            'effect_size': effect.value,
            'confidence_interval': effect.confidence_intervals,
            'p_value': effect.p_value,
            'sample_size': len(data)
        }
    
    # Meta-análise com efeitos fixos e aleatórios
    meta_analysis = perform_meta_analysis(causal_effects)
    
    return meta_analysis, causal_effects
```

**B. Análise de Heterogeneidade Cross-Cultural**
```python
def cultural_heterogeneity_analysis(causal_effects):
    """
    Análise de heterogeneidade de efeitos entre culturas
    """
    
    # Teste de heterogeneidade Cochran's Q
    q_statistic, q_p_value = cochrans_q_test(causal_effects)
    
    # I² para quantificar heterogeneidade
    i_squared = calculate_i_squared(causal_effects)
    
    # Análise de moderadores culturais
    cultural_moderators = {
        'writing_system': {'en': 'alphabetic', 'zh': 'logographic', 'es': 'alphabetic'},
        'morphological_complexity': {'en': 'low', 'es': 'high', 'zh': 'low'},
        'orthographic_depth': {'en': 'deep', 'es': 'shallow', 'zh': 'deep'}
    }
    
    moderation_results = {}
    for moderator, values in cultural_moderators.items():
        moderation_results[moderator] = test_moderation(
            causal_effects, values
        )
    
    return {
        'heterogeneity': {'Q': q_statistic, 'p': q_p_value, 'I2': i_squared},
        'moderation': moderation_results
    }
```

#### **Produtos Esperados (Semana 3-4)**
- **Meta-análise**: Efeitos causais consolidados com forest plots
- **Heterogeneidade**: Análise de variação cross-cultural
- **Moderação**: Identificação de fatores linguísticos moderadores

---

## **2. VALIDAÇÃO ESTATÍSTICA AVANÇADA**

### **2.1 Framework de Validação Cruzada Causal**

#### **Implementação**
```python
def causal_cross_validation(data, n_folds=5):
    """
    Validação cruzada específica para inferência causal
    """
    
    from sklearn.model_selection import StratifiedKFold
    
    # Estratificação por sujeito para evitar vazamento
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    
    cv_results = []
    
    for fold, (train_idx, test_idx) in enumerate(skf.split(data, data['subject_id'])):
        train_data = data.iloc[train_idx]
        test_data = data.iloc[test_idx]
        
        # Estimar modelo causal no conjunto de treino
        causal_model = fit_causal_model(train_data)
        
        # Predizer efeitos causais no conjunto de teste
        predicted_effects = causal_model.predict_effects(test_data)
        
        # Validar com intervenções simuladas
        validation_score = validate_causal_predictions(
            test_data, predicted_effects
        )
        
        cv_results.append({
            'fold': fold,
            'validation_score': validation_score,
            'effect_correlation': correlation_with_observed(predicted_effects, test_data)
        })
    
    return cv_results
```

### **2.2 Análise de Poder Estatístico**

#### **Implementação**
```python
def power_analysis_causal_effects():
    """
    Análise de poder para detectar efeitos causais
    """
    
    effect_sizes = np.arange(0.1, 0.8, 0.1)  # Cohen's d
    sample_sizes = np.arange(100, 2000, 100)
    
    power_matrix = np.zeros((len(effect_sizes), len(sample_sizes)))
    
    for i, effect_size in enumerate(effect_sizes):
        for j, sample_size in enumerate(sample_sizes):
            # Simulação Monte Carlo para poder
            power = simulate_power_causal_test(
                effect_size=effect_size,
                sample_size=sample_size,
                alpha=0.05,
                n_simulations=1000
            )
            power_matrix[i, j] = power
    
    return power_matrix, effect_sizes, sample_sizes
```

---

## **3. IMPLEMENTAÇÃO RÁPIDA - CRONOGRAMA 4 SEMANAS**

### **Semana 1: Fundações Causais**
- [ ] **Dia 1-2**: Implementar framework DAG com DoWhy
- [ ] **Dia 3-4**: Desenvolver análise de mediação temporal
- [ ] **Dia 5-7**: Validar inferência causal em dados ZuCo

**Deliverable**: `notebooks/11_causal_dag_analysis_complete.ipynb`

### **Semana 2: Mediação Neural**
- [ ] **Dia 1-3**: Implementar mediação sequencial multi-nível
- [ ] **Dia 4-5**: Análise de mediação moderada por proficiência
- [ ] **Dia 6-7**: Validação temporal com janelas EEG

**Deliverable**: `notebooks/12_neural_mediation_analysis.ipynb`

### **Semana 3: Validação Cross-Linguística**
- [ ] **Dia 1-3**: Meta-análise causal multi-idioma
- [ ] **Dia 4-5**: Análise de heterogeneidade cultural
- [ ] **Dia 6-7**: Testes de robustez e sensibilidade

**Deliverable**: `notebooks/13_cross_linguistic_causal_validation.ipynb`

### **Semana 4: Integração e Manuscrito**
- [ ] **Dia 1-2**: Integrar todas as análises causais
- [ ] **Dia 3-4**: Gerar figuras Nature-quality
- [ ] **Dia 5-7**: Escrever seções Methods/Results

**Deliverable**: Manuscrito Nature Human Behaviour draft

---

## **4. MÉTRICAS DE SUCESSO NATURE HUMAN BEHAVIOUR**

### **Rigor Metodológico**
- **Inferência Causal**: ATE significativo com múltiplos estimadores convergentes
- **Robustez**: Efeitos resistem a testes de refutação (p > 0.05 para placebo)
- **Replicabilidade**: Efeitos consistentes em ≥3 datasets independentes
- **Effect Size**: Cohen's d ≥ 0.3 para efeitos causais principais

### **Inovação Científica**
- **Novidade**: Primeira demonstração de causalidade em redes semânticas + neuroimagem
- **Impacto**: Framework aplicável a múltiplos domínios cognitivos
- **Metodologia**: Avanços em análise causal de dados neurolinguísticos

### **Relevância Comportamental**
- **Predição**: Modelos causais predizem comportamento com R² ≥ 0.25
- **Generalização**: Efeitos replicam em ≥3 idiomas
- **Aplicabilidade**: Implicações claras para educação e clínica

---

## **5. ANÁLISES ESPECÍFICAS ADICIONAIS**

### **5.1 Análise de Dose-Resposta Causal**

```python
def dose_response_analysis():
    """
    Análise de relação dose-resposta para KEC metrics
    """
    
    # Discretizar KEC entropy em quartis
    data['kec_entropy_quartile'] = pd.qcut(
        data['kec_entropy'], 
        q=4, 
        labels=['Q1_low', 'Q2_med_low', 'Q3_med_high', 'Q4_high']
    )
    
    # Estimar efeito causal para cada "dose"
    dose_effects = {}
    
    for quartile in data['kec_entropy_quartile'].unique():
        # Tratamento binário: quartile vs. baseline (Q1)
        treatment = (data['kec_entropy_quartile'] == quartile).astype(int)
        
        effect = estimate_causal_effect(
            data=data,
            treatment=treatment,
            outcome='reading_time',
            confounders=['word_frequency', 'word_length']
        )
        
        dose_effects[quartile] = effect
    
    return dose_effects
```

### **5.2 Análise de Interação Causal**

```python
def causal_interaction_analysis():
    """
    Análise de interações causais entre métricas KEC
    """
    
    # Interação Entropy × Curvature
    interaction_effects = {}
    
    # Criar variável de interação
    data['entropy_x_curvature'] = (
        data['kec_entropy_std'] * data['kec_curvature_std']
    )
    
    # Modelo causal com interação
    causal_model = """
    digraph {
        word_freq -> entropy
        word_freq -> curvature  
        word_freq -> reading_time
        
        entropy -> reading_time
        curvature -> reading_time
        entropy_x_curvature -> reading_time
        
        entropy -> entropy_x_curvature
        curvature -> entropy_x_curvature
    }
    """
    
    interaction_effect = estimate_causal_effect(
        data=data,
        treatment='entropy_x_curvature',
        outcome='reading_time',
        graph=causal_model
    )
    
    return interaction_effect
```

### **5.3 Análise de Limiar Causal**

```python
def threshold_causal_analysis():
    """
    Identificar limiares causais para efeitos KEC
    """
    
    # Análise de regressão com threshold
    from sklearn.tree import DecisionTreeRegressor
    
    # Identificar pontos de corte ótimos
    thresholds = {}
    
    for metric in ['kec_entropy', 'kec_curvature', 'kec_coherence']:
        # Árvore de decisão para identificar thresholds
        tree = DecisionTreeRegressor(max_depth=3, random_state=42)
        tree.fit(data[[metric]], data['reading_time'])
        
        # Extrair thresholds das divisões
        threshold_values = extract_tree_thresholds(tree, metric)
        
        # Testar efeito causal em cada threshold
        threshold_effects = {}
        for threshold in threshold_values:
            binary_treatment = (data[metric] > threshold).astype(int)
            
            effect = estimate_causal_effect(
                data=data,
                treatment=binary_treatment,
                outcome='reading_time',
                confounders=['word_frequency', 'word_length']
            )
            
            threshold_effects[threshold] = effect
        
        thresholds[metric] = threshold_effects
    
    return thresholds
```

---

## **6. FIGURAS NATURE-QUALITY**

### **Figura 1: Causal Framework Overview**
- **Panel A**: DAG teórico com path coefficients
- **Panel B**: Forest plot de efeitos causais por dataset
- **Panel C**: Mediação temporal (early → N400 → P600 → behavior)
- **Panel D**: Cross-linguistic replication

### **Figura 2: Causal Validation**
- **Panel A**: Sensitivity analysis (robustness tests)
- **Panel B**: Cross-validation performance
- **Panel C**: Dose-response relationships
- **Panel D**: Interaction effects heatmap

### **Figura 3: Neural Mechanisms**
- **Panel A**: Temporal mediation cascade
- **Panel B**: EEG topographies by KEC quartiles
- **Panel C**: Individual differences in mediation
- **Panel D**: Threshold effects visualization

---

## **7. RECURSOS NECESSÁRIOS**

### **Computacionais**
- **Hardware**: CPU multi-core para bootstrap (16+ cores recomendado)
- **Software**: DoWhy, CausalML, statsmodels, scikit-learn
- **Memória**: 32GB+ RAM para análises bootstrap intensivas

### **Dados**
- **Existentes**: ZuCo v1/v2, DERCo, GECO, OneStop (todos públicos)
- **SWOW**: EN, ES, ZH, NL, PT (todos disponíveis)
- **Processamento**: ~100GB storage para datasets processados

### **Timeline Realista**
- **Semana 1**: Implementação core (40h)
- **Semana 2**: Validação e testes (40h)  
- **Semana 3**: Cross-linguistic analysis (40h)
- **Semana 4**: Manuscrito e figuras (40h)
- **Total**: 160 horas de desenvolvimento focado

---

## **8. RISCOS E MITIGAÇÕES**

### **Riscos Técnicos**
- **Complexidade Causal**: Modelos podem ser instáveis
  - *Mitigação*: Múltiplos estimadores, validação cruzada
- **Poder Estatístico**: Efeitos podem ser pequenos
  - *Mitigação*: Meta-análise, pooling de datasets

### **Riscos de Dados**
- **Heterogeneidade**: Datasets podem ser incompatíveis
  - *Mitigação*: Harmonização cuidadosa, análise de sensibilidade
- **Missing Data**: Cobertura incompleta KEC-EEG
  - *Mitigação*: Imputação múltipla, análise de sensibilidade

### **Riscos de Timeline**
- **Complexidade Implementação**: Análises podem demorar
  - *Mitigação*: Priorização, implementação paralela
- **Debugging**: Bugs podem atrasar
  - *Mitigação*: Testes unitários, validação incremental

---

## **CONCLUSÃO**

Este plano posiciona o framework KEC na fronteira da neurociência causal computacional, combinando rigor metodológico com inovação científica. O foco em análises causais avançadas com implementação rápida atende perfeitamente aos critérios de Nature Human Behaviour:

### **Pontos Fortes para Nature Human Behaviour**
1. **Inovação Metodológica**: Primeira aplicação de DAGs causais em neuroimagem semântica
2. **Rigor Estatístico**: Framework robusto com múltiplas validações
3. **Relevância Comportamental**: Conexão direta estrutura-comportamento
4. **Replicabilidade**: Análises em múltiplos idiomas e datasets públicos
5. **Implementação Rápida**: Timeline executável de 4 semanas

### **Impacto Científico Esperado**
- **Teórico**: Novo paradigma para análise causal em neurociência cognitiva
- **Metodológico**: Framework replicável para outros domínios
- **Prático**: Aplicações em educação e avaliação cognitiva

**Próximos Passos Imediatos:**
1. Configurar ambiente DoWhy/CausalML
2. Implementar DAG framework básico
3. Executar primeira análise causal em dados ZuCo
4. Validar pipeline com dados sintéticos

---

**Status**: ✅ PRONTO PARA IMPLEMENTAÇÃO  
**Timeline**: 4 SEMANAS  
**Impacto**: ALTO POTENCIAL NATURE HUMAN BEHAVIOUR  
**Recursos**: DISPONÍVEIS (DATASETS PÚBLICOS)
