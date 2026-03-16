import streamlit as st
import google.generativeai as genai
import json
import requests  # <-- Importamos requests para conectar con tu Sheet

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Chef Inteligente Pro", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('models/gemini-3-flash-preview')

# Tu URL de Google Apps Script
URL_API = "https://script.google.com/macros/s/AKfycbzo01XOpLx8KjumxpUAuoyYoPzy86OWVlftmfU-vslNcbGZf0B8HX7ASdnsrfDD-Ls49w/exec"

# --- FUNCIONES DE CONEXIÓN ---
def guardar_en_sheets(ingrediente, cantidad="1"):
    """Envía un ingrediente a tu Google Sheets"""
    try:
        response = requests.post(URL_API, json={"ingrediente": ingrediente, "cantidad": cantidad, "action": "add"})
        return response.status_code == 200
    except:
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
            st.success(f"{nuevo_item} añadido.")
    
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
    archivo = st.file_uploader("Sube foto de tu ticket", type=["png", "jpg"])
    if archivo:
        st.image(archivo, use_container_width=True)
        if st.button("Procesar Ticket"):
            st.info("Analizando ticket con Gemini Vision... (Esta función requiere pasar el archivo al modelo)")
