import streamlit as st
import google.generativeai as genai
import json
import requests
from PIL import Image
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Chef Inteligente Pro", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

URL_API = "https://script.google.com/macros/s/AKfycbwxRVRKIPux8LEnKPe2kgtTGLuT1iZXCmOxCHV73Gb0l0UiA8-CBcEPipTwRpQF222O6g/exec"

# --- FUNCIONES DE CONEXIÓN ---

def obtener_despensa_real():
    """lee los productos directamente desde google sheets"""
    try:
        response = requests.get(URL_API, timeout=10)
        if response.status_code == 200:
            return response.json() 
        return []
    except Exception:
        return []

def guardar_en_sheets(ingrediente):
    """clasifica con ia, filtra no comestibles y envía a google sheets"""
    try:
        ingrediente = ingrediente.lower()
        prompt = f"""analiza el producto: '{ingrediente}'.
        determina si es un alimento. responde solo json: 
        {{"es_comestible": true/false, "categoria": "..."}}"""
        
        response = model.generate_content(prompt)
        resultado = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        
        if not resultado.get("es_comestible", False):
            st.info(f"omitido: '{ingrediente}' no es un alimento.")
            return "omitido"

        datos = {"ingrediente": ingrediente, "categoria": resultado["categoria"]}
        response = requests.post(URL_API, json=datos, timeout=10)
        return response.status_code == 200
    except Exception as e:
        st.error(f"error: {e}")
        return False

def generar_menu(ingredientes=None):
    """genera el menú. si hay ingredientes, es de aprovechamiento; si no, es libre."""
    if ingredientes:
        contexto = f"tengo estos ingredientes: {', '.join(ingredientes)}. haz un menú de aprovechamiento."
    else:
        contexto = "haz un menú variado y creativo, sin restricciones de ingredientes."

    prompt = f"""{contexto} genera un menú semanal (lunes-domingo) con comida y cena. 
    usa solo minúsculas. devuelve sólo json:
    {{"lunes": {{"comida": "...", "cena": "..."}}, "martes": {{...}}, ...}}"""
    
    response = model.generate_content(prompt)
    texto = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)

# --- INTERFAZ ---
st.title("🍳 Chef Inteligente Pro")
tab1, tab2, tab3 = st.tabs(["🛒 Despensa", "📅 Menú Semanal", "📸 Ticket"])

with tab1:
    st.header("🛒 Mi despensa")
    
    # botón de sincronización manual
    if st.button("🔄 sincronizar con la nube"):
        st.session_state.despensa = obtener_despensa_real()
        st.rerun()

    if 'despensa' not in st.session_state: 
        st.session_state.despensa = obtener_despensa_real()
    
    nuevo_item = st.text_input("añadir ingrediente:")
    if st.button("añadir"):
        if guardar_en_sheets(nuevo_item):
            st.session_state.despensa.append(nuevo_item.lower())
            st.success(f"¡{nuevo_item} guardado!")

    st.write("---")
    for item in st.session_state.despensa:
        st.write(f"✅ {item}")

with tab2:
    st.header("📅 Planificador de menús")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✨ menú creativo (libre)"):
            with st.spinner("creando menú sin límites..."):
                st.session_state.menu = generar_menu()
    
    with col2:
        if st.button("♻️ menú de aprovechamiento"):
            if not st.session_state.get('despensa'):
                st.warning("la despensa parece vacía.")
            else:
                with st.spinner("optimizando tu despensa..."):
                    st.session_state.menu = generar_menu(st.session_state.despensa)
            
    if 'menu' in st.session_state:
        for dia, comidas in st.session_state.menu.items():
            with st.expander(f"📅 {dia}"):
                st.write(f"**🍽️ comida:** {comidas['comida']}")
                st.write(f"**🌙 cena:** {comidas['cena']}")

with tab3:
    st.header("📸 Lector de tickets")
    archivo = st.file_uploader("sube tu ticket", type=["png", "jpg", "jpeg"])
    
    if archivo:
        if st.button("analizar ticket"):
            with st.spinner("leyendo..."):
                try:
                    bytes_data = archivo.getvalue()
                    prompt_ticket = "extrae los nombres de los productos. devuelve solo lista json de strings en minúsculas."
                    response = model.generate_content([{"mime_type": "image/jpeg", "data": bytes_data}, prompt_ticket])
                    st.session_state.productos_detectados = json.loads(response.text.replace("```json", "").replace("```", "").strip())
                    st.rerun()
                except Exception as e:
                    st.error(f"error: {e}")

    if 'productos_detectados' in st.session_state:
        st.subheader("✅ valida los productos:")
        productos_editados = []
        for i, prod in enumerate(st.session_state.productos_detectados):
            nuevo_valor = st.text_input(f"producto {i+1}", value=prod, key=f"tk_{i}")
            productos_editados.append(nuevo_valor)
        
        if st.button("confirmar y filtrar"):
            for item in productos_editados:
                if guardar_en_sheets(item) == True:
                    st.session_state.despensa.append(item.lower())
            del st.session_state.productos_detectados
            st.rerun()
