#!/usr/bin/env bash
set -euo pipefail

echo "🔄 INICIANDO DOWNLOAD DOS DATASETS EEG/RT FALTANTES (URLs CORRETAS)"
echo "================================================================="

ROOT_DIR="$(pwd)"
RAW_DIR="$ROOT_DIR/data/raw_public"

# Criar diretórios necessários
mkdir -p "$RAW_DIR/derco" "$RAW_DIR/geco" "$RAW_DIR/lpp" "$RAW_DIR/onestop"

echo ""
echo "📥 [1/4] Baixando DERCo (Dutch Reading Corpus)..."
echo "   Fonte: https://osf.io/8c7a6/download"
if wget -q --show-progress "https://osf.io/8c7a6/download" -O "$RAW_DIR/derco/derco_data.zip"; then
    echo "   ✅ Download concluído: derco_data.zip"
    echo "   📂 Descompactando..."
    if unzip -q "$RAW_DIR/derco/derco_data.zip" -d "$RAW_DIR/derco/"; then
        rm "$RAW_DIR/derco/derco_data.zip"
        echo "   ✅ DERCo descompactado em: $RAW_DIR/derco/"
    else
        echo "   ⚠️  Problema na descompactação, mantendo arquivo ZIP"
    fi
else
    echo "   ❌ Falha no download do DERCo"
fi

echo ""
echo "📥 [2/4] Baixando GECO (Groningen Eyetracking Corpus)..."
echo "   Fonte: https://osf.io/9y4za/download"
if wget -q --show-progress "https://osf.io/9y4za/download" -O "$RAW_DIR/geco/geco_data.zip"; then
    echo "   ✅ Download concluído: geco_data.zip"
    echo "   📂 Descompactando..."
    if unzip -q "$RAW_DIR/geco/geco_data.zip" -d "$RAW_DIR/geco/"; then
        rm "$RAW_DIR/geco/geco_data.zip"
        echo "   ✅ GECO descompactado em: $RAW_DIR/geco/"
    else
        echo "   ⚠️  Problema na descompactação, mantendo arquivo ZIP"
    fi
else
    echo "   ❌ Falha no download do GECO"
fi

echo ""
echo "📥 [3/4] Baixando LPP (Le Petit Prince)..."
echo "   Fonte: https://openneuro.org/datasets/ds005345"
if wget -q --show-progress "https://openneuro.org/crn/datasets/ds005345/snapshots/1.0.0/download" -O "$RAW_DIR/lpp/lpp_data.tar.gz"; then
    echo "   ✅ Download concluído: lpp_data.tar.gz"
    echo "   📂 Descompactando..."
    if tar -xzf "$RAW_DIR/lpp/lpp_data.tar.gz" -C "$RAW_DIR/lpp/" --strip-components=1; then
        rm "$RAW_DIR/lpp/lpp_data.tar.gz"
        echo "   ✅ LPP descompactado em: $RAW_DIR/lpp/"
    else
        echo "   ⚠️  Problema na descompactação, mantendo arquivo TAR.GZ"
    fi
else
    echo "   ❌ Falha no download do LPP"
fi

echo ""
echo "📥 [4/4] Baixando OneStop (English Reading Corpus)..."
echo "   Fonte: https://lacclab.github.io/OneStop-Eye-Movements/"
echo "   🔍 Procurando arquivos de dados OneStop..."

# Tentar baixar dados OneStop de fontes alternativas
# Primeiro tentar o repositório GitHub
if wget -q --show-progress "https://github.com/lacclab/OneStop-Eye-Movements/archive/main.zip" -O "$RAW_DIR/onestop/onestop_github.zip"; then
    echo "   ✅ Download do GitHub concluído: onestop_github.zip"
    echo "   📂 Descompactando..."
    if unzip -q "$RAW_DIR/onestop/onestop_github.zip" -d "$RAW_DIR/onestop/"; then
        rm "$RAW_DIR/onestop/onestop_github.zip"
        echo "   ✅ OneStop (GitHub) descompactado em: $RAW_DIR/onestop/"
    else
        echo "   ⚠️  Problema na descompactação do GitHub"
    fi
else
    echo "   ❌ Falha no download do OneStop (GitHub)"
    # Tentar fonte alternativa se disponível
    echo "   🔄 Tentando fonte OSF alternativa..."
    if wget -q --show-progress "https://files.osf.io/v1/resources/8c7a6/providers/osfstorage/" -O "$RAW_DIR/onestop/onestop_osf.html"; then
        echo "   📄 Página OSF baixada - verificar manualmente por links de download"
    fi
fi

echo ""
echo "🎉 DOWNLOADS CONCLUÍDOS!"
echo "========================="
echo "📋 Resumo dos downloads:"
echo "   • DERCo: $(ls -la $RAW_DIR/derco/ | wc -l) arquivos em $RAW_DIR/derco/"
echo "   • GECO: $(ls -la $RAW_DIR/geco/ | wc -l) arquivos em $RAW_DIR/geco/"
echo "   • LPP: $(ls -la $RAW_DIR/lpp/ | wc -l) arquivos em $RAW_DIR/lpp/"
echo "   • OneStop: $(ls -la $RAW_DIR/onestop/ | wc -l) arquivos em $RAW_DIR/onestop/"
echo ""

# Verificar se os datasets foram baixados corretamente
echo "🔍 VERIFICAÇÃO DE INTEGRIDADE:"
echo "================================"

check_dataset() {
    local name=$1
    local dir=$2
    local min_files=$3

    local file_count=$(find "$dir" -type f | wc -l)
    if [ "$file_count" -gt "$min_files" ]; then
        echo "   ✅ $name: $file_count arquivos encontrados"
    else
        echo "   ❌ $name: Apenas $file_count arquivos (esperado > $min_files)"
    fi
}

check_dataset "DERCo" "$RAW_DIR/derco/" 10
check_dataset "GECO" "$RAW_DIR/geco/" 5
check_dataset "LPP" "$RAW_DIR/lpp/" 5
check_dataset "OneStop" "$RAW_DIR/onestop/" 5

echo ""
echo "🔍 Execute o diagnóstico novamente:"
echo "   python scripts/dataset_diagnostic.py"
echo ""
echo "📄 Ou verifique o relatório atualizado:"
echo "   cat reports/cross_validation_report.md"
