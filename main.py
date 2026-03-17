import streamlit as st
import google.generativeai as genai
import json
import requests
from PIL import Image
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Chef Inteligente Pro", layout="wide")

# Sustituye con tu clave real en Secrets o directamente aquí
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("falta la clave google_api_key en los secretos de streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# URL de tu Google Apps Script (la que termina en /exec)
URL_API = "https://script.google.com/macros/s/AKfycbwPgCPBDH_G__oUNXjcvnHytHg9aeL3DmmtDcMiPvxhs04t6cL9jAgHygYtCK2MztcfaQ/exec"

# --- 1. FUNCIONES DE APOYO ---

def obtener_despensa_real():
    try:
        response = requests.get(URL_API, params={"t": "refresh"}, timeout=15)
        if response.status_code == 200:
            # Ahora el JS devuelve un diccionario: {"leche": 2, "huevos": 12}
            return response.json()
        return {}
    except:
        return {}

def procesar_lote_ingredientes(lista_texto):
    if not lista_texto or not lista_texto.strip(): return
    try:
        prompt = f'analiza estos productos: {lista_texto}. responde solo json minúsculas: {{"items": [{{"nombre": "...", "comestible": true, "cat": "..."}}]}}'
        res = model.generate_content(prompt)
        datos = json.loads(res.text.replace("```json", "").replace("```", "").strip())
        for item in datos.get("items", []):
            if item.get("comestible"):
                requests.post(URL_API, json={
                    "ingrediente": item["nombre"].lower().trim(), 
                    "categoria": item["cat"].lower()
                })
        st.success("¡productos guardados!")
        st.session_state.despensa = obtener_despensa_real()
        st.rerun()
    except:
        st.error("error al procesar el lote de ingredientes.")

def
