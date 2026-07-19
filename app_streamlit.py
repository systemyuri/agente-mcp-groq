# app_streamlit.py
"""
Aplicación Streamlit para el Asistente Comercial MCP
"""

import streamlit as st
import uuid
import asyncio
from agent_core import consultar_agente

# Configuración de la página
st.set_page_config(
    page_title="Asistente Comercial MCP",
    page_icon="🛒",
    layout="wide"
)

# Título y descripción
st.title("🛒 Asistente Comercial MCP")
st.markdown("""
    <div style='background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
        <p style='margin: 0;'>
            <strong>🤖 Agente de Análisis Comercial</strong> - Especializado en e-commerce de productos alimenticios.
            Pregunta sobre clientes, ventas, productos, regiones y métodos de pago.
        </p>
    </div>
""", unsafe_allow_html=True)

# Inicializar el estado de la sesión
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session-{uuid.uuid4().hex[:8]}"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "processing" not in st.session_state:
    st.session_state.processing = False

# =============================================================================
# SIDEBAR - Información y controles
# =============================================================================
with st.sidebar:
    st.header("🔧 Controles")
    
    # Mostrar ID de sesión
    st.info(f"**ID de Sesión:** `{st.session_state.session_id}`")
    
    # Botón para reiniciar conversación
    if st.button("🔄 Reiniciar Conversación", use_container_width=True):
        st.session_state.session_id = f"session-{uuid.uuid4().hex[:8]}"
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # Información del sistema
    st.header("ℹ️ Información")
    st.markdown("""
    **Tools disponibles:**
    - 🔍 `buscar_clientes`
    - 📊 `perfil_consumo_cliente`
    - 💎 `clientes_alto_valor`
    - 🏆 `top_productos_vendidos`
    - 📈 `analisis_categoria`
    - 🌎 `ventas_por_region`
    - 💳 `preferencia_metodo_pago`
    - 🏅 `calcular_nivel_cliente`
    """)
    
    st.divider()
    
    # Preguntas sugeridas
    st.header("💡 Preguntas sugeridas")
    preguntas = [
        "¿Cuál es el producto más vendido?",
        "Busca clientes de Patagonia",
        "Dame el perfil del cliente con ID 4",
        "¿Qué categoría genera más ingresos?",
        "¿Cuánto vendimos en Buenos Aires?",
        "¿Qué método de pago es el más usado?",
        "Identifica los 5 clientes que más gastaron",
    ]
    
    for pregunta in preguntas:
        if st.button(pregunta, use_container_width=True, key=f"sug_{pregunta[:20]}"):
            if not st.session_state.processing:
                st.session_state.processing = True
                # Agregar pregunta al chat
                st.session_state.messages.append({"role": "user", "content": pregunta})
                # Procesar respuesta
                try:
                    with st.spinner("Procesando..."):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        resultado = loop.run_until_complete(
                            consultar_agente(pregunta, st.session_state.session_id)
                        )
                        loop.close()
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": resultado["answer"],
                        "tools_used": resultado.get("tools_used", []),
                        "trace": resultado.get("trace", [])
                    })
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    st.session_state.processing = False
                st.rerun()

# =============================================================================
# CHAT PRINCIPAL
# =============================================================================
# Mostrar mensajes existentes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Si es un mensaje del asistente, mostrar evidencia
        if message["role"] == "assistant" and "tools_used" in message:
            with st.expander("🔍 Ver evidencia y herramientas usadas"):
                if message.get("tools_used"):
                    st.write("**📋 Herramientas usadas:**")
                    for tool in message["tools_used"]:
                        st.write(f"   - `{tool}`")
                
                if message.get("trace"):
                    st.write("**📊 Traza de orquestación:**")
                    st.json(message["trace"])

# =============================================================================
# INPUT DEL USUARIO
# =============================================================================
# Campo de entrada para el usuario
if prompt := st.chat_input("Escribe tu consulta sobre clientes, ventas, productos..."):
    # Verificar si ya hay un procesamiento en curso
    if st.session_state.processing:
        st.warning("⏳ Espera a que termine la consulta actual...")
    else:
        st.session_state.processing = True
        
        # Agregar pregunta del usuario al historial
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Mostrar el mensaje del usuario inmediatamente
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Procesar respuesta
        with st.chat_message("assistant"):
            try:
                with st.spinner("🤔 Pensando..."):
                    # Ejecutar la consulta asíncrona
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    resultado = loop.run_until_complete(
                        consultar_agente(prompt, st.session_state.session_id)
                    )
                    loop.close()
                
                # Mostrar la respuesta
                st.markdown(resultado["answer"])
                
                # Mostrar evidencia en expander
                with st.expander("🔍 Ver evidencia y herramientas usadas"):
                    if resultado.get("tools_used"):
                        st.write("**📋 Herramientas usadas:**")
                        for tool in resultado["tools_used"]:
                            st.write(f"   - `{tool}`")
                    
                    if resultado.get("trace"):
                        st.write("**📊 Traza de orquestación:**")
                        st.json(resultado["trace"])
                
                # Guardar en el historial
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": resultado["answer"],
                    "tools_used": resultado.get("tools_used", []),
                    "trace": resultado.get("trace", [])
                })
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "tools_used": [],
                    "trace": [{"type": "error", "error": str(e)}]
                })
            finally:
                st.session_state.processing = False
            
            # Forzar actualización
            st.rerun()

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption("💡 **Consejo:** Puedes hacer preguntas sobre clientes, ventas, productos, regiones y métodos de pago. El agente usará las herramientas MCP para obtener información verificable.")