import streamlit as st
import ezdxf
import fitz  # PyMuPDF
import numpy as np
from shapely.geometry import Polygon
from shapely.affinity import translate
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image
import io
import os

# --- PALETA CORPORATIVA WALDY UNIFORMES ---
COLOR_NARANJA_WALDY = "#E9531E"
COLOR_VERDE_WALDY = "#138A36"
COLOR_FONDO_SUAVE = "#F4F6F5"
COLOR_OSCURO = "#1E293B"

# Clasificación cromática por tipo de pieza de corte
COLORES_PIEZAS = {
    "Espalda": {"fill": "#E9531E", "edge": "#9A3412"},
    "Delantero": {"fill": "#138A36", "edge": "#064E3B"},
    "Manga": {"fill": "#F59E0B", "edge": "#92400E"},
    "Cuello / Pretina": {"fill": "#0284C7", "edge": "#075985"},
    "Bolsillo / Detalle": {"fill": "#64748B", "edge": "#1E293B"},
    "Molde PDF": {"fill": "#138A36", "edge": "#E9531E"}
}

# --- CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(
    page_title="Módulo de Corte CAD/CAM | Waldy Uniformes",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(f"""
<style>
    .main {{
        background-color: {COLOR_FONDO_SUAVE};
    }}
    .stButton>button {{
        background-color: {COLOR_NARANJA_WALDY};
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 0.55rem 1.1rem;
        font-size: 15px;
        transition: all 0.25s ease;
    }}
    .stButton>button:hover {{
        background-color: {COLOR_VERDE_WALDY};
        color: white;
    }}
    .header-box {{
        background-color: white;
        padding: 1.2rem 1.8rem;
        border-radius: 12px;
        border-left: 8px solid {COLOR_NARANJA_WALDY};
        border-bottom: 3px solid {COLOR_VERDE_WALDY};
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 1.2rem;
    }}
</style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO Y REINICIO TOTAL ---
if "orden_corte" not in st.session_state:
    st.session_state.orden_corte = []
if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

def reiniciar_sistema():
    st.session_state.orden_corte = []
    st.session_state.reset_counter += 1

# --- ENCABEZADO CORPORATIVO CON LOGO ORIGINAL Y BOTÓN REINICIAR ---
def mostrar_encabezado():
    with st.container():
        st.markdown('<div class="header-box">', unsafe_allow_html=True)
        col_logo, col_titulo, col_reset = st.columns(
            [1.3, 3.7, 1.1], vertical_alignment="center"
        )

        with col_logo:
            rutas_posibles = [
                "logo_waldy.jpeg",
                "logo_waldy.jpg",
                "logo_waldy.png",
                "WhatsApp Image 2026-11-08 at 6.57.34 PM.jpeg"
            ]
            logo_encontrado = None
            for ruta in rutas_posibles:
                if os.path.exists(ruta):
                    logo_encontrado = ruta
                    break

            if logo_encontrado:
                img = Image.open(logo_encontrado)
                st.image(img, use_container_width=True)
            else:
                st.markdown(f"""
                <svg viewBox="0 0 420 265" xmlns="http://www.w3.org/2000/svg"
                     style="width:100%; max-width:220px; display:block; margin:auto;">
                  <rect width="420" height="265" fill="#F8F9FA" rx="6"/>
                  <path d="M22,22 C22,12 38,12 38,22 L38,85
