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

REM ============================================================
REM CARGAR VARIABLES DE ENTORNO DESDE .env
REM ============================================================
echo 📋 Cargando variables de entorno desde .env...

REM Leer el archivo .env y establecer variables
for /f "usebackq delims=" %%a in (.env) do (
    set "%%a"
)

REM Verificar que se cargó la API Key
if "%GROQ_API_KEY%"=="" (
    echo ❌ ERROR: No se encontró GROQ_API_KEY en .env
    echo    Asegúrate de que el archivo .env existe y contiene GROQ_API_KEY
    pause
    exit /b 1
) else (
    echo ✅ GROQ_API_KEY cargada correctamente
)

REM 🔥 Verificar y cargar base de datos automáticamente
echo 📊 Verificando base de datos...
python check_and_load.py
if errorlevel 1 (
    echo ❌ Error al preparar la base de datos
    pause
    exit /b 1
)

echo.

REM Iniciar MCP Server
echo 📡 Iniciando MCP Server LOCAL...
start "MCP Server" cmd /c "python mcp_server.py"

REM Esperar a que el servidor esté listo
echo ⏳ Esperando servidor (3 segundos)...
timeout /t 3 /nobreak > nul

REM ============================================================
REM VERIFICAR CONEXIÓN
REM ============================================================
echo.
echo 🔍 Verificando conexión al MCP Server...

python -c "import requests; requests.get('http://127.0.0.1:8000/mcp', timeout=5)" 2>nul
if errorlevel 1 (
    echo ❌ ERROR: El MCP Server no responde
    echo.
    echo Posibles causas:
    echo 1. El puerto 8000 está ocupado
    echo 2. Error en mcp_server.py
    echo 3. Base de datos no encontrada
    echo.
    pause
    exit /b 1
)

echo ✅ MCP Server funcionando correctamente


REM Iniciar Streamlit
echo 🌐 Iniciando Streamlit LOCAL...
echo    Presiona Ctrl+C para detener
echo.

streamlit run app_streamlit.py

REM Al cerrar Streamlit, preguntar si cerrar MCP Server
echo.
echo 🔌 ¿Deseas cerrar el MCP Server? (S/N)
set /p respuesta=
if /i "%respuesta%"=="S" (
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq MCP Server"
    echo ✅ MCP Server cerrado
)

pause