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

URL_API = "https://script.google.com/macros/s/AKfycbwPgCPBDH_G__oUNXjcvnHytHg9aeL3DmmtDcMiPvxhs04t6cL9jAgHygYtCK2MztcfaQ/exec"

# --- 1. FUNCIONES DE APOYO ---

def obtener_despensa_real():
    try:
        response = requests.get(URL_API, params={"t": "refresh"}, timeout=15)
        if response.status_code == 200:
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
                    "ingrediente": item["nombre"].lower().strip(), 
                    "categoria": item["cat"].lower()
                })
        st.success("¡productos guardados!")
        st.session_state.despensa = obtener_despensa_real()
        st.rerun()
    except:
        st.error("error al procesar lote.")

def generar_menu_completo(ingredientes_dict=None):
    lista_ing = list(ingredientes_dict.keys()) if ingredientes_dict else []
    tipo = f"de aprovechamiento usando: {', '.join(lista_ing)}" if lista_ing else "creativo y libre"
    
    prompt = f'genera un menú semanal completo {tipo}. responde solo json minúsculas con estas llaves exactas: "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo". cada día debe tener "comida" y "cena".'
    res = model.generate_content(prompt)
    # Limpieza de posibles marcas de markdown en la respuesta de la IA
    clean_res = res.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_res)

def generar_lista_compra(menu_final, despensa_dict):
    prompt = f'menú: {json.dumps(menu_final)}. despensa: {", ".join(despensa_dict.keys())}. responde solo una lista json de strings con lo que falta.'
    res = model.generate_content(prompt)
    clean_res = res.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_res)

# --- 2. INICIALIZACIÓN ---
dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

if 'despensa' not in st.session_state:
    st.session_state.despensa = obtener_despensa_real()

if 'menu_oficial' not in st.session_state: 
    st.session_state.menu_oficial = {d: {"comida": "vacio", "cena": "vacio"} for d in dias_semana}

# --- 3. INTERFAZ ---
st.title("🍳 Chef Inteligente Pro")
t1, t2, t3, t4 = st.tabs(["🛒 Despensa", "📅 Planificador", "📝 Mi Semana", "📸 Ticket"])

with t1:
    st.header("🛒 mi despensa")
    if st.button("🔄 sincronizar"):
        st.session_state.despensa = obtener_despensa_real()
        st.rerun()
    
    texto_lote = st.text_area("añadir ingredientes:")
    if st.button("procesar e insertar"): 
        procesar_lote_ingredientes(texto_lote)

    st.write("---")
    if st.session_state.despensa and isinstance(st.session_state.despensa, dict):
        for producto, cantidad in st.session_state.despensa.items():
            col_txt, col_del = st.columns([4, 1])
            col_txt.write(f"✅ **{producto}** (x{int(cantidad)})")
            if col_del.button("🗑️", key=f"del_{producto}"):
                requests.post(URL_API, json={"tipo": "borrar_ingrediente", "ingrediente": producto})
                st.rerun()

with t2:
    st.header("📅 planificador rápido")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✨ menú creativo"):
            st.session_state.p_creativa = generar_menu_completo()
    with c2:
        if st.button("♻️ menú aprovechamiento"):
            st.session_state.p_aprovecho = generar_menu_completo(st.session_state.despensa)

    col_izq, col_der = st.columns(2)
    configs = [("p_creativa", col_izq, "creativa"), ("p_aprovecho", col_der, "aprovechamiento")]
    
    for key, col, nombre in configs:
        with col:
            if key in st.session_state:
                st.subheader(f"opción {nombre}")
                # Usamos los días oficiales para evitar errores de tildes o nombres raros de la IA
                for dia in dias_semana:
                    if dia in st.session_state[key]:
                        platos = st.session_state[key][dia]
                        with st.expander(f"📅 {dia.upper()}"):
                            st.write(f"🍴 {platos.get('comida', 'no generado')}")
                            if st.button(f"usar comida", key=f"btn_c_{key}_{dia}"):
                                st.session_state.menu_oficial[dia]["comida"] = platos.get('comida')
                            st.write(f"🌙 {platos.get('cena', 'no generado')}")
                            if st.button(f"usar cena", key=f"btn_n_{key}_{dia}"):
                                st.session_state.menu_oficial[dia]["cena"] = platos.get('cena')

    st.write("---")
    st.subheader("📍 selección actual")
    st.table(st.session_state.menu_oficial)
    
    if st.button("💾 finalizar y guardar menú"):
        payload = {"tipo": "menu_completo", "contenido": st.session_state.menu_oficial}
        requests.post(URL_API, json=payload)
        st.session_state.lista_compra = generar_lista_compra(st.session_state.menu_oficial, st.session_state.despensa)
        st.success("¡menú guardado!")

with t3:
    st.header("📝 mi semana")
    if 'lista_compra' in st.session_state:
        cm, cl = st.columns([2, 1])
        with cm:
            for dia, platos in st.session_state.menu_oficial.items():
                with st.expander(f"📅 {dia}"):
                    st.write(f"**comida:** {platos['comida']}\n\n**cena:** {platos['cena']}")
        with cl:
            st.subheader("🛒 faltas")
            for ing in st.session_state.lista_compra: st.checkbox(ing, key=f"lc_{ing}")

with t4:
    archivo = st.file_uploader("sube ticket", type=["png", "jpg", "jpeg"])
    if archivo:
        if st.button("analizar ticket"):
            img_data = archivo.getvalue()
            res = model.generate_content([{"mime_type": "image/jpeg", "data": img_data}, "extrae productos lista json strings minúsculas."])
            st.session_state.detectados = json.loads(res.text.replace("```json", "").replace("```", "").strip())
            st.rerun()

    if 'detectados' in st.session_state:
        txt = st.text_area("valida:", value=", ".join(st.session_state.detectados))
        if st.button("añadir todo"):
            procesar_lote_ingredientes(txt)
            del st.session_state.detectados
            st.rerun()
