# Curadoria da raiz do repositório

Este relatório resume a análise automática dos arquivos soltos na raiz.
Os critérios são heurísticos e servem como ponto de partida para revisão humana.

## Resumo

- Total de entradas analisadas: 122
- Ações sugeridas:
  - review: 102
  - keep: 20
- Destinos sugeridos:
  - -: 122

## Próximos passos sugeridos

- Conferir itens com ação 'review' e decidir destino.
- Mover logs para `logs/` e adicionar ao `.gitignore` se necessário.
- Mover artefatos (`*.zip`) para `artifacts/` ou publicar em releases.
- Centralizar metadados (Zenodo/CITATION/metadata) em `metadata/`.
- Scripts `run_*` e `setup_*` para `scripts/` ou `ops/` conforme o caso.
- Consolidar READMEs/CHANGELOGs em `docs/` e relatórios em `reports/`.

> Arquivo gerado por `tools/generate_root_curation.py`.
