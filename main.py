import streamlit as st
import google.generativeai as genai
import json
import requests
from PIL import Image
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Chef Inteligente Pro", layout="wide")

# Verificamos que la clave de la API exista
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("falta la clave GOOGLE_API_KEY en los secretos de streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

URL_API = "https://script.google.com/macros/s/AKfycbwxRVRKIPux8LEnKPe2kgtTGLuT1iZXCmOxCHV73Gb0l0UiA8-CBcEPipTwRpQF222O6g/exec"

# --- 1. FUNCIONES DE APOYO ---

def obtener_despensa_real():
    try:
        response = requests.get(URL_API, params={"t": "refresh"}, timeout=15)
        if response.status_code == 200:
            return [str(item).lower() for item in response.json() if item]
        return []
    except:
        return []

def procesar_lote_ingredientes(lista_texto):
    if not lista_texto.strip(): return
    try:
        prompt = f"""analiza estos productos: {lista_texto}. 
        responde solo json: {{"items": [{{"nombre": "...", "comestible": true, "cat": "..."}}, ...]}}
        usa solo minúsculas."""
        res = model.generate_content(prompt)
        datos = json.loads(res.text.replace("```json", "").replace("```", "").strip())
        
        for item in datos.get("items", []):
            if item.get("comestible"):
                payload = {"ingrediente": item["nombre"].lower(), "categoria": item["cat"].lower()}
                requests.post(URL_API, json=payload, timeout=10)
                if 'despensa' in st.session_state:
                    st.session_state.despensa.append(item["nombre"].lower())
        st.success("¡productos guardados!")
    except Exception as e:
        st.error(f"error al procesar: {e}")

def generar_propuestas(ingredientes=None):
    contexto = f"tengo estos ingredientes: {', '.join(ingredientes)}" if ingredientes else "haz propuestas creativas"
    prompt = f"""basado en {contexto}, sugiere 3 platos de comida y 3 de cena. 
    usa solo minúsculas. responde solo json:
    {{"comidas": ["...", "...", "..."], "cenas": ["...", "...", "..."]}}"""
    res = model.generate_content(prompt)
    return json.loads(res.text.replace("```json", "").replace("```", "").strip())

def generar_lista_compra(menu_final, despensa_actual):
    prompt = f"""menú: {json.dumps(menu_final)}. despensa: {', '.join(despensa_actual)}.
    ¿qué ingredientes faltan? responde solo lista json de strings en minúsculas."""
    res = model.generate_content(prompt)
    return json.loads(res.text.replace("```json", "").replace("```", "").strip())

# --- 2. INICIALIZACIÓN DE ESTADOS ---
if 'despensa' not in st.session_state:
    st.session_state.despensa = obtener_despensa_real()
if 'borrador_menu' not in st.session_state:
    st.session_state.borrador_menu = {d: {"comida": "pendiente", "cena": "pendiente"} for d in ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]}

# --- 3. INTERFAZ ---
st.title("🍳 Chef Inteligente Pro")

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Despensa", "📅 Planificador", "📝 Mi Semana", "📸 Ticket"])

with tab1:
    st.header("🛒 mi despensa")
    if st.button("🔄 sincronizar con la nube"):
        st.session_state.despensa = obtener_despensa_real()
        st.rerun()

    texto_lote = st.text_area("añadir varios ingredientes (separados por comas o líneas):")
    if st.button("procesar y enviar lista"):
        procesar_lote_ingredientes(texto_lote)

    st.write("---")
    for item in st.session_state.despensa:
        st.write(f"✅ {item}")

with tab2:
    st.header("📅 diseña tu semana")
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔍 propuestas de aprovechamiento"):
            st.session_state.propuestas = generar_propuestas(st.session_state.despensa)
    with c2:
        if st.button("✨ propuestas creativas"):
            st.session_state.propuestas = generar_propuestas()

    if 'propuestas' in st.session_state:
        col_a, col_b = st.columns(2)
        with col_a:
            p_comida = st.selectbox("elige comida:", st.session_state.propuestas["comidas"])
            dia_c = st.selectbox("día para comida:", dias, key="sel_dia_c")
            if st.button("asignar comida"):
                st.session_state.borrador_menu[dia_c]["comida"] = p_comida
        with col_b:
            p_cena = st.selectbox("elige cena:", st.session_state.propuestas["cenas"])
            dia_n = st.selectbox("día para cena:", dias, key="sel_dia_n")
            if st.button("asignar cena"):
                st.session_state.borrador_menu[dia_n]["cena"] = p_cena

    st.write("---")
    st.subheader("tu borrador actual")
    st.table(st.session_state.borrador_menu)
    
    if st.button("💾 confirmar menú y generar lista"):
        st.session_state.menu_confirmado = st.session_state.borrador_menu.copy()
        st.session_state.lista_compra = generar_lista_compra(st.session_state.menu_confirmado, st.session_state.despensa)
        st.success("¡menú y lista generados en la pestaña 'mi semana'!")

with tab3:
    st.header("📝 mi semana")
    if 'menu_confirmado' in st.session_state:
        col_m, col_l = st.columns([2, 1])
        with col_m:
            for dia, platos in st.session_state.menu_confirmado.items():
                with st.expander(f"📅 {dia}"):
                    st.write(f"**comida:** {platos['comida']}")
                    st.write(f"**cena:** {platos['cena']}")
        with col_l:
            st.subheader("🛒 lista de la compra")
            if 'lista_compra' in st.session_state:
                for ing in st.session_state.lista_compra:
                    st.checkbox(ing, key=f"compra_{ing}")
    else:
        st.info("ve al planificador para diseñar tu semana.")

with tab4:
    st.header("📸 lector de tickets")
    archivo = st.file_uploader("sube tu ticket", type=["png", "jpg", "jpeg"])
    if archivo:
        if st.button("analizar ticket"):
            with st.spinner("leyendo..."):
                img_data = archivo.getvalue()
                res = model.generate_content([{"mime_type": "image/jpeg", "data": img_data}, "extrae productos en lista json de strings minúsculas."])
                st.session_state.productos_detectados = json.loads(res.text.replace("```json", "").replace("```", "").strip())
                st.rerun()

    if 'productos_detectados' in st.session_state:
        texto_editable = st.text_area("edita la lista del ticket:", value=", ".join(st.session_state.productos_detectados))
        if st.button("confirmar y guardar ticket"):
            procesar_lote_ingredientes(texto_editable)
            del st.session_state.productos_detectados
            st.rerun()
