#!/usr/bin/env bash
# repo_autofix.sh - Script idempotente para organizar e normalizar o repositório PCS-Meta-Repo
# Uso: bash tools/repo_autofix.sh [--wide-lines] [--push origin] [--agent-mode]
# Pré-requisitos opcionais: node/npm, python3, pre-commit, mdformat
# Comportamento: detecta e corrige problemas recorrentes em YAML/Markdown/CI, respeitando hooks pre-commit e ambiente macOS
#
# Principais funções:
#  - Normaliza YAML (.github/workflows/*.yml|yaml): --- duplicado, booleans, listas, comentários, line-length
#  - Normaliza Markdown: títulos, cercas, espaçamento, MD022/MD031/MD040
#  - Gera/atualiza configs (.markdownlint.json, .markdownlintignore, .yamllint, ci-lint.yml)
#  - Modo Agentico: análise acadêmica, reprodutibilidade e otimização CI
#  - Executa linters, hooks, commits temáticos e relatório final
#
set -euo pipefail

# Variáveis globais
WIDE_LINES=0
PUSH_ORIGIN=0
SKIP_HOOKS=0
DRY_RUN=0
AGENT_MODE=0
BRANCH_PREFIX="fix/lint-autofix-"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
BRANCH="${BRANCH_PREFIX}${TIMESTAMP}"
REPO_ROOT=""
SED_INPLACE="sed -i ''"
YAML_FILES=()
MD_FILES=()
YAML_FIXED=0
MD_FIXED=0
CONFIG_FIXED=0
AGENT_REPORTS=0
COMMITS=()
SUBMODULE_ALERT=0
SUBMODULE_PATHS=()

# Função: imprime cabeçalho
print_header() {
  echo "\n=============================="
  echo "  PCS-Meta-Repo Autofix v1.0  "
  echo "==============================\n"
}

# Função: parse flags
parse_flags() {
  for arg in "$@"; do
    case "$arg" in
      --wide-lines)
        WIDE_LINES=1
        ;;
      --push*)
        PUSH_ORIGIN=1
        ;;
      --skip-hooks)
        SKIP_HOOKS=1
        ;;
      --dry-run)
        DRY_RUN=1
        ;;
      --agent-mode)
        AGENT_MODE=1
        ;;
    esac
  done
}

# Função: detecta raiz do repo e move para lá
detect_repo_root() {
  REPO_ROOT=$(git rev-parse --show-toplevel)
  cd "$REPO_ROOT"
}

# Função: detecta BSD sed
detect_sed() {
  if sed --version 2>/dev/null | grep -q GNU; then
    SED_INPLACE="sed -i"
  fi
}

