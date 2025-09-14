FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

# Copy application
COPY ragpp/ ./ragpp/
COPY pcs/ ./pcs/

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "ragpp/ragpp_web_server.py"]
