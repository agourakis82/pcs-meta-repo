#!/usr/bin/env python3
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
