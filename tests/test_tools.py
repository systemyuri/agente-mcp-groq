# tests/test_tools.py
"""
Pruebas unitarias para las herramientas MCP
"""

import json
import sys
import os
from pathlib import Path

# Agregar la raíz del proyecto al path para poder importar
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar las tools del servidor MCP
from mcp_server import (
    buscar_clientes,
    perfil_consumo_cliente,
    clientes_alto_valor,
    top_productos_vendidos,
    analisis_categoria,
    ventas_por_region,
    preferencia_metodo_pago,
    calcular_nivel_cliente
)

# =============================================================================
# PRUEBAS DE TOOLS
# =============================================================================

def test_buscar_clientes():
    """Prueba la herramienta buscar_clientes"""
    print("\n🧪 Probando: buscar_clientes")
    print("-" * 40)
    
    # Prueba 1: Búsqueda por región
    resultado = buscar_clientes("Patagonia", 3)
    datos = json.loads(resultado)
    
    assert isinstance(datos, list), "El resultado debe ser una lista"
    assert len(datos) <= 3, "El límite debe funcionar"
    if len(datos) > 0:
        assert "Nombre" in datos[0], "Debe contener nombre"
        assert "Región" in datos[0], "Debe contener región"
    
    print("✅ Búsqueda por región: OK")
    
    # Prueba 2: Búsqueda por nombre
    resultado = buscar_clientes("Karisa", 1)
    datos = json.loads(resultado)
    
    if len(datos) > 0:
        assert datos[0].get("Nombre") == "Karisa", "Debe encontrar a Karisa"
    
    print("✅ Búsqueda por nombre: OK")
    
    # Prueba 3: Validación de tipos
    resultado = buscar_clientes("Buenos Aires", "5")  # String en lugar de int
    datos = json.loads(resultado)
    assert isinstance(datos, list), "Debe manejar string como límite"
    
    print("✅ Validación de tipos: OK")

def test_perfil_consumo_cliente():
    """Prueba la herramienta perfil_consumo_cliente"""
    print("\n🧪 Probando: perfil_consumo_cliente")
    print("-" * 40)
    
    # Prueba 1: Cliente existente
    resultado = perfil_consumo_cliente(4)
    datos = json.loads(resultado)
    
    assert isinstance(datos, list), "El resultado debe ser una lista"
    if len(datos) > 0:
        assert datos[0].get("ID_Cliente") == 4, "Debe ser el cliente 4"
        assert "Total_Ordenes" in datos[0], "Debe tener total de órdenes"
        assert "Total_Gastado" in datos[0], "Debe tener total gastado"
    
    print("✅ Cliente existente: OK")
    
    # Prueba 2: Cliente inexistente
    resultado = perfil_consumo_cliente(9999)
    datos = json.loads(resultado)
    
    if isinstance(datos, list):
        assert "message" in datos[0] or "error" in datos[0], "Debe indicar no encontrado"
    
    print("✅ Cliente inexistente: OK")
    
    # Prueba 3: Validación de tipos
    resultado = perfil_consumo_cliente("4")  # String en lugar de int
    datos = json.loads(resultado)
    assert isinstance(datos, list) or "error" in datos, "Debe manejar string"
    
    print("✅ Validación de tipos: OK")

def test_clientes_alto_valor():
    """Prueba la herramienta clientes_alto_valor"""
    print("\n🧪 Probando: clientes_alto_valor")
    print("-" * 40)
    
    # Prueba 1: Con límite
    resultado = clientes_alto_valor(500, 3)
    datos = json.loads(resultado)
    
    assert isinstance(datos, list), "El resultado debe ser una lista"
    assert len(datos) <= 3, "El límite debe funcionar"
    
    print("✅ Con límite: OK")
    
    # Prueba 2: Con gasto mínimo bajo
    resultado = clientes_alto_valor(50, 5)
    datos = json.loads(resultado)
    
    assert isinstance(datos, list), "Debe devolver lista"
    if len(datos) > 0:
        assert "Total_Gastado" in datos[0], "Debe tener total gastado"
    
    print("✅ Con gasto mínimo bajo: OK")

def test_top_productos_vendidos():
    """Prueba la herramienta top_productos_vendidos"""
    print("\n🧪 Probando: top_productos_vendidos")
    print("-" * 40)
    
    # Prueba 1: Por cantidad
    resultado = top_productos_vendidos(3, "cantidad")
    datos = json.loads(resultado)
    
    assert isinstance(datos, list), "El resultado debe ser una lista"
    assert len(datos) <= 3, "El límite debe funcionar"
    if len(datos) > 0:
        assert "Nombre_producto" in datos[0], "Debe tener nombre"
        assert "Total_Vendido" in datos[0], "Debe tener cantidad"
    
    print("✅ Por cantidad: OK")
    
    # Prueba 2: Por ingresos
    resultado = top_productos_vendidos(3, "ingresos")
    datos = json.loads(resultado)
    
    assert isinstance(datos, list), "El resultado debe ser una lista"
    if len(datos) > 0:
        assert "Ingresos_Totales" in datos[0], "Debe tener ingresos"
    
    print("✅ Por ingresos: OK")
    
    # Prueba 3: Validación de tipos
    resultado = top_productos_vendidos("5", "cantidad")  # String en lugar de int
    datos = json.loads(resultado)
    assert isinstance(datos, list), "Debe manejar string como límite"
    
    print("✅ Validación de tipos: OK")

