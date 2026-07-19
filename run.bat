@echo off
echo 🚀 Iniciando Asistente Comercial MCP...
echo.

REM Verificar entorno virtual
if not exist ".venv" (
    echo ❌ Entorno virtual no encontrado. Ejecuta primero:
    echo    python -m venv .venv
    echo    .venv\Scripts\activate
    echo    pip install -r requirements.txt
    exit /b 1
)

REM Activar entorno virtual
call .venv\Scripts\activate.bat

REM Cargar variables de entorno
if exist ".env" (
    for /f "tokens=*" %%a in ('type .env') do set %%a
) else (
    echo ⚠️ Archivo .env no encontrado. Copia .env.example y configúralo.
)

REM Iniciar MCP Server en una nueva ventana
echo 📡 Iniciando MCP Server...
start "MCP Server" cmd /c python mcp_server.py

REM Esperar a que el servidor esté listo
echo ⏳ Esperando servidor...
timeout /t 3 /nobreak > nul

REM Iniciar Streamlit
echo 🌐 Iniciando Streamlit...
streamlit run app_streamlit.py