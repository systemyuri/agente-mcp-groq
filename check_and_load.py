# check_and_load.py
"""
Script para verificar la base de datos y cargar datos si es necesario
"""

import sqlite3
from pathlib import Path
import subprocess
import sys

DB_PATH = Path("./data/mcp_laboratorio.db")
DATA_PATH = Path("./data")

def verificar_base_datos():
    """Verifica si la base de datos existe y tiene datos"""
    
    # Verificar si existe el archivo
    if not DB_PATH.exists():
        print("⚠️ Base de datos no encontrada")
        return False
    
    # Verificar tamaño (si es muy pequeño, probablemente está vacía)
    if DB_PATH.stat().st_size < 1024:  # Menos de 1KB
        print("⚠️ Base de datos parece estar vacía (tamaño muy pequeño)")
        return False
    
    # Verificar si tiene la tabla ventas con datos
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Verificar que la tabla ventas existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ventas'")
            if not cursor.fetchone():
                print("⚠️ Tabla 'ventas' no encontrada")
                return False
            
            # Verificar que tiene datos
            cursor.execute("SELECT COUNT(*) FROM ventas")
            count = cursor.fetchone()[0]
            
            if count == 0:
                print("⚠️ Tabla 'ventas' está vacía")
                return False
            
            print(f"✅ Base de datos verificada: {count} registros en ventas")
            return True
            
    except Exception as e:
        print(f"⚠️ Error al verificar base de datos: {e}")
        return False

def cargar_datos():
    """Ejecuta load_data.py para cargar los datos"""
    print("📂 Cargando datos desde CSV...")
    try:
        subprocess.run([sys.executable, "load_data.py"], check=True)
        print("✅ Datos cargados exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al cargar datos: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verificando base de datos...")
    if verificar_base_datos():
        print("✅ Base de datos lista para usar")
        sys.exit(0)
    else:
        print("🔄 Base de datos necesita ser creada/cargada")
        if cargar_datos():
            print("✅ Base de datos preparada exitosamente")
            sys.exit(0)
        else:
            print("❌ No se pudo preparar la base de datos")
            sys.exit(1)