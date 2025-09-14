#!/bin/bash
# PCS AI Research Suite - PATH Setup
# Adiciona ~/.local/bin ao PATH permanentemente

SHELL_CONFIG=""

# Detectar shell e arquivo de configuração
if [[ "$SHELL" == *"bash"* ]]; then
    if [[ -f "$HOME/.bashrc" ]]; then
        SHELL_CONFIG="$HOME/.bashrc"
    elif [[ -f "$HOME/.bash_profile" ]]; then
        SHELL_CONFIG="$HOME/.bash_profile"
    fi
elif [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_CONFIG="$HOME/.zshrc"
fi

if [[ -n "$SHELL_CONFIG" ]]; then
    # Verificar se já existe
    if ! grep -q "/.local/bin" "$SHELL_CONFIG"; then
        echo "" >> "$SHELL_CONFIG"
        echo "# PCS AI Research Suite PATH" >> "$SHELL_CONFIG"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"
        echo "✅ PATH adicionado a $SHELL_CONFIG"
        echo "💡 Execute: source $SHELL_CONFIG ou reinicie o terminal"
    else
        echo "✅ PATH já configurado em $SHELL_CONFIG"
    fi
else
    echo "⚠️  Shell não detectado. Adicione manualmente:"
    echo 'export PATH="$HOME/.local/bin:$PATH"'
fi

echo ""
echo "🚀 Para usar imediatamente:"
echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
echo "pcs-ai-suite"
