import streamlit as st
import google.generativeai as genai

st.write("Verificando configuración...")

# 1. ¿Lee bien la clave?
try:
    key = st.secrets["GOOGLE_API_KEY"]
    st.success(f"Clave detectada: {key[:5]}...") # Muestra solo los primeros caracteres
except Exception as e:
    st.error("No se detecta la clave en st.secrets")

# 2. Intentar una configuración más básica
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    # Forzar una llamada pequeña
    response = model.generate_content("Hola, ¿estás ahí?")
    st.write("Respuesta de Gemini:", response.text)
except Exception as e:
    st.error(f"Error específico al llamar a Gemini: {e}")
