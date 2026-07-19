# agent_core.py
"""
Núcleo del agente: conexión MCP, Groq, memoria y ejecución
"""
import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Cargado .env desde: {env_path.absolute()}")

from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver

def get_corrected_mcp_url():
    """Obtiene y corrige la URL del MCP Server"""
    url = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
    
    # 🔥 CORRECCIÓN: Forzar http:// en lugar de https:// para localhost
    if "https://127.0.0.1" in url:
        print("⚠️ Corrigiendo https:// a http:// para localhost")
        url = url.replace("https://127.0.0.1", "http://127.0.0.1")
    
    if "https://localhost" in url:
        print("⚠️ Corrigiendo https:// a http:// para localhost")
        url = url.replace("https://localhost", "http://localhost")
    
    return url



# =============================================================================
# CONFIGURACIÓN - CON PRIORIDAD
# =============================================================================

# 🔥 Función para obtener variables con prioridad
def get_env_var(key, default=None):
    """Obtiene variable de entorno con prioridad"""
    # 1. Primero de os.environ (que ya tiene .env cargado)
    value = os.environ.get(key)
    if value and value != "tu_api_key_aqui" and "tu-servidor-mcp-remoto" not in value:
        return value
    
    # 2. Si no, usar default
    return default

# 🔥 Configurar variables
GROQ_API_KEY = get_env_var("GROQ_API_KEY")
if not GROQ_API_KEY or GROQ_API_KEY == "tu_api_key_aqui":
    raise ValueError("""
    ❌ GROQ_API_KEY no está configurada correctamente.
    
    Asegúrate de tener un archivo .env en la raíz con:
    GROQ_API_KEY=gsk_tu_api_key_real
    GROQ_MODEL=llama-3.3-70b-versatile
    MCP_SERVER_URL=http://127.0.0.1:8000/mcp
    """)

GROQ_MODEL = get_env_var("GROQ_MODEL", "llama-3.3-70b-versatile")

# 🔥 Forzar URL local si es placeholder
#MCP_SERVER_URL = get_env_var("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
MCP_SERVER_URL = get_corrected_mcp_url()

if "tu-servidor-mcp-remoto" in MCP_SERVER_URL:
    print("⚠️ URL placeholder detectada. Usando localhost...")
    MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"
    # Actualizar variable de entorno
    os.environ["MCP_SERVER_URL"] = MCP_SERVER_URL

print(f"📡 Conectando a MCP Server: {MCP_SERVER_URL}")
print(f"🤖 Usando modelo: {GROQ_MODEL}")

memory = InMemorySaver()

# =============================================================================
# SYSTEM PROMPT
# =============================================================================
SYSTEM_PROMPT = """
Eres un Asistente de Análisis Comercial especializado en un e-commerce de productos alimenticios.

🏢 CONTEXTO DE LA EMPRESA:
- Venta de productos alimenticios en Argentina (Buenos Aires, Patagonia, Centro, Cuyo, NEA, NOA)
- Categorías: Lácteos, Carnicería, Panadería, Frutas y Verduras, Congelados, Bebidas, Galletitas y Snacks, Conservas
- Métodos de pago: Efectivo, Tarjeta de Crédito, Tarjeta de Débito, Mercado Pago, Transferencia

🎯 OBJETIVO:
- Ayudar al equipo comercial y de atención al cliente con información precisa
- Responder preguntas sobre clientes, ventas, productos, regiones y métodos de pago
- Proporcionar análisis basados en datos reales

🔧 HERRAMIENTAS DISPONIBLES:

1. buscar_clientes(texto_busqueda: str, limite: int = 10)
   📌 Busca clientes por nombre, apellido o región
   💡 Ejemplos: "Busca clientes que se llamen Juan", "Clientes de Patagonia"

2. perfil_consumo_cliente(cliente_id: int)
   📌 Perfil completo de consumo de un cliente específico
   💡 Ejemplos: "Dame el perfil del cliente 4"

3. clientes_alto_valor(gasto_minimo: float = 500, limite: int = 10)
   📌 Identifica clientes con alto gasto
   💡 Ejemplos: "Top 10 clientes", "Clientes que gastaron más de $1000"

4. top_productos_vendidos(limite: int = 10, ordenar_por: str = "cantidad")
   📌 Productos más vendidos por cantidad o ingresos
   💡 Ejemplos: "¿Cuál es el producto más vendido?"

5. analisis_categoria(categoria: str = None)
   📌 Análisis de ventas por categoría de producto
   💡 Ejemplos: "¿Qué categoría vende más?"

6. ventas_por_region(region: str = None)
   📌 Resumen de ventas por región geográfica
   💡 Ejemplos: "¿Cuánto vendimos en Buenos Aires?"

7. preferencia_metodo_pago(region: str = None)
   📌 Preferencias de métodos de pago
   💡 Ejemplos: "¿Qué método de pago es más usado?"

8. calcular_nivel_cliente(gasto_total: float, total_ordenes: int)
   📌 Clasifica clientes según gasto y frecuencia

📋 POLÍTICAS DE ORQUESTACIÓN:
1. 🔍 SIEMPRE busca evidencia antes de responder. NUNCA inventes datos.
2. 🎯 Si no encuentras un cliente, sugiere búsquedas alternativas.
3. 📊 Cuando cites datos, menciona la fuente.
4. ⚠️ Si una región o categoría no tiene datos, indícalo claramente.
5. 🔒 TODAS las tools son de solo lectura.
6. 🔄 Si no conoces el ID de un cliente, usa buscar_clientes primero.

📝 FORMATO DE RESPUESTA:
1. Hallazgos principales
2. Evidencia con datos específicos
3. Recomendación o siguiente paso

🌐 RESPONDE SIEMPRE EN ESPAÑOL.
"""

