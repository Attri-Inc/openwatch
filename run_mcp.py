#!/usr/bin/env python3
"""Entry point for OpenWatch MCP server."""
import os
import sys

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("MCP_TRANSPORT", "stdio")

from src.mcp_server import mcp

mcp.run()
