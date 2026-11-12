import streamlit as st
import ezdxf
import fitz
import numpy as np
from shapely.geometry import Polygon
from shapely.affinity import translate, rotate
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from PIL import Image
import io
import os

NARANJA = "#E9531E"
VERDE = "#138A36"
FONDO = "#F4F6F5"
OSCURO = "#1E293B"

COLORES = {
    "Espalda": {"fill": "#E9531E", "edge": "#9A3412"},
    "Delantero": {"fill": "#138A36", "edge": "#064E3B"},
    "Manga": {"fill": "#F59E0B", "edge": "#92400E"},
    "Cuello / Pretina": {"fill": "#0284C7", "edge": "#075985"},
    "Bolsillo / Puño": {"fill": "#64748B", "edge": "#1E293B"},
    "Molde PDF": {"fill": "#138A36", "edge": "#E9531E"}
}

st.set_page_config(
    page_title="Módulo de Corte | Waldy Uniformes",
    page_icon="✂️",
    layout="wide"
)

css = (
    "<style>"
    ".main { background-color: #F4F6F5; }"
    ".stButton>button { background-color: #E9531E; "
    "color: white; font-weight: bold; "
    "border-radius: 8px; border: none; }"
    ".stButton>button:hover { background-color: #138A36; "
    "color: white; }"
    ".waldy-card { background: white; padding: 10px; "
    "border-radius: 10px; border: 3px solid #138A36; "
    "text-align: center; }"
    "</style>"
)
st.markdown(css, unsafe_allow_html=True)

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
    c1, c2, c3 = st.columns(
        [1.3, 3.7, 1.1], vertical_alignment="center"
    )
    with c1:
        rutas = [
            "logo_waldy.jpeg",
            "logo_waldy.jpg",
            "logo_waldy.png",
            "WhatsApp Image 2026-11-08 at 6.57.34 PM.jpeg"
        ]
        encontrado = next(
            (r for r in rutas if os.path.exists(r)), None
        )
        if encontrado:
            img = Image.open(encontrado)
            st.image(img, use_container_width=True)
        else:
            marca = (
                '<div class="waldy-card">'
                '<div style="color:#E9531E;font-size:34px;'
                'font-weight:900;line-height:1;">Waldy</div>'
                '<div style="color:#E9531E;font-size:13px;'
                'font-weight:800;letter-spacing:2px;'
                'border-top:3px solid #138A36;'
                'margin-top:4px;padding-top:2px;">'
                'UNIFORMES</div></div>'
            )
            st.markdown(marca, unsafe_allow_html=True)
    with c2:
        t_html = (
            "<h2 style='color:#1E293B;margin:0;'>"
            "Módulo CAD/CAM de Corte Textil</h2>"
        )
        s_html = (
            "<p style='color:#138A36;font-weight:700;"
            "margin:0;'>Waldy Uniformes • Control por Pieza, "
            "Corte Al Hilo/Través y Ficha de Confección</p>"
        )
        st.markdown(t_html, unsafe_allow_html=True)
        st.markdown(s_html, unsafe_allow_html=True)
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

