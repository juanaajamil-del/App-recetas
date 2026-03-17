import streamlit as st
import google.generativeai as genai
import json
import requests
from PIL import Image
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Chef Inteligente Pro", layout="wide")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("falta la clave google_api_key en los secretos de streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# URL actualizada con la que me has proporcionado
URL_API = "https://script.google.com/macros/s/AKfycbxzFILdNWLMMAy6srZK8ZHJ41EU6IKJZwCoM1kziQZA_ZfFgQirWFOeXNB7_cmcUzbQ_w/exec"

# --- 1. FUNCIONES DE APOYO ---

def obtener_despensa_real():
    try:
        response = requests.get(URL_API, params={"t": "refresh"}, timeout=15)
        if response.status_code == 200:
            return [str(item).lower() for item in response.json() if item]
        return []
    except: return []

def procesar_lote_ingredientes(lista_texto):
    if not lista_texto or not lista_texto.strip(): return
    try:
        prompt = f'analiza estos productos: {lista_texto}. responde solo json minúsculas: {{"items": [{{"nombre": "...", "comestible": true, "cat": "..."}}]}}'
        res = model.generate_content(prompt)
        datos = json.loads(res.text.replace("```json", "").replace("```", "").strip())
        for item in datos.get("items", []):
            if item.get("comestible"):
                requests.post(URL_API, json={"ingrediente": item["nombre"].lower(), "categoria": item["cat"].lower()})
        st.success("¡productos guardados!")
        st.session_state.despensa = obtener_despensa_real()
        st.rerun()
    except: st.error("error al procesar lote.")

def generar_menu_completo(ingredientes=None):
    tipo = f"de aprovechamiento usando: {', '.join(ingredientes)}" if ingredientes else "creativo y libre"
    prompt = f'genera un menú semanal completo (lunes a domingo, comida y cena) {tipo}. usa solo minúsculas. responde solo json: {{"lunes": {{"comida": "...", "cena": "..."}}, "martes": {{...}}, ...}}'
    res = model.generate_content(prompt)
    return json.loads(res.text.replace("```json", "").replace("```", "").strip())

def generar_lista_compra(menu_final, despensa_actual):
    prompt = f'menú: {json.dumps(menu_final)}. despensa: {", ".join(despensa_actual)}. ¿qué falta? responde lista json de strings minúsculas.'
    res = model.generate_content(prompt)
    return json.loads(res.text.replace("```json", "").replace("```", "").strip())

# --- 2. INICIALIZACIÓN ---
if 'despensa' not in st.session_state: st.session_state.despensa = obtener_despensa_real()
if 'menu_oficial' not in st.session_state: 
    st.session_state.menu_oficial = {d: {"comida": "vacio", "cena": "vacio"} for d in ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]}

# --- 3. INTERFAZ ---
st.title("🍳 Chef Inteligente Pro")
t1, t2, t3, t4 = st.tabs(["🛒 Despensa", "📅 Planificador", "📝 Mi Semana", "📸 Ticket"])

with t1:
    st.header("🛒 mi despensa")
    if st.button("🔄 sincronizar con google sheets"):
        st.session_state.despensa = obtener_despensa_real()
        st.rerun()
    
    texto_lote = st.text_area("añadir ingredientes (por comas o líneas):")
    if st.button("procesar lote"): 
        with st.spinner("guardando..."):
            procesar_lote_ingredientes(texto_lote)

    st.write("---")
    st.subheader("stock actual")
    if st.session_state.despensa:
        for item in st.session_state.despensa:
            col_txt, col_del = st.columns([4, 1])
            with col_txt:
                st.write(f"✅ {item}")
            with col_del:
                if st.button("🗑️", key=f"del_{item}"):
                    payload = {"tipo": "borrar_ingrediente", "ingrediente": item}
                    requests.post(URL_API, json