# Função: análise acadêmica inteligente (modo agentico)
academic_quality_analysis() {
  if [[ $AGENT_MODE -eq 0 ]]; then
    return 0
  fi

  echo "[AGENT] 🔍 Executando análise de qualidade acadêmica..."

  quality_score=0
  total_checks=0
  issues=()

  # Verificar estrutura de papers
  if [ -d "papers" ]; then
    for paper_dir in papers/*/; do
      if [ -d "$paper_dir" ]; then
        ((total_checks++))
        if [ -f "${paper_dir}README.md" ] || [ -f "${paper_dir}main.tex" ]; then
          ((quality_score++))
        else
          issues+=("Paper sem documentação: $paper_dir")
        fi
      fi
    done
  fi

  # Verificar CITATION.cff
  ((total_checks++))
  if [ -f "CITATION.cff" ]; then
    ((quality_score++))
  else
    issues+=("Arquivo CITATION.cff ausente")
  fi

  # Verificar README principal
  ((total_checks++))
  if [ -f "README.md" ]; then
    ((quality_score++))
  else
    issues+=("README.md principal ausente")
  fi

  # Evitar divisão por zero
  if [[ $total_checks -eq 0 ]]; then
    percentage=0
  else
    percentage=$((quality_score * 100 / total_checks))
  fi

  # Gerar relatório
  mkdir -p reports
  {
    echo "# 📊 Relatório de Qualidade Acadêmica"
    echo "**Data:** $(date)"
    echo "**Modo:** Agentico Automático"
    echo ""
    echo "## 🎯 Score de Qualidade: ${percentage}%"
    echo ""
    echo "### ✅ Verificações Passadas: $quality_score/$total_checks"
    echo ""
    echo "### ⚠️ Issues Identificados:"
    for issue in "${issues[@]}"; do
      echo "- $issue"
    done
    echo ""
    echo "### 📋 Recomendações:"
    echo ""
    echo "1. **Estrutura de Papers**: Cada paper deve ter README.md ou main.tex"
    echo "2. **Citação**: Manter CITATION.cff atualizado"
    echo "3. **Documentação**: README.md principal com badges e descrição"
    echo ""
    echo "### 🔍 Análise Detalhada:"
    echo ""
    echo "- **Papers Encontrados**: $(find papers -type d -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)"
    echo "- **Arquivos de Documentação**: $(find papers -name "*.md" -o -name "*.tex" 2>/dev/null | wc -l)"
    echo "- **Referências**: $(find . -name "*.bib" 2>/dev/null | wc -l)"
    echo ""
    echo "---"
    echo "*Gerado automaticamente pelo modo agentico*"
  } > reports/academic-quality.md

  echo "[AGENT] 📊 Relatório acadêmico gerado: reports/academic-quality.md"
  ((AGENT_REPORTS++))
}

# Função: análise de reprodutibilidade (modo agentico)
reproducibility_analysis() {
  if [[ $AGENT_MODE -eq 0 ]]; then
    return 0
  fi

  echo "[AGENT] 🔬 Executando análise de reprodutibilidade..."

  local repro_score=0
  local total_checks=0
  local issues=()

  # Verificar requirements.txt ou pyproject.toml
  ((total_checks++))
  if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ] || [ -f "environment.yml" ]; then
    ((repro_score++))
  else
    issues+=("Arquivo de dependências ausente (requirements.txt/pyproject.toml)")
  fi

  # Verificar notebooks
  if [ -d "notebooks" ]; then
    ((total_checks++))
    local notebook_count=$(find notebooks -name "*.ipynb" 2>/dev/null | wc -l)
    if [ "$notebook_count" -gt 0 ]; then
      ((repro_score++))
    else
      issues+=("Nenhum notebook Jupyter encontrado")
    fi
  fi

  # Verificar dados
  ((total_checks++))
  if [ -d "data" ] || find . -name "*.csv" -o -name "*.json" -o -name "*.pkl" | grep -v node_modules | grep -q .; then
    ((repro_score++))
  else
    issues+=("Dados de pesquisa não encontrados")
  fi

  # Calcular percentual
  local percentage=$((repro_score * 100 / total_checks))

  # Gerar relatório
  cat > reports/reproducibility.md << EOF
# 🔬 Relatório de Reproducibilidade
**Data:** $(date)
**Modo:** Agentico Automático

## 🎯 Score de Reproducibilidade: ${percentage}%

### ✅ Verificações Passadas: $repro_score/$total_checks

### ⚠️ Issues Identificados:
$(printf '%s\n' "${issues[@]}" | sed 's/^/- /')

### 📋 Recomendações para Reproducibilidade:

1. **Dependências**: Mantenha requirements.txt ou pyproject.toml atualizado
2. **Notebooks**: Documente passos de execução claramente
3. **Dados**: Organize dados em diretório dedicado
4. **Scripts**: Forneça scripts de reprodução automatizados

### 🔍 Análise Detalhada:

- **Dependências Python**: $([ -f "requirements.txt" ] && echo "✅ requirements.txt" || echo "❌ Ausente")
- **Configuração Poetry**: $([ -f "pyproject.toml" ] && echo "✅ pyproject.toml" || echo "❌ Ausente")
- **Notebooks**: $(find notebooks -name "*.ipynb" 2>/dev/null | wc -l) encontrados
- **Scripts de Análise**: $(find . -name "*.py" -path "./src/*" 2>/dev/null | wc -l) encontrados
- **Arquivos de Dados**: $(find . -name "*.csv" -o -name "*.json" -o -name "*.pkl" | grep -v node_modules | wc -l) encontrados

### 🚀 Melhorias Sugeridas:

1. Criar `scripts/reproduce.sh` para execução automatizada
2. Adicionar `Dockerfile` para ambiente containerizado
3. Documentar pipeline de análise em `docs/reproducibility.md`

---
*Gerado automaticamente pelo modo agentico*
EOF

  echo "[AGENT] 🔬 Relatório de reprodutibilidade gerado: reports/reproducibility.md"
  ((AGENT_REPORTS++))
}

# Função: otimização inteligente de CI (modo agentico)
ci_optimization() {
  if [[ $AGENT_MODE -eq 0 ]]; then
    return 0
  fi

  echo "[AGENT] ⚡ Otimizando workflows CI..."

  # Verificar se há duplicatas de workflows
  local duplicates=$(find .github/workflows -name "*.yml" | xargs basename -a | sort | uniq -d)
  if [ -n "$duplicates" ]; then
    echo "[AGENT] ⚠️ Workflows duplicados encontrados: $duplicates"
    echo "[AGENT] 💡 Recomendação: Remover arquivos .tmp e consolidar workflows"
  fi

  # Verificar eficiência dos workflows
  local workflow_count=$(find .github/workflows -name "*.yml" | wc -l)
  echo "[AGENT] 📊 $workflow_count workflows ativos detectados"

  # Sugerir otimizações
  if [ "$workflow_count" -gt 10 ]; then
    echo "[AGENT] 💡 Alta quantidade de workflows. Considere consolidar jobs relacionados"
  fi
}

# Wrapper para git add que respeita DRY_RUN
safe_git_add() {
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY-RUN] git add $*"
  else
    git add "$@"
  fi
}

# Wrapper para git commit que respeita DRY_RUN
safe_git_commit() {
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY-RUN] git commit $*"
    return 0
  else
    git commit "$@"
  fi
}

# Função: garante que o diretório tools existe
ensure_tools_dir() {
  if [[ ! -d "tools" ]]; then
    mkdir -p "tools"
    echo "[INFO] Diretório tools criado."
  fi
}

# Função: troca/cria branch de trabalho
ensure_branch() {
  local current_branch=$(git rev-parse --abbrev-ref HEAD)
  if [[ "$current_branch" == ${BRANCH_PREFIX}* ]]; then
    BRANCH="$current_branch"
  else
    git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"
  fi
}

# Função: alerta submódulo acidental
check_submodule() {
  if [ -d "pcs-meta-repo/pcs-meta-repo" ]; then
    SUBMODULE_ALERT=1
  fi
}

# Carrega paths de submódulos a partir de .gitmodules para evitar adicionar arquivos dentro deles
load_submodules() {
  SUBMODULE_PATHS=()
  if [ -f .gitmodules ]; then
    while IFS= read -r line; do
      if [[ $line =~ path[[:space:]]*=[[:space:]]*(.*) ]]; then
        SUBMODULE_PATHS+=("${BASH_REMATCH[1]}/")
      fi
    done < .gitmodules
  fi
}

# Verifica se um arquivo está dentro de um submódulo
is_in_submodule() {
  local file="$1"
  for p in "${SUBMODULE_PATHS[@]}"; do
    if [[ $file == ./$p* || $file == $p* ]]; then
      return 0
    fi
  done
  return 1
}

# Função: gera/atualiza configs
fix_configs() {
  local changed=0
  # .markdownlint.json
  cat > .markdownlint.json <<EOF
{
  "MD022": { "lines_above": 1, "lines_below": 1 },
  "MD031": true,
  "MD040": true,
  "MD041": false,
  "default": true,
  "MD007": { "indent": 2 },
  "MD009": { "br_spaces": 2 },
  "MD012": { "maximum": 1 }
}
EOF
  safe_git_add -f .markdownlint.json && changed=1

  # .markdownlintignore
  cat > .markdownlintignore <<EOF
node_modules/**
**/venv/**
**/.venv/**
**/vendor/**
**/third_party/**
**/third-party/**
**/build/**
**/__pycache__/**
EOF
  safe_git_add -f .markdownlintignore && changed=1

  # .yamllint
  if [[ $WIDE_LINES -eq 1 ]]; then
    cat > .yamllint <<EOF
---
extends: default
rules:
  document-start:
    present: true
  truthy:
    allowed-values: ['true', 'false']
    check-keys: false
  brackets:
    min-spaces-inside: 0
    max-spaces-inside: 0
  line-length:
    max: 120
    allow-non-breakable-words: true
EOF
  else
    cat > .yamllint <<EOF
---
extends: default
rules:
  document-start:
    present: true
  truthy:
    allowed-values: ['true', 'false']
    check-keys: false
  brackets:
    min-spaces-inside: 0
    max-spaces-inside: 0
  line-length:
    max: 80
    allow-non-breakable-words: true
EOF
  fi
  safe_git_add -f .yamllint && changed=1

  # .github/workflows/ci-lint.yml
  mkdir -p .github/workflows
  cat > .github/workflows/ci-lint.yml <<EOF
---
name: CI Lint
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install markdownlint-cli2
        run: npm install -g markdownlint-cli2
      - name: Install yamllint
        run: pip install yamllint
      - name: Run markdownlint
        run: markdownlint-cli2 "**/*.md"
      - name: Run yamllint
        run: yamllint .github/workflows
EOF
  safe_git_add -f .github/workflows/ci-lint.yml && changed=1

  CONFIG_FIXED=$changed
}

