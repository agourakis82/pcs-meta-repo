# Agents Manifest (stub)

> Este arquivo stub existe para evitar warnings/erros de workflows que procuram por `agents.md`.
> Quando quiser ativar automações “agent”, descreva-as abaixo.

## repo-hygiene (manual)
- scope: /
- steps:
  - pre-commit run --all-files
  - npx -y markdownlint-cli2 --config .markdownlint-cli2.jsonc "**/*.md" "#.git" "#node_modules"
  - yamllint -s .

## ci-latex (opt-in)
- requires: papers/*/Definitions/mdpi.cls
- steps:
  - export TEXINPUTS="papers/*/Definitions:.:$TEXINPUTS"
  - latexmk -pdf -interaction=nonstopmode -halt-on-error <main.tex>
