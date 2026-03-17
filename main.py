import streamlit as st
import google.generativeai as genai
import json
import requests
from PIL import Image
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Chef Inteligente Pro", layout="wide")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash-exp')

URL_API = "https://script.google.com/macros/s/AKfycbwxRVRKIPux8LEnKPe2kgtTGLuT1iZXCmOxCHV73Gb0l0UiA8-CBcEPipTwRpQF222O6g/exec"

# --- FUNCIONES DE CONEXIÓN ---

def guardar_en_sheets(ingrediente):
    """Clasifica con IA, filtra no comestibles y envía a Google Sheets"""
    try:
        # 1. La IA clasifica y decide si es comestible
        prompt = f"""Analiza el producto: '{ingrediente}'.
        Determina si es un producto alimenticio.
        Responde exclusivamente en formato JSON: {{"es_comestible": true/false, "categoria": "..."}}
        Categorías posibles: Verdura, Carne, Lácteo, Fruta, Granos, Limpieza, Otros.
        Si es un producto de limpieza, bolsa, o no comestible, marca es_comestible como false."""
        
        response = model.generate_content(prompt)
        resultado = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        
        if not resultado.get("es_comestible", False):
            st.info(f"Omitido: '{ingrediente}' no es un producto alimenticio.")
            return "omitido"

        # 2. Enviamos a Google
        datos = {"ingrediente": ingrediente, "categoria": resultado["categoria"]}
        response = requests.post(URL_API, json=datos, timeout=10)
        
        return True if response.status_code == 200 else False
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def generar_menu():
    prompt = """Genera un menú semanal (Lunes-Domingo) con Comida y Cena. Devuelve SÓLO JSON:
    {"Lunes": {"Comida": "...", "Cena": "..."}, "Martes": {...}, ...}"""
    response = model.generate_content(prompt)
    texto = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)

# --- ESTILO VISUAL ---
st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; width: 100%; border: 1px solid #FF4B4B; }
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
        res = guardar_en_sheets(nuevo_item)
        if res == True:
            st.session_state.despensa.append(nuevo_item)
            st.success(f"¡{nuevo_item} añadido!")
        elif res == False:
            st.error("Error al sincronizar.")

    for item in st.session_state.despensa:
        st.write(f"✅ {item}")

with tab2:
    st.header("📅 Menú de la semana")
    if st.button("Generar Menú"):
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
        img = Image.open(archivo)
        st.image(img, caption="Ticket subido", use_container_width=True)
        
        if st.button("Analizar Ticket"):
            with st.spinner("Leyendo ticket con IA..."):
                try:
                    bytes_data = archivo.getvalue()
                    # Pedimos explícitamente el formato y forzamos a que no dé explicaciones
                    prompt_ticket = "Extrae los nombres de los productos de este ticket. Devuelve exclusivamente una lista en formato JSON de strings, sin texto adicional. Ejemplo: [\"manzanas\", \"detergente\"]"
                    
                    response = model.generate_content([
                        {"mime_type": "image/jpeg", "data": bytes_data},
                        prompt_ticket
                    ])
                    
                    # Limpieza agresiva de la respuesta
                    texto_raw = response.text
                    if "```json" in texto_raw:
                        texto_limpio = texto_raw.split("```json")[1].split("```")[0].strip()
                    elif "```" in texto_raw:
                        texto_limpio = texto_raw.split("```")[1].split("```")[0].strip()
                    else:
                        texto_limpio = texto_raw.strip()
                    
                    st.session_state.productos_detectados = json.loads(texto_limpio)
                    st.rerun() # Recargamos para mostrar los inputs de validación
                except Exception as e:
                    st.error(f"Error al procesar el ticket: {e}")
                    st.write("Respuesta de la IA (para depurar):", response.text if 'response' in locals() else "Sin respuesta")

    if 'productos_detectados' in st.session_state:
        st.subheader("✅ Valida los productos:")
        # Creamos una copia para editar
        productos_editados = []
        for i, prod in enumerate(st.session_state.productos_detectados):
            nuevo_valor = st.text_input(f"Producto {i+1}", value=prod, key=f"ticket_prod_{i}")
            productos_editados.append(nuevo_valor)
        
        if st.button("Confirmar y filtrar"):
            exitos = 0
            for item in productos_editados:
                res = guardar_en_sheets(item)
                if res == True:
                    st.session_state.despensa.append(item)
                    exitos += 1
            
            if exitos > 0:
                st.success(f"¡Sincronizados {exitos} productos comestibles!")
            
            # Limpiamos la lista de detectados tras procesar
            del st.session_state.productos_detectados
            st.rerun()
