#!/bin/bash
# Script de deployment para Google Cloud Run

set -e

echo "🚀 Iniciando deployment da Darwin Platform no Google Cloud Run"

# Verificar se gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI não encontrado. Instale primeiro:"
    echo "curl https://sdk.cloud.google.com | bash"
    exit 1
fi

# Verificar se está logado
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Não está autenticado no Google Cloud. Execute:"
    echo "gcloud auth login"
    exit 1
fi

# Configurações
PROJECT_ID=$(gcloud config get-value project)
REGION=${REGION:-us-central1}
SERVICE_NAME=${SERVICE_NAME:-darwin-platform}
MEMORY=${MEMORY:-2Gi}
CPU=${CPU:-2}
MAX_INSTANCES=${MAX_INSTANCES:-10}
IMAGE_NAME="us-central1-docker.pkg.dev/$PROJECT_ID/darwin-repo/darwin-platform"

echo "📋 Configurações:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo "  Memory: $MEMORY"
echo "  CPU: $CPU"

# Verificar se as APIs estão habilitadas
echo "🔧 Verificando APIs necessárias..."
REQUIRED_APIS=(
    "aiplatform.googleapis.com"
    "run.googleapis.com"
    "secretmanager.googleapis.com"
    "cloudbuild.googleapis.com"
    "artifactregistry.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    if ! gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo "⚠️  Habilitando API: $api"
        gcloud services enable "$api"
    else
        echo "✅ API já habilitada: $api"
    fi
done

# Verificar se service account existe
SA_EMAIL="darwin-platform@$PROJECT_ID.iam.gserviceaccount.com"
if ! gcloud iam service-accounts list --filter="email:$SA_EMAIL" --format="value(email)" | grep -q "$SA_EMAIL"; then
    echo "🔑 Criando service account..."
    gcloud iam service-accounts create darwin-platform \
        --display-name="Darwin Platform Service Account"
    
    echo "🔐 Configurando permissões..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/aiplatform.user"
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/secretmanager.secretAccessor"
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/run.invoker"
else
    echo "✅ Service account já existe: $SA_EMAIL"
    echo "🔐 Verificando permissões..."
    
    # Verificar e adicionar permissões se necessário
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/aiplatform.user" 2>/dev/null || true
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/secretmanager.secretAccessor" 2>/dev/null || true
fi

# Garantir repositório do Artifact Registry
REPO_NAME=${REPO_NAME:-darwin-repo}
REPO_LOCATION=${REPO_LOCATION:-$REGION}
if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REPO_LOCATION" >/dev/null 2>&1; then
    echo "🏗  Criando repositório $REPO_NAME no Artifact Registry..."
    gcloud artifacts repositories create "$REPO_NAME" \
        --repository-format=docker \
        --location="$REPO_LOCATION" \
        --description="Darwin Platform images"
else
    echo "✅ Repositório do Artifact Registry existe: $REPO_NAME ($REPO_LOCATION)"
fi

# IAM essenciais para build/deploy
CLOUDBUILD_SA="${PROJECT_NUMBER:-$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)') }@cloudbuild.gserviceaccount.com"
COMPUTE_DEFAULT_SA="${PROJECT_NUMBER:-$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)') }-compute@developer.gserviceaccount.com"

echo "🔒 Ajustando permissões IAM para build/deploy..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$CLOUDBUILD_SA" \
  --role="roles/artifactregistry.writer" 2>/dev/null || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$CLOUDBUILD_SA" \
  --role="roles/storage.admin" 2>/dev/null || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/artifactregistry.reader" 2>/dev/null || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$COMPUTE_DEFAULT_SA" \
  --role="roles/storage.objectViewer" 2>/dev/null || true

# Verificar/criar secrets básicos
echo "🔐 Verificando secrets..."
if ! gcloud secrets describe api-keys >/dev/null 2>&1; then
    echo "⚠️  Criando secret para API keys..."
    echo "dev-key-1,dev-key-2,dev-key-3" | gcloud secrets create api-keys --data-file=-
else
    echo "✅ Secret api-keys já existe"
fi

# Verificar se existe o secret para a Gemini API
if ! gcloud secrets describe gemini-api-key >/dev/null 2>&1; then
    echo "⚠️  Secret gemini-api-key não encontrado. Criando placeholder..."
    echo "configure-sua-chave-real-depois" | gcloud secrets create gemini-api-key --data-file=-
    echo "⚠️  IMPORTANTE: Configure a chave real do Gemini depois com:"
    echo "gcloud secrets versions add gemini-api-key --data-file=-"
else
    echo "✅ Secret gemini-api-key já existe"
fi

# Deploy
echo "🚀 Fazendo build e push da imagem..."
gcloud builds submit --tag "$IMAGE_NAME" .

echo "🚀 Fazendo deployment..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory "$MEMORY" \
    --cpu "$CPU" \
    --max-instances "$MAX_INSTANCES" \
    --set-env-vars "PROJECT_ID=$PROJECT_ID" \
    --set-env-vars "LOCATION=$REGION" \
    --set-env-vars "CONTEXT_CACHE_ENABLED=true" \
    --set-env-vars "RAG_ENGINE_ENABLED=false" \
    --set-env-vars "VECTOR_SEARCH_ENABLED=false" \
    --set-env-vars "DEBUG=false" \
    --set-secrets "API_KEYS=api-keys:latest" \
    --set-secrets "GEMINI_API_KEY=gemini-api-key:latest" \
    --service-account "$SA_EMAIL" \
    --timeout=900 \
    --quiet

# Obter URL do serviço
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")

echo ""
echo "🎉 Deployment concluído com sucesso!"
echo "📍 URL do serviço: $SERVICE_URL"
echo "📚 Documentação da API: $SERVICE_URL/docs"
echo "❤️  Health check: $SERVICE_URL/health"
echo ""
echo "🧪 Para testar:"
echo "curl $SERVICE_URL/health"
