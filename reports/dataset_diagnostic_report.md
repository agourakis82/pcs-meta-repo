# 🔍 DIAGNÓSTICO ABRANGENTE DOS DATASETS EEG/RT

**Data de geração:** 2025-09-11 20:11:50

## 📋 RESUMO EXECUTIVO

Este relatório diagnostica o status de todos os datasets EEG/RT mencionados:
- **ZuCo v1 & v2**: Datasets de EEG durante leitura
- **DERCo**: Dutch Reading Corpus (EEG + Eye-tracking)
- **GECO**: Groningen Eyetracking Corpus
- **LPP**: Le Petit Prince (EEG + fMRI)
- **OneStop**: English Reading Corpus (Eye-tracking)

## 📁 STATUS DOS DATASETS BRUTOS

### ZuCo v1 (Task 1-2-3)

- **Descrição**: EEG durante leitura de sentenças
- **Fonte**: https://osf.io/2urht/
- **Status**: ✅ Encontrado em `/home/agourakis82/workspace/pcs-meta-repo/data/raw_public/zuco/v1`
- **Conteúdo**: 826 arquivos encontrados
- **task1-SR**: ❌ Nenhum arquivo encontrado
- **task2-NR**: ❌ Nenhum arquivo encontrado
- **task3-TSR**: ❌ Nenhum arquivo encontrado

### ZuCo v2 (Task 2)

- **Descrição**: EEG durante leitura de texto natural
- **Fonte**: https://osf.io/q3zws/
- **Status**: ✅ Encontrado em `/home/agourakis82/workspace/pcs-meta-repo/data/raw_public/zuco/v2`
- **Conteúdo**: 536 arquivos encontrados
- **task2-TSR**: ❌ Nenhum arquivo encontrado

### DERCo (Dutch Reading Corpus)

- **Descrição**: Corpus holandês com EEG e eye-tracking
- **Fonte**: https://osf.io/8c7a6/
- **Status**: ✅ Encontrado em `/home/agourakis82/workspace/pcs-meta-repo/data/raw_public/derco`
- **Conteúdo**: 238 arquivos encontrados
- **eeg**: ✅ 4 arquivos
- **et**: ❌ Nenhum arquivo encontrado

### GECO (Groningen Eyetracking Corpus)

- **Descrição**: Corpus holandês com eye-tracking
- **Fonte**: https://osf.io/9y4za/
- **Status**: ✅ Encontrado em `/home/agourakis82/workspace/pcs-meta-repo/data/raw_public/geco`
- **Conteúdo**: 8 arquivos encontrados
- **et**: ✅ 1 arquivos
- **behavioral**: ❌ Nenhum arquivo encontrado

### LPP (Le Petit Prince)

- **Descrição**: EEG/fMRI durante audição de história
- **Fonte**: https://openneuro.org/datasets/ds005345
- **Status**: ✅ Encontrado em `/home/agourakis82/workspace/pcs-meta-repo/data/raw_public/lpp`
- **Conteúdo**: 0 arquivos encontrados
- **eeg**: ❌ Nenhum arquivo encontrado
- **fmri**: ❌ Nenhum arquivo encontrado
- **stimuli**: ❌ Nenhum arquivo encontrado

### OneStop (English Reading Corpus)

- **Descrição**: Corpus inglês com eye-tracking
- **Fonte**: https://osf.io/8c7a6/
- **Status**: ✅ Encontrado em `/home/agourakis82/workspace/pcs-meta-repo/data/raw_public/onestop`
- **Conteúdo**: 64 arquivos encontrados
- **et**: ✅ 2 arquivos
- **behavioral**: ❌ Nenhum arquivo encontrado

## 🔬 STATUS DOS DATASETS PROCESSADOS

### Integrated Neuro Swow

- **Tamanho**: 155.7 MB
- **Colunas**: 28

### Zuco Aligned

- **Status**: ❌ NÃO encontrado em `/home/agourakis82/workspace/pcs-meta-repo/data/processed/zuco_aligned_real_et_eeg.csv`

### Zuco Word Level

- **Status**: ❌ NÃO encontrado em `/home/agourakis82/workspace/pcs-meta-repo/data/processed/zuco_word_level_all_subjects_real_et_eeg.csv`

## ⚙️  CONFIGURAÇÕES E SCRIPTS

- ✅ `scripts/swow_zuco_pipeline.py` - Encontrado
- ✅ `scripts/optimize_zuco_v2.py` - Encontrado
- ✅ `tools/zuco_loader.py` - Encontrado
- ✅ `tools/auto_discover_zuco.py` - Encontrado

## 🎯 RECOMENDAÇÕES

### Ações Sugeridas:

1. **Verificar downloads**: Confirmar se todos os datasets foram baixados corretamente
2. **Atualizar caminhos**: Revisar arquivos de configuração para caminhos absolutos
3. **Executar pipeline**: Rodar o pipeline de integração SWOW-ZuCo
4. **Validar integridade**: Verificar integridade dos dados processados

### Scripts Úteis:

- `scripts/swow_zuco_pipeline.py` - Pipeline principal de integração
- `tools/zuco_loader.py` - Loader específico para ZuCo
- `scripts/optimize_zuco_v2.py` - Otimizações para ZuCo v2

