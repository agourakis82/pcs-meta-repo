<!-- markdownlint-disable MD013 -->

# Agent Starter Pack (GitHub chores)

Este pacote adiciona automações e padrões mínimos para reduzir tarefas burocráticas:
- CI de links, Markdown, Python e LaTeX
- Templates de Issue/PR, CODEOWNERS, EditorConfig
- Pre-commit (ruff/black/isort)

## Como aplicar (gh CLI)
```bash
# no diretório do seu repositório local
unzip github_agent_starter_pack.zip -d ./
git checkout -b chore/agent-pack
git add -A
git commit -m "chore(ops): add agent starter pack (CI, templates, pre-commit)"
git push -u origin chore/agent-pack
gh pr create --title "chore(ops): agent starter pack" --body "Adds CI, templates and pre-commit to reduce chores."
```text

## Pre-commit
```bash
pip install pre-commit
pre-commit install
pre-commit run -a
```text
