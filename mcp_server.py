# mcp_server.py
"""
Servidor MCP para Asistente Comercial de E-commerce
"""

import json
import os
import sqlite3
from pathlib import Path
from fastmcp import FastMCP

# Configuración desde variables de entorno
DB_PATH = Path(os.environ.get("MCP_DB_PATH", "./data/mcp_laboratorio.db"))

# Verificar que la base de datos existe
if not DB_PATH.exists():
    print(f"⚠️ Base de datos no encontrada en: {DB_PATH}")
    print("   Ejecuta: python load_data.py o python create_db_direct.py")
    print("   Continuando con la ruta especificada...")

# Instancia del servidor MCP
mcp = FastMCP(
    name="Asistente Comercial E-commerce",
    instructions=(
        "Servidor MCP para análisis de ventas, clientes y productos de un e-commerce. "
        "Expone herramientas de consulta para datos de clientes, ventas, productos, "
        "categorías y métodos de pago."
    ),
)

# -----------------------------------------------------------------------------
# CONECTOR SQLITE (helper interno, NO es una tool MCP)
# -----------------------------------------------------------------------------
def ejecutar_sql(sql: str, parametros: tuple = ()) -> list[dict]:
    """Ejecuta una consulta SQL interna, controlada y parametrizada."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        try:
            filas = conn.execute(sql, parametros).fetchall()
            return [dict(fila) for fila in filas]
        except sqlite3.Error as e:
            return [{"error": f"Error en la consulta: {str(e)}"}]


# =============================================================================
# FUNCIÓN HELPER MEJORADA PARA CONVERTIR PARÁMETROS
# =============================================================================
def asegurar_int(valor, default=10, minimo=1, maximo=20):
    """
    Convierte un valor a entero con límites.
    Maneja strings, floats, None y otros tipos.
    """
    # Si es None, usar default
    if valor is None:
        return default
    
    # Si es string, intentar convertir
    if isinstance(valor, str):
        # Eliminar espacios y comillas
        valor_limpio = valor.strip().strip('"').strip("'")
        try:
            valor = int(float(valor_limpio))  # float() maneja "1.0" y similares
        except (ValueError, TypeError):
            return default
    
    # Si es float, convertir a int
    if isinstance(valor, float):
        valor = int(valor)
    
    # Si no es entero, usar default
    if not isinstance(valor, int):
        return default
    
    # Aplicar límites
    return max(minimo, min(valor, maximo))

def asegurar_float(valor, default=500.0, minimo=0, maximo=1000000):
    """
    Convierte un valor a float con límites.
    Maneja strings, ints, None y otros tipos.
    """
    if valor is None:
        return default
    
    if isinstance(valor, str):
        valor_limpio = valor.strip().strip('"').strip("'")
        try:
            valor = float(valor_limpio)
        except (ValueError, TypeError):
            return default
    
    if not isinstance(valor, (int, float)):
        return default
    
    valor = float(valor)
    return max(minimo, min(valor, maximo))

# =============================================================================
# TOOLS DE CLIENTES
# =============================================================================
@mcp.tool()
def buscar_clientes(texto_busqueda: str, limite: int = 10) -> str:
    """
    Busca clientes por nombre, apellido o región.
    
    Args:
        texto_busqueda: Texto para buscar en nombre, apellido o región
        limite: Máximo de resultados (1-25)
    """
    # 🔥 FORZAR TIPO
    limite = asegurar_int(limite, default=10, minimo=1, maximo=25)
    
    if not isinstance(texto_busqueda, str):
        texto_busqueda = str(texto_busqueda)
    
    patron = f"%{texto_busqueda.strip()}%"
    
    sql = """
        SELECT
            ID_Cliente,
            Nombre,
            Apellido,
            Región,
            Email
        FROM clientes
        WHERE Nombre LIKE ?
           OR Apellido LIKE ?
           OR Región LIKE ?
        LIMIT ?
    """
    filas = ejecutar_sql(sql, (patron, patron, patron, limite))
    return json.dumps(filas or [{"message": "No se encontraron clientes"}], ensure_ascii=False)

@mcp.tool()
def perfil_consumo_cliente(cliente_id: int) -> str:
    """
    Obtiene el perfil de consumo completo de un cliente específico.
    
    Args:
        cliente_id: ID del cliente (entero)
    """
    # 🔥 FORZAR TIPO
    try:
        if isinstance(cliente_id, str):
            cliente_id = int(float(cliente_id.strip()))
        elif isinstance(cliente_id, float):
            cliente_id = int(cliente_id)
        elif not isinstance(cliente_id, int):
            cliente_id = 0
    except (ValueError, TypeError):
        return json.dumps({"error": "cliente_id debe ser un número entero"}, ensure_ascii=False)
    
    if cliente_id <= 0:
        return json.dumps({"error": "cliente_id debe ser un número positivo"}, ensure_ascii=False)
    
    sql = """
        SELECT
            c.ID_Cliente,
            c.Nombre,
            c.Apellido,
            c.Región,
            c.Email,
            COUNT(v.ID_Venta) AS Total_Ordenes,
            ROUND(SUM(v.Cantidad * p.Precio_Unitario), 2) AS Total_Gastado,
            ROUND(AVG(v.Cantidad * p.Precio_Unitario), 2) AS Ticket_Promedio,
            MIN(v.Fecha) AS Primera_Compra,
            MAX(v.Fecha) AS Ultima_Compra,
            ROUND(AVG(v.Cantidad), 2) AS Promedio_Unidades_por_Compra
        FROM clientes c
        LEFT JOIN ventas v ON c.ID_Cliente = v.ID_Cliente
        LEFT JOIN productos p ON v.ID_Producto = p.ID_Producto
        WHERE c.ID_Cliente = ?
        GROUP BY c.ID_Cliente
    """
    filas = ejecutar_sql(sql, (cliente_id,))
    
    if not filas:
        return json.dumps({"message": "Cliente no encontrado"}, ensure_ascii=False)
    
    if filas[0].get('Total_Ordenes') == 0 or filas[0].get('Total_Ordenes') is None:
        filas[0]['message'] = "Cliente encontrado pero no tiene compras registradas"
    
    return json.dumps(filas, ensure_ascii=False)

@mcp.tool()
def clientes_alto_valor(gasto_minimo: float = 500, limite: int = 10) -> str:
    """
    Identifica clientes con alto gasto.
    
    Args:
        gasto_minimo: Monto mínimo de gasto para considerar
        limite: Máximo de resultados (1-50)
    """
    # 🔥 FORZAR TIPOS
    gasto_minimo = asegurar_float(gasto_minimo, default=500.0, minimo=0, maximo=1000000)
    limite = asegurar_int(limite, default=10, minimo=1, maximo=50)
    
    sql = """
        SELECT
            c.ID_Cliente,
            c.Nombre,
            c.Apellido,
            c.Región,
            COUNT(v.ID_Venta) AS Total_Ordenes,
            ROUND(SUM(v.Cantidad * p.Precio_Unitario), 2) AS Total_Gastado,
            ROUND(AVG(v.Cantidad * p.Precio_Unitario), 2) AS Ticket_Promedio
        FROM clientes c
        JOIN ventas v ON c.ID_Cliente = v.ID_Cliente
        JOIN productos p ON v.ID_Producto = p.ID_Producto
        GROUP BY c.ID_Cliente
        HAVING Total_Gastado >= ?
        ORDER BY Total_Gastado DESC
        LIMIT ?
    """
    filas = ejecutar_sql(sql, (gasto_minimo, limite))
    return json.dumps(filas or [{"message": "No se encontraron clientes con ese nivel de gasto"}], ensure_ascii=False)

# =============================================================================
# TOOLS DE PRODUCTOS Y VENTAS
# =============================================================================
@mcp.tool()
def top_productos_vendidos(limite: int = 10, ordenar_por: str = "cantidad") -> str:
    """
    Lista los productos más vendidos por cantidad o ingresos.
    
    Args:
        limite: Número de productos a mostrar (1-20)
        ordenar_por: "cantidad" o "ingresos"
    """
    # 🔥 FORZAR TIPO: Asegurar que limite es entero
    limite = asegurar_int(limite, default=10, minimo=1, maximo=20)
    
    # Asegurar que ordenar_por es string válido
    if not isinstance(ordenar_por, str):
        ordenar_por = "cantidad"
    ordenar_por = ordenar_por.lower().strip()
    if ordenar_por not in ["cantidad", "ingresos"]:
        ordenar_por = "cantidad"
    
    if ordenar_por == "ingresos":
        columna_orden = "Ingresos_Totales DESC"
    else:
        columna_orden = "Total_Vendido DESC"
    
    sql = f"""
        SELECT
            p.Nombre_producto,
            p.Categoría,
            SUM(v.Cantidad) AS Total_Vendido,
            ROUND(SUM(v.Cantidad * p.Precio_Unitario), 2) AS Ingresos_Totales
        FROM ventas v
        JOIN productos p ON v.ID_Producto = p.ID_Producto
        GROUP BY p.ID_Producto
        ORDER BY {columna_orden}
        LIMIT ?
    """
    filas = ejecutar_sql(sql, (limite,))
    return json.dumps(filas or [{"message": "No hay productos registrados"}], ensure_ascii=False)

@mcp.tool()
def analisis_categoria(categoria: str = None) -> str:
    """
    Análisis de ventas por categoría de producto.
    
    Args:
        categoria: Nombre de categoría específica (opcional)
    """
    if categoria:
        sql = """
            SELECT
                cat.Categoría,
                COUNT(v.ID_Venta) AS Total_Ordenes,
                SUM(v.Cantidad) AS Total_Unidades,
                ROUND(SUM(v.Cantidad * p.Precio_Unitario), 2) AS Ingresos_Totales,
                ROUND(SUM(v.Cantidad * p.Precio_Unitario) * 100.0 /
                      (SELECT SUM(v2.Cantidad * p2.Precio_Unitario)
                       FROM ventas v2
                       JOIN productos p2 ON v2.ID_Producto = p2.ID_Producto), 2) AS Porcentaje_Del_Total
            FROM ventas v
            JOIN productos p ON v.ID_Producto = p.ID_Producto
            JOIN categorias cat ON p.Categoría = cat.Categoría
            WHERE cat.Categoría = ?
            GROUP BY cat.Categoría
        """
        filas = ejecutar_sql(sql, (categoria,))
    else:
        sql = """
            SELECT
                cat.Categoría,
                COUNT(v.ID_Venta) AS Total_Ordenes,
                SUM(v.Cantidad) AS Total_Unidades,
                ROUND(SUM(v.Cantidad * p.Precio_Unitario), 2) AS Ingresos_Totales,
                ROUND(SUM(v.Cantidad * p.Precio_Unitario) * 100.0 /
                      (SELECT SUM(v2.Cantidad * p2.Precio_Unitario)
                       FROM ventas v2
                       JOIN productos p2 ON v2.ID_Producto = p2.ID_Producto), 2) AS Porcentaje_Del_Total
            FROM ventas v
            JOIN productos p ON v.ID_Producto = p.ID_Producto
            JOIN categorias cat ON p.Categoría = cat.Categoría
            GROUP BY cat.Categoría
            ORDER BY Ingresos_Totales DESC
        """
        filas = ejecutar_sql(sql)
    
    return json.dumps(filas or [{"message": "No hay datos disponibles"}], ensure_ascii=False)

# =============================================================================
# TOOLS DE REGIONES
# =============================================================================
@mcp.tool()
def ventas_por_region(region: str = None) -> str:
    """
    Resumen de ventas por región geográfica.
    
    Args:
        region: Nombre de región específica (opcional)
    """
    if region:
        sql = """
            SELECT
                c.Región,
                COUNT(v.ID_Venta) AS Total_Ordenes,
                ROUND(SUM(v.Cantidad * p.Precio_Unitario), 2) AS Total_Ventas,
                ROUND(AVG(v.Cantidad * p.Precio_Unitario), 2) AS Promedio_Orden
            FROM clientes c
            JOIN ventas v ON c.ID_Cliente = v.ID_Cliente
            JOIN productos p ON v.ID_Producto = p.ID_Producto
            WHERE c.Región = ?
            GROUP BY c.Región
        """
        filas = ejecutar_sql(sql, (region,))
    else:
        sql = """
            SELECT
                c.Región,
                COUNT(v.ID_Venta) AS Total_Ordenes,
                ROUND(SUM(v.Cantidad * p.Precio_Unitario), 2) AS Total_Ventas,
                ROUND(AVG(v.Cantidad * p.Precio_Unitario), 2) AS Promedio_Orden
            FROM clientes c
            JOIN ventas v ON c.ID_Cliente = v.ID_Cliente
            JOIN productos p ON v.ID_Producto = p.ID_Producto
            GROUP BY c.Región
            ORDER BY Total_Ventas DESC
        """
        filas = ejecutar_sql(sql)
    
    return json.dumps(filas or [{"message": "No hay datos disponibles"}], ensure_ascii=False)

# =============================================================================
# TOOLS DE MÉTODOS DE PAGO
# =============================================================================
@mcp.tool()
def preferencia_metodo_pago(region: str = None) -> str:
    """
    Analiza preferencias de métodos de pago.
    
    Args:
        region: Región específica (opcional)
    """
    if region:
        sql = """
            SELECT
                mp.Método,
                COUNT(v.ID_Venta) AS Total_Usos,
                ROUND(SUM(v.Cantidad * p.Precio_Unitario), 2) AS Monto_Total,
                ROUND(COUNT(v.ID_Venta) * 100.0 / (SELECT COUNT(*) FROM ventas), 2) AS Porcentaje_Usos
            FROM ventas v
            JOIN metodos_pago mp ON v.Método_Pago = mp.ID_Metodo
            JOIN productos p ON v.ID_Producto = p.ID_Producto
            JOIN clientes c ON v.ID_Cliente = c.ID_Cliente
            WHERE c.Región = ?
            GROUP BY mp.Método
            ORDER BY Total_Usos DESC
        """
        filas = ejecutar_sql(sql, (region,))
    else:
        sql = """
            SELECT
                mp.Método,
                COUNT(v.ID_Venta) AS Total_Usos,
                ROUND(SUM(v.Cantidad * p.Precio_Unitario), 2) AS Monto_Total,
                ROUND(COUNT(v.ID_Venta) * 100.0 / (SELECT COUNT(*) FROM ventas), 2) AS Porcentaje_Usos
            FROM ventas v
            JOIN metodos_pago mp ON v.Método_Pago = mp.ID_Metodo
            JOIN productos p ON v.ID_Producto = p.ID_Producto
            GROUP BY mp.Método
            ORDER BY Total_Usos DESC
        """
        filas = ejecutar_sql(sql)
    
    return json.dumps(filas or [{"message": "No hay datos disponibles"}], ensure_ascii=False)

# =============================================================================
# TOOL DE FUNCIÓN LOCAL
# =============================================================================
@mcp.tool()
def calcular_nivel_cliente(gasto_total: float, total_ordenes: int) -> str:
    """
    Clasifica a un cliente según su nivel de gasto y frecuencia de compras.
    
    Reglas:
    - VIP: gasto >= 5000 y órdenes >= 20
    - Premium: gasto >= 2000 y órdenes >= 10
    - Regular: otros casos
    
    Args:
        gasto_total: Monto total gastado por el cliente
        total_ordenes: Número total de órdenes del cliente
    """
    if isinstance(gasto_total, str):
        try:
            gasto_total = float(gasto_total)
        except ValueError:
            gasto_total = 0.0
    
    if isinstance(total_ordenes, str):
        try:
            total_ordenes = int(total_ordenes)
        except ValueError:
            total_ordenes = 0
    
    if gasto_total >= 5000 and total_ordenes >= 20:
        nivel = "VIP"
        motivo = "Cliente de alto valor con compras frecuentes"
        recomendacion = "Ofrecer beneficios exclusivos y atención prioritaria"
    elif gasto_total >= 2000 and total_ordenes >= 10:
        nivel = "Premium"
        motivo = "Cliente con buen nivel de gasto y frecuencia"
        recomendacion = "Ofrecer descuentos especiales y seguimiento comercial"
    else:
        nivel = "Regular"
        motivo = "Cliente con gasto o frecuencia moderada"
        recomendacion = "Mantener comunicación y ofrecer promociones para incentivar compras"
    
    return json.dumps(
        {
            "nivel": nivel,
            "motivo": motivo,
            "recomendacion": recomendacion,
            "evidencia": {
                "gasto_total": gasto_total,
                "total_ordenes": total_ordenes,
            },
        },
        ensure_ascii=False,
    )

# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
if __name__ == "__main__":
    print("🚀 Iniciando MCP Server...")
    print(f"   Base de datos: {DB_PATH}")
    print("   ✅ Con validación de tipos para parámetros")
    print("")
    print("📋 Tools disponibles:")
    print("   - buscar_clientes")
    print("   - perfil_consumo_cliente")
    print("   - clientes_alto_valor")
    print("   - top_productos_vendidos")
    print("   - analisis_categoria")
    print("   - ventas_por_region")
    print("   - preferencia_metodo_pago")
    print("   - calcular_nivel_cliente")
    print("")
    print("🌐 Servidor HTTP escuchando en http://127.0.0.1:8000")
    print("   Endpoint MCP: http://127.0.0.1:8000/mcp")
    
    #mcp.run(transport="http", host="127.0.0.1", port=8000)
    mcp.run(transport="http", host="0.0.0.0", port=8000)