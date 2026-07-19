#!/bin/bash

echo "🚀 Iniciando Asistente Comercial MCP..."
echo ""

# Verificar entorno virtual
if [ ! -d ".venv" ]; then
    echo "❌ Entorno virtual no encontrado. Ejecuta primero:"
    echo "   python -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi