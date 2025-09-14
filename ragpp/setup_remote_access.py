#!/usr/bin/env python3
"""
RAG++ Remote Access Setup with Fixed IP
Configure RAG++ server for remote access using your fixed IP.
"""

import os
import socket
import subprocess
import urllib.request
from pathlib import Path


def get_local_ip():
    """Get local IP address."""
    try:
        # Connect to a remote server to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception:
        return "127.0.0.1"


def get_public_ip():
    """Get public IP address."""
    try:
        response = urllib.request.urlopen("https://api.ipify.org", timeout=5)
        public_ip = response.read().decode("utf-8").strip()
        return public_ip
    except Exception as e:
        print(f"⚠️  Could not get public IP: {e}")
        return None


def check_port_open(port=8000):
    """Check if port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", port))
            return True
    except OSError:
        return False


def create_firewall_script():
    """Create script to open firewall ports."""

    firewall_script = """#!/bin/bash
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
"""

    script_path = Path("configure_firewall.sh")
    with open(script_path, "w") as f:
        f.write(firewall_script)

    os.chmod(script_path, 0o755)
    print(f"📄 Script de firewall criado: {script_path}")
    return script_path


def create_remote_server_script():
    """Create script to start server for remote access."""

    local_ip = get_local_ip()
    public_ip = get_public_ip()

    server_script = f"""#!/bin/bash
# RAG++ Remote Server Startup Script

echo "🌐 Iniciando RAG++ para Acesso Remoto"
echo "===================================="

# Configurar variáveis de ambiente
export RAG_API_TOKEN="wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo"
export RAG_HOST="0.0.0.0"  # Escuta em todas as interfaces
export RAG_PORT="8000"

# IPs detectados
echo "🔍 Informações de Rede:"
echo "  IP Local: {local_ip}"
echo "  IP Público: {public_ip or 'Não detectado'}"
echo ""

# Verificar se a porta está livre
if lsof -i :8000 &> /dev/null; then
    echo "⚠️  Porta 8000 já está em uso!"
    echo "Parando processos existentes..."
    pkill -f "ragpp_web_server"
    sleep 2
fi

# Iniciar servidor
echo "🚀 Iniciando servidor RAG++..."
echo "📱 Acesso Local: http://{local_ip}:8000"
if [ "{public_ip}" != "None" ] && [ "{public_ip}" != "" ]; then
    echo "🌐 Acesso Remoto: http://{public_ip}:8000"
fi
echo "📖 Documentação: http://{local_ip}:8000/docs"
echo ""
echo "⏹️  Para parar: Ctrl+C ou 'pkill -f ragpp_web_server'"
echo ""

# Executar servidor
cd /home/agourakis82/workspace/pcs-meta-repo
python ragpp/ragpp_web_server.py

echo "🛑 Servidor parado."
"""

    script_path = Path("start_remote_server.sh")
    with open(script_path, "w") as f:
        f.write(server_script)

    os.chmod(script_path, 0o755)
    print(f"📄 Script de servidor remoto criado: {script_path}")
    return script_path, local_ip, public_ip


def create_nginx_reverse_proxy():
    """Create Nginx reverse proxy configuration."""

    nginx_config = """# RAG++ Nginx Reverse Proxy
# /etc/nginx/sites-available/ragpp

server {
    listen 80;
    server_name your-domain.com;  # Substitua pelo seu domínio ou IP
    
    # Redirect HTTP to HTTPS (opcional)
    # return 301 https://$server_name$request_uri;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers for ChatGPT
        add_header Access-Control-Allow-Origin "https://chat.openai.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "https://chat.openai.com";
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
            add_header Access-Control-Allow-Headers "Authorization, Content-Type";
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 204;
        }
    }
}

