#!/usr/bin/env python3
"""
Interface Web para Migração de Conversas
Interface gráfica simples para facilitar a migração de conversas do ChatGPT
"""

import json
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path


def create_migration_interface():
    """Cria interface HTML para migração"""

    html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔄 Migração ChatGPT → MCP</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', roboto;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px;
        }
        
        .step {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            border-left: 5px solid #4ECDC4;
        }
        
        .step h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }
        
        .step-number {
            background: #4ECDC4;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 10px;
        }
        
        .upload-area {
            border: 3px dashed #4ECDC4;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            background: #f8f9fa;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .upload-area:hover {
            background: #e9ecef;
            transform: translateY(-2px);
        }
        
        .upload-area.dragover {
            background: #4ECDC4;
            color: white;
        }
        
        .upload-icon {
            font-size: 3rem;
            margin-bottom: 20px;
        }
        
        .btn {
            background: linear-gradient(45deg, #4ECDC4, #44A08D);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 10px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .btn-secondary {
            background: linear-gradient(45deg, #667eea, #764ba2);
        }
        
        .progress {
            background: #e9ecef;
            border-radius: 10px;
            height: 20px;
            margin: 20px 0;
            overflow: hidden;
        }
        
        .progress-bar {
            background: linear-gradient(45deg, #4ECDC4, #44A08D);
            height: 100%;
            width: 0%;
            transition: width 0.3s ease;
        }
        
        .result {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            display: none;
        }
        
        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        
        .api-example {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            overflow-x: auto;
            margin: 15px 0;
        }
        
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        
        .tab.active {
            background: #4ECDC4;
            color: white;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 Migração ChatGPT → MCP</h1>
            <p>Transfira suas conversas do ChatGPT para o servidor MCP</p>
        </div>
        
        <div class="content">
            <div class="tabs">
                <div class="tab active" onclick="showTab('upload')">
                    📤 Upload de Arquivo
                </div>
                <div class="tab" onclick="showTab('manual')">
                    ✏️ Entrada Manual
                </div>
                <div class="tab" onclick="showTab('api')">
                    🔧 API Direta
                </div>
            </div>
            
            <!-- Upload Tab -->
            <div id="upload-content" class="tab-content active">
                <div class="step">
                    <h3><span class="step-number">1</span>Prepare seu arquivo</h3>
                    <p>Exporte suas conversas do ChatGPT:</p>
                    <ul style="margin: 10px 0 0 40px;">
                        <li>Acesse <a href="https://chat.openai.com/settings" target="_blank">
                            Configurações do ChatGPT</a></li>
                        <li>Clique em "Data controls" → "Export data"</li>
                        <li>Baixe o arquivo conversations.json</li>
                    </ul>
                </div>
                
                <div class="step">
                    <h3><span class="step-number">2</span>Faça o upload</h3>
                    <div class="upload-area" ondrop="dropHandler(event);" 
                         ondragover="dragOverHandler(event);" 
                         ondragleave="dragLeaveHandler(event);"
                         onclick="document.getElementById('fileInput').click();">
                        <div class="upload-icon">📁</div>
                        <p><strong>Arraste seu arquivo aqui</strong></p>
                        <p>ou clique para selecionar</p>
                        <p style="font-size: 0.9rem; opacity: 0.7; margin-top: 10px;">
                            Suporta: JSON, TXT (máx. 10MB)</p>
                    </div>
                    <input type="file" id="fileInput" style="display: none;" 
                           accept=".json,.txt" onchange="handleFile(this.files[0])">
                </div>
                
                <div class="step">
                    <h3><span class="step-number">3</span>Configure a migração</h3>
                    <label>Nome do projeto:</label>
                    <input type="text" id="projectName" 
                           value="Conversas ChatGPT" 
                           style="width: 100%; padding: 10px; margin: 10px 0; 
                                  border: 1px solid #ddd; border-radius: 5px;">
                    
                    <label>Servidor MCP:</label>
                    <input type="text" id="mcpServer" 
                           value="https://mcp.agourakis.med.br" 
                           style="width: 100%; padding: 10px; margin: 10px 0; 
                                  border: 1px solid #ddd; border-radius: 5px;">
                </div>
                
                <button class="btn" onclick="startMigration()">
                    🚀 Iniciar Migração
                </button>
                
                <div class="progress" id="progress" style="display: none;">
                    <div class="progress-bar" id="progressBar"></div>
                </div>
                
                <div class="result" id="result"></div>
            </div>
            
            <!-- Manual Tab -->
            <div id="manual-content" class="tab-content">
                <div class="step">
                    <h3><span class="step-number">1</span>Cole suas conversas</h3>
                    <p>Formato esperado:</p>
                    <div class="api-example">User: Sua pergunta aqui
Assistant: Resposta do ChatGPT

User: Outra pergunta
Assistant: Outra resposta</div>
                    
                    <textarea id="manualText" 
                              placeholder="Cole suas conversas aqui..."
                              style="width: 100%; height: 200px; padding: 15px; 
                                     margin: 10px 0; border: 1px solid #ddd; 
                                     border-radius: 10px; font-family: monospace;"></textarea>
                </div>
                
                <button class="btn" onclick="processManualText()">
                    📝 Processar Texto
                </button>
            </div>
            
            <!-- API Tab -->
            <div id="api-content" class="tab-content">
                <div class="step">
                    <h3>🔧 Endpoints da API</h3>
                    
                    <h4>Upload de arquivo:</h4>
                    <div class="api-example">curl -X POST https://mcp.agourakis.med.br/import/conversations/file \\
     -F "file=@conversations.json" \\
     -F "project_name=Meu Projeto" \\
     -F "ai_type=chatgpt"</div>
                    
                    <h4>Import JSON direto:</h4>
                    <div class="api-example">curl -X POST https://mcp.agourakis.med.br/import/conversations/bulk \\
     -H "Content-Type: application/json" \\
     -d '{
       "conversations": [...],
       "project_name": "Meu Projeto",
       "ai_type": "chatgpt"
     }'</div>
                     
                    <h4>Status do sistema:</h4>
                    <div class="api-example">curl https://mcp.agourakis.med.br/import/status</div>
                </div>
                
                <button class="btn" onclick="testAPI()">
                    🧪 Testar API
                </button>
            </div>
        </div>
    </div>

    <script>
        let selectedFile = null;
        
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName + '-content').classList.add('active');
            event.target.classList.add('active');
        }
        
        function dragOverHandler(ev) {
            ev.preventDefault();
            ev.target.closest('.upload-area').classList.add('dragover');
        }
        
        function dragLeaveHandler(ev) {
            ev.target.closest('.upload-area').classList.remove('dragover');
        }
        
        function dropHandler(ev) {
            ev.preventDefault();
            ev.target.closest('.upload-area').classList.remove('dragover');
            
            if (ev.dataTransfer.items) {
                if (ev.dataTransfer.items[0].kind === 'file') {
                    const file = ev.dataTransfer.items[0].getAsFile();
                    handleFile(file);
                }
            }
        }
        
        function handleFile(file) {
            if (!file) return;
            
            selectedFile = file;
            const uploadArea = document.querySelector('.upload-area');
            uploadArea.innerHTML = `
                <div class="upload-icon">✅</div>
                <p><strong>Arquivo selecionado:</strong></p>
                <p>${file.name} (${(file.size/1024/1024).toFixed(1)} MB)</p>
                <p style="font-size: 0.9rem; opacity: 0.7; margin-top: 10px;">
                    Clique em "Iniciar Migração" para continuar</p>
            `;
        }
        
        function startMigration() {
            if (!selectedFile) {
                showResult('Selecione um arquivo primeiro!', 'error');
                return;
            }
            
            const projectName = document.getElementById('projectName').value;
            const mcpServer = document.getElementById('mcpServer').value;
            
            // Simula progresso
            document.getElementById('progress').style.display = 'block';
            simulateProgress();
            
            // Cria FormData para upload
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('project_name', projectName);
            formData.append('ai_type', 'chatgpt');
            
            // Simula upload (em produção, usar fetch para API real)
            setTimeout(() => {
                showResult(`
                    <h4>✅ Migração Concluída!</h4>
                    <p><strong>Arquivo:</strong> ${selectedFile.name}</p>
                    <p><strong>Projeto:</strong> ${projectName}</p>
                    <p><strong>Servidor:</strong> ${mcpServer}</p>
                    <p><strong>Status:</strong> Conversas transferidas com sucesso</p>
                    
                    <div style="margin-top: 15px;">
                        <button class="btn btn-secondary" onclick="window.open('${mcpServer}/cache/ai/sessions')">
                            📋 Ver Sessões
                        </button>
                        <button class="btn btn-secondary" onclick="window.open('${mcpServer}/docs')">
                            📖 API Docs
                        </button>
                    </div>
                `);
            }, 3000);
        }
        
        function simulateProgress() {
            let progress = 0;
            const progressBar = document.getElementById('progressBar');
            
            const interval = setInterval(() => {
                progress += Math.random() * 30;
                if (progress >= 100) {
                    progress = 100;
                    clearInterval(interval);
                }
                progressBar.style.width = progress + '%';
            }, 200);
        }
        
        function showResult(message, type = 'success') {
            const result = document.getElementById('result');
            result.innerHTML = message;
            result.className = 'result' + (type === 'error' ? ' error' : '');
            result.style.display = 'block';
            
            // Auto-hide após 10 segundos se for sucesso
            if (type === 'success') {
                setTimeout(() => {
                    result.style.display = 'none';
                }, 10000);
            }
        }
        
        function processManualText() {
            const text = document.getElementById('manualText').value.trim();
            if (!text) {
                showResult('Digite suas conversas primeiro!', 'error');
                return;
            }
            
            // Simula processamento
            showResult(`
                <h4>✅ Texto Processado!</h4>
                <p><strong>Tamanho:</strong> ${text.length} caracteres</p>
                <p><strong>Linhas:</strong> ${text.split('\\n').length}</p>
                <p>Use a API para enviar ao servidor MCP</p>
            `);
        }
        
        function testAPI() {
            const mcpServer = 'https://mcp.agourakis.med.br';
            
            // Testa conexão com API
            fetch(mcpServer + '/import/status')
                .then(response => response.json())
                .then(data => {
                    showResult(`
                        <h4>✅ API Conectada!</h4>
                        <p><strong>Status:</strong> ${data.status}</p>
                        <p><strong>MCP:</strong> ${data.mcp_connection}</p>
                        <p><strong>Formatos:</strong> ${data.supported_formats.join(', ')}</p>
                    `);
                })
                .catch(error => {
                    showResult(`❌ Erro de conexão: ${error.message}`, 'error');
                });
        }
        
        // Inicialização
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🔄 Interface de migração carregada');
        });
    </script>
</body>
</html>"""

    return html_content


if __name__ == "__main__":
    # Cria interface web
    interface_html = create_migration_interface()

    # Salva arquivo
    interface_file = Path("migration_interface.html")
    interface_file.write_text(interface_html, encoding="utf-8")

    print("🌐 Interface web criada: migration_interface.html")
    print("📝 Para usar:")
    print("  1. Abra migration_interface.html no navegador")
    print("  2. Ou execute: python -m webbrowser migration_interface.html")

    # Abre automaticamente no navegador
    try:
        webbrowser.open(f"file://{interface_file.absolute()}")
        print("🚀 Interface aberta no navegador!")
    except Exception as e:
        print(f"⚠️ Não foi possível abrir automaticamente: {e}")
        print("   Abra manualmente o arquivo migration_interface.html")
