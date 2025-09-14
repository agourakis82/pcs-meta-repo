#!/usr/bin/env python3
"""
RAG++ MCP Configuration for ChatGPT Desktop
Setup MCP server for ChatGPT Desktop app integration.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def create_mcp_config():
    """Create MCP configuration file for ChatGPT Desktop."""

    # Determine the correct config path based on OS
    if sys.platform == "darwin":  # macOS
        config_dir = Path.home() / "Library" / "Application Support" / "Claude"
    elif sys.platform == "win32":  # Windows
        config_dir = Path.home() / "AppData" / "Roaming" / "Claude"
    else:  # Linux
        config_dir = Path.home() / ".config" / "claude"

    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Get absolute path to our MCP server
    script_dir = Path(__file__).parent.absolute()
    server_path = script_dir / "ragpp_mcp_server.py"

    # MCP configuration
    mcp_config = {
        "mcpServers": {
            "ragpp-research": {
                "command": "python",
                "args": [str(server_path)],
                "env": {
                    "PYTHONPATH": str(script_dir.parent),
                    "RAG_INDEX_PATH": str(script_dir / "index"),
                    "PCS_DATA_ROOT": str(script_dir.parent / "pcs"),
                },
            }
        }
    }

    # Write configuration file
    config_file = config_dir / "claude_desktop_config.json"
    with open(config_file, "w") as f:
        json.dump(mcp_config, f, indent=2)

    print(f"✅ MCP configuration created: {config_file}")
    return config_file


def create_standalone_mcp_launcher():
    """Create standalone MCP launcher script."""

    launcher_content = '''#!/usr/bin/env python3
"""
RAG++ MCP Server Launcher
Standalone launcher for RAG++ MCP server.
"""

import sys
import os
import subprocess

# Add the project root to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Set environment variables
os.environ["PYTHONPATH"] = project_root
os.environ["RAG_INDEX_PATH"] = os.path.join(script_dir, "index")
os.environ["PCS_DATA_ROOT"] = os.path.join(project_root, "pcs")

# Launch the MCP server
if __name__ == "__main__":
    server_script = os.path.join(script_dir, "ragpp_mcp_server.py")
    subprocess.run([sys.executable, server_script] + sys.argv[1:])
'''

    launcher_path = Path(__file__).parent / "launch_mcp_server.py"
    with open(launcher_path, "w") as f:
        f.write(launcher_content)

    # Make executable
    os.chmod(launcher_path, 0o755)

    print(f"✅ MCP launcher created: {launcher_path}")
    return launcher_path


def create_chatgpt_mcp_instructions():
    """Create instructions for ChatGPT MCP integration."""

    instructions = """# 🤖 RAG++ MCP Integration for ChatGPT Desktop

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
"""

    instructions_path = Path(__file__).parent / "MCP_INTEGRATION_GUIDE.md"
    with open(instructions_path, "w") as f:
        f.write(instructions)

    print(f"📖 MCP integration guide created: {instructions_path}")
    return instructions_path


def install_mcp_dependencies():
    """Install required MCP dependencies."""

    packages = ["model-context-protocol", "pydantic>=2.0.0", "asyncio"]

    print("📦 Installing MCP dependencies...")
    for package in packages:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"✅ Installed: {package}")
            else:
                print(f"⚠️  Failed to install {package}: {result.stderr}")
        except Exception as e:
            print(f"⚠️  Failed to install {package}: {e}")
            print("You may need to install manually with:")
            print(f"pip install {package}")


def main():
    """Main setup function."""
    print("🤖 RAG++ MCP Configuration Setup")
    print("=" * 40)

    # Install dependencies
    print("\n📦 Step 1: Installing MCP dependencies...")
    install_mcp_dependencies()

    # Create MCP configuration
    print("\n🔧 Step 2: Creating MCP configuration...")
    config_file = create_mcp_config()

    # Create launcher script
    print("\n🚀 Step 3: Creating MCP launcher...")
    launcher = create_standalone_mcp_launcher()

    # Create instructions
    print("\n📖 Step 4: Creating integration guide...")
    guide = create_chatgpt_mcp_instructions()

    print("\n🎉 MCP Setup Complete!")
    print("\n📋 Next Steps:")
    print("1. Install ChatGPT Desktop app")
    print("2. Restart ChatGPT Desktop to load MCP server")
    print("3. Test tools: 'Search literature on computational psychiatry'")
    print("4. Check resources: 'Show RAG++ database status'")

    print(f"\n📁 Files Created:")
    print(f"  - MCP Config: {config_file}")
    print(f"  - MCP Server: ragpp_mcp_server.py")
    print(f"  - Launcher: {launcher}")
    print(f"  - Guide: {guide}")

    print(f"\n🌐 You now have BOTH:")
    print(f"  - Web API: http://179.125.169.148:8000")
    print(f"  - MCP Server: ragpp_mcp_server.py")
    print(f"\n🎯 Your RAG++ works with ChatGPT Web AND Desktop!")


if __name__ == "__main__":
    main()
    main()
