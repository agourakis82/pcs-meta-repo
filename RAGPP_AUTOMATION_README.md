# RAG++ Production Automation Suite

> Sistema completo de automação para manutenção e operação do RAG++ em produção

## 📋 Visão Geral

Este conjunto de scripts automatiza todas as tarefas de manutenção, backup, monitoramento e atualização do sistema RAG++ em produção, garantindo alta disponibilidade e performance consistente.

## 🛠️ Componentes

### Scripts de Manutenção

#### `maintenance_ragpp.sh`

- **Função**: Manutenção automática semanal do sistema
- **Executa**:
  - Verificação de saúde do sistema
  - Limpeza de cache antigo
  - Otimização de banco de dados
  - Limpeza de logs antigos
  - Backup automático
  - Verificação de serviços
  - Geração de relatórios

#### `backup_ragpp.sh`

- **Função**: Backup completo dos dados importantes
- **Inclui**:
  - Banco de dados RAG
  - Dados de memória
  - Configurações do sistema
  - Logs do sistema
  - Metadados do backup

#### `restore_ragpp.sh`

- **Função**: Restauração de backups
- **Recursos**:
  - Restauração seletiva de componentes
  - Verificação de integridade
  - Backup automático antes da restauração

### Scripts de Monitoramento

#### `monitor_ragpp.sh`

- **Função**: Monitoramento contínuo da saúde do sistema
- **Monitora**:
  - Status do serviço
  - Conectividade HTTP
  - Estatísticas de cache
  - Recursos do sistema
  - Performance do servidor

#### `check_integrity.sh`

- **Função**: Verificação completa da integridade do sistema
- **Verifica**:
  - Arquivos essenciais
  - Permissões
  - Serviço systemd
  - Conectividade
  - Banco de dados
  - Espaço em disco
  - Backups
  - Cron jobs

### Scripts de Instalação

#### `install_ragpp_cron.sh`

- **Função**: Instalação automática de cron jobs
- **Configura**:
  - Manutenção semanal
  - Backup diário
  - Monitoramento contínuo
  - Limpeza de logs
  - Verificação de integridade
  - Reinício preventivo
  - Atualização de dependências

#### `update_dependencies.sh`

- **Função**: Atualização automática de dependências Python
- **Executa**:
  - Backup de requirements
  - Atualização do pip
  - Atualização de pacotes
  - Verificação de segurança
  - Reinício de serviços

## 📊 Cron Jobs Automáticos

O sistema configura automaticamente os seguintes cron jobs:

```bash
# Manutenção semanal (domingo 2:00 AM)
0 2 * * 0 /home/agourakis82/workspace/pcs-meta-repo/maintenance_ragpp.sh

# Backup diário (3:00 AM)
0 3 * * * /home/agourakis82/workspace/pcs-meta-repo/backup_ragpp.sh

# Monitoramento contínuo (a cada 30 minutos)
*/30 * * * * /home/agourakis82/workspace/pcs-meta-repo/monitor_ragpp.sh

# Limpeza de logs (segunda 4:00 AM)
0 4 * * 1 /usr/bin/journalctl --vacuum-time=30d

# Verificação de integridade (6:00 AM)
0 6 * * * /home/agourakis82/workspace/pcs-meta-repo/check_integrity.sh

# Reinício preventivo (mês 1, 5:00 AM)
0 5 1 * * /usr/bin/systemctl restart ragpp

# Atualização de dependências (mês 15, 2:00 AM)
0 2 15 * * /home/agourakis82/workspace/pcs-meta-repo/update_dependencies.sh
```

## 🚀 Instalação Rápida

### 1. Configuração Inicial

```bash
# Instalar serviço de produção
sudo ./setup_production.sh

# Instalar cron jobs
./install_ragpp_cron.sh
```

### 2. Verificação

```bash
# Verificar integridade
./check_integrity.sh

# Verificar cron jobs
crontab -l
```

### 3. Primeiro Backup

```bash
# Executar backup manual
./backup_ragpp.sh
```

## 📁 Estrutura de Arquivos