# HTTPS Configuration (com SSL certificate)
# server {
#     listen 443 ssl;
#     server_name your-domain.com;
#     
#     ssl_certificate /path/to/your/cert.pem;
#     ssl_certificate_key /path/to/your/key.pem;
#     
#     location / {
#         proxy_pass http://127.0.0.1:8000;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto $scheme;
#     }
# }
"""

    config_path = Path("nginx_ragpp.conf")
    with open(config_path, "w") as f:
        f.write(nginx_config)

    print(f"📄 Configuração Nginx criada: {config_path}")
    return config_path


def create_remote_access_guide():
    """Create comprehensive remote access guide."""

    local_ip = get_local_ip()
    public_ip = get_public_ip()

    guide_content = f"""# 🌐 RAG++ Remote Access Guide

## 📋 Informações da Sua Rede

- **IP Local detectado:** `{local_ip}`
- **IP Público detectado:** `{public_ip or 'Não detectado - verifique manualmente'}`
- **Porta do serviço:** `8000`

---

## 🚀 Setup Rápido (3 passos)

### 1. Configurar Firewall
```bash
# Executar script automático
./configure_firewall.sh

# Ou manual (Ubuntu/Debian):
sudo ufw allow 8000/tcp
sudo ufw enable

# Manual (CentOS/RHEL):
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### 2. Iniciar Servidor Remoto
```bash
./start_remote_server.sh
```

### 3. Testar Acesso
```bash
# Local
curl http://{local_ip}:8000/health

# Remoto (substitua pelo seu IP público)
curl http://SEU_IP_PUBLICO:8000/health
```

---

## 🔧 Configuração Detalhada

### Descobrir seu IP Público
```bash
# Opção 1
curl ifconfig.me

# Opção 2
curl ipinfo.io/ip

# Opção 3
dig +short myip.opendns.com @resolver1.opendns.com
```

### Verificar se a Porta está Aberta
```bash
# Testar localmente
nc -zv {local_ip} 8000

# Testar remotamente (de outro computador)
nc -zv SEU_IP_PUBLICO 8000

# Online tool: https://www.yougetsignal.com/tools/open-ports/
```

### Configurar Roteador (se necessário)
Se você está atrás de um roteador/NAT:

1. **Acesse o painel do roteador** (geralmente 192.168.1.1)
2. **Port Forwarding/Redirecionamento de Porta:**
   - Porta Externa: `8000`
   - Porta Interna: `8000`
   - IP Interno: `{local_ip}`
   - Protocolo: `TCP`

---

## 🌍 Acesso ChatGPT Remoto

### URLs de Acesso:
- **Local:** `http://{local_ip}:8000`
- **Remoto:** `http://SEU_IP_PUBLICO:8000`
- **Documentação:** `http://SEU_IP_PUBLICO:8000/docs`

### Configurar ChatGPT Custom Action:
```json
{{
  "servers": [
    {{
      "url": "http://SEU_IP_PUBLICO:8000"
    }}
  ]
}}
```

### Token de Autenticação:
```
Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo
```

---

## 🔒 Segurança Recomendada

### 1. HTTPS com Let's Encrypt (Recomendado)
```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado (substitua pelo seu domínio)
sudo certbot --nginx -d seu-dominio.com

# Renovação automática
sudo crontab -e
# Adicionar: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Nginx Reverse Proxy
```bash
# Instalar Nginx
sudo apt install nginx

# Copiar configuração
sudo cp nginx_ragpp.conf /etc/nginx/sites-available/ragpp
sudo ln -s /etc/nginx/sites-available/ragpp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Restrições de IP (Opcional)
No Nginx config, adicione:
```nginx
# Permitir apenas IPs específicos
allow 192.168.1.0/24;    # Sua rede local
allow SEU_IP_PUBLICO;     # Seu IP fixo
deny all;
```

---

## 🧪 Testes de Conectividade

### Teste Local:
```bash
curl -X POST "http://{local_ip}:8000/search" \\
  -H "Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo" \\
  -H "Content-Type: application/json" \\
  -d '{{"query": "test connection"}}'
```

### Teste Remoto:
```bash
curl -X POST "http://SEU_IP_PUBLICO:8000/search" \\
  -H "Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo" \\
  -H "Content-Type: application/json" \\
  -d '{{"query": "remote test"}}'
```

