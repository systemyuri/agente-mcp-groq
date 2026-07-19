# create_db_direct.py
"""
Script para crear la base de datos directamente desde los CSV
con rutas absolutas si es necesario
"""

import pandas as pd
import sqlite3
from pathlib import Path
import os

# Obtener la ruta absoluta del proyecto
PROJECT_PATH = Path(__file__).parent.absolute()
DATA_PATH = PROJECT_PATH / "data"
DB_PATH = DATA_PATH / "mcp_laboratorio.db"

print(f"📁 Proyecto en: {PROJECT_PATH}")
print(f"📁 Datos en: {DATA_PATH}")
print(f"💾 Base de datos: {DB_PATH}")

def crear_base_datos():
    """Crea la base de datos desde los CSV"""
    
    # Verificar que la carpeta data existe
    if not DATA_PATH.exists():
        DATA_PATH.mkdir(exist_ok=True)
        print(f"✅ Carpeta data creada: {DATA_PATH}")
    
    # Lista de archivos necesarios
    archivos = {
        'clientes': 'clientes.csv',
        'ventas': 'ventas.csv',
        'productos': 'productos.csv',
        'categorias': 'categorias.csv',
        'metodos_pago': 'metodos_pago.csv'
    }
    
    # Verificar que todos los CSV existen
    archivos_faltantes = []
    for nombre, archivo in archivos.items():
        ruta = DATA_PATH / archivo
        if not ruta.exists():
            archivos_faltantes.append(archivo)
    
    if archivos_faltantes:
        print(f"\n❌ Faltan archivos CSV en {DATA_PATH}:")
        for archivo in archivos_faltantes:
            print(f"   - {archivo}")
        print("\n📌 Coloca los archivos CSV en la carpeta data/")
        print("   Puedes descargarlos desde tu notebook de Colab")
        return False
    
    print("\n📂 Cargando archivos CSV...")
    dataframes = {}
    
    for nombre, archivo in archivos.items():
        ruta = DATA_PATH / archivo
        try:
            df = pd.read_csv(ruta)
            df.columns = df.columns.str.strip()
            dataframes[nombre] = df
            print(f"   ✅ {archivo}: {len(df)} registros, {len(df.columns)} columnas")
        except Exception as e:
            print(f"   ❌ Error al cargar {archivo}: {e}")
            return False
    
    print("\n💾 Guardando en SQLite...")
    
    # Si la base de datos ya existe, la eliminamos para empezar frescos
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"   🗑️ Base de datos anterior eliminada")
    
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            for nombre, df in dataframes.items():
                # Convertir fechas si existen
                for col in ["Fecha", "Fecha_Resgistro", "Fecha_Registro", "fecha", "date"]:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
                
                # Crear tabla e insertar datos
                df.to_sql(nombre, conn, if_exists="replace", index=False)
                print(f"   ✅ Tabla '{nombre}': {len(df)} filas")
        
        print(f"\n✅ Base de datos creada exitosamente: {DB_PATH}")
        print(f"   Tamaño: {DB_PATH.stat().st_size / 1024:.2f} KB")
        return True
        
    except Exception as e:
        print(f"\n❌ Error al crear la base de datos: {e}")
        return False

if __name__ == "__main__":
    crear_base_datos()