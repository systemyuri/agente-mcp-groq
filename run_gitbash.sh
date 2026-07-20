#!/bin/bash
# run_gitbash.sh - Versión específica para Git Bash en Windows

# 🔥 Configurar encoding para Git Bash
export PYTHONIOENCODING=utf-8
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

# 🔥 Asegurar que Python usa UTF-8
export PYTHONUTF8=1

echo "🚀 Iniciando Asistente Comercial MCP (Git Bash)..."
echo ""

# ============================================================
# VERIFICAR ENTORNO VIRTUAL
# ============================================================
if [ ! -d ".venv" ]; then
    echo "❌ Entorno virtual no encontrado."
    echo "   Ejecuta: python -m venv .venv"
    echo "   source .venv/Scripts/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activar entorno virtual (ruta de Windows en Git Bash)
source .venv/Scripts/activate

# ============================================================
# CARGAR VARIABLES DE ENTORNO
# ============================================================
echo "📋 Cargando variables de entorno..."

if [ -f ".env" ]; then
    # Cargar variables línea por línea
    while IFS='=' read -r key value; do
        if [[ ! -z "$key" && ! "$key" =~ ^# ]]; then
            # Remover espacios y comillas
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs | sed -e 's/^"//' -e 's/"$//')
            export "$key=$value"
        fi
    done < .env
    echo "✅ Variables cargadas"
else
    echo "❌ Archivo .env no encontrado"
    exit 1
fi

if [ -z "$GROQ_API_KEY" ]; then
    echo "❌ GROQ_API_KEY no configurada"
    exit 1
fi

echo "✅ GROQ_API_KEY configurada"
echo ""

# ============================================================
# VERIFICAR BASE DE DATOS
# ============================================================
echo "📊 Verificando base de datos..."

# Función para verificar BD
verificar_bd() {
    if [ ! -f "data/mcp_laboratorio.db" ]; then
        return 1
    fi
    python -c "import sqlite3; conn=sqlite3.connect('data/mcp_laboratorio.db'); cursor=conn.cursor(); cursor.execute('SELECT COUNT(*) FROM ventas'); count=cursor.fetchone()[0]; exit(0 if count>0 else 1)" 2>/dev/null
    return $?
}

if verificar_bd; then
    echo "✅ Base de datos lista"
else
    echo "⚠️ Preparando base de datos..."
    python load_data.py
    if [ $? -ne 0 ]; then
        echo "❌ Error al preparar base de datos"
        exit 1
    fi
    echo "✅ Base de datos preparada"
fi

echo ""

# ============================================================
# INICIAR SERVIDORES
# ============================================================
echo "📡 Iniciando MCP Server..."
python mcp_server.py &
MCP_PID=$!
echo "   PID: $MCP_PID"

echo "⏳ Esperando servidor..."
sleep 5

echo ""
echo "🔍 Verificando conexión..."

python -c "import requests; requests.get('http://127.0.0.1:8000/mcp', timeout=5)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ MCP Server no responde"
    kill $MCP_PID 2>/dev/null
    exit 1
fi

echo "✅ MCP Server funcionando"
echo ""

# ============================================================
# INICIAR STREAMLIT
# ============================================================
echo "🌐 Iniciando Streamlit..."
echo "   Presiona Ctrl+C para detener"
echo ""

# Función de limpieza
cleanup() {
    echo ""
    echo "🔌 Deteniendo MCP Server..."
    kill $MCP_PID 2>/dev/null
    echo "✅ MCP Server detenido"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Ejecutar Streamlit
streamlit run app_streamlit.py

# Limpieza al cerrar
echo ""
echo "🔌 Deteniendo MCP Server..."
kill $MCP_PID 2>/dev/null
echo "✅ MCP Server detenido"

read -p "Presiona Enter para salir..."