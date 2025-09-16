# PLANO SISTEMÁTICO DE CORREÇÃO DE ERROS DE DADOS - PCS META REPO

## ANÁLISE INICIAL COMPLETA
**Pergunta Original**: É só o ZuCo que está causando erros de dados?
**Resposta**: **NÃO**. Problemas sistêmicos em múltiplos datasets.

## STATUS DOS DATASETS:
- ✅ **COMPLIANT**: ZuCo v1/v2, DERCo
- ⚠️ **NEEDS IMPROVEMENT**: GECO, LPP, OneStop  
- 🔍 **ISSUES**: SWOW (multilingual)

## PROBLEMAS IDENTIFICADOS:
1. **Schema validation parcial** - Datasets não seguem contracts_v4.4 completamente
2. **Import paths hardcoded** - Problemas de importação em GECO, LPP, OneStop
3. **Placeholder data** - Dados de teste em vez de implementação real
4. **Target degeneracy** - Problemas de qualidade de dados
5. **Issues multilíngues** - Especialmente no SWOW
6. **Validação inconsistente** - Cada dataset usa validação diferente

## PLANO DE IMPLEMENTAÇÃO (5 FASES):

### FASE 1: INFRAESTRUTURA DE VALIDAÇÃO ⚡ [EM EXECUÇÃO]
**Objetivo**: Criar base sólida para validação uniforme
- [x] Criar validation_utils.py centralizado
- [ ] Padronizar schema validation
- [ ] Implementar quality gates uniformes
- [ ] Criar testes automatizados

### FASE 2: CORREÇÃO GECO LOADER
**Objetivo**: Tornar GECO totalmente compliant
- [ ] Fix import paths hardcoded
- [ ] Implementar real data loading (remover placeholder)
- [ ] Schema compliance completa
- [ ] Validação robusta

### FASE 3: CORREÇÃO LPP LOADER  
**Objetivo**: Resolver compliance parcial do LPP
- [ ] Remove placeholder data
- [ ] Implementar validação robusta
- [ ] Fix compliance issues
- [ ] Quality assurance completa

### FASE 4: CORREÇÃO ONESTOP LOADER
**Objetivo**: Resolver import e validation issues
- [ ] Fix import paths
- [ ] Schema validation completa
- [ ] Quality assurance
- [ ] Testes de integração

### FASE 5: SWOW MULTILINGUAL FIX
**Objetivo**: Resolver issues multilíngues do SWOW
- [ ] Resolver issues multilíngues
- [ ] Padronizar processamento
- [ ] Audit compliance
- [ ] Documentação completa

## PROGRESSO DE EXECUÇÃO:
- **INICIADO**: 2025-01-29
- **FASE ATUAL**: 1 - Infraestrutura de Validação
- **STATUS**: Em execução - validation_utils.py criado
