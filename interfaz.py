import streamlit as st
import ezdxf, fitz, io, os
import numpy as np
from shapely.geometry import Polygon
from shapely.affinity import translate, rotate
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image

NARANJA, VERDE, OSCURO = "#E9531E", "#138A36", "#1E293B"
COLORES = {
    "Espalda": ("#E9531E", "#9A3412"),
    "Delantero": ("#138A36", "#064E3B"),
    "Manga": ("#F59E0B", "#92400E"),
    "Cuello / Pretina": ("#0284C7", "#075985"),
    "Bolsillo / Puño": ("#64748B", "#1E293B"),
    "Molde PDF": ("#138A36", "#E9531E")
}

st.set_page_config(page_title="Corte | Waldy Uniformes", page_icon="✂️", layout="wide")
st.markdown(f"<style>.main{{background:#F4F6F5}}.stButton>button{{background:{NARANJA};color:#fff;font-weight:bold;border-radius:8px;border:none}}.stButton>button:hover{{background:{VERDE};color:#fff}}</style>", unsafe_allow_html=True)

if "orden_corte" not in st.session_state:
    st.session_state.orden_corte = []
if "rc" not in st.session_state:
    st.session_state.rc = 0
if "ver_prenda" not in st.session_state:
    st.session_state.ver_prenda = False

def reiniciar():
    st.session_state.orden_corte = []
    st.session_state.ver_prenda = False
    st.session_state.rc += 1

def encabezado():
    c1, c2, c3 = st.columns([1.3, 3.7, 1.1], vertical_alignment="center")
    with c1:
        rutas = ["logo_waldy.jpeg", "logo_waldy.jpg", "logo_waldy.png", "WhatsApp Image 2026-11-08 at 6.57.34 PM.jpeg"]
        logo = next((r for r in rutas if os.path.exists(r)), None)
        if logo:
            st.image(Image.open(logo), use_container_width=True)
        else:
            st.markdown(f'<div style="background:#fff;padding:8px;border-radius:10px;border:3px solid {VERDE};text-align:center"><b style="color:{NARANJA};font-size:32px;line-height:1">Waldy</b><div style="color:{NARANJA};font-size:12px;font-weight:800;letter-spacing:2px;border-top:3px solid {VERDE};margin-top:3px">UNIFORMES</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f"<h2 style='color:{OSCURO};margin:0'>Módulo CAD/CAM de Corte Textil</h2><p style='color:{VERDE};font-weight:700;margin:0'>Waldy Uniformes • Control por Pieza, Corte Al Hilo/Través y Ficha de Confección</p>", unsafe_allow_html=True)
    with c3:
        if st.button("🔄 Reiniciar", use_container_width=True):
            reiniciar()
            st.rerun()
    st.markdown("---")

CATALOGO = {
    "🏫 Escolar - Camisa / Blusa": (46, 58, "sup_larga"),
    "🏫 Escolar - Camiseta Polo": (45, 56, "sup_corta"),
    "🏫 Escolar - Chaqueta Sudadera": (50, 60, "chaqueta"),
    "🏫 Escolar - Pantalón Sudadera": (36, 88, "pantalon"),
    "🏫 Escolar - Pantalón Diario": (38, 92, "pantalon"),
    "🏫 Escolar - Jardinera / Falda": (44, 52, "falda"),
    "🏢 Empresarial - Camisa Oxford": (52, 68, "sup_larga"),
    "🏢 Empresarial - Camiseta Polo": (50, 65, "sup_corta"),
    "🏢 Empresarial - Chaqueta": (56, 70, "chaqueta"),
    "🏢 Empresarial - Chaleco": (53, 63, "chaleco"),
    "🏢 Empresarial - Pantalón Drill": (44, 100, "pantalon"),
    "🏢 Empresarial - Overol": (55, 145, "overol"),
}

FICHAS = {
    "🏫 Escolar - Camisa / Blusa": ("#F8FAFC", "#CBD5E1", "camisa", "Cuello camisero fusionado, pechera con 6 botones, bolsillo parche izquierdo y puños pespuntados a 1/16."),
    "🏫 Escolar - Camiseta Polo": ("#1E3A8A", "#172554", "polo", "Cuello tejido rib, pechera de 3 botones, manga corta con dobladillo recubridora y abertura lateral."),
    "🏫 Escolar - Chaqueta Sudadera": ("#138A36", "#064E3B", "cierre", "Cremallera frontal separable, cuello alto doble tela, bolsillos laterales ribeteados y puños en rib."),
    "🏫 Escolar - Pantalón Sudadera": ("#1E293B", "#0F172A", "pant", "Pretina enresortada con pespunte múltiple, tiro reforzado con puntada de seguridad y bota recta."),
    "🏫 Escolar - Pantalón Diario": ("#334155", "#1E293B", "pant", "Pretina entretelada con pasadores, cremallera con aletilla, bolsillos diagonales y bota dobladillada."),
    "🏫 Escolar - Jardinera / Falda": ("#1E3A8A", "#172554", "falda", "Pretina anatómica con cierre lateral, tablas encontradas planchadas y dobladillo invisible."),
    "🏢 Empresarial - Camisa Oxford": ("#E0F2FE", "#7DD3FC", "camisa", "Tela Oxford, cuello button-down, canesú doble en espalda, bolsillo para bordado y costura francesa."),
    "🏢 Empresarial - Camiseta Polo": ("#E9531E", "#9A3412", "polo", "Tela Piqué lacoste, cuello y puños tejidos, tapa costura en cuello y doble pespunte en hombros."),
    "🏢 Empresarial - Chaqueta": ("#0F172A", "#334155", "cierre", "Tela antifluidos, forro interno acolchado, cierre frontal con solapa protectora y bolsillos con cierre."),
    "🏢 Empresarial - Chaleco": ("#F59E0B", "#B45309", "chaleco", "Cintas reflectivas textiles de 2 pulgadas en pecho y espalda, cierre central y bolsillos cargo."),
    "🏢 Empresarial - Pantalón Drill": ("#1E3A8A", "#172554", "pant", "Drill industrial de alto calibre, triple costura en tiro y entrepierna, bolsillos cargo y presillas."),
    "🏢 Empresarial - Overol": ("#E9531E", "#9A3412", "overol", "Enterizo manga larga, elástico en cintura trasera, cierre doble carro, cintas reflectivas y 5 bolsillos."),
}

PIEZAS_TIPO = {
    "sup_larga": ["Espalda", "Delanteros (x2)", "Mangas (x2)", "Cuello", "Puños (x2)", "Bolsillo"],
    "sup_corta": ["Espalda", "Delanteros (x2)", "Mangas (x2)", "Cuello", "Bolsillo"],
    "chaqueta": ["Espalda", "Delanteros (x2)", "Mangas (x2)", "Cuello", "Puños (x2)", "Bolsillos (x2)"],
    "chaleco": ["Espalda", "Delanteros (x2)", "Cuello", "Bolsillos (x2)"],
    "pantalon": ["Piernas Delanteras (x2)", "Piernas Traseras (x2)", "Pretina", "Bolsillos (x2)"],
    "falda": ["Paño Delantero", "Paño Trasero", "Pretina", "Bolsillo"],
    "overol": ["Cuerpo Delantero (x2)", "Cuerpo Trasero (x2)", "Mangas (x2)", "Cuello", "Bolsillos (x2)"]
}

TALLAS = {"6": 0.72, "8": 0.78, "10": 0.84, "12": 0.89, "14": 0.94, "16": 0.97, "S": 1.00, "M": 1.06, "L": 1.12, "XL": 1.18, "XXL": 1.25}

def dibujar_prenda(prenda):
    cb, cs, det, notas = FICHAS[prenda]
    tipo = CATALOGO[prenda][2]
    fig, ax = plt.subplots(figsize=(5, 5.2), dpi=140)
    ax.set_facecolor("#F8FAFC")
    if tipo in ["sup_larga", "sup_corta", "chaqueta", "chaleco"]:
        c = np.array([[32,86],[42,90],[58,90],[68,86],[72,68],[70,24],[30,24],[28,68]])
        ax.fill(c[:,0]+1.5, c[:,1]-1.5, color="#CBD5E1", alpha=0.5)
        ax.fill(c[:,0], c[:,1], facecolor=cb, edgecolor=cs, lw=2)
        ax.plot([30.5, 69.5], [27, 27], color=cs, ls="--", lw=1)
        if tipo in ["sup_larga", "chaqueta"]:
            for m in [np.array([[32,86],[14,42],[21,39],[30,68]]), np.array([[68,86],[86,42],[79,39],[70,68]])]:
                ax.fill(m[:,0], m[:,1], facecolor=cb, edgecolor=cs, lw=1.8)
        elif tipo == "sup_corta":
            for m in [np.array([[32,86],[17,65],[24,60],[30,68]]), np.array([[68,86],[83,65],[76,60],[70,68]])]:
                ax.fill(m[:,0], m[:,1], facecolor=cb, edgecolor=cs, lw=1.8)
        cu = np.array([[41,90],[50,81],[59,90],[55,93],[45,93]])
        ax.fill(cu[:,0], cu[:,1], facecolor="#fff", edgecolor=cs, lw=1.6)
        if det in ["camisa", "polo"]:
            ax.plot([50, 50], [81, 25 if det == "camisa" else 63], color=cs, lw=1.4)
            for by in ([77,71,65] if det == "polo" else [77,68,59,50,41,32]):
                ax.scatter([50], [by], color="#fff", edgecolor=cs, s=22, zorder=5)
            bo = np.array([[56,69],[65,69],[65,58],[60.5,55],[56,58]])
            ax.fill(bo[:,0], bo[:,1], facecolor=cb, edgecolor=cs, lw=1.3)
        else:
            ax.plot([50, 50], [83, 24], color="#E2E8F0", lw=2.2)
            if det == "chaleco":
                ax.add_patch(plt.Rectangle((30, 44), 40, 4.5, facecolor="#FEF08A", edgecolor="#CA8A04"))
                ax.add_patch(plt.Rectangle((30, 33), 40, 4.5, facecolor="#FEF08A", edgecolor="#CA8A04"))
    elif tipo == "pantalon":
        p = np.array([[33,92],[67,92],[71,58],[68,12],[54,12],[50,56],[46,12],[32,12],[29,58]])
        ax.fill(p[:,0]+1.5, p[:,1]-1.5, color="#CBD5E1", alpha=0.5)
        ax.fill(p[:,0], p[:,1], facecolor=cb, edgecolor=cs, lw=2)
        ax.add_patch(plt.Rectangle((33,