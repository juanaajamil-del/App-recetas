import streamlit as st
import google.generativeai as genai
import json
import requests

# 1. Configuración
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
URL_API = "https://script.google.com/macros/s/AKfycbzo01XOpLx8KjumxpUAuoyYoPzy86OWVlftmfU-vslNcbGZf0B8HX7ASdnsrfDD-Ls49w/exec"

st.set_page_config(page_title="Despensa Inteligente", page_icon="🍳")
st.title("🍳 Mi Despensa Inteligente")

# 2. Funciones de comunicación
def modificar_despensa(ingrediente, cantidad, accion):
    datos = {"ingrediente": ingrediente, "cantidad": cantidad, "action": accion}
    try:
        response = requests.post(URL_API, json=datos)
        return response.status_code == 200
    except:
        return False

def generar_menu_semanal():
    prompt = """
    Eres un experto en nutrición y ahorro. Genera un menú semanal para 7 días optimizando ingredientes comunes.
    Devuélveme la respuesta ÚNICAMENTE en formato JSON:
    {
      "menu": {"Lunes": "...", "Martes": "...", ...},
      "lista_compra_total": ["ingrediente1", "ingrediente2", ...]
    }
    """
    response = model.generate_content(prompt)
    return json.loads(response.text.replace("```json", "").replace("```", ""))

# 3. Interfaz Principal
if st.button("Generar menú semanal optimizado"):
    with st.spinner("La IA está calculando el menú más económico..."):
        data = generar_menu_semanal()
        st.session_state.menu_data = data
        st.rerun()

if 'menu_data' in st.session_state:
    st.subheader("Tu menú semanal")
    st.write(st.session_state.menu_data["menu"])
    
    st.subheader("🛒 Lista de la compra")
    st.write(st.session_state.menu_data["lista_compra_total"])
    
    if st.button("Añadir toda la lista a mi despensa"):
        for item in st.session_state.menu_data["lista_compra_total"]:
            modificar_despensa(item, 1, "add")
        st.success("¡Despensa actualizada en Google Sheets!")