FICHAS_CONFECCION = {
    "🏫 Escolar - Camisa / Blusa": (
        "#F8FAFC", "#CBD5E1", "cuello_camisa",
        "Cuello camisero fusionado, pechera con 6 botones, "
        "bolsillo parche izquierdo y puños pespuntados a 1/16."
    ),
    "🏫 Escolar - Camiseta Polo": (
        "#1E3A8A", "#172554", "cuello_polo",
        "Cuello tejido rib, pechera de 3 botones, manga corta "
        "con dobladillo recubridora y abertura lateral."
    ),
    "🏫 Escolar - Chaqueta Sudadera": (
        "#138A36", "#064E3B", "cremallera",
        "Cremallera frontal separable, cuello alto doble tela, "
        "bolsillos laterales ribeteados y puños en rib."
    ),
    "🏫 Escolar - Pantalón Sudadera": (
        "#1E293B", "#0F172A", "sudadera_pant",
        "Pretina enresortada con pespunte múltiple, tiro "
        "reforzado con puntada de seguridad y bota recta."
    ),
    "🏫 Escolar - Pantalón Diario": (
        "#334155", "#1E293B", "clasico_pant",
        "Pretina entretelada con pasadores, cremallera con "
        "aletilla, bolsillos diagonales y bota dobladillada."
    ),
    "🏫 Escolar - Jardinera / Falda": (
        "#1E3A8A", "#172554", "falda_tablas",
        "Pretina anatómica con cierre lateral, tablas "
        "encontradas planchadas y dobladillo invisible."
    ),
    "🏢 Empresarial - Camisa Oxford": (
        "#E0F2FE", "#7DD3FC", "cuello_camisa",
        "Tela Oxford, cuello button-down, canesú doble en "
        "espalda, bolsillo para bordado y costura francesa."
    ),
    "🏢 Empresarial - Camiseta Polo": (
        "#E9531E", "#9A3412", "cuello_polo",
        "Tela Piqué lacoste, cuello y puños tejidos, tapa "
        "costura en cuello y doble pespunte en hombros."
    ),
    "🏢 Empresarial - Chaqueta": (
        "#0F172A", "#334155", "cremallera",
        "Tela antifluidos, forro interno acolchado, cierre "
        "frontal con solapa protectora y bolsillos con cierre."
    ),
    "🏢 Empresarial - Chaleco": (
        "#F59E0B", "#B45309", "chaleco_ref",
        "Cintas reflectivas textiles de 2 pulgadas en pecho "
        "y espalda, cierre central y bolsillos cargo."
    ),
    "🏢 Empresarial - Pantalón Drill": (
        "#1E3A8A", "#172554", "clasico_pant",
        "Drill industrial de alto calibre, triple costura en "
        "tiro y entrepierna, bolsillos cargo y presillas."
    ),
    "🏢 Empresarial - Overol": (
        "#E9531E", "#9A3412", "overol_ind",
        "Enterizo manga larga, elástico en cintura trasera, "
        "cierre doble carro, cintas reflectivas y 5 bolsillos."
    ),
}

