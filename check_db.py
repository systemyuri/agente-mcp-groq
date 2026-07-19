# check_db.py
"""
Script para verificar el contenido de la base de datos
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("./data/mcp_laboratorio.db")

def check_database():
    """Verifica que la base de datos tenga todas las tablas"""
    
    if not DB_PATH.exists():
        print(f"❌ Base de datos no encontrada en: {DB_PATH}")
        print("   Ejecuta: python load_data.py")
        return False
    
    print(f"✅ Base de datos encontrada: {DB_PATH}")
    print(f"   Tamaño: {DB_PATH.stat().st_size / 1024:.2f} KB")
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
        
        print("\n📋 Tablas encontradas:")
        for tabla in tablas:
            nombre = tabla[0]
            cursor.execute(f"SELECT COUNT(*) FROM {nombre}")
            count = cursor.fetchone()[0]
            print(f"   ✅ {nombre}: {count} filas")
        
        # Verificar que todas las tablas necesarias existen
        tablas_necesarias = ['clientes', 'ventas', 'productos', 'categorias', 'metodos_pago']
        tablas_existentes = [t[0] for t in tablas]
        
        print("\n🔍 Verificando tablas necesarias:")
        for tabla in tablas_necesarias:
            if tabla in tablas_existentes:
                print(f"   ✅ {tabla}")
            else:
                print(f"   ❌ {tabla} - FALTA")
                return False
    
    print("\n✅ Todas las tablas están presentes")
    return True

if __name__ == "__main__":
    check_database()