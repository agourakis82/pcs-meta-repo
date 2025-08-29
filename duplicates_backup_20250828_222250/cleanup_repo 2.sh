#!/usr/bin/env bash
# cleanup_repo.sh - Script para limpar arquivos duplicados e organizar branches
# Uso: bash cleanup_repo.sh [--dry-run] [--force]

set -euo pipefail

DRY_RUN=0
FORCE=0

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
  echo -e "${GREEN}=============================="
  echo "  PCS-Meta-Repo Cleanup v1.0  "
  echo -e "==============================${NC}\n"
}

parse_flags() {
  for arg in "$@"; do
    case "$arg" in
      --dry-run)
        DRY_RUN=1
        ;;
      --force)
        FORCE=1
        ;;
    esac
  done
}

backup_file() {
  local file="$1"
  local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$backup_dir"
  cp "$file" "$backup_dir/"
  echo "Backup criado: $backup_dir/$(basename "$file")"
}

remove_duplicates() {
  echo -e "${YELLOW}🔍 Procurando arquivos duplicados...${NC}"

  # Arquivos com " 2" no nome
  local duplicates=()
  while IFS= read -r -d '' file; do
    duplicates+=("$file")
  done < <(find . -name "* 2.*" -o -name "* 2" -print0)

  if [[ ${#duplicates[@]} -eq 0 ]]; then
    echo "Nenhum arquivo duplicado encontrado."
    return 0
  fi

  echo "Encontrados ${#duplicates[@]} arquivos duplicados:"
  printf '  %s\n' "${duplicates[@]}"

  if [[ $DRY_RUN -eq 1 ]]; then
    echo -e "${YELLOW}[DRY-RUN] Simulando remoção...${NC}"
    return 0
  fi

  if [[ $FORCE -eq 0 ]]; then
    read -p "Deseja fazer backup antes de remover? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      for file in "${duplicates[@]}"; do
        backup_file "$file"
      done
    fi

    read -p "Confirmar remoção dos arquivos duplicados? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Operação cancelada."
      return 1
    fi
  fi

  echo -e "${RED}Removendo arquivos duplicados...${NC}"
  for file in "${duplicates[@]}"; do
    rm -f "$file"
    echo "Removido: $file"
  done
}

remove_temp_files() {
  echo -e "${YELLOW}🧹 Removendo arquivos temporários...${NC}"

  # Arquivos .tmp''
  local temp_files=()
  while IFS= read -r -d '' file; do
    temp_files+=("$file")
  done < <(find . -name "*.tmp''" -print0)

  if [[ ${#temp_files[@]} -eq 0 ]]; then
    echo "Nenhum arquivo temporário encontrado."
    return 0
  fi

  echo "Encontrados ${#temp_files[@]} arquivos temporários:"
  printf '  %s\n' "${temp_files[@]}"

  if [[ $DRY_RUN -eq 1 ]]; then
    echo -e "${YELLOW}[DRY-RUN] Simulando remoção...${NC}"
    return 0
  fi

  if [[ $FORCE -eq 0 ]]; then
    read -p "Confirmar remoção dos arquivos temporários? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Operação cancelada."
      return 1
    fi
  fi

  echo -e "${RED}Removendo arquivos temporários...${NC}"
  for file in "${temp_files[@]}"; do
    rm -f "$file"
    echo "Removido: $file"
  done
}

analyze_branches() {
  echo -e "${YELLOW}📊 Analisando branches...${NC}"

  echo "Branches locais:"
  git branch | cat

  echo -e "\nBranches remotos:"
  git branch -r | cat

  echo -e "\n${GREEN}Recomendações para merge:${NC}"
  echo "1. Branches 'fix/lint-autofix-*' podem ser removidos após merge"
  echo "2. Branches 'codex/*' são automáticos e podem ser limpos"
  echo "3. Mantenha apenas branches principais: main, develop (se existir)"
  echo "4. Branches de features devem ser merged ou removidos"
}

cleanup_branches() {
  echo -e "${YELLOW}🧹 Limpando branches antigos...${NC}"

  if [[ $DRY_RUN -eq 1 ]]; then
    echo -e "${YELLOW}[DRY-RUN] Simulando limpeza de branches...${NC}"
    echo "Branches que seriam removidos:"
    git branch | grep -E "(fix/lint-autofix|codex/)" | cat
    return 0
  fi

  if [[ $FORCE -eq 0 ]]; then
    read -p "Deseja fazer merge dos branches de fix antes de remover? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      echo "Fazendo merge dos branches de fix..."
      for branch in $(git branch | grep "fix/lint-autofix" | sed 's/*//'); do
        echo "Merging $branch..."
        git merge "$branch" --no-edit || true
      done
    fi

    read -p "Confirmar remoção dos branches antigos? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Operação cancelada."
      return 1
    fi
  fi

  echo -e "${RED}Removendo branches antigos...${NC}"
  git branch | grep -E "(fix/lint-autofix|codex/)" | xargs git branch -D 2>/dev/null || true
  echo "Branches antigos removidos."
}

main() {
  print_header
  parse_flags "$@"

  if [[ $DRY_RUN -eq 1 ]]; then
    echo -e "${YELLOW}🔍 MODO DRY-RUN ATIVADO - Nenhuma alteração será feita${NC}\n"
  fi

  remove_duplicates
  echo
  remove_temp_files
  echo
  analyze_branches
  echo
  cleanup_branches

  echo -e "\n${GREEN}✅ Limpeza concluída!${NC}"
  echo "Para continuar:"
  echo "1. Verifique se os arquivos importantes não foram removidos"
  echo "2. Faça commit das mudanças: git add -A && git commit -m 'chore: cleanup duplicates and temp files'"
  echo "3. Push as mudanças: git push origin main"
}

main "$@"
