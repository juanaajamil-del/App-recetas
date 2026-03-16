import streamlit as st
import google.generativeai as genai

st.title("🧪 Diagnóstico de Conexión")

if st.button("Comprobar modelos disponibles"):
    try:
        # 1. Configurar
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # 2. Listar
        st.write("Conexión establecida. Listando modelos:")
        models = genai.list_models()
        for m in models:
            st.write(f"- {m.name}")
            
    except Exception as e:
        st.error(f"Error detectado: {e}")
