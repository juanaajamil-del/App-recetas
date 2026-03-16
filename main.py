import streamlit as st
import google.generativeai as genai
import json
import requests
from PIL import Image
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Chef Inteligente Pro", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('models/gemini-3-flash-preview')

# Tu URL de Google Apps Script
URL_API = "https://script.google.com/macros/s/AKfycbyqRDVhhwL7jrR60IqUVa23BbJblCRh6wmhFYvPSwnLxQqbYgQvNwXMi2O5BYs_68kbdw/exec"

# --- FUNCIONES DE CONEXIÓN ---
def guardar_en_sheets(ingrediente, cantidad="1"):
    """Envía un ingrediente a tu Google Sheets con diagnóstico de errores"""
    try:
        datos = {"ingrediente": ingrediente, "cantidad": cantidad, "action": "add"}
        response = requests.post(URL_API, json=datos, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            # Si Google responde pero con error, lo mostramos
            st.error(f"Error en Google Sheets ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        # Si ni siquiera hay conexión, lo mostramos
        st.error(f"Error de conexión con el script: {e}")
        return False

def generar_menu():
    prompt = """Genera un menú semanal (Lunes-Domingo) con Comida y Cena. Devuelve SÓLO JSON:
    {"Lunes": {"Comida": "...", "Cena": "..."}, "Martes": {...}, ...}"""
    response = model.generate_content(prompt)
    texto = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)

# --- ESTILO VISUAL PRO ---
st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; width: 100%; border: 1px solid #FF4B4B; }
    .stExpander { border-radius: 10px; border: 1px solid #ddd; }
    </style>
""", unsafe_allow_html=True)

# --- INTERFAZ ---
st.title("🍳 Chef Inteligente Pro")
tab1, tab2, tab3 = st.tabs(["🛒 Despensa", "📅 Menú Semanal", "📸 Ticket"])

with tab1:
    st.header("🛒 Mi Despensa")
    if 'despensa' not in st.session_state: st.session_state.despensa = []
    
    nuevo_item = st.text_input("Añadir ingrediente manualmente:")
    if st.button("Añadir"):
        if guardar_en_sheets(nuevo_item):
            st.session_state.despensa.append(nuevo_item)
            st.success(f"{nuevo_item} añadido correctamente a la nube.")
        else:
            st.warning("Se guardó en la app, pero falló el envío a Google Sheets.")
    
    for item in st.session_state.despensa:
        st.write(f"✅ {item}")

with tab2:
    st.header("📅 Menú de la semana")
    if st.button("Generar Menú Semanal"):
        with st.spinner("Creando tu menú gourmet..."):
            st.session_state.menu = generar_menu()
            
    if 'menu' in st.session_state:
        for dia, comidas in st.session_state.menu.items():
            with st.expander(f"📅 {dia}"):
                st.write(f"**🍽️ Comida:** {comidas['Comida']}")
                st.write(f"**🌙 Cena:** {comidas['Cena']}")

with tab3:
    st.header("📸 Lector de Tickets")
    archivo = st.file_uploader("Sube foto de tu ticket", type=["png", "jpg", "jpeg"])
    
    if archivo:
        # Corregir rotación visual (opcional, ajusta si sale girada)
        img = Image.open(archivo)
        st.image(img, caption="Ticket subido", use_container_width=True)
        
        if st.button("Analizar Ticket"):
            with st.spinner("Leyendo ticket con IA..."):
                bytes_data = archivo.getvalue()
                response = model.generate_content([
                    {"mime_type": "image/jpeg", "data": bytes_data},
                    "Extrae los productos de este ticket. Devuelve solo una lista JSON de strings."
                ])
                
                try:
                    lista_detectada = json.loads(response.text.replace("```json", "").replace("```", "").strip())
                    st.session_state.productos_detectados = lista_detectada
                except:
                    st.error("No se pudo procesar el formato del ticket.")

    if 'productos_detectados' in st.session_state:
        st.subheader("✅ Valida los productos:")
        for i, prod in enumerate(st.session_state.productos_detectados):
            st.session_state.productos_detectados[i] = st.text_input(f"Prod {i+1}", value=prod)
        
        if st.button("Confirmar y enviar a la nube"):
            exitos = 0
            with st.spinner("Sincronizando con Google Sheets..."):
                for item in st.session_state.productos_detectados:
                    if guardar_en_sheets(item):
                        st.session_state.despensa.append(item)
                        exitos += 1
                
                if exitos > 0:
                    st.success(f"¡Sincronizados {exitos} productos!")
                    del st.session_state.productos_detectados
                    st.rerun()