def test_analisis_categoria():
    """Prueba la herramienta analisis_categoria"""
    print("\n🧪 Probando: analisis_categoria")
    print("-" * 40)
    
    # Prueba 1: Todas las categorías
    resultado = analisis_categoria()
    datos = json.loads(resultado)
    
    assert isinstance(datos, list), "El resultado debe ser una lista"
    if len(datos) > 0:
        assert "Categoría" in datos[0], "Debe tener categoría"
        assert "Ingresos_Totales" in datos[0], "Debe tener ingresos"
    
    print("✅ Todas las categorías: OK")
    
    # Prueba 2: Categoría específica
    resultado = analisis_categoria("Lácteos")
    datos = json.loads(resultado)
    
    assert isinstance(datos, list), "El resultado debe ser una lista"
    if len(datos) > 0:
        assert datos[0].get("Categoría") == "Lácteos", "Debe ser la categoría Lácteos"
    
    print("✅ Categoría específica: OK")

def test_ventas_por_region():
    """Prueba la herramienta ventas_por_region"""
    print("\n🧪 Probando: ventas_por_region")
    print("-" * 40)
    
    # Prueba 1: Todas las regiones
    resultado = ventas_por_region()
    datos = json.loads(resultado)
    
    assert isinstance(datos, list), "El resultado debe ser una lista"
    if len(datos) > 0:
        assert "Región" in datos[0], "Debe tener región"
        assert "Total_Ventas" in datos[0], "Debe tener total ventas"
    
    print("✅ Todas las regiones: OK")
    
    # Prueba 2: Región específica
    resultado = ventas_por_region("Buenos Aires")
    datos = json.loads(resultado)
    
    assert isinstance(datos, list), "El resultado debe ser una lista"
    if len(datos) > 0:
        assert datos[0].get("Región") == "Buenos Aires", "Debe ser Buenos Aires"
    
    print("✅ Región específica: OK")

def test_preferencia_metodo_pago():
    """Prueba la herramienta preferencia_metodo_pago"""
    print("\n🧪 Probando: preferencia_metodo_pago")
    print("-" * 40)
    
    # Prueba 1: Todos los métodos
    resultado = preferencia_metodo_pago()
    datos = json.loads(resultado)
    
    assert isinstance(datos, list), "El resultado debe ser una lista"
    if len(datos) > 0:
        assert "Método" in datos[0], "Debe tener método"
        assert "Total_Usos" in datos[0], "Debe tener total usos"
    
    print("✅ Todos los métodos: OK")
    
    # Prueba 2: Por región
    resultado = preferencia_metodo_pago("Patagonia")
    datos = json.loads(resultado)
    
    assert isinstance(datos, list), "El resultado debe ser una lista"
    
    print("✅ Por región: OK")

def test_calcular_nivel_cliente():
    """Prueba la herramienta calcular_nivel_cliente"""
    print("\n🧪 Probando: calcular_nivel_cliente")
    print("-" * 40)
    
    # Prueba 1: Cliente VIP
    resultado = calcular_nivel_cliente(6000, 25)
    datos = json.loads(resultado)
    
    assert isinstance(datos, dict), "El resultado debe ser un diccionario"
    assert datos.get("nivel") == "VIP", "Debe ser VIP"
    assert "motivo" in datos, "Debe tener motivo"
    
    print("✅ Cliente VIP: OK")
    
    # Prueba 2: Cliente Premium
    resultado = calcular_nivel_cliente(3000, 15)
    datos = json.loads(resultado)
    
    assert isinstance(datos, dict), "El resultado debe ser un diccionario"
    assert datos.get("nivel") == "Premium", "Debe ser Premium"
    
    print("✅ Cliente Premium: OK")
    
    # Prueba 3: Cliente Regular
    resultado = calcular_nivel_cliente(500, 5)
    datos = json.loads(resultado)
    
    assert isinstance(datos, dict), "El resultado debe ser un diccionario"
    assert datos.get("nivel") == "Regular", "Debe ser Regular"
    
    print("✅ Cliente Regular: OK")

# =============================================================================
# EJECUTAR TODAS LAS PRUEBAS
# =============================================================================

def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("=" * 60)
    print("🧪 EJECUTANDO PRUEBAS DE TOOLS MCP")
    print("=" * 60)
    
    tests = [
        test_buscar_clientes,
        test_perfil_consumo_cliente,
        test_clientes_alto_valor,
        test_top_productos_vendidos,
        test_analisis_categoria,
        test_ventas_por_region,
        test_preferencia_metodo_pago,
        test_calcular_nivel_cliente,
    ]
    
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ {test.__name__} falló: {e}")
        except Exception as e:
            print(f"❌ {test.__name__} error inesperado: {e}")
    
    print("\n" + "=" * 60)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()