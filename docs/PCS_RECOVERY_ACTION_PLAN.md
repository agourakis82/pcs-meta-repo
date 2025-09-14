# 🚨 PCS PROJECT - RECOVERY ACTION PLAN

**Data:** December 19, 2024  
**Status:** CRITICAL RECOVERY PHASE INITIATED  
**Versão:** Recovery Plan v1.0  

---

## 📊 **SITUAÇÃO ATUAL CONFIRMADA**

### **✅ SUCESSOS VALIDADOS**
1. **SWOW Multilíngue**: 4 idiomas (EN/ES/NL/ZH) processados e validados
2. **KEC Metrics**: Entropy, curvature, coherence calculadas corretamente
3. **Ferramentas de Diagnóstico**: Scripts funcionais implementados
4. **Identificação de Problemas**: Causa raiz dos dados constantes identificada

### **🚨 PROBLEMAS CRÍTICOS CONFIRMADOS**
1. **Target Constante**: `fixation_duration` = 200.0 (100% dos casos)
2. **Dados ZuCo Incompletos**: Tasks específicas não processadas adequadamente
3. **Amostras Insuficientes**: DERCo (4 participantes), GECO (2 participantes)
4. **Pipeline Quebrado**: Integração neural-semântica comprometida

### **🔍 DESCOBERTAS DA INVESTIGAÇÃO**
- **ZuCo v1**: Dados existem mas em estrutura com espaços nos nomes das pastas
- **Tasks Disponíveis**: `task1- SR`, `task3 - TSR` encontradas
- **Dados Preprocessados**: Existem mas não estão sendo carregados corretamente
- **Pipeline Antigo**: Scripts não adaptados para nova estrutura de dados

---

## 🎯 **PLANO DE RECUPERAÇÃO DETALHADO**

### **FASE 1: CORREÇÃO IMEDIATA DOS DADOS ZUCO (URGENTE)**

#### **Passo 1.1: Reprocessar ZuCo com Estrutura Correta**
```bash
# Criar script de correção para nomes com espaços
python scripts/fix_zuco_paths.py
```

#### **Passo 1.2: Extrair Dados Reais de Fixação**
```bash
# Processar dados preprocessados do ZuCo
python scripts/load_real_zuco_data.py --validate
```

#### **Passo 1.3: Validar Variabilidade dos Dados**
```bash
# Garantir que novos dados têm variabilidade adequada
python scripts/validate_model_pipeline.py --strict
```

### **FASE 2: EXPANSÃO DE AMOSTRAS (CRÍTICO)**

#### **Passo 2.1: Localizar Dados Completos**
- **DERCo**: Buscar dados de eye-tracking faltantes
- **GECO**: Verificar se existem mais participantes disponíveis
- **LPP**: Completar download dos dados EEG/fMRI

#### **Passo 2.2: Implementar Validação de Amostra**
```python
def validate_sample_size(dataset, min_participants=10):
    if dataset.nunique_participants() < min_participants:
        raise ValueError(f"Amostra insuficiente: {dataset.nunique_participants()}")
```

### **FASE 3: REINTEGRAÇÃO E VALIDAÇÃO (ESSENCIAL)**

#### **Passo 3.1: Reprocessar Pipeline Completo**
```bash
# Pipeline completo com validação em cada etapa
python scripts/comprehensive_reprocessing.py --validate-each-step
```

#### **Passo 3.2: Validação Estatística Rigorosa**
```bash
# Validar todos os targets antes de análises
python scripts/statistical_validation.py --all-targets
```

---

## 🔧 **SCRIPTS DE CORREÇÃO NECESSÁRIOS**

### **Script 1: Correção de Caminhos ZuCo**
```python
# scripts/fix_zuco_paths.py
import os
import shutil

def fix_zuco_directory_names():
    """Corrige nomes de diretórios com espaços no ZuCo"""
    base_path = "data/raw_public/zuco/v1"
    
    # Mapear nomes problemáticos
    name_fixes = {
        "task1- SR": "task1_SR",
        "task3 - TSR": "task3_TSR",
        "Matlab files": "matlab_files",
        "Raw data": "raw_data"
    }
    
    for old_name, new_name in name_fixes.items():
        old_path = os.path.join(base_path, old_name)
        new_path = os.path.join(base_path, new_name)
        if os.path.exists(old_path):
            shutil.move(old_path, new_path)
            print(f"Renamed: {old_name} -> {new_name}")
```

