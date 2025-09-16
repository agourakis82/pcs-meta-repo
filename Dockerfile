FROM python:3.11-slim

WORKDIR /app

# Copia o arquivo de dependências
COPY requirements-darwin.txt ./requirements.txt

# Define variáveis de ambiente para otimizar o Python
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala as dependências do Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY services/ ./services/
COPY api/ ./api/
COPY main.py ./
COPY gemini_direct_api.py ./

# Cria um diretório para armazenamento em memória (se necessário)
RUN mkdir -p /tmp/darwin-memory

# Cria um usuário não-root para segurança
RUN useradd -m -u 1001 darwin

# Muda a propriedade dos diretórios para o novo usuário
RUN chown -R darwin:darwin /app /tmp/darwin-memory

# Muda para o usuário não-root
USER darwin

# O Cloud Run injeta a variável PORT. Usamos 8080 como padrão para testes locais.
ENV PORT=${PORT:-8080}

# Expõe a porta que o container vai escutar
EXPOSE 8080

# Comando para iniciar a aplicação
CMD exec uvicorn main:app --host 0.0.0.0 --port 8080