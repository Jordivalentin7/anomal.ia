import os
import pandas as pd
import random
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from mistralai import Mistral  # Importamos la librería oficial nueva

# 1. Cargar configuración
load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")

if not api_key:
    raise ValueError("❌ Falta la MISTRAL_API_KEY en el archivo .env")

# 2. Configurar el cliente de Mistral
client = Mistral(api_key=api_key)

# --- SISTEMA EXPERTO (Tus reglas) ---
SYSTEM_PROMPT = """
Eres un ingeniero experto en gestión de agua.
Analiza los datos basándote en:
- pH Normal: 6.5 - 9.5
- Cloro Normal: 0.2 - 1.0 mg/L (CRÍTICO si < 0.2)
- Presión Normal: 2.0 - 6.0 bar

Salida requerida:
1. Estado: [NORMAL / ALERTA / PELIGRO]
2. Análisis breve.
"""

def generar_datos_agua(n_registros=1):
    """Genera datos simulados."""
    print(f"🌊 Generando {n_registros} registros simulados...")
    datos = []
    fecha_base = datetime.now()

    for i in range(n_registros):
        # Forzamos fallo a veces
        es_anomalo = random.random() < 0.5 
        
        if es_anomalo:
            cloro = round(random.uniform(0.0, 0.18), 2) # Peligro bajo
        else:
            cloro = round(random.uniform(0.4, 0.9), 2)

        registro = {
            "timestamp": (fecha_base - timedelta(minutes=10*i)).strftime("%Y-%m-%d %H:%M:%S"),
            "id_sensor": "POZO-NORD-01",
            "ph": round(random.uniform(6.5, 8.5), 2),
            "cloro_residual": cloro, 
            "presion_bar": round(random.uniform(2.0, 5.0), 2)
        }
        datos.append(registro)
    
    return pd.DataFrame(datos)

def analizar_con_mistral(dato):
    """Envía el dato a la API oficial de Mistral."""
    
    prompt_usuario = f"Lectura de sensor: {json.dumps(dato)}"
    
    try:
        # Llamada a la API v1.0 de Mistral
        chat_response = client.chat.complete(
            model="open-mixtral-8x7b", # El modelo Mixtral 8x7B oficial
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.1
        )
        return chat_response.choices[0].message.content
    except Exception as e:
        return f"Error conectando con Mistral: {e}"

if __name__ == "__main__":
    # 1. Dato
    df = generar_datos_agua(1)
    dato = df.iloc[0].to_dict()
    
    print(f"\n📊 ENVIANDO A MIXTRAL (Europa): {dato}")
    
    # 2. Análisis
    respuesta = analizar_con_mistral(dato)
    
    print("-" * 60)
    print("🇪🇺 RESPUESTA DE MIXTRAL 8x7B:")
    print(respuesta)
    print("-" * 60)