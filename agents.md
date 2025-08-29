# Agents Manifest - PCS-Meta-Repo

> Sistema de agentes automatizados para manutenção e curadoria acadêmica do repositório PCS-Meta-Repo.

## 🤖 Modo Agentico Ativo

### repo-hygiene (automático)

- **scope**: `/`
- **trigger**: push, pull_request
- **steps**:
  - `pre-commit run --all-files`
  - `npx -y markdownlint-cli2 --config .markdownlint.json "**/*.md"`
  - `yamllint -s .github/workflows/`
  - `python -m py_compile src/**/*.py` (se existir)
- **auto-commit**: ✅ Ativado para branches de desenvolvimento

### academic-quality-assurance (automático)

- **scope**: `papers/`, `docs/`, `notebooks/`
- **trigger**: push to main/develop
- **steps**:
  - Validar estrutura de papers (abstract, introduction, methods, results, discussion)
  - Verificar presença de CITATION.cff
  - Validar metadados Zenodo
  - Checar referências bibliográficas
- **reports**: Gera relatório em `reports/academic-quality.md`

### reproducibility-check (automático)

- **scope**: `notebooks/`, `src/`, `data/`
- **trigger**: pull_request
- **steps**:
  - Executar notebooks (se possível)
  - Verificar dependências em requirements.txt
  - Validar estrutura de dados
  - Checar scripts de reprodução
- **reports**: Gera relatório em `reports/reproducibility.md`

### ci-latex (condicional)

- **requires**: `papers/*/Definitions/mdpi.cls` ou `papers/*/main.tex`
- **trigger**: push to papers/
- **steps**:
  - `export TEXINPUTS="papers/*/Definitions:.:$TEXINPUTS"`
  - `latexmk -pdf -interaction=nonstopmode -halt-on-error <main.tex>`
  - Validar referências e bibliografia
- **artifacts**: PDFs gerados salvos como artifacts

### dependency-audit (semanal)

- **scope**: `/`
- **trigger**: schedule (weekly)
- **steps**:
  - Auditar dependências Python/Node.js
  - Verificar vulnerabilidades conhecidas
  - Checar compatibilidade de versões
  - Atualizar requirements.txt/pyproject.toml
- **auto-commit**: ✅ Para atualizações de segurança

## 🚀 Recursos Agenticos

### Auto-Committing

- Commits automáticos para correções de linting
- Mensagens padronizadas seguindo conventional commits
- Push automático para branches de desenvolvimento

### Quality Gates

- Bloqueio de PRs com erros de linting
- Validação de estrutura acadêmica
- Checagem de reprodutibilidade

### Intelligent Reporting

- Relatórios automáticos de qualidade
- Métricas de cobertura de código
- Análise de complexidade ciclomática

## ⚙️ Configuração

### Ativação

```bash
# O modo agentico é ativado automaticamente pelos workflows
# Para desenvolvimento local:
pre-commit install
pre-commit run --all-files
```text

### Personalização

- Edite este arquivo para adicionar novos agentes
- Modifique workflows em `.github/workflows/`
- Configure regras em `.pre-commit-config.yaml`

## 📊 Status dos Agentes

- ✅ **repo-hygiene**: Ativo
- ✅ **academic-quality-assurance**: Ativo
- ✅ **reproducibility-check**: Ativo
- ⏳ **ci-latex**: Condicional
- ⏳ **dependency-audit**: Agendado

---
*Modo Agentico v1.0 - PCS-Meta-Repo*stub)

> Este arquivo stub existe para evitar warnings/erros de workflows que procuram por `agents.md`.
> Quando quiser ativar automações “agent”, descreva-as abaixo.

## repo-hygiene (manual)

- scope: /
- steps:
  - pre-commit run --all-files
<<<<<<< Updated upstream
  - npx -y markdownlint-cli2 --config .markdownlint-cli2.jsonc "**/*.md" "#.git" "#node_modules"
=======
  - npx -y markdownlint-cli2 --config .markdownlint-cli2.jsonc "\**/*.md" "#.git" "#node_modules"
>>>>>>> Stashed changes
  - yamllint -s .

## ci-latex (opt-in)

- requires: papers/*/Definitions/mdpi.cls
- steps:
  - export TEXINPUTS="papers/*/Definitions:.:$TEXINPUTS"
  - latexmk -pdf -interaction=nonstopmode -halt-on-error <main.tex>
