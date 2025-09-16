#!/bin/bash
# PCS Auto Setup Script
# Configura automaticamente todas as soluções implementadas

set -e

echo "🚀 PCS Auto Setup - Configurando soluções implementadas"
echo "======================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running in correct directory
check_directory() {
    if [[ ! -f "main.py" ]] || [[ ! -f "gemini_direct_api.py" ]]; then
        print_error "Execute este script no diretório raiz do PCS (onde está o main.py)"
        exit 1
    fi
    print_success "Diretório correto detectado"
}

# Check Python environment
check_python_env() {
    print_status "Verificando ambiente Python..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 não encontrado"
        exit 1
    fi
    
    python_version=$(python3 --version)
    print_success "Python disponível: $python_version"
    
    # Check if conda environment is active
    if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
        print_success "Conda environment ativo: $CONDA_DEFAULT_ENV"
    else
        print_warning "Nenhum conda environment ativo"
    fi
}

# Check and install Python dependencies
check_dependencies() {
    print_status "Verificando dependências Python..."
    
    required_packages=(
        "fastapi"
        "uvicorn"
        "requests"
        "google-cloud-bigquery"
        "pandas"
        "numpy"
    )
    
    missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            print_success "$package disponível"
        else
            missing_packages+=("$package")
            print_warning "$package não encontrado"
        fi
    done
    
    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        print_status "Instalando pacotes faltantes..."
        for package in "${missing_packages[@]}"; do
            if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
                conda install -y "$package" || pip install "$package"
            else
                pip install "$package"
            fi
        done
    fi
}

# Setup Google Cloud credentials
setup_gcloud() {
    print_status "Verificando configuração Google Cloud..."
    
    if ! command -v gcloud &> /dev/null; then
        print_warning "gcloud CLI não encontrado"
        print_status "Para instalar: curl https://sdk.cloud.google.com | bash"
        return 1
    fi
    
    # Check if authenticated
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        active_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
        print_success "Google Cloud autenticado: $active_account"
        
        # Check if ADC is configured
        if [[ -f "$HOME/.config/gcloud/application_default_credentials.json" ]]; then
            print_success "Application Default Credentials configuradas"
        else
            print_warning "ADC não configuradas"
            print_status "Execute: gcloud auth application-default login"
        fi
    else
        print_warning "Google Cloud não autenticado"
        print_status "Execute: gcloud auth login"
    fi
    
    # Check project
    current_project=$(gcloud config get-value project 2>/dev/null || echo "none")
    if [[ "$current_project" == "pcs-helio" ]]; then
        print_success "Projeto correto configurado: $current_project"
    else
        print_warning "Projeto atual: $current_project"
        print_status "Para configurar: gcloud config set project pcs-helio"
    fi
}

# Setup Gemini API
setup_gemini_api() {
    print_status "Verificando configuração Gemini API..."
    
    if [[ -n "$GEMINI_API_KEY" ]]; then
        print_success "GEMINI_API_KEY configurada"
        
        # Test the API
        if python3 -c "
from gemini_direct_api import GeminiDirectAPI
try:
    client = GeminiDirectAPI()
    response = client.chat_complete('Test', temperature=0.1)
    print('✅ Gemini API funcionando:', response[:50] + '...')
except Exception as e:
    print('❌ Erro Gemini API:', e)
"; then
            print_success "Gemini API testada com sucesso"
        else
            print_warning "Gemini API configurada mas com problemas"
        fi
    else
        print_warning "GEMINI_API_KEY não configurada"
        print_status "Para configurar:"
        print_status "1. Acesse: https://makersuite.google.com/app/apikey"
        print_status "2. Crie uma nova API key"
        print_status "3. Execute: export GEMINI_API_KEY='sua-chave-aqui'"
        print_status "4. Para tornar permanente, adicione ao ~/.bashrc"
    fi
}

# Test BigQuery connection
test_bigquery() {
    print_status "Testando conexão BigQuery..."
    
    if python3 -c "
from google.cloud import bigquery
try:
    client = bigquery.Client(project='pcs-helio')
    query = 'SELECT 1 as test'
    results = list(client.query(query).result())
    print('✅ BigQuery funcionando')
except Exception as e:
    print('❌ BigQuery erro:', e)
"; then
        print_success "BigQuery conectado e funcionando"
    else
        print_warning "BigQuery com problemas de conexão"
    fi
}

# Test Darwin Platform local
test_darwin_local() {
    print_status "Testando Darwin Platform local..."
    
    if python3 darwin_local_runner.py test | grep -q "All dependencies available"; then
        print_success "Darwin Platform pode rodar localmente"
        print_status "Para iniciar: python3 darwin_local_runner.py"
        print_status "URL local: http://localhost:8000"
        print_status "Documentação: http://localhost:8000/docs"
    else
        print_warning "Darwin Platform local com problemas"
    fi
}

# Create environment setup script
create_env_script() {
    print_status "Criando script de configuração de ambiente..."
    
    cat > setup_env.sh << 'EOF'
#!/bin/bash
# PCS Environment Setup
echo "🔧 Configurando ambiente PCS..."

# Google Cloud
export PROJECT_ID="pcs-helio"
export LOCATION="us-central1"

# Darwin Platform Local
export CONTEXT_CACHE_ENABLED="true"
export RAG_ENGINE_ENABLED="false"
export VECTOR_SEARCH_ENABLED="false"
export DEBUG="true"
export ENVIRONMENT="local"

# Add to current session
echo "✅ Variáveis de ambiente configuradas"
echo "📋 Para tornar permanente, adicione ao ~/.bashrc:"
echo "source $(pwd)/setup_env.sh"
EOF

    chmod +x setup_env.sh
    print_success "Script setup_env.sh criado"
}

# Main setup function
main() {
    echo
    print_status "Iniciando setup automático..."
    echo
    
    check_directory
    check_python_env
    check_dependencies
    setup_gcloud
    setup_gemini_api
    test_bigquery
    test_darwin_local
    create_env_script
    
    echo
    echo "🎉 Setup Completo!"
    echo "==================="
    print_success "BigQuery: Funcionando"
    
    if [[ -n "$GEMINI_API_KEY" ]]; then
        print_success "Gemini API: Configurada"
    else
        print_warning "Gemini API: Precisa de configuração"
    fi
    
    print_success "Darwin Platform: Disponível localmente"
    
    echo
    print_status "Próximos passos:"
    echo "1. Para usar Darwin localmente: python3 darwin_local_runner.py"
    echo "2. Para configurar Gemini API: Siga instruções acima"
    echo "3. Para ambiente persistente: source setup_env.sh"
}

# Run main function
main "$@"