---

## 🚨 Troubleshooting

### Problema: "Connection refused"
- ✅ Verificar se o servidor está rodando
- ✅ Verificar firewall local
- ✅ Verificar port forwarding do roteador

### Problema: "Timeout"
- ✅ Verificar IP público correto
- ✅ Verificar se ISP bloqueia a porta
- ✅ Testar com porta alternativa (8080, 3000)

### Problema: "CORS error"
- ✅ Verificar se ChatGPT domains estão na allowlist
- ✅ Usar Nginx reverse proxy
- ✅ Verificar headers CORS

### Logs do Servidor:
```bash
# Verificar logs em tempo real
tail -f /var/log/nginx/access.log  # Se usando Nginx
python ragpp/ragpp_web_server.py  # Logs diretos
```

---

## 📱 Acesso Mobile

Seu smartphone pode acessar via:
- **WiFi local:** `http://{local_ip}:8000`
- **Dados móveis:** `http://SEU_IP_PUBLICO:8000`

---

## ⚡ Scripts Úteis

### Verificar Status:
```bash
#!/bin/bash
echo "🔍 Status RAG++ Remote"
echo "====================="
curl -s http://{local_ip}:8000/health | jq .
echo ""
curl -s http://SEU_IP_PUBLICO:8000/health | jq . || echo "❌ Não acessível remotamente"
```

### Monitoramento:
```bash
#!/bin/bash
while true; do
    if curl -s http://{local_ip}:8000/health > /dev/null; then
        echo "✅ $(date): Servidor OK"
    else
        echo "❌ $(date): Servidor DOWN"
    fi
    sleep 60
done
```

---

## 🎯 Exemplo Completo

1. **Configure firewall:** `./configure_firewall.sh`
2. **Inicie servidor:** `./start_remote_server.sh`
3. **Teste local:** `curl http://{local_ip}:8000/health`
4. **Configure ChatGPT** com URL: `http://SEU_IP_PUBLICO:8000`
5. **Teste no ChatGPT:** "Search for recent AI research"

**Pronto! Seu RAG++ está acessível remotamente! 🚀**
"""

    guide_path = Path("REMOTE_ACCESS_GUIDE.md")
    with open(guide_path, "w") as f:
        f.write(guide_content)

    print(f"📖 Guia de acesso remoto criado: {guide_path}")
    return guide_path


def main():
    """Main setup function for remote access."""
    print("🌐 RAG++ Remote Access Setup")
    print("============================")

    # Get network information
    local_ip = get_local_ip()
    public_ip = get_public_ip()

    print(f"\n🔍 Informações de Rede:")
    print(f"  IP Local: {local_ip}")
    print(f"  IP Público: {public_ip or 'Não detectado'}")

    # Check port availability
    if check_port_open(8000):
        print(f"  Porta 8000: ✅ Disponível")
    else:
        print(f"  Porta 8000: ⚠️  Em uso (será liberada)")

    print(f"\n📁 Criando arquivos de configuração...")

    # Create configuration files
    firewall_script = create_firewall_script()
    server_script, local_ip, public_ip = create_remote_server_script()
    nginx_config = create_nginx_reverse_proxy()
    guide = create_remote_access_guide()

    print(f"\n🎉 Setup completo!")
    print(f"\n📋 Próximos passos:")
    print(f"1. Configure firewall: ./configure_firewall.sh")
    print(f"2. Inicie servidor: ./start_remote_server.sh")
    print(f"3. Teste local: curl http://{local_ip}:8000/health")

    if public_ip:
        print(f"4. Teste remoto: curl http://{public_ip}:8000/health")
        print(f"5. ChatGPT URL: http://{public_ip}:8000")
    else:
        print(f"4. Descubra seu IP público: curl ifconfig.me")
        print(f"5. Configure port forwarding no roteador (se necessário)")

    print(f"\n📖 Leia o guia completo: {guide}")
    print(f"🔑 Token: wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo")


if __name__ == "__main__":
    main()
    main()
