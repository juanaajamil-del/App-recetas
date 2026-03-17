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

URL_API = "https://script.google.com/macros/s/AKfycbwxRVRKIPux8LEnKPe2kgtTGLuT1iZXCmOxCHV73Gb0l0UiA8-CBcEPipTwRpQF222O6g/exec"

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
        prompt = f"analiza: {lista_texto}. responde solo json minúsculas: {{"items": [{{"nombre": "...", "comestible": true, "cat": "..."}}]}}"
        res = model.generate_content(prompt)
        datos = json.loads(res.text.replace("```json", "").replace("```", "").strip())
        for item in datos.get("items", []):
            if item.get("comestible"):
                requests.post(URL_API, json={"ingrediente": item["nombre"].lower(), "categoria": item["cat"].lower()})
                if 'despensa' in st.session_state: st.session_state.despensa.append(item["nombre"].lower())
        st.success("¡productos guardados!")
    except: st.error("error al procesar lote.")

def generar_menu_completo(ingredientes=None):
    tipo = f"de aprovechamiento usando: {', '.join(ingredientes)}" if ingredientes else "creativo y libre"
    prompt = f"""genera un menú semanal completo (lunes a domingo, comida y cena) {tipo}. 
    usa solo minúsculas. responde solo json:
    {{"lunes": {{"comida": "...", "cena": "..."}}, "martes": {{...}}, ...}}"""
    res = model.generate_content(prompt)
    return json.loads(res.text.replace("```json", "").replace("```", "").strip())

def generar_lista_compra(menu_final, despensa_actual):
    prompt = f"menú: {json.dumps(menu_final)}. despensa: {', '.join(despensa_actual)}. ¿qué falta? responde lista json de strings minúsculas."
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
    if st.button("🔄 sincronizar"):
        st.session_state.despensa = obtener_despensa_real()
        st.rerun()
    texto_lote = st.text_area("añadir ingredientes:")
    if st.button("procesar lote"): procesar_lote_ingredientes(texto_lote)
    st.write("---")
    for item in st.session_state.despensa: st.write(f"✅ {item}")

with t2:
    st.header("📅 planificador rápido")
    c1, c2 = st.columns(2)
    
    with c1:
        if st.button("✨ generar menú creativo completo"):
            st.session_state.propuesta_creativa = generar_menu_completo()
    with c2:
        if st.button("♻️ generar menú aprovechamiento completo"):
            st.session_state.propuesta_aprovecho = generar_menu_completo(st.session_state.despensa)

    col_izq, col_der = st.columns(2)
    
    # Mostrar propuestas para elegir
    propuestas = [("propuesta_creativa", col_izq, "creativa"), ("propuesta_aprovecho", col_der, "aprovechamiento")]
    for key, col, nombre in propuestas:
        with col:
            if key in st.session_state:
                st.subheader(f"opción {nombre}")
                for dia, platos in st.session_state[key].items():
                    with st.expander(f"📅 {dia}"):
                        st.write(f"🍴 {platos['comida']}")
                        if st.button(f"usar comida {dia}", key=f"c_{key}_{dia}"):
                            st.session_state.menu_oficial[dia]["comida"] = platos['comida']
                        st.write(f"🌙 {platos['cena']}")
                        if st.button(f"usar cena {dia}", key=f"n_{key}_{dia}"):
                            st.session_state.menu_oficial[dia]["cena"] = platos['cena']

    st.write("---")
    st.subheader("📍 tu menú oficial seleccionado")
    st.table(st.session_state.menu_oficial)
    
    if st.button("💾 finalizar y generar lista de compra"):
        st.session_state.lista_compra = generar_lista_compra(st.session_state.menu_oficial, st.session_state.despensa)
        st.success("¡listo! revisa la pestaña 'mi semana'")

with t3:
    st.header("📝 mi semana")
    if 'lista_compra' in st.session_state:
        cm, cl = st.columns([2, 1])
        with cm:
            for dia, platos in st.session_state.menu_oficial.items():
                with st.expander(f"📅 {dia}"):
                    st.write(f"**comida:** {platos['comida']}\n\n**cena:** {platos['cena']}")
        with cl:
            st.subheader("🛒 lista compra")
            for ing in st.session_state.lista_compra: st.checkbox(ing, key=f"lc_{ing}")
    else: st.info("selecciona platos en el planificador.")

with t4:
    archivo = st.file_uploader("sube ticket")
    if archivo:
        if st.button("analizar"):
            img_data = archivo.getvalue()
            res = model.generate_content([{"mime_type": "image/jpeg", "data": img_data}, "extrae productos lista json strings minúsculas."])
            st.session_state.detectados = json.loads(res.text.replace("```json", "").replace("```", "").strip())
    if 'detectados' in st.session_state:
        txt = st.text_area("valida:", value=", ".join(st.session_state.detectados))
        if st.button("guardar"):
            procesar_lote_ingredientes(txt)
            del st.session_state.detectados
            st.rerun()
