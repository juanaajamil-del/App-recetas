import streamlit as st
import google.generativeai as genai
import json
import requests
from PIL import Image
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Chef Inteligente Pro", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Usamos el modelo que ya confirmamos que funciona bien
model = genai.GenerativeModel('gemini-2.5-flash')

URL_API = "https://script.google.com/macros/s/AKfycbwxRVRKIPux8LEnKPe2kgtTGLuT1iZXCmOxCHV73Gb0l0UiA8-CBcEPipTwRpQF222O6g/exec"

# --- 1. FUNCIONES DE CONEXIÓN Y DESPENSA ---

def obtener_despensa_real():
    """lee los productos directamente desde google sheets"""
    try:
        response = requests.get(URL_API, params={"t": "refresh"}, timeout=15)
        if response.status_code == 200:
            return [str(item).lower() for item in response.json() if item]
        return []
    except Exception:
        return []

def procesar_lote_ingredientes(lista_texto):
    """clasifica una lista de texto y la envía a la nube (ahorra cuota)"""
    if not lista_texto.strip(): return
    try:
        prompt = f"""analiza estos productos: {lista_texto}. 
        responde solo json: {{"items": [{{"nombre": "...", "comestible": true/false, "cat": "..."}}, ...]}}
        usa solo minúsculas."""
        res = model.generate_content(prompt)
        datos = json.loads(res.text.replace("```json", "").replace("```", "").strip())
        
        for item in datos.get("items", []):
            if item["comestible"]:
                payload = {"ingrediente": item["nombre"].lower(), "categoria": item["cat"].lower()}
                requests.post(URL_API, json=payload, timeout=10)
                if 'despensa' in st.session_state:
                    st.session_state.despensa.append(item["nombre"].lower())
        st.success("¡productos procesados y guardados!")
    except Exception as e:
        st.error(f"error al procesar: {e}")

# --- 2. FUNCIONES DE MENÚ Y COMPRA ---

def generar_propuestas(ingredientes=None):
    """sugiere platos basados en la despensa o libres"""
    contexto = f"tengo estos ingredientes: {', '.join(ingredientes)}" if ingredientes else "haz propuestas creativas"
    prompt = f"""basado en {contexto}, sugiere 3 platos de comida y 3 de cena. 
    usa solo minúsculas. responde solo json:
    {{"comidas": ["...", "...", "..."], "cenas": ["...", "...", "..."]}}"""
    res = model.generate_content(prompt)
    return json.loads(res.text.replace("```json", "").replace("```", "").strip())

def generar_lista_compra(menu_final, despensa_actual):
    """calcula qué falta para el menú elegido"""
    prompt = f"""menú: {json.dumps(menu_final)}. despensa: {', '.join(despensa_actual)}.
    ¿qué ingredientes faltan? responde solo lista json de strings en minúsculas."""
    res = model.generate_content(prompt)
    return json.loads(res.text.replace("```json", "").replace("```", "").strip())

#
