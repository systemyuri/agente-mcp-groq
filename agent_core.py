# agent_core.py
"""
Núcleo del agente: conexión MCP, Groq, memoria y ejecución
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
# Variables de entorno
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY no está configurada en las variables de entorno")

GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")

# Memoria (InMemorySaver)
memory = InMemorySaver()

# =============================================================================
# SYSTEM PROMPT MEJORADO
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

1. buscar_clientes(texto_busqueda, limite=10)
   📌 Busca clientes por nombre, apellido o región
   💡 Ejemplos: "Busca clientes que se llamen Juan", "Clientes de Patagonia"
   📊 Retorna: ID, Nombre, Apellido, Región, Email

2. perfil_consumo_cliente(cliente_id)
   📌 Perfil completo de consumo de un cliente específico
   💡 Ejemplos: "Dame el perfil del cliente 4", "¿Cuánto ha gastado el cliente ID 4?"
   📊 Retorna: Total órdenes, Total gastado, Ticket promedio, Fechas de compra

3. clientes_alto_valor(gasto_minimo=500, limite=10)
   📌 Identifica clientes con alto gasto
   💡 Ejemplos: "Top 10 clientes", "Clientes que gastaron más de $1000"
   📊 Retorna: Cliente, Total gastado, Total órdenes, Ticket promedio

4. top_productos_vendidos(limite=10, ordenar_por="cantidad")
   📌 Productos más vendidos por cantidad o ingresos
   💡 Ejemplos: "¿Cuál es el producto más vendido?", "Top 5 por ingresos"
   📊 Retorna: Producto, Categoría, Total vendido, Ingresos totales

5. analisis_categoria(categoria=None)
   📌 Análisis de ventas por categoría de producto
   💡 Ejemplos: "¿Qué categoría vende más?", "Ventas de Lácteos"
   📊 Retorna: Categoría, Ventas, Unidades, Ingresos, % del total

6. ventas_por_region(region=None)
   📌 Resumen de ventas por región geográfica
   💡 Ejemplos: "¿Cuánto vendimos en Buenos Aires?", "Ranking de regiones"
   📊 Retorna: Región, Total ventas, Total órdenes, Promedio

7. preferencia_metodo_pago(region=None)
   📌 Preferencias de métodos de pago
   💡 Ejemplos: "¿Qué método de pago es más usado?", "Preferencia en Buenos Aires"
   📊 Retorna: Método, Usos, Monto total, % del total

8. calcular_nivel_cliente(gasto_total, total_ordenes)
   📌 Clasifica clientes según gasto y frecuencia
   💡 Ejemplos: "¿Qué nivel tiene este cliente?", "¿Es VIP?"
   📊 Retorna: Nivel (VIP, Premium, Regular) y recomendación

📋 POLÍTICAS DE ORQUESTACIÓN:

1. 🔍 SIEMPRE busca evidencia antes de responder. NUNCA inventes datos.
2. 🎯 Si no encuentras un cliente, sugiere búsquedas alternativas.
3. 📊 Cuando cites datos, menciona la fuente (ej: "Según los datos de ventas...").
4. ⚠️ Si una región o categoría no tiene datos, indícalo claramente.
5. 🔒 TODAS las tools son de solo lectura. NUNCA afirmes que modificaste datos.
6. 🔄 Si no conoces el ID de un cliente, usa buscar_clientes primero.
7. 📈 Para preguntas de consumo general, usa perfil_consumo_cliente.
8. 🏆 Para comparativas o rankings, usa las tools correspondientes.

🔒 REGLAS DE SEGURIDAD:
1. No ejecutes acciones de escritura (crear, modificar, eliminar).
2. Si no hay información suficiente, explica la limitación y pide el dato faltante.
3. No compartas datos sensibles como emails completos innecesariamente.

📝 FORMATO DE RESPUESTA:
1. Hallazgos principales (resumen de lo que encontraste)
2. Evidencia con datos específicos (mostrar números concretos)
3. Recomendación o siguiente paso (acción sugerida)

🌐 RESPONDE SIEMPRE EN ESPAÑOL.
"""

# =============================================================================
# FUNCIÓN PARA OBTENER EL AGENTE
# =============================================================================
async def get_agent(session_id: str = None):
    """
    Crea o recupera un agente con su propia configuración de memoria.
    
    Args:
        session_id: Identificador de la sesión (opcional)
    
    Returns:
        Tuple (agent, config)
    """
    # Configurar el cliente MCP
    servers_config = {
        "mi_servidor": {
            "transport": "http",
            "url": MCP_SERVER_URL,
        }
    }
    
    # Crear cliente MCP y descubrir tools
    mcp_client = MultiServerMCPClient(servers_config)
    tools = await mcp_client.get_tools()
    
    # Crear el modelo LLM con Groq
    llm = ChatGroq(
        model=GROQ_MODEL,
        temperature=0,
        api_key=GROQ_API_KEY,
    )
    
    # Crear el agente
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=memory,  # Memoria de corto plazo
    )
    
    # Configuración de la sesión
    config = {
        "configurable": {
            "thread_id": session_id or "default-session",
        }
    }
    
    return agent, config

# =============================================================================
# FUNCIÓN PARA CONSULTAR AL AGENTE
# =============================================================================
async def consultar_agente(pregunta: str, session_id: str = None):
    """
    Consulta al agente y retorna la respuesta con trazabilidad.
    
    Args:
        pregunta: Pregunta del usuario
        session_id: Identificador de la sesión
    
    Returns:
        Dict con respuesta, trace y tools usadas
    """
    try:
        # Obtener el agente con su configuración
        agent, config = await get_agent(session_id)
        
        # Ejecutar el agente
        resultado = await agent.ainvoke(
            {"messages": [{"role": "user", "content": pregunta}]},
            config=config
        )
        
        # Extraer mensajes
        messages = resultado.get("messages", [])
        
        # Extraer herramientas usadas y trace
        tools_usadas = []
        trace = []
        
        for mensaje in messages:
            # Si es un mensaje del LLM con tool_calls
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
            
            # Si es un mensaje de tool (resultado)
            elif hasattr(mensaje, 'content') and hasattr(mensaje, 'type') and mensaje.type == 'tool':
                contenido = mensaje.content
                try:
                    # Intentar parsear como JSON
                    if isinstance(contenido, str):
                        datos = json.loads(contenido)
                    else:
                        datos = contenido
                    
                    trace.append({
                        "type": "tool_result",
                        "result": datos
                    })
                except:
                    trace.append({
                        "type": "tool_result",
                        "result": contenido
                    })
        
        # Extraer la respuesta final
        respuesta_final = ""
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                respuesta_final = last_message.content
            else:
                respuesta_final = str(last_message)
        
        return {
            "answer": respuesta_final,
            "tools_used": list(set(tools_usadas)),  # Eliminar duplicados
            "trace": trace,
            "session_id": session_id or "default-session"
        }
    
    except Exception as e:
        return {
            "answer": f"❌ Error al procesar la consulta: {str(e)}",
            "tools_used": [],
            "trace": [{"type": "error", "error": str(e)}],
            "session_id": session_id or "default-session"
        }