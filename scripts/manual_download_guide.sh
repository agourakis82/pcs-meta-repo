#!/usr/bin/env bash
set -euo pipefail

echo "🔄 VARREDURA COMPLETA E DOWNLOAD DOS DATASETS EEG/RT"
echo "===================================================="

ROOT_DIR="$(pwd)"
RAW_DIR="$ROOT_DIR/data/raw_public"

# Criar diretórios necessários
mkdir -p "$RAW_DIR/derco" "$RAW_DIR/geco" "$RAW_DIR/lpp" "$RAW_DIR/onestop"

echo ""
echo "🔍 [1/4] Verificando acesso aos datasets..."

# Testar acesso aos datasets
echo "   📡 Testando DERCo..."
if curl -s --head "https://osf.io/8c7a6/" | head -1 | grep -q "200"; then
    echo "   ✅ DERCo acessível"
else
    echo "   ❌ DERCo não acessível"
fi

echo "   📡 Testando GECO..."
if curl -s --head "https://osf.io/9y4za/" | head -1 | grep -q "200"; then
    echo "   ✅ GECO acessível"
else
    echo "   ❌ GECO não acessível"
fi

echo "   📡 Testando LPP..."
if curl -s --head "https://openneuro.org/datasets/ds005345" | head -1 | grep -q "200"; then
    echo "   ✅ LPP acessível"
else
    echo "   ❌ LPP não acessível"
fi

echo "   📡 Testando OneStop..."
if curl -s --head "https://osf.io/8c7a6/" | head -1 | grep -q "200"; then
    echo "   ✅ OneStop acessível"
else
    echo "   ❌ OneStop não acessível"
fi

echo ""
echo "💡 INSTRUÇÕES PARA DOWNLOAD MANUAL:"
echo "==================================="
echo ""
echo "📥 DERCo (Dutch Reading Corpus):"
echo "   • Acesse: https://osf.io/8c7a6/"
echo "   • Procure pelo arquivo ZIP do dataset"
echo "   • Baixe e extraia para: $RAW_DIR/derco/"
echo ""
echo "📥 GECO (Groningen Eyetracking Corpus):"
echo "   • Acesse: https://osf.io/9y4za/"
echo "   • Procure pelo arquivo ZIP do dataset"
echo "   • Baixe e extraia para: $RAW_DIR/geco/"
echo ""
echo "📥 LPP (Le Petit Prince):"
echo "   • Acesse: https://openneuro.org/datasets/ds005345"
echo "   • Use o botão 'Download' ou AWS CLI"
echo "   • Extraia para: $RAW_DIR/lpp/"
echo ""
echo "📥 OneStop (English Reading Corpus):"
echo "   • Acesse: https://osf.io/8c7a6/"
echo "   • Procure pelo arquivo ZIP do dataset"
echo "   • Baixe e extraia para: $RAW_DIR/onestop/"
echo ""

echo "🔄 Após baixar os datasets, execute:"
echo "   python scripts/dataset_diagnostic.py"
echo ""

# Verificar se há algum dataset já baixado
echo "📊 STATUS ATUAL DOS DIRETÓRIOS:"
echo "==============================="

for dataset in "derco" "geco" "lpp" "onestop"; do
    dir_path="$RAW_DIR/$dataset"
    if [ -d "$dir_path" ]; then
        file_count=$(find "$dir_path" -type f | wc -l)
        echo "   📁 $dataset: $file_count arquivos encontrados"
    else
        echo "   📁 $dataset: diretório vazio"
    fi
done

echo ""
echo "🎯 PRÓXIMOS PASSOS:"
echo "==================="
echo "1. Baixe manualmente os datasets dos links acima"
echo "2. Extraia os arquivos nos diretórios corretos"
echo "3. Execute o diagnóstico novamente"
echo "4. Execute o pipeline de integração SWOW-ZuCo"
