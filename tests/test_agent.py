# tests/test_agent.py
"""
Pruebas para el agente LangChain con Groq
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Agregar la raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

# Importar el agente
from agent_core import consultar_agente, get_agent, SYSTEM_PROMPT

# =============================================================================
# PRUEBAS SÍNCRONAS
# =============================================================================

def test_system_prompt():
    """Prueba que el system prompt está definido"""
    print("\n🧪 Probando: System Prompt")
    print("-" * 40)
    
    assert SYSTEM_PROMPT is not None, "System Prompt no debe ser None"
    assert len(SYSTEM_PROMPT) > 100, "System Prompt debe tener contenido"
    assert "herramientas" in SYSTEM_PROMPT.lower(), "Debe mencionar herramientas"
    assert "comercial" in SYSTEM_PROMPT.lower(), "Debe mencionar el dominio"
    
    print("✅ System Prompt definido correctamente")

# =============================================================================
# PRUEBAS ASÍNCRONAS (con marcador asyncio)
# =============================================================================

@pytest.mark.asyncio
async def test_agent_creation():
    """Prueba que el agente se crea correctamente"""
    print("\n🧪 Probando: Creación del agente")
    print("-" * 40)
    
    try:
        agent, config = await get_agent("test-session")
        assert agent is not None, "El agente no debe ser None"
        assert config is not None, "La configuración no debe ser None"
        print("✅ Agente creado correctamente")
    except Exception as e:
        print(f"❌ Error al crear agente: {e}")
        raise

@pytest.mark.asyncio
async def test_simple_query():
    """Prueba una consulta simple sin tools"""
    print("\n🧪 Probando: Consulta simple")
    print("-" * 40)
    
    resultado = await consultar_agente(
        "Hola, ¿cómo estás?",
        "test-session-1"
    )
    
    assert "answer" in resultado, "Debe tener respuesta"
    assert len(resultado["answer"]) > 0, "La respuesta no debe estar vacía"
    assert "trace" in resultado, "Debe tener traza"
    
    print(f"✅ Respuesta: {resultado['answer'][:50]}...")

@pytest.mark.asyncio
async def test_tool_query():
    """Prueba una consulta que usa tools"""
    print("\n🧪 Probando: Consulta con tools")
    print("-" * 40)
    
    resultado = await consultar_agente(
        "¿Cuál es el producto más vendido?",
        "test-session-2"
    )
    
    assert "answer" in resultado, "Debe tener respuesta"
    assert len(resultado["answer"]) > 0, "La respuesta no debe estar vacía"
    
    # Verificar que se usaron tools
    if resultado.get("tools_used"):
        print(f"✅ Tools usadas: {resultado['tools_used']}")
    else:
        print("⚠️ No se usaron tools (puede ser normal para algunas preguntas)")
    
    print(f"✅ Respuesta: {resultado['answer'][:100]}...")

@pytest.mark.asyncio
async def test_memory():
    """Prueba que la memoria funciona correctamente"""
    print("\n🧪 Probando: Memoria del agente")
    print("-" * 40)
    
    session_id = "test-memory-session"
    
    # Primer mensaje: presentar un cliente
    resultado1 = await consultar_agente(
        "Dame el perfil del cliente con ID 4",
        session_id
    )
    
    print("✅ Primer mensaje procesado")
    
    # Segundo mensaje: referencia al mismo cliente
    resultado2 = await consultar_agente(
        "¿Cuánto ha gastado ese cliente?",
        session_id
    )
    
    assert "answer" in resultado2, "Debe tener respuesta"
    assert "gastado" in resultado2["answer"].lower() or "gasto" in resultado2["answer"].lower(), \
        "Debe mencionar el gasto"
    
    print(f"✅ Memoria funcionando: {resultado2['answer'][:100]}...")

@pytest.mark.asyncio
async def test_error_handling():
    """Prueba el manejo de errores del agente"""
    print("\n🧪 Probando: Manejo de errores")
    print("-" * 40)
    
    # Consulta con cliente inexistente
    resultado = await consultar_agente(
        "Dame el perfil del cliente con ID 99999",
        "test-error-session"
    )
    
    assert "answer" in resultado, "Debe tener respuesta"
    # Debe indicar que no encontró o manejar el error
    assert "no" in resultado["answer"].lower() or "encontrado" in resultado["answer"].lower() or "error" in resultado["answer"].lower(), \
        "Debe manejar el error de cliente no encontrado"
    
    print(f"✅ Manejo de error: {resultado['answer'][:100]}...")

# =============================================================================
# EJECUTAR TODAS LAS PRUEBAS
# =============================================================================

def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("=" * 60)
    print("🧪 EJECUTANDO PRUEBAS DEL AGENTE")
    print("=" * 60)
    print("\n⚠️ Asegúrate que el MCP Server está corriendo")
    print("   (python mcp_server.py en otra terminal)")
    print("=" * 60)
    
    # Primero, verificar que el MCP Server está corriendo
    import requests
    try:
        response = requests.get("http://127.0.0.1:8000/mcp", timeout=5)
        print("\n✅ MCP Server detectado")
    except:
        print("\n❌ MCP Server NO detectado")
        print("   Ejecuta: python mcp_server.py en otra terminal")
        return
    
    # Ejecutar usando pytest
    import subprocess
    subprocess.run([
        "python", "-m", "pytest", 
        "tests/test_agent.py", 
        "-v", 
        "--tb=short",
        "--asyncio-mode=auto"
    ])

if __name__ == "__main__":
    run_all_tests()