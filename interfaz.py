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

COLORES_PIEZAS = {
    "Espalda": {"fill": "#E9531E", "edge": "#9A3412"},
    "Delantero": {"fill": "#138A36", "edge": "#064E3B"},
    "Manga": {"fill": "#F59E0B", "edge": "#92400E"},
    "Cuello / Pretina": {"fill": "#0284C7", "edge": "#075985"},
    "Bolsillo / Detalle": {"fill": "#64748B", "edge": "#1E293B"},
    "Molde PDF": {"fill": "#138A36", "edge": "#E9531E"}
}

st.set_page_config(
    page_title="Módulo de Corte CAD/CAM | Waldy Uniformes",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

css_estilos = (
    "<style>"
    f".main {{ background-color: {COLOR_FONDO_SUAVE}; }}"
    f".stButton>button {{ background-color: {COLOR_NARANJA_WALDY}; color: white; font-weight: bold; border-radius: 8px; border: none; padding: 0.55rem 1.1rem; font-size: 15px; }}"
    f".stButton>button:hover {{ background-color: {COLOR_VERDE_WALDY}; color: white; }}"
    f".header-box {{ background-color: white; padding: 1.2rem 1.8rem; border-radius: 12px; border-left: 8px solid {COLOR_NARANJA_WALDY}; border-bottom: 3px solid {COLOR_VERDE_WALDY}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 1.2rem; }}"
    "</style>"
)
st.markdown(css_estilos, unsafe_allow_html=True)

if "orden_corte" not in st.session_state:
    st.session_state.orden_corte = []
if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

def reiniciar_sistema():
    st.session_state.orden_corte = []
    st.session_state.reset_counter += 1

def obtener_svg_waldy():
    p1 = f'<svg viewBox="0 0 420 265" xmlns="http://www.w3.org/2000/svg" style="width:100%; max-width:220px; display:block; margin:auto;">'
    p2 = '<rect width="420" height="265" fill="#F8F9FA" rx="6"/>'
    p3 = f'<path d="M22,22 C22,12 38,12 38,22 L38,85 C38,95 52,95 52,85 L52,55 C52,45 68,45 68,55 L68,85 C68,95 82,95 82,85 L82,22 C82,12 98,12 98,22 L98,88 C98,112 72,118 60,104 C48,118 22,112 22,88 Z" fill="{COLOR_NARANJA_WALDY}"/>'
    p4 = f'<path d="M158,42 C130,42 110,60 110,80 C110,100 130,115 158,115 L164,115 L164,42 Z M148,96 C134,96 126,88 126,79 C126,70 134,61 148,61 L148,96 Z" fill="{COLOR_NARANJA_WALDY}"/>'
    p5 = f'<rect x="176" y="42" width="17" height="73" rx="8" fill="{COLOR_NARANJA_WALDY}"/>'
    p6 = f'<path d="M254,14 L254,42 L248,42 C220,42 204,58 204,79 C204,100 220,115 248,115 L270,115 L270,14 C270,6 254,6 254,14 Z M254,96 L248,96 C232,96 221,89 221,79 C221,69 232,61 248,61 L254,61 Z" fill="{COLOR_NARANJA_WALDY}"/>'
    p7 = f'<path d="M282,48 L282,85 C282,106 298,116 320,116 L326,116 L326,48 C326,40 310,40 310,48 L310,96 C302,96 298,91 298,83 L298,48 C298,40 282,40 282,48 Z" fill="{COLOR_NARANJA_WALDY}"/>'
    p8 = f'<rect x="333" y="42" width="17" height="73" rx="4" fill="{COLOR_NARANJA_WALDY}"/><rect x="333" y="123" width="17" height="22" rx="2" fill="{COLOR_NARANJA_WALDY}"/>'
    p9 = f'<path d="M324,123 L26,123 C20,123 16,127 16,133 L16,240 C16,246 20,250 26,250 L340,250 C346,250 350,246 350,240 L350,153 L327,153 L327,227 L39,227 L39,146 L324,146 Z" fill="{COLOR_VERDE_WALDY}"/>'
    p10 = f'<text x="183" y="207" font-family="Arial Narrow, Impact, sans-serif" font-weight="900" font-size="52" fill="{COLOR_NARANJA_WALDY}" text-anchor="middle" letter-spacing="1">UNIFORMES</text></svg>'
    return p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9 + p10

def mostrar_encabezado():
    with st.container():
        st.markdown('<div class="header-box">', unsafe_allow_html=True)
        col_logo, col_titulo, col_reset = st.columns([1.3, 3.7, 1.1], vertical_alignment="center")

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
                st.markdown(obtener_svg_waldy(), unsafe_allow_html=True)

        with col_titulo:
            st.markdown(f"<h1 style='color:{COLOR_OSCURO}; margin-bottom:0; font-size:26px;'>Módulo CAD/CAM de Patronaje y Corte Textil</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:{COLOR_VERDE_WALDY}; font-weight:700; font-size:15px; margin-top:4px;'>Línea Escolar y Dotación Empresarial • Tendido Estrictamente al Hilo de Tela (Urdimbre)</p>", unsafe_allow_html=True)

        with col_reset:
            if st.button("🔄 Reiniciar Todo", use_container_width=True):
                reiniciar_sistema()
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

CATALOGO_PRENDAS = {
    "🏫 Escolar - Camisa / Blusa Colegial": {"base_w": 46, "base_h": 58, "tipo": "superior_manga_larga"},
    "🏫 Escolar - Camiseta Polo Institucional": {"base_w": 45, "base_h": 56, "tipo": "superior_manga_corta"},
    "🏫 Escolar - Chaqueta Sudadera": {"base_w": 50, "base_h": 60, "tipo": "chaqueta"},
    "🏫 Escolar - Pantalón Sudadera": {"base_w": 36, "base_h": 88, "tipo": "pantalon"},
    "🏫 Escolar - Pantalón Clásico / Diario": {"base_w": 38, "base_h": 92, "tipo": "pantalon"},
    "🏫 Escolar - Jardinera / Falda Tableada": {"base_w": 44, "base_h": 52, "tipo": "falda"},
    "🏢 Empresarial - Camisa Oxford Manga Larga": {"base_w": 52, "base_h": 68, "tipo": "superior_manga_larga"},
    "🏢 Empresarial - Camiseta Polo Piqué": {"base_w": 50, "base_h": 65, "tipo": "superior_manga_corta"},
    "🏢 Empresarial - Chaqueta Impermeable / Térmica": {"base_w": 56, "base_h": 70, "tipo": "chaqueta"},
    "🏢 Empresarial - Chaleco Reflectivo / Operativo": {"base_w": 53, "base_h": 63, "tipo": "chaleco"},
    "🏢 Empresarial - Pantalón Drill / Gabardina": {"base_w": 44, "base_h": 100, "tipo": "pantalon"},
    "🏢 Empresarial - Overol Enterizo Industrial": {"base_w": 55, "base_h": 145, "tipo": "overol"},
}

FACTORES_TALLA = {
    "6 (Infantil)": 0.72, "8 (Infantil)": 0.78, "10 (Juvenil)": 0.84,
    "12 (Juvenil)": 0.89, "14 (Juvenil)": 0.94, "16 (Juvenil)": 0.97,
    "S": 1.00, "M": 1.06, "L": 1.12, "XL": 1.18, "XXL": 1.25
}

def generar_geometria_al_hilo(prenda_nombre, talla, cantidad):
    info = CATALOGO_PRENDAS[prenda_nombre]
    factor = FACTORES_TALLA[talla]
    w = info["base_w"] * factor
    h = info["base_h"] * factor
    tipo = info["tipo"]
    piezas_orden = []

    for idx in range(1, cantidad + 1):
        etiqueta_base = f"{prenda_nombre.split(' - ')[1]} ({talla}) #{idx}"

        if tipo in ["superior_manga_larga", "superior_manga_corta", "chaqueta"]:
            espalda = Polygon([(0, 0), (w, 0), (w, h * 0.65), (w * 0.85, h * 0.72), (w * 0.82, h * 0.95), (w * 0.65, h), (w * 0.35, h), (w * 0.18, h * 0.95), (w * 0.15, h * 0.72), (0, h * 0.65)])
            piezas_orden.append({"poly": espalda, "categoria": "Espalda", "nombre": f"Espalda {etiqueta_base}"})

            for lado in ["Izq", "Der"]:
                delantero = Polygon([(0, 0), (w * 0.52, 0), (w * 0.52, h * 0.86), (w * 0.35, h * 0.98), (w * 0.15, h * 0.72), (0, h * 0.65)])
                piezas_orden.append({"poly": delantero, "categoria": "Delantero", "nombre": f"Delantero {lado} {etiqueta_base}"})

            largo_m = h * 0.85 if tipo != "superior_manga_corta" else h * 0.38
            ancho_m = w * 0.44
            for m_lado in ["Izq", "Der"]:
                manga = Polygon([(ancho_m * 0.15, 0), (ancho_m * 0.85, 0), (ancho_m, largo_m * 0.75), (ancho_m * 0.5, largo_m), (0, largo_m * 0.75)])
                piezas_orden.append({"poly": manga, "categoria": "Manga", "nombre": f"Manga {m_lado} {etiqueta_base}"})

            cuello = Polygon([(0, 0), (7.5, 0), (7.5, w * 0.76), (0, w * 0.76)])
            piezas_orden.append({"poly": cuello, "categoria": "Cuello / Pretina", "nombre": f"Cuello {etiqueta_base}"})

        elif tipo == "chaleco":
            espalda = Polygon([(0, 0), (w, 0), (w, h * 0.62), (w * 0.80, h * 0.96), (w * 0.20, h * 0.96), (0, h * 0.62)])
            piezas_orden.append({"poly": espalda, "categoria": "Espalda", "nombre": f"Espalda {etiqueta_base}"})
            for lado in ["Izq", "Der"]:
                delantero = Polygon([(0, 0), (w * 0.5, 0), (w * 0.5, h * 0.65), (w * 0.25, h * 0.96), (0, h * 0.62)])
                piezas_orden.append({"poly": delantero, "categoria": "Delantero", "nombre": f"Delantero {lado} {etiqueta_base}"})
            bolsillo = Polygon([(0, 0), (16, 0), (16, 18), (0, 18)])
            piezas_orden.append({"poly": bolsillo, "categoria": "Bolsillo / Detalle", "nombre": f"Bolsillo {etiqueta_base}"})

        elif tipo == "pantalon":
            for pierna in ["Izq", "Der"]:
                del_p = Polygon([(w * 0.15, 0), (w * 0.65, 0), (w * 0.85, h * 0.72), (w, h * 0.76), (w * 0.92, h), (w * 0.1, h)])
                tras_p = Polygon([(w * 0.12, 0), (w * 0.72, 0), (w * 0.95, h * 0.70), (w * 1.12, h * 0.75), (w * 0.98, h * 1.03), (w * 0.08, h)])
                piezas_orden.append({"poly": del_p, "categoria": "Delantero", "nombre": f"Pierna Del {pierna} {etiqueta_base}"})
                piezas_orden.append({"poly": tras_p, "categoria": "Espalda", "nombre": f"Pierna Tras {pierna} {etiqueta_base}"})
            pretina = Polygon([(0, 0), (9.0, 0), (9.0, w * 2.0), (0, w * 2.0)])
            piezas_orden.append({"poly": pretina, "categoria": "Cuello / Pretina", "nombre": f"Pretina {etiqueta_base}"})

        elif tipo == "falda":
            pano_del = Polygon([(0, 0), (w * 1.35, 0), (w * 1.15, h), (w * 0.2, h)])
            pano_tras = Polygon([(0, 0), (w * 1.35, 0), (w * 1.15, h), (w * 0.2, h)])
            pretina = Polygon([(0, 0), (8.5, 0), (8.5, w * 1.85), (0, w * 1.85)])
            piezas_orden.append({"poly": pano_del, "categoria": "Delantero", "nombre": f"Paño Del {etiqueta_base}"})
            piezas_orden.append({"poly": pano_tras, "categoria": "Espalda", "nombre": f"Paño Tras {etiqueta_base}"})
            piezas_orden.append({"poly": pretina, "categoria": "Cuello / Pretina", "nombre": f"Pretina {etiqueta_base}"})

        elif tipo == "overol":
            for lado in ["Izq", "Der"]:
                cuerpo_del = Polygon([(w * 0.1, 0), (w * 0.55, 0), (w * 0.65, h * 0.48),
