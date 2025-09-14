#!/bin/bash
# Script para configurar chave SSH no servidor 192.168.4.198
# Execute este script no servidor após copiar a chave pública

set -e

echo "🔑 Configurando chave SSH no servidor"
echo "====================================="

# Criar diretório .ssh se não existir
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Adicionar chave pública ao authorized_keys
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCshzvo42A0n7slhnG9laBOlnjN/rATS23BE7L0e+B8c+5NKHY1s2k2cm9reHpIFjEfgN8nZj6VkwltT0TL6xwZWzPxvKbxdOcbbWXPmU5DoyYg6Gb3MjbCX1rwC4LsHcImQ/6xSh7w/b/ntemf6JF1e0FJDjUVdFutmzXfzTwsmJnyZAcbzgVlgdSjn/6dzWOGYqXfC81CEk2VSOgm3kbWWbmY/SH0hduy9F8KTHPOq2AEisISNrMIIriLtgpm/UFqos1MgjAQkZxtsjQcHaYnQ7yuq72nWDoHD39iwbdUtpCs+s+V1MgxjtZWj6qqVzpkvMkXw4ceD/dGysl+ZcVtWDOJssxz9eZV1emj/vcOwiqeNIomdQ1JFIsb5s/bqP+753kAcUf3yoOQePBiSN1sxCpis89o2hvenCHcZxlE+rSLkLnOotSdgfwDWwd9PitSBR2m49EThPVBEweyVvVWxVyp8Eytqk9nM9sEV0y2hVBh9D7SV77iNmFgyOhdPUVVTNh+8YF8FOyGp1ugqgxJbkqyB4CT9zK+xT7zTrksbqgBJtfaMFyKrgoVuaDHShFhOOzEaccqKYITqbWPYYogQq400LeAbcn9QAE/Zj7Di9lxKQTQclc0vzC1JIynqvlhTwKzjl4Nef6zBdCPxk4NU2MUZYrTcW2jRekh3k8HFw== agourakis82@github" >> ~/.ssh/authorized_keys

# Configurar permissões corretas
chmod 600 ~/.ssh/authorized_keys

# Verificar configuração SSH
echo "📋 Verificando configuração SSH..."
if grep -q "PasswordAuthentication yes" /etc/ssh/sshd_config 2>/dev/null; then
    echo "⚠️  Senha SSH ainda habilitada. Para segurança, considere desabilitar:"
    echo "sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config"
    echo "sudo systemctl reload ssh"
fi

echo ""
echo "✅ Chave SSH configurada com sucesso!"
echo "======================================"
echo "Agora você pode conectar do WSL2 sem senha:"
echo "ssh user@192.168.4.198"
echo ""
echo "📝 Substitua 'user' pelo seu nome de usuário no servidor."