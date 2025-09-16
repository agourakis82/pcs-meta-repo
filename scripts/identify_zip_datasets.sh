#!/usr/bin/env bash
set -euo pipefail

echo "🔍 IDENTIFICAÇÃO DE DATASETS NOS ARQUIVOS ZIP"
echo "============================================="

ROOT_DIR="$(pwd)"

# Lista de arquivos ZIP a verificar (excluindo .attic e Zone.Identifier)
ZIP_FILES=(
    "EEG-based Reading Experiment.zip"
    "Behavioural Word-Prediction Experiment.zip"
    "SWOW-EN18 (1).zip"
    "SWOW-RP22 (1).zip"
    "SWOW-ZH24.zip"
    "DutchWordAssociationData_April2012CSV.zip"
    "DutchWordAssociationData_April2012Matlab.zip"
)

echo ""
echo "📋 VERIFICAÇÃO DOS ARQUIVOS ZIP:"
echo "================================="

for zip_file in "${ZIP_FILES[@]}"; do
    if [ -f "$zip_file" ]; then
        echo ""
        echo "🔍 Analisando: $zip_file"
        echo "   Tamanho: $(du -h "$zip_file" | cut -f1)"

        # Verificar conteúdo
        if unzip -l "$zip_file" > /dev/null 2>&1; then
            file_count=$(unzip -l "$zip_file" | tail -1 | awk '{print $2}')
            echo "   Arquivos: $file_count"

            # Verificar tipos de dados
            has_eeg=$(unzip -l "$zip_file" | grep -i -E "\.(fif|eeg|bdf|cnt|vhdr|vmrk)$" | wc -l)
            has_et=$(unzip -l "$zip_file" | grep -i -E "\.(asc|gaz|fix|eye|et)$" | wc -l)
            has_csv=$(unzip -l "$zip_file" | grep -i "\.csv$" | wc -l)
            has_mat=$(unzip -l "$zip_file" | grep -i "\.mat$" | wc -l)

            echo "   Conteúdo:"
            [ "$has_eeg" -gt 0 ] && echo "   • EEG: $has_eeg arquivos"
            [ "$has_et" -gt 0 ] && echo "   • Eye-tracking: $has_et arquivos"
            [ "$has_csv" -gt 0 ] && echo "   • CSV: $has_csv arquivos"
            [ "$has_mat" -gt 0 ] && echo "   • MATLAB: $has_mat arquivos"

            # Verificar datasets específicos
            has_derco=$(unzip -l "$zip_file" | grep -i "derco" | wc -l)
            has_geco=$(unzip -l "$zip_file" | grep -i "geco" | wc -l)
            has_lpp=$(unzip -l "$zip_file" | grep -i "lpp" | wc -l)
            has_onestop=$(unzip -l "$zip_file" | grep -i "onestop" | wc -l)
            has_zuco=$(unzip -l "$zip_file" | grep -i "zuco" | wc -l)

            if [ "$has_derco" -gt 0 ] || [ "$has_geco" -gt 0 ] || [ "$has_lpp" -gt 0 ] || [ "$has_onestop" -gt 0 ] || [ "$has_zuco" -gt 0 ]; then
                echo "   🎯 DATASETS IDENTIFICADOS:"
                [ "$has_derco" -gt 0 ] && echo "   • DERCo encontrado!"
                [ "$has_geco" -gt 0 ] && echo "   • GECO encontrado!"
                [ "$has_lpp" -gt 0 ] && echo "   • LPP encontrado!"
                [ "$has_onestop" -gt 0 ] && echo "   • OneStop encontrado!"
                [ "$has_zuco" -gt 0 ] && echo "   • ZuCo encontrado!"
            fi

            # Mostrar estrutura de diretórios
            echo "   📁 Estrutura:"
            unzip -l "$zip_file" | head -20 | tail -10 | awk '{print "   " $4}' | head -5

        else
            echo "   ❌ Erro ao ler arquivo ZIP"
        fi
    fi
done

echo ""
echo "🎯 RESUMO DA ANÁLISE:"
echo "====================="
echo "• Arquivos ZIP verificados: ${#ZIP_FILES[@]}"
echo "• Maior arquivo: EEG-based Reading Experiment.zip (17GB)"
echo "• Contém dados de EEG preprocessados"
echo ""
echo "💡 PRÓXIMOS PASSOS:"
echo "==================="
echo "1. Identificar se algum ZIP contém os datasets faltantes"
echo "2. Extrair datasets identificados para os diretórios corretos"
echo "3. Executar diagnóstico novamente"
