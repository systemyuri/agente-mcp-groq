# load_data.py
"""
Script para cargar datos CSV a SQLite
"""

import pandas as pd
import sqlite3
from pathlib import Path

# Ruta de la base de datos
DB_PATH = Path("./data/mcp_laboratorio.db")
DATA_PATH = Path("./data")

def load_csv_to_sqlite():
    """Carga todos los CSV a SQLite"""
    
    # Verificar que los archivos existen
    archivos = ["clientes.csv", "ventas.csv", "productos.csv", "categorias.csv", "metodos_pago.csv"]
    archivos_faltantes = [a for a in archivos if not (DATA_PATH / a).exists()]
    
    if archivos_faltantes:
        print(f"❌ Faltan archivos: {', '.join(archivos_faltantes)}")
        print("Coloca los archivos CSV en la carpeta 'data/'")
        return
    
    print("📂 Cargando datos...")
    
    # Cargar CSVs
    dataframes = {}
    for archivo in archivos:
        nombre_tabla = archivo.replace('.csv', '')
        df = pd.read_csv(DATA_PATH / archivo)
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
        dataframes[nombre_tabla] = df
        print(f"   ✅ {archivo}: {len(df)} registros")
    
    # Guardar en SQLite
    print("\n💾 Guardando en SQLite...")
    with sqlite3.connect(DB_PATH) as conn:
        for nombre_tabla, df in dataframes.items():
            # Convertir fechas si existen
            for col in ["Fecha", "Fecha_Resgistro", "Fecha_Registro", "fecha", "date"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
            
            df.to_sql(nombre_tabla, conn, if_exists="replace", index=False)
            print(f"   ✅ Tabla '{nombre_tabla}': {len(df)} filas")
    
    print(f"\n✅ Base de datos creada: {DB_PATH}")

if __name__ == "__main__":
    load_csv_to_sqlite()