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

# Activar entorno virtual
source .venv/bin/activate

# Cargar variables de entorno
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️ Archivo .env no encontrado. Copia .env.example y configúralo."
fi

# Iniciar MCP Server en segundo plano
echo "📡 Iniciando MCP Server..."
python mcp_server.py &
MCP_PID=$!
echo "   PID: $MCP_PID"

# Esperar a que el servidor esté listo
echo "⏳ Esperando servidor..."
sleep 3

# Iniciar Streamlit
echo "🌐 Iniciando Streamlit..."
streamlit run app_streamlit.py

# Detener MCP Server al cerrar Streamlit
kill $MCP_PID