```
pcs-meta-repo/
├── backup_ragpp.sh              # Script de backup
├── restore_ragpp.sh             # Script de restauração
├── maintenance_ragpp.sh         # Manutenção automática
├── monitor_ragpp.sh             # Monitoramento contínuo
├── check_integrity.sh           # Verificação de integridade
├── update_dependencies.sh       # Atualização de dependências
├── install_ragpp_cron.sh        # Instalação de cron jobs
├── uninstall_ragpp_cron.sh      # Desinstalação de cron jobs (gerado)
├── ragpp_cron.conf              # Configuração de cron jobs
├── ragpp.service                # Serviço systemd
├── setup_production.sh          # Configuração de produção
├── reports/                     # Relatórios gerados
│   ├── maintenance_*.md
│   ├── integrity_check_*.md
│   └── dependency_update_*.md
└── backups/                     # Backups automáticos
    └── ragpp_backup_*.tar.gz
```

## 📊 Relatórios Gerados

### Relatório de Manutenção

- **Localização**: `reports/maintenance_YYYYMMDD.md`
- **Conteúdo**: Status do sistema, ações executadas, próximos passos

### Relatório de Integridade

- **Localização**: `reports/integrity_check_YYYYMMDD_HHMMSS.md`
- **Conteúdo**: Verificação de todos os componentes, problemas detectados

### Relatório de Dependências

- **Localização**: `reports/dependency_update_YYYYMMDD.md`
- **Conteúdo**: Pacotes atualizados, versões, status da atualização

## 🔧 Comandos Úteis

### Monitoramento

```bash
# Ver status do serviço
systemctl status ragpp

# Ver logs em tempo real
journalctl -u ragpp -f

# Ver cron jobs ativos
crontab -l

# Ver próximos agendamentos
systemctl list-timers
```

### Manutenção Manual

```bash
# Executar manutenção completa
./maintenance_ragpp.sh

# Fazer backup manual
./backup_ragpp.sh

# Verificar integridade
./check_integrity.sh

# Atualizar dependências
./update_dependencies.sh
```

### Gestão de Backups

```bash
# Listar backups disponíveis
ls -la backups/

# Restaurar backup específico
./restore_ragpp.sh backups/ragpp_backup_20231201_143000.tar.gz

# Verificar tamanho dos backups
du -sh backups/*
```

## ⚙️ Configuração Avançada

### Personalização de Cron Jobs

Edite `ragpp_cron.conf` para ajustar agendamentos:

```bash
# Exemplo: manutenção diária em vez de semanal
0 2 * * * /home/agourakis82/workspace/pcs-meta-repo/maintenance_ragpp.sh
```

### Configuração de Logs

- **Manutenção**: `/var/log/ragpp_maintenance.log`
- **Systemd**: `journalctl -u ragpp`
- **Aplicação**: Configurado no `ragpp_server_optimized.py`

### Limites de Recursos

Configure em `ragpp.service`:

```ini
MemoryLimit=2G
CPUQuota=200%
RestartSec=5
```

## 🔍 Troubleshooting

### Serviço Não Inicia

```bash
# Ver logs detalhados
journalctl -u ragpp -n 50

# Ver status do serviço
systemctl status ragpp

# Reiniciar manualmente
sudo systemctl restart ragpp
```

### Cron Jobs Não Executam

```bash
# Ver logs do cron
grep CRON /var/log/syslog

# Testar execução manual
./maintenance_ragpp.sh

# Verificar permissões
ls -la maintenance_ragpp.sh
```

### Backup Falha

```bash
# Verificar espaço em disco
df -h /

# Verificar permissões
ls -la ragpp/

# Executar backup com debug
bash -x backup_ragpp.sh
```

## 🔒 Segurança

### Recursos de Segurança Implementados

- ✅ Usuário dedicado para o serviço
- ✅ Permissões restritivas nos arquivos
- ✅ Logs de auditoria
- ✅ Verificação de integridade
- ✅ Backups automáticos
- ✅ Atualizações de segurança

### Recomendações Adicionais

- Configure firewall para portas específicas
- Use HTTPS em produção
- Implemente rotação de logs
- Configure monitoramento de segurança
- Faça backups off-site

## 📞 Suporte

Para problemas ou dúvidas:

1. **Verifique os logs**: `journalctl -u ragpp -f`
2. **Execute verificação**: `./check_integrity.sh`
3. **Consulte relatórios**: `ls reports/`
4. **Verifique documentação**: Leia este README

## 🤝 Contribuição

Para contribuir com melhorias:

1. Teste as mudanças localmente
2. Execute `./check_integrity.sh`
3. Verifique se não quebra cron jobs
4. Atualize este README se necessário

---

*Sistema de Automação RAG++ v1.0 - Produção Ready*

