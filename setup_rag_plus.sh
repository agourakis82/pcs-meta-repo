#!/bin/bash
# RAG++ Enhanced Research Agent - Setup Script
# =============================================

set -e  # Exit on any error

echo "🚀 RAG++ Enhanced Research Agent - Setup"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
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

# Check if we're in the right directory
if [[ ! -f "rag_plus_agent.py" ]]; then
    print_error "Please run this script from the pcs-meta-repo directory"
    exit 1
fi

print_status "Starting RAG++ system setup..."

# 1. Check Python version
print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.8"

if python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"; then
    print_success "Python version: $python_version (✓)"
else
    print_error "Python 3.8+ required. Current: $python_version"
    exit 1
fi

# 2. Check if Google Cloud SDK is installed
print_status "Checking Google Cloud SDK..."
if command -v gcloud &> /dev/null; then
    gcloud_version=$(gcloud version | grep "Google Cloud SDK" | cut -d' ' -f4)
    print_success "Google Cloud SDK: $gcloud_version (✓)"
else
    print_warning "Google Cloud SDK not found"
    echo "Please install from: https://cloud.google.com/sdk/docs/install"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 3. Check GCP Project ID
print_status "Checking GCP configuration..."
if [[ -z "$GCP_PROJECT_ID" ]]; then
    print_warning "GCP_PROJECT_ID environment variable not set"
    echo "Please set your GCP project ID:"
    read -p "Project ID: " project_id
    export GCP_PROJECT_ID="$project_id"
    
    # Add to .bashrc for persistence
    if ! grep -q "export GCP_PROJECT_ID" ~/.bashrc; then
        echo "export GCP_PROJECT_ID=\"$project_id\"" >> ~/.bashrc
        print_success "Added GCP_PROJECT_ID to ~/.bashrc"
    fi
else
    print_success "GCP_PROJECT_ID: $GCP_PROJECT_ID (✓)"
fi

# 4. Install Python dependencies
print_status "Installing Python dependencies..."
if [[ -f "requirements-rag-plus.txt" ]]; then
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements-rag-plus.txt
    print_success "Dependencies installed"
else
    print_error "requirements-rag-plus.txt not found"
    exit 1
fi

# 5. Create local configuration
print_status "Creating local configuration..."
if [[ ! -f "rag_plus_config_local.yaml" ]]; then
    cp rag_plus_config.yaml rag_plus_config_local.yaml
    
    # Replace project ID in config
    if [[ ! -z "$GCP_PROJECT_ID" ]]; then
        sed -i "s/your-gcp-project-id/$GCP_PROJECT_ID/g" rag_plus_config_local.yaml
        print_success "Configuration created with your project ID"
    else
        print_warning "Configuration created - please edit rag_plus_config_local.yaml"
    fi
else
    print_success "Local configuration already exists"
fi

# 6. Test GCP authentication
print_status "Testing GCP authentication..."
if command -v gcloud &> /dev/null; then
    if gcloud auth application-default print-access-token &> /dev/null; then
        print_success "GCP authentication working (✓)"
    else
        print_warning "GCP authentication not configured"
        echo "Run: gcloud auth application-default login"
    fi
fi

# 7. Check required APIs
print_status "Checking required GCP APIs..."
if command -v gcloud &> /dev/null && [[ ! -z "$GCP_PROJECT_ID" ]]; then
    required_apis=("aiplatform.googleapis.com" "bigquery.googleapis.com")
    
    for api in "${required_apis[@]}"; do
        if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
            print_success "API enabled: $api (✓)"
        else
            print_warning "API not enabled: $api"
            read -p "Enable $api? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                gcloud services enable $api
                print_success "API enabled: $api"
            fi
        fi
    done
fi

# 8. Create directories for logs and cache
print_status "Creating system directories..."
mkdir -p logs cache data
print_success "Directories created"

# 9. Test basic functionality
print_status "Testing basic functionality..."
python3 -c "
try:
    from rag_plus_agent import RAGConfig
    print('✅ RAG agent import successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
except Exception as e:
    print(f'⚠️  Warning: {e}')
"

# 10. Setup complete
echo
echo "🎉 Setup Complete!"
echo "=================="
echo
echo "Next steps:"
echo "1. Ensure GCP authentication: gcloud auth application-default login"
echo "2. Verify your project ID in rag_plus_config_local.yaml"
echo "3. Run demo: python3 rag_plus_main.py --demo"
echo "4. Run interactive: python3 rag_plus_main.py --interactive"
echo
echo "For more information, see README-RAG-PLUS.md"
echo

# Optional: Run demo
read -p "Run demo now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting demo..."
    python3 rag_plus_main.py --demo --config rag_plus_config_local.yaml
fi

print_success "Setup script completed!"