# Função: lista arquivos YAML/MD
find_files() {
  mapfile -t YAML_FILES < <(find .github/workflows -type f \( -name '*.yml' -o -name '*.yaml' \))
  # Exclude common large/ignored directories to avoid touching node_modules, build artifacts, virtualenvs, .git, etc.
  mapfile -t MD_FILES < <(find . \
    -type f -name '*.md' \
    ! -path '*/node_modules/*' \
    ! -path '*/build/*' \
    ! -path '*/pcs-lm/build/*' \
    ! -path '*/.git/*' \
    ! -path '*/.venv/*' \
    ! -path '*/venv/*' \
    ! -path '*/__pycache__/*' \
    ! -path '*/boost-src/*' \
    ! -path '*/third_party/*' \
    ! -path '*/third-party/*' \
    ! -path '*/vendor/*')
}

# Função: autofix YAML
fix_yaml() {
  local fixed=0
  for f in "${YAML_FILES[@]}"; do
    local orig=$(cat "$f")
    local tmp="$f.tmp"
    cp "$f" "$tmp"
    # 1. Garante apenas um --- na primeira linha
    if ! grep -q '^---' "$tmp"; then
      $SED_INPLACE '1i\
---' "$tmp"
    fi
    # Remove --- duplicados entre linhas 2-20
    awk '{
      if (NR >= 2 && NR <= 20) {
        if ($0 == "---") {
          next
        }
      }
      print
    }' "$tmp" > "$tmp.awk" && mv "$tmp.awk" "$tmp"
    # 2. Normaliza booleans True/False fora de aspas (BSD sed)
    $SED_INPLACE -E "/[\"']/!s/([[:space:]:])True([[:space:],#]|$)/\1true\2/g" "$tmp"
    $SED_INPLACE -E "/[\"']/!s/([[:space:]:])False([[:space:],#]|$)/\1false\2/g" "$tmp"
    # 3. Remove espaços em listas em fluxo: [ main , develop ] -> [main, develop]
    $SED_INPLACE -E 's/\[ *([^\]]*) *\]/[\1]/g; s/, +/, /g' "$tmp"
    # 4. Força dois espaços antes de # em comentários inline
    $SED_INPLACE -E 's/([^ ]) #/  #/g' "$tmp"
    # 5. Line-length: quebra linhas >80/120 em run:/args: (portável awk)
    if [[ $WIDE_LINES -eq 0 ]]; then
      awk -v maxlen=80 '
      {
        orig=$0
        # captura indentação inicial (espaços/tabs)
        match(orig,/^[ \t]*/)
        indent=substr(orig,1,RLENGTH)
        # se linha longa e começa com "run:"
        if (length(orig) > maxlen && orig ~ /^[ \t]*run:[ \t]*/) {
          # remove prefixo "run:" e espaços seguintes
          sub(/^[ \t]*run:[ \t]*/,"",orig)
          print indent "run: |"
          print indent "  " orig
        }
        # se linha longa e começa com "args:"
        else if (length(orig) > maxlen && orig ~ /^[ \t]*args:[ \t]*/) {
          sub(/^[ \t]*args:[ \t]*/,"",orig)
          print indent "args: >"
          print indent "  " orig
        }
        else {
          print $0
        }
      }' "$tmp" > "$tmp.awk" && mv "$tmp.awk" "$tmp" || true
    fi
    # 6. Prettier (use npx to avoid creating repo-local node_modules which can conflict with .gitignore)
    if command -v npx >/dev/null 2>&1; then
      npx --yes prettier --write "$tmp" >/dev/null 2>&1 || true
    elif command -v prettier >/dev/null 2>&1; then
      prettier --write "$tmp" >/dev/null 2>&1 || true
    else
      echo "[WARN] prettier not available; skipping formatting for $f"
    fi
    # Se mudou, substitui
    if ! cmp -s "$f" "$tmp"; then
      mv "$tmp" "$f"
      # Skip adding files that are inside submodules or ignored by git
      if is_in_submodule "$f"; then
        echo "[WARN] pulando add para submódulo: $f"
      else
        if git check-ignore -q -- "$f"; then
          echo "[WARN] arquivo ignorado por .gitignore, pulando add: $f"
        else
          safe_git_add -- "$f" || echo "[WARN] git add falhou para: $f"
        fi
      fi
      fixed=$((fixed+1))
    else
      rm "$tmp"
    fi
  done
  YAML_FIXED=$fixed
}

