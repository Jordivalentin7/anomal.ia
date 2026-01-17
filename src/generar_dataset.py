import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

# Configuración del dataset
NUM_REGISTROS = 100
CARPETA_DATA = "data"
NOMBRE_ARCHIVO = "dataset_evaluacion.csv"

def generar_escenario_normal(fecha):
    """Genera un registro operativo correcto."""
    return {
        "timestamp": fecha,
        "id_sensor": f"POZO-{random.randint(1, 3)}",
        "ph": round(random.uniform(7.0, 8.0), 2),
        "cloro_residual": round(random.uniform(0.4, 0.8), 2),
        "presion_bar": round(random.uniform(3.5, 4.5), 2),
        "consumo_kwh": round(random.uniform(45, 50), 2),
        "caudal_m3h": round(random.uniform(140, 160), 2),
        "etiqueta_real": "NORMAL"  # Esta es la "solución" correcta
    }

def generar_fuga(fecha):
    """Simula una rotura de tubería: Baja presión y aumenta caudal (o se mantiene)."""
    return {
        "timestamp": fecha,
        "id_sensor": f"POZO-{random.randint(1, 3)}",
        "ph": round(random.uniform(7.0, 8.0), 2),
        "cloro_residual": round(random.uniform(0.4, 0.8), 2),
        "presion_bar": round(random.uniform(0.5, 1.8), 2), # <--- PRESIÓN MUY BAJA
        "consumo_kwh": round(random.uniform(45, 50), 2),
        "caudal_m3h": round(random.uniform(160, 180), 2), # Caudal alto por la fuga
        "etiqueta_real": "ANOMALIA_FUGA"
    }

def generar_error_quimico(fecha):
    """Simula fallo en cloración."""
    cloro_malo = random.choice([round(random.uniform(0.0, 0.15), 2), round(random.uniform(1.2, 2.0), 2)])
    return {
        "timestamp": fecha,
        "id_sensor": f"POZO-{random.randint(1, 3)}",
        "ph": round(random.uniform(6.0, 9.0), 2), # pH inestable
        "cloro_residual": cloro_malo, # <--- CLORO FUERA DE RANGO
        "presion_bar": round(random.uniform(3.5, 4.5), 2),
        "consumo_kwh": round(random.uniform(45, 50), 2),
        "caudal_m3h": round(random.uniform(140, 160), 2),
        "etiqueta_real": "ANOMALIA_QUIMICA"
    }

def generar_fallo_bomba(fecha):
    """Simula bomba atascada: Mucho consumo, poco agua."""
    return {
        "timestamp": fecha,
        "id_sensor": f"POZO-{random.randint(1, 3)}",
        "ph": round(random.uniform(7.0, 8.0), 2),
        "cloro_residual": round(random.uniform(0.4, 0.8), 2),
        "presion_bar": round(random.uniform(1.0, 2.5), 2), # Presión baja
        "consumo_kwh": round(random.uniform(60, 80), 2),   # <--- CONSUMO DISPARADO
        "caudal_m3h": round(random.uniform(20, 50), 2),    # <--- CAUDAL MÍNIMO
        "etiqueta_real": "ANOMALIA_BOMBA"
    }

def main():
    registros = []
    fecha_base = datetime.now()

    print(f"⚙️ Generando {NUM_REGISTROS} registros sintéticos...")

    for i in range(NUM_REGISTROS):
        fecha_actual = (fecha_base - timedelta(minutes=15*i)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Probabilidades de escenarios
        dado = random.random()
        
        if dado < 0.70: # 70% de datos normales
            dato = generar_escenario_normal(fecha_actual)
        elif dado < 0.80: # 10% Fugas
            dato = generar_fuga(fecha_actual)
        elif dado < 0.90: # 10% Químico
            dato = generar_error_quimico(fecha_actual)
        else: # 10% Fallo Bomba
            dato = generar_fallo_bomba(fecha_actual)
            
        registros.append(dato)

    # Crear DataFrame
    df = pd.DataFrame(registros)
    
    # Asegurar que existe la carpeta data
    if not os.path.exists(CARPETA_DATA):
        os.makedirs(CARPETA_DATA)
        
    ruta_completa = os.path.join(CARPETA_DATA, NOMBRE_ARCHIVO)
    
    # Guardar CSV
    df.to_csv(ruta_completa, index=False)
    
    print(f"✅ ¡Hecho! Dataset guardado en: {ruta_completa}")
    print("\nResumen de anomalías generadas:")
    print(df['etiqueta_real'].value_counts())

if __name__ == "__main__":
    main()