# =============================================================================
# CLIENTE MCP COMPARTIDO (SINGLETON)
# =============================================================================
_mcp_client = None
_agent_cache = {}

async def get_mcp_client():
    """Obtiene un cliente MCP compartido (singleton)"""
    global _mcp_client
    
    if _mcp_client is None:
        try:
            print(f"🔌 Conectando a MCP Server en: {MCP_SERVER_URL}")
            servers_config = {
                "mi_servidor": {
                    "transport": "http",
                    "url": MCP_SERVER_URL,
                }
            }
            _mcp_client = MultiServerMCPClient(servers_config)
            
            # Probar conexión
            tools = await _mcp_client.get_tools()
            print(f"✅ Conectado a MCP Server. Tools disponibles: {len(tools)}")
            
        except Exception as e:
            print(f"❌ Error al conectar con MCP Server: {e}")
            raise
    
    return _mcp_client

async def get_agent(session_id: str = None):
    """Obtiene un agente cacheado por sesión"""
    
    cache_key = session_id or "default"
    
    if cache_key not in _agent_cache:
        try:
            # Obtener cliente MCP
            mcp_client = await get_mcp_client()
            
            # Obtener tools
            tools = await mcp_client.get_tools()
            
            if not tools:
                raise ValueError("No se encontraron herramientas en el MCP Server")
            
            # Crear modelo Groq
            llm = ChatGroq(
                model=GROQ_MODEL,
                temperature=0,
                api_key=GROQ_API_KEY,
            )
            
            # Crear agente
            agent = create_agent(
                model=llm,
                tools=tools,
                system_prompt=SYSTEM_PROMPT,
                checkpointer=memory,
            )
            
            _agent_cache[cache_key] = agent
            print(f"✅ Agente creado para sesión: {cache_key}")
            
        except Exception as e:
            print(f"❌ Error al crear agente: {e}")
            raise
    
    config = {
        "configurable": {
            "thread_id": cache_key,
        }
    }
    
    return _agent_cache[cache_key], config

# =============================================================================
# FUNCIÓN DE CONSULTA MEJORADA
# =============================================================================
async def consultar_agente(pregunta: str, session_id: str = None):
    """
    Consulta al agente con manejo de errores robusto.
    """
    try:
        # Obtener agente
        agent, config = await get_agent(session_id)
        
        # Ejecutar consulta
        resultado = await agent.ainvoke(
            {"messages": [{"role": "user", "content": pregunta}]},
            config=config
        )
        
        # Procesar resultado
        messages = resultado.get("messages", [])
        
        tools_usadas = []
        trace = []
        
        for mensaje in messages:
            # Tool calls
            if hasattr(mensaje, 'tool_calls') and mensaje.tool_calls:
                for llamada in mensaje.tool_calls:
                    tool_name = llamada.get('name', 'N/A')
                    args = llamada.get('args', {})
                    tools_usadas.append(tool_name)
                    trace.append({
                        "type": "tool_call",
                        "tool": tool_name,
                        "args": args
                    })
            
            # Tool results
            elif hasattr(mensaje, 'content') and hasattr(mensaje, 'type') and mensaje.type == 'tool':
                contenido = mensaje.content
                try:
                    if isinstance(contenido, str):
                        try:
                            datos = json.loads(contenido)
                            trace.append({
                                "type": "tool_result",
                                "result": datos
                            })
                        except:
                            trace.append({
                                "type": "tool_result",
                                "result": contenido
                            })
                    else:
                        trace.append({
                            "type": "tool_result",
                            "result": contenido
                        })
                except Exception as e:
                    trace.append({
                        "type": "tool_error",
                        "error": str(e)
                    })
        
        # Extraer respuesta final
        respuesta_final = ""
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                respuesta_final = last_message.content
            else:
                respuesta_final = str(last_message)
        
        return {
            "answer": respuesta_final,
            "tools_used": list(set(tools_usadas)),
            "trace": trace,
            "session_id": session_id or "default-session"
        }
    
    except Exception as e:
        error_msg = str(e)
        return {
            "answer": f"❌ Error al procesar la consulta: {error_msg}",
            "tools_used": [],
            "trace": [{"type": "error", "error": error_msg}],
            "session_id": session_id or "default-session"
        }