# Função: autofix Markdown
fix_md() {
  local fixed=0
  for f in "${MD_FILES[@]}"; do
    local orig=$(cat "$f")
    local tmp="$f.tmp"
    cp "$f" "$tmp"
    # 1. Corrige cercas sem linguagem -> text (compatível com macOS)
    $SED_INPLACE -E '/^```$/ { s/^```$/```text/; }' "$tmp"
    # 2. Linhas em branco antes/depois de títulos/cercas
    $SED_INPLACE -E '/^#/ { x; /./! { s/^/\n/; }; x; }' "$tmp"
    $SED_INPLACE -E '/^```/ { x; /./! { s/^/\n/; }; x; }' "$tmp"
    # 3. mdformat --wrap no (use 'no' to disable wrapping)
    if command -v python3 >/dev/null 2>&1 && python3 -c "import mdformat" >/dev/null 2>&1; then
      # Tenta mdformat mas continua mesmo se falhar
      if ! python3 -m mdformat --wrap no "$tmp" >/dev/null 2>&1; then
        echo "[WARN] mdformat falhou para $f. Continuando sem mdformat."
      fi
    else
      echo "[INFO] mdformat não encontrado, pulando formatação mdformat para $f"
    fi
    # 4. markdownlint-cli2 --fix and 5. prettier --write
    if command -v npx >/dev/null 2>&1; then
      npx --yes markdownlint-cli2 --fix "$tmp" >/dev/null 2>&1 || true
      npx --yes prettier --write "$tmp" >/dev/null 2>&1 || true
    else
      if command -v markdownlint-cli2 >/dev/null 2>&1; then
        markdownlint-cli2 --fix "$tmp" >/dev/null 2>&1 || true
      fi
      if command -v prettier >/dev/null 2>&1; then
        prettier --write "$tmp" >/dev/null 2>&1 || true
      fi
    fi
    # Se mudou, substitui
    if ! cmp -s "$f" "$tmp"; then
      mv "$tmp" "$f"
      if is_in_submodule "$f"; then
        echo "[WARN] pulando add para submódulo: $f"
      else
        if git check-ignore -q -- "$f"; then
          echo "[WARN] arquivo ignorado por .gitignore, pulando add: $f"
        else
          safe_git_add -- "$f" || echo "[WARN] git add falhou para: $f"
        fi
      fi
      fixed=$((fixed+1))
    else
      rm "$tmp"
    fi
  done
  MD_FIXED=$fixed
}

