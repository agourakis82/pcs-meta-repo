# PCS AI Research Suite - Installation Guide

## 🚀 **Sistema de Build e Atalhos Criado!**

### ✅ **Compilação e Instalação Completa**

O sistema PCS AI Research Suite agora possui um sistema completo de build, instalação e atalhos.

---

## 📋 **Comandos Disponíveis**

### 🔧 **Build e Instalação**
```bash
# Compilar e instalar
make gui-build
make gui-install

# Ou diretamente
./build_install.sh

# Desinstalar
make gui-uninstall
./build_install.sh uninstall
```

### 🚀 **Executar Interface Gráfica**

#### **Método 1: Launcher Principal (Recomendado)**
```bash
./pcs               # Menu interativo
./pcs clean         # Versão limpa (sem emojis)
./pcs demo          # Versão demo
./pcs full          # Versão completa
```

#### **Método 2: Make Targets**
```bash
make gui            # Menu interativo
make gui-run        # Versão limpa
make gui-run-demo   # Versão demo  
make gui-run-full   # Versão completa
```

#### **Método 3: Comandos Diretos (após configurar PATH)**
```bash
pcs-ai-suite        # Versão limpa
pcs-ai-suite-demo   # Versão demo
pcs-ai-suite-full   # Versão completa
```

#### **Método 4: Python Direto**
```bash
python3 scripts/pcs_clean_gui.py   # Versão limpa
python3 scripts/pcs_demo_gui.py    # Versão demo
python3 scripts/pcs_gui.py         # Versão completa
```

---

## 🎯 **Configuração do PATH**

Para usar os comandos `pcs-ai-suite*` de qualquer lugar:

```bash
# Configurar automaticamente
./setup_path.sh

# Ou adicionar manualmente ao ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
```

---

## 🖥️ **Integração com Desktop**

### **Arquivos Criados:**
- **Executáveis:** `~/.local/bin/pcs-ai-suite*`
- **Atalhos Desktop:** `~/.local/share/applications/pcs-ai-suite*.desktop`
- **Ícone:** `~/.local/share/icons/pcs-ai-suite.svg`

### **Como Usar:**
1. **Menu de Aplicações:** Procure por "PCS AI Research Suite"
2. **Duplo-click:** Nos arquivos `.desktop`
3. **Terminal:** Use os comandos listados acima

---

## 📁 **Estrutura de Arquivos**

```
pcs-meta-repo/
├── pcs                      # Launcher principal (RECOMENDADO)
├── build_install.sh         # Script de build e instalação
├── setup_path.sh           # Configuração de PATH
├── launch_gui.sh           # Launcher original
├── test_installation.sh    # Teste da instalação
├── scripts/
│   ├── pcs_clean_gui.py    # Interface limpa (sem emojis)
│   ├── pcs_demo_gui.py     # Interface demo
│   └── pcs_gui.py          # Interface completa
└── Makefile                # Targets make atualizados
```

---

## 🎨 **Versões da Interface**

### **1. Clean (Recomendada)**
- ✅ Sem emojis ou caracteres especiais
- ✅ Compatível com qualquer terminal
- ✅ Interface profissional
- ✅ Todas as funcionalidades

### **2. Demo**  
- ✅ Interface simplificada
- ✅ Ideal para testes rápidos
- ✅ Menor uso de recursos

### **3. Full**
- ✅ Interface completa com emojis
- ⚠️ Pode ter problemas de encoding em alguns sistemas

---

## 🧪 **Testar Instalação**

```bash
# Verificar se tudo foi instalado corretamente
./test_installation.sh

# Testar launcher principal
./pcs --help
```

---

## 🔄 **Comandos Úteis**

### **Verificar Status**
```bash
which pcs-ai-suite          # Verificar se comando está disponível
ls ~/.local/bin/pcs-ai-*    # Listar executáveis instalados
ls ~/.local/share/applications/pcs-ai-* # Listar atalhos desktop
```

### **Resolver Problemas**
```bash
# Reconfigurar PATH
source ~/.bashrc

# Reinstalar
make gui-uninstall
make gui-install

# Verificar dependências
python3 -c "import tkinter; print('Tkinter OK')"
```

---

## 🎯 **Início Rápido**

**Para começar a usar AGORA:**

```bash
cd /path/to/pcs-meta-repo
./pcs clean
```

**Ou com make:**

```bash
make gui
```

---

## ✨ **Funcionalidades da Interface**

- 🧠 **AI Search & Analysis** - Busca inteligente com IA
- 📊 **Research Strategy Generation** - Geração de estratégias
- 🔍 **Literature Gap Analysis** - Análise de lacunas
- 📝 **Manuscript Outline Creation** - Criação de outlines
- 💾 **MCP Memory Management** - Gerenciamento de memórias
- ⚙️ **System Status Monitoring** - Monitoramento do sistema

---

**🎉 Sistema completamente instalado e pronto para uso!**
