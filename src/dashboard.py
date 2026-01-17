import streamlit as st
import pandas as pd
import os

# Configuración de la página
st.set_page_config(page_title="Monitor de Agua con IA", layout="wide")

st.title("💧 Sistema Inteligente de Gestión de Agua")
st.markdown("---")

# Cargar datos
ruta_csv = os.path.join("data", "dataset_evaluacion.csv")

try:
    df = pd.read_csv(ruta_csv)
    
    # Métricas clave (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Registros", len(df))
    col2.metric("Anomalías Detectadas", len(df[df['etiqueta_real'] != 'NORMAL']))
    col3.metric("Promedio pH", round(df['ph'].mean(), 2))
    col4.metric("Promedio Presión", round(df['presion_bar'].mean(), 2))

    # Tabla interactiva
    st.subheader("📋 Registro de Telemetría (Dataset)")
    
    # Colorear las filas según si es Anomalía o Normal
    def colorear_anomalias(val):
        color = 'red' if val != 'NORMAL' else 'green'
        return f'color: {color}; font-weight: bold'

    st.dataframe(
        df.style.applymap(colorear_anomalias, subset=['etiqueta_real']),
        use_container_width=True,
        height=400
    )

except FileNotFoundError:
    st.error("❌ No encuentro el archivo CSV. Asegúrate de haber ejecutado 'generar_dataset.py' primero.")