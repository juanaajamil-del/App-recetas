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

def generar_menu_completo(ingredientes_dict=None):
    # Convertimos las llaves del diccionario en una lista para el prompt
    lista_ing = list(ingredientes_dict.keys()) if ingredientes_dict else []
    tipo = f"de aprovechamiento usando preferiblemente: {', '.join(lista_ing)}" if lista_ing else "creativo y libre"
    
    prompt = f'genera un menú semanal completo (lunes a domingo, comida y cena) {tipo}. usa solo minúsculas. responde solo json: {{"lunes": {{"comida": "...", "cena": "..."}}, "martes": {{...}}, ...}}'
    res = model.generate_content(prompt)
    return json.loads(res.text.replace("```json", "").replace("```", "").strip())

def generar_lista_compra(menu_final, despensa_dict):
    lista_ing = list(despensa_dict.keys())
    prompt = f'menú: {json.dumps(menu_final)}. tengo en despensa: {", ".join(lista_ing)}. ¿qué ingredientes me faltan para completar este menú? responde solo una lista json de strings en minúsculas.'
    res = model.generate_content(prompt)
    return json.loads(res.text.replace("```json", "").replace("```", "").strip())

# --- 2. INICIALIZACIÓN DE ESTADO ---
if 'despensa' not in st.session_state:
    st.session_state.despensa = obtener_despensa_real()

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
    if st.button("procesar e insertar"): 
        with st.spinner("guardando en la nube..."):
            procesar_lote_ingredientes(texto_lote)

    st.write("---")
    st.subheader("stock actual (cantidades sumadas)")
    if st.session_state.despensa and isinstance(st.session_state.despensa, dict):
        for producto, cantidad in st.session_state.despensa.items():
            col_txt, col_del = st.columns([4, 1])
            with col_txt:
                st.write(f"✅ **{producto}** (x{int(cantidad)})")
            with col_del:
                # Usamos el nombre como key; el JS borrará todas las filas de ese nombre
                if st.button("🗑️", key=f"del_{producto}"):
                    payload = {"tipo": "borrar_ingrediente", "ingrediente": producto}
                    requests.post(URL_API, json=payload)
                    st.rerun()
    else:
        st.info("la despensa está vacía o no se pudo cargar.")

with t2:
    st.header("📅 planificador rápido")
    st.info("genera una propuesta completa y selecciona los platos que más te gusten.")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✨ menú creativo"):
            with st.spinner("creando platos nuevos..."):
                st.session_state.p_creativa = generar_menu_completo()
    with c2:
        if st.button("♻️ menú aprovechamiento"):
            with st.spinner("revisando tu despensa..."):
                st.session_state.p_aprovecho = generar_menu_completo(st.session_state.despensa)

    col_izq, col_der = st.columns(2)
    configs = [("p_creativa", col_izq, "creativa"), ("p_aprovecho", col_der, "aprovechamiento")]
    
    for key, col, nombre in configs:
        with col:
            if key in st.session_state:
                st.subheader(f"opción {nombre}")
                for dia, platos in st.session_state[key].items():
                    with st.expander(f"📅 {dia}"):
                        st.write(f"🍴 {platos['comida']}")
                        if st.button(f"usar comida {dia}", key=f"btn_c_{key}_{dia}"):
                            st.session_state.menu_oficial[dia]["comida"] = platos['comida']
                        st.write(f"🌙 {platos['cena']}")
                        if st.button(f"usar cena {dia}", key=f"btn_n_{key}_{dia}"):
                            st.session_state.menu_oficial[dia]["cena"] = platos['cena']

    st.write("---")
    st.subheader("📍 selección para mi semana")
    st.table(st.session_state.menu_oficial)
    
    if st.button("💾 finalizar y guardar menú"):
        with st.spinner("sincronizando menú y lista de compra..."):
            payload = {"tipo": "menu_completo", "contenido": st.session_state.menu_oficial}
            requests.post(URL_API, json=payload)
            st.session_state.lista_compra = generar_lista_compra(st.session_state.menu_oficial, st.session_state.despensa)
            st.success("¡menú guardado en google sheets!")

with t3:
    st.header("📝 mi semana")
    if 'lista_compra' in st.session_state:
        cm, cl = st.columns([2, 1])
        with cm:
            for dia, platos in st.session_state.menu_oficial.items():
                with st.expander(f"📅 {dia}"):
                    st.write(f"**comida:** {platos['comida']}")
                    st.write(f"**cena:** {platos['cena']}")
        with cl:
            st.subheader("🛒 faltas")
            for ing in st.session_state.lista_compra: 
                st.checkbox(ing, key=f"lc_{ing}")
    else:
        st.info("primero confirma tu menú en el planificador.")

with t4:
    st.header("📸 lector de tickets")
    archivo = st.file_uploader("sube una foto del ticket de compra", type=["png", "jpg", "jpeg"])
    if archivo:
        if st.button("analizar ticket"):
            with st.spinner("la ia está leyendo el ticket..."):
                img_data = archivo.getvalue()
                res = model.generate_content([
                    {"mime_type": "image/jpeg", "data": img_data}, 
                    "extrae los productos de este ticket. responde solo una lista json de strings en minúsculas."
                ])
                st.session_state.detectados = json.loads(res.text.replace("```json", "").replace("```", "").strip())
                st.rerun()

    if 'detectados' in st.session_state:
        txt = st.text_area("valida y edita los productos detectados:", value=", ".join(st.session_state.detectados))
        if st.button("añadir todo a la despensa"):
            procesar_lote_ingredientes(txt)
            del st.session_state.detectados
            st.rerun()
