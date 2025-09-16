#!/usr/bin/env bash
set -euo pipefail

echo "📦 EXTRAÇÃO DOS DATASETS IDENTIFICADOS"
echo "======================================"

ROOT_DIR="$(pwd)"
RAW_DIR="$ROOT_DIR/data/raw_public"

echo ""
echo "🎯 EXTRAINDO DATASETS IDENTIFICADOS:"
echo "===================================="

# 1. Extrair EEG-based Reading Experiment.zip para DERCo
echo ""
echo "📥 [1/3] Extraindo DERCo (EEG) de: EEG-based Reading Experiment.zip"
echo "   Destino: $RAW_DIR/derco/"
if [ -f "EEG-based Reading Experiment.zip" ]; then
    mkdir -p "$RAW_DIR/derco/eeg_data"
    echo "   Extraindo dados de EEG..."
    unzip -q "EEG-based Reading Experiment.zip" -d "$RAW_DIR/derco/eeg_data/"
    echo "   ✅ DERCo (EEG) extraído com sucesso!"
else
    echo "   ❌ Arquivo EEG-based Reading Experiment.zip não encontrado"
fi

# 2. Extrair Behavioural Word-Prediction Experiment.zip para DERCo
echo ""
echo "📥 [2/3] Extraindo DERCo (Comportamental) de: Behavioural Word-Prediction Experiment.zip"
echo "   Destino: $RAW_DIR/derco/"
if [ -f "Behavioural Word-Prediction Experiment.zip" ]; then
    mkdir -p "$RAW_DIR/derco/behavioral_data"
    echo "   Extraindo dados comportamentais..."
    unzip -q "Behavioural Word-Prediction Experiment.zip" -d "$RAW_DIR/derco/behavioral_data/"
    echo "   ✅ DERCo (Comportamental) extraído com sucesso!"
else
    echo "   ❌ Arquivo Behavioural Word-Prediction Experiment.zip não encontrado"
fi

# 3. Extrair SWOW-EN18 para GECO (apesar de ser SWOW, seguindo identificação do usuário)
echo ""
echo "📥 [3/3] Extraindo GECO de: SWOW-EN18 (1).zip"
echo "   Destino: $RAW_DIR/geco/"
if [ -f "SWOW-EN18 (1).zip" ]; then
    mkdir -p "$RAW_DIR/geco/swow_data"
    echo "   Extraindo dados SWOW-EN..."
    unzip -q "SWOW-EN18 (1).zip" -d "$RAW_DIR/geco/swow_data/"
    echo "   ✅ GECO (SWOW-EN) extraído com sucesso!"
else
    echo "   ❌ Arquivo SWOW-EN18 (1).zip não encontrado"
fi

echo ""
echo "📊 VERIFICAÇÃO DA EXTRAÇÃO:"
echo "==========================="

echo ""
echo "🔍 Conteúdo dos diretórios extraídos:"
echo "-------------------------------------"

for dataset_dir in "derco" "geco"; do
    if [ -d "$RAW_DIR/$dataset_dir" ]; then
        echo ""
        echo "📁 $dataset_dir/:"
        find "$RAW_DIR/$dataset_dir" -type f | wc -l | xargs echo "   Arquivos totais:"
        du -sh "$RAW_DIR/$dataset_dir" | xargs echo "   Tamanho total:"
        echo "   Estrutura:"
        find "$RAW_DIR/$dataset_dir" -type d | head -10 | sed 's|.*|   &|'
    else
        echo "   ❌ Diretório $dataset_dir não encontrado"
    fi
done

echo ""
echo "🎉 EXTRAÇÃO CONCLUÍDA!"
echo "======================"
echo "📋 Resumo:"
echo "   • DERCo: Dados de EEG + comportamentais extraídos"
echo "   • GECO: Dados SWOW-EN extraídos"
echo ""
echo "🔍 Próximo passo: Executar diagnóstico para verificar integração"
echo "   python scripts/dataset_diagnostic.py"
