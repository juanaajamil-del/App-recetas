import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Mi Menú Inteligente", page_icon="🥗")

st.title("🥗 Generador de Menús Inteligente")
st.subheader("Optimiza tu compra y ahorra dinero")

# --- SECCIÓN DE PERFIL ---
with st.sidebar:
    st.header("Tu Perfil")
    personas = st.number_input("¿Cuántas personas?", min_value=1, max_value=10, value=2)
    presupuesto = st.select_slider("Presupuesto semanal", options=["Bajo", "Medio", "Alto"])
    preferencias = st.multiselect("Preferencias", ["Legumbres", "Pollo", "Pescado", "Pasta", "Verdura"], ["Verdura", "Pollo"])
    odio = st.text_input("Alimentos que NO quiero (ej. Cebolla)")

# --- LÓGICA DE LA APP ---
if st.button("Generar Menú y Lista de la Compra"):
    st.info("Generando plan optimizado...")
    
    # Simulación de menú optimizado (Aquí es donde luego conectaremos con la IA de Gemini)
    # Por ahora, para que pruebes la app, generamos un ejemplo funcional:
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("📅 Menú Semanal")
        menu = {
            "Día": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
            "Comida": ["Lentejas con verduras", "Pollo al curry", "Ensalada de lentejas (Sobrante)", "Salteado de pollo y brócoli", "Crema de brócoli (Sobrante)"],
            "Cena": ["Tortilla francesa", "Crema de verduras", "Pescado al horno", "Ensalada mixta", "Pizza casera"]
        }
        st.table(pd.DataFrame(menu))
        
    with col2:
        st.warning("🛒 Lista de la Compra (Optimizada)")
        st.write("- **Lentejas:** 1 paquete (usado en 2 platos)")
        st.write("- **Pollo:** 500g (usado en 2 platos)")
        st.write("- **Brócoli:** 1 pieza grande (usado en 2 platos)")
        st.write("- **Huevos:** 1 docena")
        st.caption("Nota: Se han aprovechado los sobrantes del Lunes y Jueves para ahorrar un 20%.")

st.write("---")
st.caption("Usa el menú lateral para ajustar tus preferencias.")
