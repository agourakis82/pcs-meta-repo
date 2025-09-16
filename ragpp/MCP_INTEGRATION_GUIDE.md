# 🤖 RAG++ MCP Integration for ChatGPT Desktop

## 📋 Overview

Your RAG++ system is now compatible with the Model Context Protocol (MCP), allowing direct integration with ChatGPT Desktop app and other MCP-compatible clients.

## 🚀 ChatGPT Desktop Integration

### 1. Install ChatGPT Desktop App
- Download from: https://openai.com/chatgpt/desktop/
- Install and set up your account

### 2. Configure MCP Server

The configuration has been automatically created at:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%/Claude/claude_desktop_config.json` 
- **Linux:** `~/.config/claude/claude_desktop_config.json`

### 3. Restart ChatGPT Desktop

After configuration, restart ChatGPT Desktop to load the MCP server.

## 🛠️ Available MCP Tools

Your RAG++ system provides these tools via MCP:

### `search_literature`
Search scientific literature using hybrid RAG++ system.
```json
{
  "query": "machine learning psychiatry",
  "max_results": 10,
  "search_type": "hybrid"
}
```

### `store_research_finding`
Store new research findings in the knowledge base.
```json
{
  "title": "New Finding in Digital Phenotyping",
  "content": "Description of the finding...",
  "source": "Journal Name 2025",
  "metadata": {"authors": "Smith et al.", "year": 2025}
}
```

### `get_recent_findings`
Retrieve recent research findings.
```json
{
  "limit": 20,
  "category": "computational_psychiatry"
}
```

### `collect_new_research`
Collect new research papers from PubMed.
```json
{
  "topics": ["digital phenotyping", "computational psychiatry"],
  "years": [2024, 2025],
  "max_papers": 50
}
```

### `synthesize_knowledge`
Synthesize knowledge across multiple papers.
```json
{
  "topic": "machine learning in psychiatry",
  "focus_areas": ["prediction models", "biomarkers"]
}
```

## 📊 Available MCP Resources

### `ragpp://database/status`
Current status and statistics of the RAG++ knowledge base.

### `ragpp://database/indexed_papers`
List of all indexed research papers.

### `ragpp://config/system`
System configuration and capabilities.

### `ragpp://findings/recent`
Latest research findings in the knowledge base.

## 🧪 Testing MCP Integration

### In ChatGPT Desktop:

1. **Search Literature:**
   "Use the search_literature tool to find recent papers on computational psychiatry"

2. **Get System Status:**
   "Check the RAG++ database status using the available resources"

3. **Store New Finding:**
   "Store this research finding: [your finding description]"

4. **Synthesize Knowledge:**
   "Synthesize current knowledge on digital phenotyping using the available tools"

## 🔧 Manual Testing

### Command Line Testing:
```bash
# Test MCP server directly
cd /home/agourakis82/workspace/pcs-meta-repo/ragpp
python launch_mcp_server.py

# Test with MCP client
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | python ragpp_mcp_server.py
```

### Standalone Usage:
```bash
# Launch MCP server for external clients
./launch_mcp_server.py

# Server will communicate via stdio using MCP protocol
```

## 🌐 Web + MCP Hybrid Access

You now have **both** web API and MCP access:

### Web API (Remote Access):
- **URL:** `http://179.125.169.148:8000`
- **Token:** `Bearer wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo`
- **Use Cases:** ChatGPT Web Custom Actions, external applications

### MCP Protocol (Desktop Integration):
- **Server:** `ragpp_mcp_server.py`
- **Config:** Auto-configured for ChatGPT Desktop
- **Use Cases:** ChatGPT Desktop app, Claude Desktop, other MCP clients

## 🎯 Benefits of MCP Integration

1. **Native Integration:** Direct tool access in ChatGPT Desktop
2. **Real-time Updates:** Dynamic resource discovery
3. **Structured Communication:** Type-safe tool schemas
4. **Resource Access:** Direct access to knowledge base resources
5. **Bidirectional:** Can both read from and write to your knowledge base

## 🔍 Troubleshooting

### MCP Server Not Loading:
1. Check config file path and syntax
2. Verify Python environment has required packages
3. Check server logs: `python ragpp_mcp_server.py --debug`

### Tools Not Available:
1. Restart ChatGPT Desktop after config changes
2. Verify MCP server is running: `ps aux | grep ragpp_mcp_server`
3. Check for import errors in the server script

### Search Not Working:
1. Ensure RAG++ index exists: `ls ragpp/index/`
2. Verify environment variables are set
3. Test RAG++ system independently

## 🎉 Success!

Your RAG++ system now supports:
- ✅ **Web API** (http://179.125.169.148:8000) for remote access
- ✅ **MCP Protocol** for ChatGPT Desktop integration
- ✅ **168 indexed papers** accessible via both interfaces
- ✅ **Hybrid search** across literature and memory
- ✅ **Research collection** and synthesis capabilities

**You can now use your RAG++ system directly within ChatGPT Desktop app!** 🚀
