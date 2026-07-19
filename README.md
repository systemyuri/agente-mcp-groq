# 🛒 Asistente Comercial MCP

Sistema de agente de IA para análisis comercial de un e-commerce de productos alimenticios.

## 📋 Problema que resuelve

El asistente ayuda a equipos comerciales y de atención al cliente a obtener información rápida y verificable sobre:

- **Clientes**: Búsqueda, perfil de consumo, identificación de alto valor
- **Productos**: Productos más vendidos, análisis por categoría
- **Ventas**: Análisis por región, métodos de pago
- **Análisis**: Clasificación de clientes (VIP, Premium, Regular)

## 🏗️ Arquitectura
```text
Usuario → Streamlit → Agente LangChain + Groq → MCP Server → SQLite  
↓  
Memoria (InMemorySaver)
```




## 🔧 Herramientas MCP

| Tool | Propósito | Entrada | Salida |
|------|-----------|---------|--------|
| `buscar_clientes` | Buscar clientes | texto_busqueda, limite | Lista de clientes |
| `perfil_consumo_cliente` | Perfil de consumo | cliente_id | Métricas de consumo |
| `clientes_alto_valor` | Clientes con alto gasto | gasto_minimo, limite | Top clientes |
| `top_productos_vendidos` | Productos más vendidos | limite, ordenar_por | Ranking de productos |
| `analisis_categoria` | Ventas por categoría | categoria (opcional) | Métricas por categoría |
| `ventas_por_region` | Ventas por región | region (opcional) | Métricas por región |
| `preferencia_metodo_pago` | Preferencias de pago | region (opcional) | Métricas de pago |
| `calcular_nivel_cliente` | Clasificar cliente | gasto_total, total_ordenes | Nivel y recomendación |

## 🧠 Memoria

- **Tipo**: Corto plazo (InMemorySaver)
- **Session ID**: Identificador único por conversación
- **Ventana**: Últimos 6-10 mensajes
- **Limitación**: La memoria se pierde al reiniciar el servidor

## 🚀 Instalación Local

1. **Clonar el repositorio**
```bash
git clone https://github.com/systemyuri/agente-mcp-groq.git
cd agente-mcp-groq