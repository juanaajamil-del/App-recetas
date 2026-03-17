import streamlit as st
import google.generativeai as genai
import json
import requests
from PIL import Image
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Chef Inteligente Pro", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Usamos el modelo estable que te funcionó
model = genai.GenerativeModel('gemini-2.5-flash')

URL_API = "https://script.google.com/macros/s/AKfycbwxRVRKIPux8LEnKPe2kgtTGLuT1iZXCmOxCHV73Gb0l0UiA8-CBcEPipTwRpQF222O6g/exec"

# --- FUNCIONES DE CONEXIÓN ---

def obtener_despensa_real():
    """lee los productos directamente desde google sheets"""
    try:
        # Añadimos un parámetro para evitar el caché del navegador
        response = requests.get(URL_API, params={"t": "123"}, timeout=15)
        if response.status_code == 200:
            return [str(item).lower() for item in response.json() if item]
        return []
    except Exception:
        return []

def procesar_lote_ingredientes(lista_texto):
    """toma una lista de texto, la clasifica y la envía a la nube en un solo paso"""
    if not lista_texto.strip():
        return
    
    try:
        # una sola llamada a la ia para clasificar toda la lista
        prompt = f"""analiza esta lista de productos: {lista_texto}.
        determina cuáles son comestibles. responde solo json:
        {{"items": [{{"nombre": "...", "comestible": true/false, "cat": "..."}}, ...]}}"""
        
        response = model.generate_content(prompt)
        datos = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        
        exitos = 0
        for item in datos.get("items", []):
            if item["comestible"]:
                # enviamos a google sheets
                payload = {"ingrediente": item["nombre"].lower(), "categoria": item["cat"].lower()}
                requests.post(URL_API, json=payload, timeout=10)
                st.session_state.despensa.append(item["nombre"].lower())
                exitos += 1
            else:
                st.info(f"omitido: {item['nombre']} (no es un alimento)")
        
        if exitos > 0:
            st.success(f"¡se han añadido {exitos} productos correctamente!")
            
    except Exception as e:
        st.error(f"error al procesar la lista: {e}")

def generar_menu(ingredientes=None):
    if ingredientes:
        contexto = f"tengo estos ingredientes: {', '.join(ingredientes)}. haz un menú de aprovechamiento."
    else:
        contexto = "haz un menú variado y creativo."

    prompt = f"""{contexto} genera un menú semanal (lunes-domingo) con comida y cena en minúsculas. 
    devuelve sólo json: {{"lunes": {{"comida": "...", "cena": "..."}}, ...}}"""
    
    response = model.generate_content(prompt)
    return json.loads(response.text.replace("```json", "").replace("```", "").strip())

# --- INTERFAZ ---
st.title("🍳 Chef Inteligente Pro")
tab1, tab2, tab3 = st.tabs(["🛒 Despensa", "📅 Menú Semanal", "📸 Ticket"])

with tab1:
    st.header("🛒 Mi despensa")
    
    col_sync, col_info = st.columns([1, 3])
    with col_sync:
        if st.button("🔄 sincronizar nube"):
            st.session_state.despensa = obtener_despensa_real()
            st.rerun()

    if 'despensa' not in st.session_state: 
        st.session_state.despensa = obtener_despensa_real()
    
    # NUEVA FUNCIÓN: ENTRADA POR LOTE
    st.subheader("añadir varios ingredientes")
    texto_lote = st.text_area("escribe aquí los productos separados por comas o líneas (ej: tomates, leche, detergente...)", placeholder="ej: manzanas\npan\naceite")
    
    if st.button("procesar y enviar lista"):
        with st.spinner("la ia está clasificando tu lista..."):
            procesar_lote_ingredientes(texto_lote)

    st.write("---")
    st.write("**en la despensa actualmente:**")
    for item in st.session_state.despensa:
        st.write(f"✅ {item}")

with tab2:
    st.header("📅 Planificador")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✨ menú creativo"):
            st.session_state.menu = generar_menu()
    with c2:
        if st.button("♻️ menú aprovechamiento"):
            st.session_state.menu = generar_menu(st.session_state.get('despensa', []))
            
    if 'menu' in st.session_state:
        for dia, comidas in st.session_state.menu.items():
            with st.expander(f"📅 {dia}"):
                st.write(f"**comida:** {comidas['comida']}")
                st.write(f"**cena:** {comidas['cena']}")

with tab3:
    st.header("📸 Lector de tickets")
    archivo = st.file_uploader("sube tu ticket", type=["png", "jpg", "jpeg"])
    if archivo:
        if st.button("analizar ticket"):
            with st.spinner("leyendo..."):
                img_data = archivo.getvalue()
                res = model.generate_content([{"mime_type": "image/jpeg", "data": img_data}, "extrae productos en lista json de strings minúsculas."])
                st.session_state.productos_detectados = json.loads(res.text.replace("```json", "").replace("```", "").strip())
                st.rerun()

    if 'productos_detectados' in st.session_state:
        st.subheader("valida y envía")
        # los mostramos en un área de texto para que sea rápido editar si la ia falló
        texto_editable = st.text_area("edita la lista si es necesario:", value=", ".join(st.session_state.productos_detectados))
        if st.button("confirmar y guardar todo"):
            procesar_lote_ingredientes(texto_editable)
            del st.session_state.productos_detectados
            st.rerun()
