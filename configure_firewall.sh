#!/bin/bash
# RAG++ Firewall Configuration Script

echo "🔥 Configurando Firewall para RAG++..."

# Para Ubuntu/Debian (ufw)
if command -v ufw &> /dev/null; then
    echo "📋 Configurando UFW..."
    sudo ufw allow 8000/tcp
    sudo ufw allow ssh
    sudo ufw --force enable
    echo "✅ UFW configurado"
fi

# Para CentOS/RHEL/Fedora (firewalld)
if command -v firewall-cmd &> /dev/null; then
    echo "📋 Configurando firewalld..."
    sudo firewall-cmd --permanent --add-port=8000/tcp
    sudo firewall-cmd --permanent --add-service=ssh
    sudo firewall-cmd --reload
    echo "✅ Firewalld configurado"
fi

# Para sistemas com iptables
if command -v iptables &> /dev/null && ! command -v ufw &> /dev/null && ! command -v firewall-cmd &> /dev/null; then
    echo "📋 Configurando iptables..."
    sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
    sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
    # Salvar regras (varia por distribuição)
    if [ -f /etc/debian_version ]; then
        sudo iptables-save > /etc/iptables/rules.v4
    elif [ -f /etc/redhat-release ]; then
        sudo service iptables save
    fi
    echo "✅ Iptables configurado"
fi

echo "🎉 Firewall configurado com sucesso!"
echo "Porta 8000 aberta para RAG++ API"
