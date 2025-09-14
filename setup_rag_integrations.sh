#!/bin/bash
# RAG++ Integration Setup Script
# Configura RAG++ com ChatGPT, Codex e GitHub Copilot

cd /home/agourakis82/workspace/pcs-meta-repo

echo "🌟 RAG++ Integration Setup"
echo "=========================="
echo ""
echo "Configurando integração com:"
echo "• ChatGPT/GPT-4"
echo "• GitHub Copilot"
echo "• VS Code Enhanced"
echo ""

# Execute integration setup
python ragpp/ragpp_integrations.py --setup all

echo ""
echo "🎯 Setup complete! Usage examples:"
echo ""
echo "1. ChatGPT Integration:"
echo "   python ragpp/integrations/openai_integration.py --action chat --query 'recent psychiatric research'"
echo ""
echo "2. Code Generation:"
echo "   python ragpp/integrations/openai_integration.py --action code --query 'function to analyze EEG data'"
echo ""
echo "3. Copilot Enhancement:"
echo "   # Just start coding in VS Code - enhanced context is automatic!"
echo ""
echo "4. Test All Integrations:"
echo "   python ragpp/ragpp_integrations.py --test"
echo ""
