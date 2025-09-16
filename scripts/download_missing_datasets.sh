#!/usr/bin/env bash
set -euo pipefail

echo "🔄 INICIANDO DOWNLOAD DOS DATASETS EEG/RT FALTANTES"
echo "=================================================="

ROOT_DIR="$(pwd)"
RAW_DIR="$ROOT_DIR/data/raw_public"

# Criar diretórios necessários
mkdir -p "$RAW_DIR/derco" "$RAW_DIR/geco" "$RAW_DIR/lpp" "$RAW_DIR/onestop"

echo ""
echo "📥 [1/4] Baixando DERCo (Dutch Reading Corpus)..."
echo "   Fonte: https://osf.io/8c7a6/"
if wget -q --show-progress "https://osf.io/8c7a6/download" -O "$RAW_DIR/derco.zip"; then
    echo "   ✅ Download concluído: derco.zip"
    echo "   📂 Descompactando..."
    unzip -q "$RAW_DIR/derco.zip" -d "$RAW_DIR/derco/" && rm "$RAW_DIR/derco.zip"
    echo "   ✅ DERCo descompactado em: $RAW_DIR/derco/"
else
    echo "   ❌ Falha no download do DERCo"
fi

echo ""
echo "📥 [2/4] Baixando GECO (Groningen Eyetracking Corpus)..."
echo "   Fonte: https://osf.io/9y4za/"
if wget -q --show-progress "https://osf.io/9y4za/download" -O "$RAW_DIR/geco.zip"; then
    echo "   ✅ Download concluído: geco.zip"
    echo "   📂 Descompactando..."
    unzip -q "$RAW_DIR/geco.zip" -d "$RAW_DIR/geco/" && rm "$RAW_DIR/geco.zip"
    echo "   ✅ GECO descompactado em: $RAW_DIR/geco/"
else
    echo "   ❌ Falha no download do GECO"
fi

echo ""
echo "📥 [3/4] Baixando LPP (Le Petit Prince)..."
echo "   Fonte: https://openneuro.org/datasets/ds005345"
if wget -q --show-progress "https://openneuro.org/crn/datasets/ds005345/snapshots/1.0.0/download" -O "$RAW_DIR/lpp.tar.gz"; then
    echo "   ✅ Download concluído: lpp.tar.gz"
    echo "   📂 Descompactando..."
    tar -xzf "$RAW_DIR/lpp.tar.gz" -C "$RAW_DIR/lpp/" --strip-components=1 && rm "$RAW_DIR/lpp.tar.gz"
    echo "   ✅ LPP descompactado em: $RAW_DIR/lpp/"
else
    echo "   ❌ Falha no download do LPP"
fi

echo ""
echo "📥 [4/4] Baixando OneStop (English Reading Corpus)..."
echo "   Fonte: https://osf.io/8c7a6/"
if wget -q --show-progress "https://osf.io/8c7a6/download" -O "$RAW_DIR/onestop.zip"; then
    echo "   ✅ Download concluído: onestop.zip"
    echo "   📂 Descompactando..."
    unzip -q "$RAW_DIR/onestop.zip" -d "$RAW_DIR/onestop/" && rm "$RAW_DIR/onestop.zip"
    echo "   ✅ OneStop descompactado em: $RAW_DIR/onestop/"
else
    echo "   ❌ Falha no download do OneStop"
fi

echo ""
echo "🎉 DOWNLOADS CONCLUÍDOS!"
echo "========================="
echo "📋 Resumo:"
echo "   • DERCo: $RAW_DIR/derco/"
echo "   • GECO: $RAW_DIR/geco/"
echo "   • LPP: $RAW_DIR/lpp/"
echo "   • OneStop: $RAW_DIR/onestop/"
echo ""
echo "🔍 Execute o diagnóstico novamente:"
echo "   python scripts/dataset_diagnostic.py"
echo ""
echo "📄 Ou verifique o relatório atualizado:"
echo "   cat reports/dataset_diagnostic_report.md"
