# tests/test_connection.py
"""
Prueba de conexión al MCP Server
"""

import sys
import os
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

@pytest.mark.asyncio
async def test_mcp():
    """Prueba la conexión al MCP Server"""
    print("\n🔍 Probando conexión al MCP Server")
    print("-" * 40)
    
    mcp_url = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
    
    # Corregir URL si es necesario
    if "https://127.0.0.1" in mcp_url:
        mcp_url = mcp_url.replace("https://127.0.0.1", "http://127.0.0.1")
    if "https://localhost" in mcp_url:
        mcp_url = mcp_url.replace("https://localhost", "http://localhost")
    
    print(f"📡 Conectando a: {mcp_url}")
    
    try:
        servers_config = {
            "mi_servidor": {
                "transport": "http",
                "url": mcp_url,
            }
        }
        
        mcp_client = MultiServerMCPClient(servers_config)
        tools = await mcp_client.get_tools()
        
        assert len(tools) >= 3, f"Se esperaban al menos 3 tools, se encontraron {len(tools)}"
        
        print(f"✅ Conectado exitosamente!")
        print(f"📦 Herramientas encontradas: {len(tools)}")
        for tool in tools:
            print(f"   - {tool.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise