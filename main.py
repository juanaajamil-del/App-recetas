import streamlit as st
import pandas as pd
import requests

# URL de tu "puente" de Google Apps Script
URL_API = "https://script.google.com/macros/s/AKfycbzo01XOpLx8KjumxpUAuoyYoPzy86OWVlftmfU-vslNcbGZf0B8HX7ASdnsrfDD-Ls49w/exec"

st.set_page_config(page_title="Mi Despensa Inteligente", page_icon="🍳")

st.title("🍳 Mi Despensa Inteligente")

# Función para modificar datos vía tu Web App
def modificar_despensa(ingrediente, cantidad, accion):
    datos = {"ingrediente": ingrediente, "cantidad": cantidad, "action": accion}
    try:
        response = requests.post(URL_API, json=datos)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error al conectar con la despensa: {e}")
        return False

# Interfaz de gestión
st.subheader("Control de inventario")
col1, col2, col3 = st.columns(3)

with col1:
    ing = st.text_input("Ingrediente")
with col2:
    cant = st.number_input("Cantidad", min_value=0)
with col3:
    st.write("Acciones:")
    if st.button("Añadir"):
        if modificar_despensa(ing, cant, "add"):
            st.success("¡Añadido!")
    if st.button("Actualizar"):
        if modificar_despensa(ing, cant, "update"):
            st.success("¡Actualizado!")

# Visualización de cómo fluyen los datos entre tu App y la Hoja
st.write("---")
st.info("Nota: Tu aplicación envía los datos a través del script que configuramos, manteniendo tu hoja siempre al día.")



# Aquí es donde integrarás tu lógica de Gemini para el menú
st.subheader("Generar menú semanal")
if st.button("Cocinar algo hoy"):
    st.write("Analizando tu despensa...")
    # Aquí puedes llamar a tu modelo de IA para sugerir platos