def dibujar_prenda_terminada(prenda_nombre):
    color_base, color_sombra, detalle, notas = FICHAS_CONFECCION[prenda_nombre]
    tipo = CATALOGO[prenda_nombre][2]

    fig, ax = plt.subplots(figsize=(5.2, 5.4), dpi=140)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    # Sombra suave detrás de la prenda
    offset_s = 1.6

    if tipo in ["sup_larga", "sup_corta", "chaqueta", "chaleco"]:
        # Cuerpo principal
        cuerpo = np.array([
            [32, 86], [42, 90], [58, 90], [68, 86],
            [72, 68], [70, 24], [30, 24], [28, 68]
        ])
        ax.fill(
            cuerpo[:, 0] + offset_s, cuerpo[:, 1] - offset_s,
            color="#CBD5E1", alpha=0.5, zorder=1
        )
        ax.fill(
            cuerpo[:, 0], cuerpo[:, 1],
            facecolor=color_base, edgecolor=color_sombra,
            linewidth=2.0, zorder=3
        )
        # Costura dobladillo inferior
        ax.plot([30.5, 69.5], [27, 27], color=color_sombra,
                linestyle="--", linewidth=1.0, zorder=4)

        # Mangas según tipo
        if tipo in ["sup_larga", "chaqueta"]:
            m_izq = np.array([[32, 86], [14, 42], [21, 39], [30, 68]])
            m_der = np.array([[68, 86], [86, 42], [79, 39], [70, 68]])
            for m in [m_izq, m_der]:
                ax.fill(m[:, 0] + offset_s, m[:, 1] - offset_s,
                        color="#CBD5E1", alpha=0.5, zorder=1)
                ax.fill(m[:, 0], m[:, 1], facecolor=color_base,
                        edgecolor=color_sombra, linewidth=1.8, zorder=2)
            # Puños
            ax.plot([14.5, 20.5], [44, 41.5], color=color_sombra, lw=2.5, zorder=4)
            ax.plot([85.5, 79.5], [44, 41.5], color=color_sombra, lw=2.5, zorder=4)

        elif tipo == "sup_corta":
            m_izq = np.array([[32, 86], [17, 65], [24, 60], [30, 68]])
            m_der = np.array([[68, 86], [83, 65], [76, 60], [70, 68]])
            for m in [m_izq, m_der]:
                ax.fill(m[:, 0] + offset_s, m[:, 1] - offset_s,
                        color="#CBD5E1", alpha=0.5, zorder=1)
                ax.fill(m[:, 0], m[:, 1], facecolor=color_base,
                        edgecolor=color_sombra, linewidth=1.8, zorder=2)

        # Cuello anatómico
        cuello = np.array([[41, 90], [50, 81], [59, 90], [55, 93], [45, 93]])
        ax.fill(cuello[:, 0], cuello[:, 1], facecolor="#FFFFFF",
                edgecolor=color_sombra, linewidth=1.6, zorder=5)

        # Detalles de confección frontal
        if detalle in ["cuello_camisa", "cuello_polo"]:
            largo_p = 25 if detalle == "cuello_camisa" else 63
            ax.plot([50, 50], [81, largo_p], color=color_sombra, lw=1.4, zorder=5)
            botones_y = [77, 71, 65] if detalle == "cuello_polo" else [77, 68, 59, 50, 41, 32]
            for by in botones_y:
                ax.scatter([50], [by], color="#FFFFFF", edgecolor=color_sombra, s=22, zorder=6)
            # Bolsillo izquierdo
            bols = np.array([[56, 69], [65, 69], [65, 58], [60.5, 55], [56, 58]])
            ax.fill(bols[:, 0], bols[:, 1], facecolor=color_base,
                    edgecolor=color_sombra, linewidth=1.3, zorder=5)

        elif detalle in ["cremallera", "chaleco_ref"]:
            ax.plot([50, 50], [83, 24], color="#E2E8F0", lw=2.4, zorder=5)
            ax.plot([50, 50], [83, 24], color=OSCURO, lw=1.0, linestyle=":", zorder=6)
            if detalle == "chaleco_ref":
                # Cintas reflectivas
                ax.add_patch(plt.Rectangle((30, 44), 40, 4.5, facecolor="#FEF08A", edgecolor="#CA8A04", zorder=5))
                ax.add_patch(plt.Rectangle((30, 33), 40, 4.5, facecolor="#FEF08A", edgecolor="#CA8A04", zorder=5))

    elif tipo == "pantalon":
        pant = np.array([
            [33, 92], [67, 92], [71, 58], [68, 12],
            [54, 12], [50, 56], [46, 12], [32, 12], [29, 58]
        ])
        ax.fill(pant[:, 0] + offset_s, pant[:, 1] - offset_s,
                color="#CBD5E1", alpha=0.5, zorder=1)
        ax.fill(pant[:, 0], pant[:, 1], facecolor=color_base,
                edgecolor=color_sombra, linewidth=2.0, zorder=3)
        # Pretina y tiro
        ax.add_patch(plt.Rectangle((33, 87), 34, 5, facecolor=color_sombra, alpha=0.45, zorder=4))
        ax.plot([50, 50], [87, 56], color="#94A3B8", linestyle="--", lw=1.3, zorder=5)
        # Bolsillos laterales
        ax.plot([33, 39], [85, 72], color="#94A3B8", lw=1.4, zorder=5)
        ax.plot([67, 61], [85, 72], color="#94A3B8", lw=1.4, zorder=5)

    elif tipo == "falda":
        falda = np.array([[34, 86], [66, 86], [76, 32], [24, 32]])
        ax.fill(falda[:, 0] + offset_s, falda[:, 1] - offset_s,
                color="#CBD5E1", alpha=0.5, zorder=1)
        ax.fill(falda[:, 0], falda[:, 1], facecolor=color_base,
                edgecolor=color_sombra, linewidth=2.0, zorder=3)
        ax.add_patch(plt.Rectangle((34, 81), 32, 5, facecolor=color_sombra, alpha=0.5, zorder=4))
        # Pliegues de tablas
        for tx_top, tx_bot in [(42, 37), (50, 50), (58, 63)]:
            ax.plot([tx_top, tx_bot], [81, 32], color="#94A3B8", lw=1.3, zorder=5)

    elif tipo == "overol":
        ov = np.array([
            [33, 93], [43, 96], [57, 96], [67, 93],
            [84, 56], [78, 53], [67, 76], [68, 55],
            [66, 10], [53, 10], [50, 48], [47, 10],
            [34, 10], [32, 55], [33, 76], [22, 53], [16, 56]
        ])
        ax.fill(ov[:, 0] + offset_s, ov[:, 1] - offset_s,
                color="#CBD5E1", alpha=0.5, zorder=1)
        ax.fill(ov[:, 0], ov[:, 1], facecolor=color_base,
                edgecolor=color_sombra, linewidth=2.0, zorder=3)
        # Cremallera, cintura y reflectivos
        ax.plot([50, 50], [92, 48], color="#FFFFFF", lw=1.8, zorder=5)
        ax.add_patch(plt.Rectangle((32.5, 54), 35, 3.5, facecolor=color_sombra, zorder=4))
        ax.add_patch(plt.Rectangle((34, 24), 12, 3, facecolor="#FEF08A", zorder=5))
        ax.add_patch(plt.Rectangle((54, 24), 12, 3, facecolor="#FEF08A", zorder=5))

    # Etiqueta de marca Waldy en el plano
    ax.text(50, 4, "ESPECIFICACIÓN DE CONFECCIÓN - WALDY UNIFORMES",
            ha="center", va="center", fontsize=8, fontweight="bold", color=OSCURO)
    ax.set_title(prenda_nombre, fontsize=11, fontweight="bold", color=NARANJA, pad=10)
    ax.set_xlim(5, 95)
    ax.set_ylim(0, 102)
    ax.axis("off")
    plt.tight_layout()
    return fig, notas

