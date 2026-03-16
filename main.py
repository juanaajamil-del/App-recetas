import streamlit as st
import google.generativeai as genai
import requests
import json

# Configuración inicial
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('models/gemini-3-flash-preview')

st.set_page_config(page_title="Chef Inteligente Pro", layout="wide")
st.title("🍳 Despensa y Menú Inteligente")

# Tabs de navegación profesional
tab1, tab2, tab3 = st.tabs(["🛒 Compras y Tickets", "🍳 Tu Despensa", "📅 Menú Semanal"])

with tab1:
    st.header("Gestión de Compras")
    # Lector de tickets (OCR mediante Gemini)
    uploaded_file = st.file_uploader("Sube una foto de tu ticket", type=["jpg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="Procesando ticket...")
        # Aquí llamarías a Gemini Vision para extraer ingredientes
        st.success("Ticket procesado. Ingredientes extraídos: Tomate, Leche, Pollo.")

with tab2:
    st.header("Estado de tu Despensa")
    # Simulación de lectura de tu Google Sheets (o integración real)
    ingredientes = {"Tomate": 2, "Pollo": 1, "Arroz": 500}
    for item, cant in ingredientes.items():
        col_a, col_b = st.columns([3, 1])
        col_a.write(f"**{item}** - {cant} unidades")
        if col_b.button("Añadir al menú", key=item):
            st.info(f"{item} añadido al plan.")

with tab3:
    st.header("Planificación semanal")
    if st.button("Generar menú detallado"):
        # Prompt mejorado para comida y cena
        prompt = """
        Genera un menú semanal para 7 días incluyendo comida y cena.
        Devuelve JSON con estructura: {"Lunes": {"Comida": "...", "Cena": "..."}, ...}
        """
        # ... lógica de llamada a Gemini ...success("¡Despensa actualizada en Google Sheets!")
