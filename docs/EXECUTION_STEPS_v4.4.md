## Execução Passo-a-Passo do Pipeline v4.4

Vou agora executar o pipeline completo seguindo o runbook. Começando com verificação inicial.

### Passo 0: Verificação Inicial
Execute o script que acabamos de criar:

```bash
cd /home/agourakis82/workspace/pcs-meta-repo
python scripts/run_pipeline_v4.4.py
```

Isso irá:
1. Verificar dependências
2. Executar QA inicial  
3. Computar checksums
4. Verificar estrutura v4.4

### Estrutura Esperada após v4.4:
```
/docs               ✓ Criado (GOVERNANCE, RUNBOOK)
/src                ✓ Criado (cli/, datasets/, figures/)  
/scripts            ✓ Criado (pipeline, checksums, inventory)
/notebooks          Existente
/data               
├── L0_raw          Placeholder (dados não redistribuídos)
├── L1_tidy         Para datasets processados
├── L2_derived/kec/ Para KEC multilíngue  
└── processed/v4.4/ Para integração
/figures/v4.4       Para figuras finais
/reports            Para QA e proveniência
/tools              ✓ Criado (verificadores, linters)
/config             ✓ Criado (data_root, datasets)
```

### Próximos Passos:

1. **Dados Reais**: Configure `config/data_root.yaml` com seus paths
2. **Fetch Data**: Execute scripts de fetch para datasets reais
3. **Tidy RT**: Processe datasets RT/ET para L1
4. **Tidy EEG**: Processe datasets EEG para L1  
5. **KEC Compile**: Compile KEC para EN/ES/NL/ZH
6. **Integration**: Integre SWOW↔KEC↔(EEG/RT)
7. **Models**: Execute modelos preditivos
8. **Figures**: Gere figuras F1-F3
9. **QA Final**: Verificação e release

Execute `python scripts/run_pipeline_v4.4.py` para começar!