### **Script 2: Extração de Dados Reais**
```python
# scripts/extract_real_fixation_data.py
import pandas as pd
import numpy as np

def extract_real_fixation_durations():
    """Extrai durações reais de fixação dos dados ZuCo"""
    
    # Carregar dados preprocessados
    zuco_path = "data/raw_public/zuco/v1/Preprocessed"
    
    # Processar arquivos de eye-tracking
    fixation_data = []
    
    for file in os.listdir(zuco_path):
        if file.endswith('.mat') or file.endswith('.csv'):
            # Extrair dados reais de fixação
            data = load_zuco_file(file)
            if 'fixation_duration' in data.columns:
                # Garantir variabilidade
                if data['fixation_duration'].std() > 0:
                    fixation_data.append(data)
    
    return pd.concat(fixation_data, ignore_index=True)
```

### **Script 3: Validação Completa**
```python
# scripts/comprehensive_validation.py
def validate_complete_pipeline():
    """Validação completa do pipeline corrigido"""
    
    checks = {
        'data_quality': validate_data_quality(),
        'sample_sizes': validate_sample_sizes(),
        'target_variability': validate_target_variability(),
        'statistical_power': validate_statistical_power()
    }
    
    for check_name, result in checks.items():
        if not result['passed']:
            raise ValidationError(f"Failed: {check_name} - {result['message']}")
    
    return True
```

---

## 📋 **CRONOGRAMA DE RECUPERAÇÃO**

### **Semana 1: Correção de Dados**
- [ ] **Dia 1-2**: Corrigir estrutura de diretórios ZuCo
- [ ] **Dia 3-4**: Extrair dados reais de fixação
- [ ] **Dia 5**: Validar variabilidade dos novos dados

### **Semana 2: Expansão de Amostras**
- [ ] **Dia 1-3**: Localizar e processar dados completos
- [ ] **Dia 4-5**: Validar tamanhos de amostra adequados

### **Semana 3: Reintegração**
- [ ] **Dia 1-3**: Reprocessar pipeline completo
- [ ] **Dia 4-5**: Validação estatística final

### **Semana 4: Validação Final**
- [ ] **Dia 1-2**: Re-executar análises com dados corrigidos
- [ ] **Dia 3-4**: Atualizar documentação e relatórios
- [ ] **Dia 5**: Preparar para retomada de análises científicas

---

## 🎯 **CRITÉRIOS DE SUCESSO**

### **Dados Corrigidos**
- [ ] Target `fixation_duration` com variabilidade > 0.05
- [ ] Valores únicos > 1% do total de observações
- [ ] Distribuição realística (não constante)

### **Amostras Adequadas**
- [ ] DERCo: > 10 participantes
- [ ] GECO: > 10 participantes  
- [ ] ZuCo: Todas as tasks processadas

### **Pipeline Validado**
- [ ] Validação automática em cada etapa
- [ ] Protocolo de qualidade implementado
- [ ] Backup e versionamento funcionais

### **Análises Válidas**
- [ ] Modelos com performance realística (R² < 0.95)
- [ ] Estatísticas descritivas coerentes
- [ ] Correlações interpretáveis

---

## 🚀 **PRÓXIMAS AÇÕES IMEDIATAS**

### **Hoje (Prioridade Máxima)**
1. **Implementar script de correção de caminhos ZuCo**
2. **Extrair dados reais de fixação dos arquivos preprocessados**
3. **Validar variabilidade dos novos dados**

### **Esta Semana (Crítico)**
1. **Localizar dados completos de DERCo e GECO**
2. **Implementar validação automática de qualidade**
3. **Reprocessar pipeline com dados corrigidos**

### **Próximas Semanas (Essencial)**
1. **Validar estatisticamente todos os resultados**
2. **Re-executar análises científicas**
3. **Atualizar documentação e manuscritos**

---

## 💡 **LIÇÕES PARA PREVENÇÃO FUTURA**

1. **Validação Obrigatória**: Implementar checks automáticos em cada etapa
2. **Nomes Padronizados**: Evitar espaços e caracteres especiais em diretórios
3. **Backup Sistemático**: Manter versões dos dados em cada transformação
4. **Documentação Detalhada**: Registrar todas as transformações aplicadas
5. **Testes Unitários**: Criar testes para cada função de processamento

---

**Status**: 🚨 **PLANO DE RECUPERAÇÃO ATIVO**  
**Próxima Atualização**: Após implementação dos scripts de correção  
**Responsável**: Sistema de Recuperação PCS  
**Objetivo**: Restaurar funcionalidade completa do pipeline em 4 semanas