# Função: valida hooks pre-commit
validate_hooks() {
  if command -v pre-commit >/dev/null 2>&1; then
    pre-commit run --all-files --show-diff-on-failure || {
      # Se erro de YAML, reaplica saneamento dos ---
      for f in "${YAML_FILES[@]}"; do
        # Remove linhas '---' duplicadas entre 2 e 20 de forma portátil (awk funciona no macOS)
        awk 'NR < 2 { print; next } NR > 20 { print; next } { if ($0 != "---") print }' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
      done
      pre-commit run --all-files --show-diff-on-failure || {
        echo "[ERRO] Hooks pre-commit falharam. Ajuste manualmente os arquivos indicados."
        exit 1
      }
    }
  fi
}

# Função: commits temáticos
make_commits() {
  local staged
  staged=$(git diff --cached --name-only)
  if echo "$staged" | grep -qE '(.markdownlint.json|.markdownlintignore|.yamllint|ci-lint.yml)'; then
  safe_git_commit -m "chore(lint/ci): add/refresh lint configs and CI lint workflow" && COMMITS+=("configs/ci") || echo "[WARN] commit configs falhou (pular)"
    staged=$(git diff --cached --name-only)
  fi
  if echo "$staged" | grep -qE '(.github/workflows/.*\.(yml|yaml))'; then
  safe_git_commit -m "style(ci-yaml): normalize workflows (---, booleans, flow lists, comments)" && COMMITS+=("yaml") || echo "[WARN] commit yaml falhou (pular)"
    staged=$(git diff --cached --name-only)
  fi
  if echo "$staged" | grep -qE '(\.md$)'; then
  safe_git_commit -m "style(md): fix MD022/MD031/MD040; normalize fences/headings/spacing" && COMMITS+=("md") || echo "[WARN] commit md falhou (pular)"
    staged=$(git diff --cached --name-only)
  fi
  # Commit D: arquivos restantes
  if [ -n "$staged" ]; then
  safe_git_commit -m "chore(repo): autofix restantes (código/texto)" && COMMITS+=("restantes") || echo "[WARN] commit restantes falhou (pular)"
  fi
}

