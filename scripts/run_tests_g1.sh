#!/bin/bash

# Script de Validação G1 - Sistema de Documentação Automática
# Valida se todos os componentes do sistema de documentação estão funcionando

echo "🔍 VALIDAÇÃO G1 - SISTEMA DE DOCUMENTAÇÃO AUTOMÁTICA"
echo "=" "="="="="="="="="="="="="="="="="="="="="="="="="="="="="="="="="="="="

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contador de sucessos
SUCCESS_COUNT=0
TOTAL_TESTS=10

# Função para testar arquivo
test_file() {
    local file="$1"
    local description="$2"
    
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✅${NC} $description: ${BLUE}$file${NC}"
        ((SUCCESS_COUNT++))
    else
        echo -e "${RED}❌${NC} $description: ${RED}$file (não encontrado)${NC}"
    fi
}

# Função para testar diretório
test_directory() {
    local dir="$1"
    local description="$2"
    
    if [[ -d "$dir" ]]; then
        echo -e "${GREEN}✅${NC} $description: ${BLUE}$dir${NC}"
        ((SUCCESS_COUNT++))
    else
        echo -e "${RED}❌${NC} $description: ${RED}$dir (não encontrado)${NC}"
    fi
}

echo "🔄 Verificando estrutura de documentação..."

# Verificar diretórios principais
test_directory "docs/api" "Diretório API docs"
test_directory "docs/guides" "Diretório de guias"

# Verificar arquivos de documentação
test_file "docs/api/README.md" "Documentação da API"
test_file "docs/guides/installation.md" "Guia de instalação"
test_file "docs/guides/quickstart.md" "Guia de uso rápido"
test_file "docs/guides/troubleshooting.md" "Guia de troubleshooting"
test_file "docs/code-documentation.md" "Documentação do código"
test_file "CHANGELOG.md" "Changelog"

echo
echo "🔄 Verificando script gerador..."

if [[ -x "scripts/generate_docs.py" ]]; then
    echo -e "${GREEN}✅${NC} Script gerador executável: ${BLUE}scripts/generate_docs.py${NC}"
    ((SUCCESS_COUNT++))
else
    echo -e "${RED}❌${NC} Script gerador não executável: ${RED}scripts/generate_docs.py${NC}"
fi

echo
echo "🔄 Testando geração de documentação..."

# Executar gerador silenciosamente para testar
if python scripts/generate_docs.py > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Gerador executa sem erros"
    ((SUCCESS_COUNT++))
else
    echo -e "${RED}❌${NC} Erro na execução do gerador"
fi

echo
echo "📊 RESULTADOS DA VALIDAÇÃO:"
echo "=" "="="="="="="="="="="="="="="="="="="="="="="="="="="="="="="="="="="="

# Calcular porcentagem
PERCENTAGE=$((SUCCESS_COUNT * 100 / TOTAL_TESTS))

if [[ $SUCCESS_COUNT -eq $TOTAL_TESTS ]]; then
    echo -e "${GREEN}🎉 SUCESSO: $SUCCESS_COUNT/$TOTAL_TESTS testes passaram! ($PERCENTAGE%)${NC}"
    echo -e "${GREEN}✅ Sistema G1 de Documentação está totalmente funcional!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  PARCIAL: $SUCCESS_COUNT/$TOTAL_TESTS testes passaram ($PERCENTAGE%)${NC}"
    echo -e "${RED}❌ Alguns componentes do Sistema G1 precisam de atenção${NC}"
    exit 1
fi