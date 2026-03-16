import streamlit as st
import pandas as pd
import requests

# ... (URL_API y función modificar_despensa igual que antes)

st.title("🍳 Mi Despensa Inteligente")

# 1. Simulación de datos si la despensa está vacía
if 'despensa' not in st.session_state:
    st.session_state.despensa = pd.DataFrame(columns=["Ingrediente", "Cantidad"])

# 2. Interfaz inteligente
st.subheader("Tu menú de la semana")

if st.session_state.despensa.empty:
    st.warning("¡Tu despensa está vacía! Generaré un menú sugerido y una lista de la compra.")
    if st.button("Generar menú desde cero"):
        st.write("IA: Te sugiero un menú mediterráneo. Ingredientes necesarios: Arroz, Tomate, Pollo.")
        st.session_state.lista_compra = ["Arroz", "Tomate", "Pollo"]
else:
    st.success("Analizando tu despensa actual...")
    # Aquí llamaremos a Gemini en el siguiente paso

# 3. Gestión de compra
if 'lista_compra' in st.session_state:
    st.subheader("🛒 Lista de la compra")
    st.write(st.session_state.lista_compra)
    if st.button("Añadir todo a la despensa"):
        for item in st.session_state.lista_compra:
            modificar_despensa(item, 1, "add")
        st.success("¡Despensa actualizada!")
