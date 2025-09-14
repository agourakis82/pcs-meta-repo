# Configuração MCP via Tailscale para ChatGPT

## 🌐 Informações de Acesso

- **IP Tailscale**: 100.78.95.18
- **Domínio Tailscale**: demetriospcs.tail21cbc4.ts.net
- **Porta**: 8000
- **URL Base**: http://demetriospcs.tail21cbc4.ts.net:8000

## 🔑 Autenticação

- **Tipo**: Bearer Token
- **Token**: wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo

## 📡 Endpoints Disponíveis

### Saúde do Sistema
```
GET http://demetriospcs.tail21cbc4.ts.net:8000/health
```

### Busca na Memória
```
POST http://demetriospcs.tail21cbc4.ts.net:8000/memory/search
Headers: Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo
Body: {"query": "sua busca aqui", "max_results": 5}
```

### Armazenar Memória
```
POST http://demetriospcs.tail21cbc4.ts.net:8000/memory/store
Headers: Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo
Body: {"content": "conteúdo", "title": "título", "type": "conversation"}
```

### Categorias de Pesquisa
```
GET http://demetriospcs.tail21cbc4.ts.net:8000/research/categories
```

## 🧪 Teste Rápido

Execute o script de teste:
```bash
./test_mcp_tailscale.sh
```

## 🔧 Configuração no ChatGPT

1. Acesse as configurações de Custom GPT
2. Configure a ação com a URL base: http://demetriospcs.tail21cbc4.ts.net:8000
3. Adicione o header de autenticação: Authorization: Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo
4. Importe o schema OpenAPI de: http://demetriospcs.tail21cbc4.ts.net:8000/openapi.json

## 📱 Acesso de Outros Dispositivos

Qualquer dispositivo na sua rede Tailscale pode acessar:
- **iPhone/iPad**: http://demetriospcs.tail21cbc4.ts.net:8000
- **MacBook**: http://demetriospcs.tail21cbc4.ts.net:8000
- **Windows**: http://demetriospcs.tail21cbc4.ts.net:8000

## 🔒 Segurança

- Acesso restrito à rede Tailscale
- Autenticação via Bearer Token
- Firewall configurado para permitir apenas tráfego Tailscale