PIEZAS_POR_TIPO = {
    "sup_larga": [
        "Espalda", "Delanteros (x2)", "Mangas (x2)",
        "Cuello", "Puños (x2)", "Bolsillo"
    ],
    "sup_corta": [
        "Espalda", "Delanteros (x2)", "Mangas (x2)",
        "Cuello", "Bolsillo"
    ],
    "chaqueta": [
        "Espalda", "Delanteros (x2)", "Mangas (x2)",
        "Cuello", "Puños (x2)", "Bolsillos (x2)"
    ],
    "chaleco": [
        "Espalda", "Delanteros (x2)",
        "Cuello", "Bolsillos (x2)"
    ],
    "pantalon": [
        "Piernas Delanteras (x2)",
        "Piernas Traseras (x2)",
        "Pretina", "Bolsillos (x2)"
    ],
    "falda": [
        "Paño Delantero", "Paño Trasero",
        "Pretina", "Bolsillo"
    ],
    "overol": [
        "Cuerpo Delantero (x2)",
        "Cuerpo Trasero (x2)",
        "Mangas (x2)", "Cuello", "Bolsillos (x2)"
    ]
}

TALLAS = {
    "6": 0.72, "8": 0.78, "10": 0.84, "12": 0.89,
    "14": 0.94, "16": 0.97, "S": 1.00, "M": 1.06,
    "L": 1.12, "XL": 1.18, "XXL": 1.25
}

def aplicar_sentido(poly, sentido):
    if sentido == "Al Través (90°)":
        rot = rotate(poly, 90, origin=(0, 0))
        minx, miny, _, _ = rot.bounds
        return translate(rot, xoff=-minx, yoff=-miny)
    return poly

def crear_piezas(prenda, talla, cant, piezas_sel, sentido):
    bw, bh, tipo = CATALOGO[prenda]
    f = TALLAS[talla]
    w, h = bw * f, bh * f
    res = []

    for _ in range(cant):
        if "Espalda" in piezas_sel:
            pts = [
                (0, 0), (w, 0), (w, h * 0.65),
                (w * 0.82, h * 0.95), (w * 0.65, h),
                (w * 0.35, h), (w * 0.18, h * 0.95),
                (0, h * 0.65)
            ]
            res.append({
                "poly": aplicar_sentido(Polygon(pts), sentido),
                "cat": "Espalda", "sentido": sentido
            })

        if "Delanteros (x2)" in piezas_sel:
            for _ in range(2):
                pts = [
                    (0, 0), (w * 0.52, 0),
                    (w * 0.52, h * 0.86),
                    (w * 0.35, h * 0.98), (0, h * 0.65)
                ]
                res.append({
                    "poly": aplicar_sentido(Polygon(pts), sentido),
                    "cat": "Delantero", "sentido": sentido
                })

        if "Mangas (x2)" in piezas_sel:
            lm = h * 0.85 if tipo != "sup_corta" else h * 0.38
            if tipo == "overol":
                lm = h * 0.34
            am = w * 0.44
            for _ in range