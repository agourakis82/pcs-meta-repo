# 🌐 RAG++ Remote Access Guide

## 📋 Informações da Sua Rede

- **IP Local detectado:** `172.20.7.45`
- **IP Público detectado:** `179.125.169.148`
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
curl http://172.20.7.45:8000/health

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
nc -zv 172.20.7.45 8000

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
   - IP Interno: `172.20.7.45`
   - Protocolo: `TCP`

---

## 🌍 Acesso ChatGPT Remoto

### URLs de Acesso:
- **Local:** `http://172.20.7.45:8000`
- **Remoto:** `http://SEU_IP_PUBLICO:8000`
- **Documentação:** `http://SEU_IP_PUBLICO:8000/docs`

### Configurar ChatGPT Custom Action:
```json
{
  "servers": [
    {
      "url": "http://SEU_IP_PUBLICO:8000"
    }
  ]
}
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
curl -X POST "http://172.20.7.45:8000/search" \
  -H "Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo" \
  -H "Content-Type: application/json" \
  -d '{"query": "test connection"}'
```

### Teste Remoto:
```bash
curl -X POST "http://SEU_IP_PUBLICO:8000/search" \
  -H "Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo" \
  -H "Content-Type: application/json" \
  -d '{"query": "remote test"}'
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
- **WiFi local:** `http://172.20.7.45:8000`
- **Dados móveis:** `http://SEU_IP_PUBLICO:8000`

---

## ⚡ Scripts Úteis

### Verificar Status:
```bash
#!/bin/bash
echo "🔍 Status RAG++ Remote"
echo "====================="
curl -s http://172.20.7.45:8000/health | jq .
echo ""
curl -s http://SEU_IP_PUBLICO:8000/health | jq . || echo "❌ Não acessível remotamente"
```

### Monitoramento:
```bash
#!/bin/bash
while true; do
    if curl -s http://172.20.7.45:8000/health > /dev/null; then
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
3. **Teste local:** `curl http://172.20.7.45:8000/health`
4. **Configure ChatGPT** com URL: `http://SEU_IP_PUBLICO:8000`
5. **Teste no ChatGPT:** "Search for recent AI research"

**Pronto! Seu RAG++ está acessível remotamente! 🚀**