# Função: relatório final
report() {
  echo "\n=============================="
  echo "  PCS-Meta-Repo Autofix v1.0  "
  echo "==============================\n"

  echo "Resumo da execução:"
  echo "- YAML corrigidos: $YAML_FIXED"
  echo "- Markdown corrigidos: $MD_FIXED"
  echo "- Configs/CI corrigidos: $CONFIG_FIXED"
  echo "- Commits criados: ${#COMMITS[@]}"

  if [[ $AGENT_MODE -eq 1 ]]; then
    echo "- Relatórios agenticos: $AGENT_REPORTS"
    echo ""
    echo "🤖 MODO AGENTICO ATIVO:"
    echo "  📊 Relatório acadêmico: reports/academic-quality.md"
    echo "  🔬 Relatório reprodutibilidade: reports/reproducibility.md"
  fi

  if [[ $SUBMODULE_ALERT -eq 1 ]]; then
    echo "[ALERTA] Submódulo pcs-meta-repo/pcs-meta-repo detectado. Verifique se é intencional."
  fi

  if [[ $PUSH_ORIGIN -eq 1 ]]; then
    git push -u origin "$BRANCH"
    echo "Branch '$BRANCH' enviado para origin."
  fi

  echo "\n[OK] Script concluído. Se restarem pendências, ajuste manualmente conforme instruções acima."
}

# MAIN
print_header
parse_flags "$@"
detect_repo_root
detect_sed
ensure_tools_dir
ensure_branch
check_submodule
load_submodules
fix_configs
find_files
fix_yaml
fix_md

# Modo Agentico: Análises inteligentes
if [[ $AGENT_MODE -eq 1 ]]; then
  academic_quality_analysis
  reproducibility_analysis
  ci_optimization
fi

validate_hooks
make_commits
report
