
FIGURES — Pipeline editorial (Scientific Reports)

Arquivos incluídos:
- editorial_preamble.py: toolkit de estilo, exportação multi-formato, rótulos de painéis e rodapé.
- make_figures.py: runner reprodutível com --dry-run e --only.
- analyze_swow.py: distribuição de grau + CCDF (grafo .graphml/.gpickle), saída multi-formato.
- figure_map.json: mapeamento de basenames → nomes finais para o manuscrito.
- latex_includes.tex: trechos prontos de LaTeX para inserir as figuras no wlscirep.

Uso rápido:
1) Ajuste o Python/venv e dependências (matplotlib, numpy, networkx).
2) Rode um dry-run:
   python make_figures.py --dry-run
3) Execute de fato:
   python make_figures.py
4) Saídas:
   - figs/: figuras brutas (PNG/PDF/SVG)
   - figs_final/: cópias com nomes finais do manuscrito

Personalização:
- Edite FINAL_NAMES em make_figures.py OU edite figure_map.json e sincronize o dicionário.
- Para letras de painéis, use editorial_preamble.label_panels([...]).
- Para rodapé, use editorial_preamble.finalize(fig, outdir, basename, footer="Texto").

Contato: insira estes arquivos na pasta onde estão seus scripts de figura.
