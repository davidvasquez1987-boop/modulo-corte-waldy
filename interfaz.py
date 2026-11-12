import streamlit as st
import ezdxf
import fitz
import io
import os
import numpy as np
from shapely.geometry import Polygon
from shapely.affinity import translate, rotate
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image

NARANJA = "#E9531E"
VERDE = "#138A36"
OSCURO = "#1E293B"

COLORES = {
    "Espalda": ("#E9531E", "#9A3412"),
    "Delantero": ("#138A36", "#064E3B"),
    "Manga": ("#F59E0B", "#92400E"),
    "Cuello / Pretina": ("#0284C7", "#075985"),
    "Bolsillo / Puño": ("#64748B", "#1E293B"),
    "Molde PDF": ("#138A36", "#E9531E")
}

st.set_page_config(
    page_title="Módulo de Corte | Waldy Uniformes",
    page_icon="✂️",
    layout="wide"
)

st.markdown(
    "<style>"
    ".main{background:#F4F6F5}"
    ".stButton>button{background:#E9531E;color:#fff;"
    "font-weight:bold;border-radius:8px;border:none}"
    ".stButton>button:hover{background:#138A36;color:#fff}"
    "</style>",
    unsafe_allow_html=True
)

for k, v in [("orden_corte", []), ("rc", 0), ("ver_prenda", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

def reiniciar():
    st.session_state.orden_corte = []
    st.session_state.ver_prenda = False
    st.session_state.rc += 1

def encabezado():
    c1, c2, c3 = st.columns([1.3, 3.7, 1.1], vertical_alignment="center")
    with c1:
        rutas = [
            "logo_waldy.jpeg", "logo_waldy.jpg", "logo_waldy.png",
            "WhatsApp Image 2026-11-08 at 6.57.34 PM.jpeg"
        ]
        logo = next((r for r in rutas if os.path.exists(r)), None)
        if logo:
            st.image(Image.open(logo), use_container_width=True)
        else:
            st.markdown(
                '<div style="background:#fff;padding:8px;'
                'border-radius:10px;border:3px solid #138A36;'
                'text-align:center">'
                '<b style="color:#E9531E;font-size:32px;'
                'line-height:1">Waldy</b>'
                '<div style="color:#E9531E;font-size:12px;'
                'font-weight:800;letter-spacing:2px;'
                'border-top:3px solid #138A36;'
                'margin-top:3px">UNIFORMES</div></div>',
                unsafe_allow_html=True
            )
    with c2:
        st.markdown(
            "<h2 style='color:#1E293B;margin:0'>"
            "Módulo CAD/CAM de Corte Textil</h2>"
            "<p style='color:#138A36;font-weight:700;margin:0'>"
            "Waldy Uniformes • Control por Pieza, Corte Al Hilo/Través "
            "y Ficha de Confección</p>",
            unsafe_allow_html=True
        )
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
    "🏫 Escolar - Camisa / Blusa": (
        "#F8FAFC", "#CBD5E1", "camisa",
        "Cuello camisero fusionado, pechera 6 botones, "
        "bolsillo parche y puños pespuntados a 1/16."
    ),
    "🏫 Escolar - Camiseta Polo": (
        "#1E3A8A", "#172554", "polo",
        "Cuello tejido rib, pechera de 3 botones, "
        "dobladillo recubridora y abertura lateral."
    ),
    "🏫 Escolar - Chaqueta Sudadera": (
        "#138A36", "#064E3B", "cierre",
        "Cremallera separable, cuello alto doble tela, "
        "bolsillos laterales ribeteados y puños en rib."
    ),
    "🏫 Escolar - Pantalón Sudadera": (
        "#1E293B", "#0F172A", "pant",
        "Pretina enresortada con pespunte múltiple, "
        "tiro con puntada de seguridad y bota recta."
    ),
    "🏫 Escolar - Pantalón Diario": (
        "#334155", "#1E293B", "pant",
        "Pretina entretelada con pasadores, aletilla "
        "con cierre, bolsillos diagonales y bota."
    ),
    "🏫 Escolar - Jardinera / Falda": (
        "#1E3A8A", "#172554", "falda",
        "Pretina anatómica con cierre lateral, tablas "
        "encontradas planchadas y dobladillo invisible."
    ),
    "🏢 Empresarial - Camisa Oxford": (
        "#E0F2FE", "#7DD3FC", "camisa",
        "Tela Oxford, cuello button-down, canesú doble "
        "en espalda, bolsillo y costura francesa."
    ),
    "🏢 Empresarial - Camiseta Polo": (
        "#E9531E", "#9A3412", "polo",
        "Tela Piqué lacoste, cuello y puños tejidos, "
        "tapa costura y doble pespunte en hombros."
    ),
    "🏢 Empresarial - Chaqueta": (
        "#0F172A", "#334155", "cierre",
        "Tela antifluidos, forro acolchado, cierre "
        "con solapa protectora y bolsillos."
    ),
    "🏢 Empresarial - Chaleco": (
        "#F59E0B", "#B45309", "chaleco",
        "Cintas reflectivas de 2 pulgadas en pecho "
        "y espalda, cierre central y bolsillos cargo."
    ),
    "🏢 Empresarial - Pantalón Drill": (
        "#1E3A8A", "#172554", "pant",
        "Drill industrial, triple costura en tiro "
        "y entrepierna, bolsillos cargo y presillas."
    ),
    "🏢 Empresarial - Overol": (
        "#E9531E", "#9A3412", "overol",
        "Enterizo manga larga, elástico en cintura, "
        "cierre doble carro, reflectivos y 5 bolsillos."
    ),
}

PIEZAS_TIPO = {
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
        "Piernas Delanteras (x2)", "Piernas Traseras (x2)",
        "Pretina", "Bolsillos (x2)"
    ],
    "falda": [
        "Paño Delantero", "Paño Trasero",
        "Pretina", "Bolsillo"
    ],
    "overol": [
        "Cuerpo Delantero (x2)", "Cuerpo Trasero (x2)",
        "Mangas (x2)", "Cuello", "Bolsillos (x2)"
    ]
}

TALLAS = {
    "6": 0.72, "8": 0.78, "10": 0.84, "12": 0.89,
    "14": 0.94, "16": 0.97, "S": 1.00, "M": 1.06,
    "L": 1.12, "XL": 1.18, "XXL": 1.25
}

def dibujar_prenda(prenda):
    cb, cs, det, notas = FICHAS[prenda]
    tipo = CATALOGO[prenda][2]
    fig, ax = plt.subplots(figsize=(5, 5.2), dpi=140)
    ax.set_facecolor("#F8FAFC")

    if tipo in ["sup_larga", "sup_corta", "chaqueta", "chaleco"]:
        ax.fill(
            [32, 42, 58, 68, 72, 70, 30, 28],
            [86, 90, 90, 86, 68, 24, 24, 68],
            facecolor=cb, edgecolor=cs, lw=2
        )
        ax.plot([30.5, 69.5], [27, 27], color=cs, ls="--", lw=1)
        if tipo in ["sup_larga", "chaqueta"]:
            ax.fill(
                [32, 14, 21, 30], [86, 42, 39, 68],
                facecolor=cb, edgecolor=cs, lw=1.8
            )
            ax.fill(
                [68, 86, 79, 70], [86, 42, 39, 68],
                facecolor=cb, edgecolor=cs, lw=1.8
            )
        elif tipo == "sup_corta":
            ax.fill(
                [32, 17, 24, 30], [86, 65, 60, 68],
                facecolor=cb, edgecolor=cs, lw=1.8
            )
            ax.fill(
                [68, 83, 76, 70], [86, 65, 60, 68],
                facecolor=cb, edgecolor=cs, lw=1.8
            )
        ax.fill(
            [41, 50, 59, 55, 45], [90, 81, 90, 93, 93],
            facecolor="#fff", edgecolor=cs, lw=1.6
        )
        if det in ["camisa", "polo"]:
            fin = 25 if det == "camisa" else 63
            ax.plot([50, 50], [81, fin], color=cs, lw=1.4)
            bots = [77, 71, 65] if det == "polo" else [77, 68, 59, 50, 41]
            for by in bots:
                ax.scatter(
                    [50], [by], color="#fff",
                    edgecolor=cs, s=22, zorder=5
                )
            ax.fill(
                [56, 65, 65, 60.5, 56],
                [69, 69, 58, 55, 58],
                facecolor=cb, edgecolor=cs, lw=1.3
            )
        else:
            ax.plot([50, 50], [83, 24], color="#E2E8F0", lw=2.2)
            if det == "chaleco":
                ax.add_patch(plt.Rectangle(
                    (30, 44), 40, 4.5,
                    facecolor="#FEF08A", edgecolor="#CA8A04"
                ))
                ax.add_patch(plt.Rectangle(
                    (30, 33), 40, 4.5,
                    facecolor="#FEF08A", edgecolor="#CA8A04"
                ))
    elif tipo == "pantalon":
        ax.fill(
            [33, 67, 71, 68, 54, 50, 46, 32, 29],
            [92, 92, 58, 12, 12, 56, 12, 12, 58],
            facecolor=cb, edgecolor=cs, lw=2
        )
        ax.add_patch(plt.Rectangle(
            (33, 87), 34, 5, facecolor=cs, alpha=0.45
        ))
        ax.plot([50, 50], [87, 56], color="#94A3B8", ls="--", lw=1.3)
    elif tipo == "falda":
        ax.fill(
            [34, 66, 76, 24], [86, 86, 32, 32],
            facecolor=cb, edgecolor=cs, lw=2
        )
        ax.add_patch(plt.Rectangle(
            (34, 81), 32, 5, facecolor=cs, alpha=0.5
        ))
        for t1, t2 in [(42, 37), (50, 50), (58, 63)]:
            ax.plot([t1, t2], [81, 32], color="#94A3B8", lw=1.3)
    elif tipo == "overol":
        ax.fill(
            [33, 43, 57, 67, 84, 78, 67, 68, 66, 53, 50, 47, 34, 32, 33, 22, 16],
            [93, 96, 96, 93, 56, 53, 76, 55, 10, 10, 48, 10, 10, 55, 76, 53, 56],
            facecolor=cb, edgecolor=cs, lw=2
        )
        ax.plot([50, 50], [92, 48], color="#fff", lw=1.8)
        ax.add_patch(plt.Rectangle((32.5, 54), 35, 3.5, facecolor=cs))

    ax.text(
        50, 4, "FICHA CONFECCIÓN - WALDY UNIFORMES",
        ha="center", fontsize=8, fontweight="bold", color=OSCURO
    )
    ax.set_title(prenda, fontsize=11, fontweight="bold", color=NARANJA)
    ax.set_xlim(5, 95)
    ax.set_ylim(0, 102)
    ax.axis("off")
    plt.tight_layout()
    return fig, notas

def rotar_sentido(poly, sentido):
    if sentido == "Al Través (90°)":
        r = rotate(poly, 90, origin=(0, 0))
        mx, my, _, _ = r.bounds
        return translate(r, xoff=-mx, yoff=-my)
    return poly

def crear_piezas(prenda, talla, cant, sel, sentido):
    bw, bh, tipo = CATALOGO[prenda]
    f = TALLAS[talla]
    w, h = bw * f, bh * f
    res = []

    def add(pts, cat):
        p_rot = rotar_sentido(Polygon(pts), sentido)
        res.append({"poly": p_rot, "cat": cat, "sentido": sentido})

    for _ in range(cant):
        if "Espalda" in sel:
            add([
                (0, 0), (w, 0), (w, h * 0.65), (w * 0.82, h * 0.95),
                (w * 0.65, h), (w * 0.35, h), (w * 0.18, h * 0.95),
                (0, h * 0.65)
            ], "Espalda")
        if "Delanteros (x2)" in sel:
            for _ in range(2):
                add([
                    (0, 0), (w * 0.52, 0), (w * 0.52, h * 0.86),
                    (w * 0.35, h * 0.98), (0, h * 0.65)
                ], "Delantero")
        if "Mangas (x2)" in sel:
            fac = 0.34 if tipo == "overol" else (
                0.38 if tipo == "sup_corta" else 0.85
            )
            lm, am = h * fac, w * 0.44
            for _ in range(2):
                add([
                    (am * 0.15, 0), (am * 0.85, 0), (am, lm * 0.75),
                    (am * 0.5, lm), (0, lm * 0.75)
                ], "Manga")
        if "Cuello" in sel:
            add(
                [(0, 0), (7.5, 0), (7.5, w * 0.76), (0, w * 0.76)],
                "Cuello / Pretina"
            )
        if "Puños (x2)" in sel:
            for _ in range(2):
                add([(0, 0), (7, 0), (7, 23), (0, 23)], "Bolsillo / Puño")
        if "Bolsillo" in sel:
            add([(0, 0), (13, 0), (13, 15), (0, 15)], "Bolsillo / Puño")
        if "Bolsillos (x2)" in sel:
            for _ in range(2):
                add([(0, 0), (15, 0), (15, 17), (0, 17)], "Bolsillo / Puño")
        if "Piernas Delanteras (x2)" in sel:
            for _ in range(2):
                add([
                    (w * 0.15, 0), (w * 0.65, 0), (w * 0.85, h * 0.72),
                    (w, h * 0.76), (w * 0.92, h), (w * 0.1, h)
                ], "Delantero")
        if "Piernas Traseras (x2)" in sel:
            for _ in range(2):
                add([
                    (w * 0.12, 0), (w * 0.72, 0), (w * 0.95, h * 0.70),
                    (w * 1.12, h * 0.75), (w * 0.98, h * 1.03), (w * 0.08, h)
                ], "Espalda")
        if "Pretina" in sel:
            add(
                [(0, 0), (9, 0), (9, w * 2), (0, w * 2)],
                "Cuello / Pretina"
            )
        if "Paño Delantero" in sel:
            add(
                [(0, 0), (w * 1.35, 0), (w * 1.15, h), (w * 0.2, h)],
                "Delantero"
            )
        if "Paño Trasero" in sel:
            add(
                [(0, 0), (w * 1.35, 0), (w * 1.15, h), (w * 0.2, h)],
                "Espalda"
            )
        if "Cuerpo Delantero (x2)" in sel:
            for _ in range(2):
                add([
                    (w * 0.1, 0), (w * 0.55, 0), (w * 0.65, h * 0.48),
                    (w * 0.65, h * 0.90), (w * 0.4, h), (0, h * 0.75)
                ], "Delantero")
        if "Cuerpo Trasero (x2)" in sel:
            for _ in range(2):
                add([
                    (w * 0.1, 0), (w * 0.60, 0), (w * 0.72, h * 0.48),
                    (w * 0.68, h * 0.96), (w * 0.35, h), (0, h * 0.78)
                ], "Espalda")
    return res

def leer_pdf(archivo, sentido):
    res = []
    doc = fitz.open(stream=archivo.read(), filetype="pdf")
    for pag in doc:
        pts = []
        for path in pag.get_drawings():
            for it in path.get("items", []):
                if it[0] in ['l', 'c']:
                    pts.extend([(it[1].x, it[1].y), (it[-1].x, it[-1].y)])
                elif it[0] == 're':
                    r = it[1]
                    pts.extend([
                        (r.x0, r.y0), (r.x1, r.y0),
                        (r.x1, r.y1), (r.x0, r.y1)
                    ])
        if len(pts) > 4:
            cm = [(round(p[0] / 28.35, 1), round(p[1] / 28.35, 1)) for p in pts]
            unicos = list(dict.fromkeys(cm))
            if len(unicos) > 3:
                try:
                    poly = Polygon(unicos).simplify(0.4, preserve_topology=True)
                    if poly.is_valid and not poly.is_empty and poly.area > 5:
                        res.append({
                            "poly": rotar_sentido(poly, sentido),
                            "cat": "Molde PDF",
                            "sentido": sentido
                        })
                except Exception:
                    pass
    return res

def anidar_piezas(piezas, ancho_util, margen, paso):
    proc, area_neta, desc = [], 0.0, 0
    for it in piezas:
        pm = it["poly"].buffer(margen, join_style=2)
        mx, my, xx, xy = pm.bounds
        if (xx - mx) > ancho_util:
            desc += 1
            continue
        area_neta += pm.area
        proc.append({
            "poly": pm, "cat": it["cat"],
            "sentido": it["sentido"], "area": pm.area
        })
    proc.sort(key=lambda x: x["area"], reverse=True)
    ubicadas = []
    barra = st.progress(0)
    for idx, it in enumerate(proc):
        pb = it["poly"]
        mx, my, xx, xy = pb.bounds
        ap = xx - mx
        pn = translate(pb, xoff=-mx, yoff=-my)
        y, ok = 0.0, False
        while not ok:
            x = 0.0
            while x + ap <= ancho_util:
                cand = translate(pn, xoff=x, yoff=y)
                if not any(cand.intersects(u["poly"]) for u in ubicadas):
                    ubicadas.append({
                        "poly": cand, "cat": it["cat"],
                        "sentido": it["sentido"]
                    })
                    ok = True
                    break
                x += paso
            y += paso
        barra.progress((idx + 1) / len(proc))
    barra.empty()
    return ubicadas, area_neta, desc

def dibujar_plano(ubicadas, ancho_util, area_neta):
    largo = max((u["poly"].bounds[3] for u in ubicadas), default=10.0)
    alto_f = max(6.5, min(18.0, (largo / ancho_util) * 8.0))
    fig, ax = plt.subplots(figsize=(10, alto_f), dpi=150)
    ax.add_patch(plt.Rectangle(
        (0, 0), ancho_util, largo + 5, fill=True,
        facecolor='#F1F5F9', edgecolor=OSCURO, lw=2, ls='--'
    ))
    ax.annotate(
        '', xy=(-2.5, largo), xytext=(-2.5, 0),
        arrowprops=dict(arrowstyle="<->", color=NARANJA, lw=2)
    )
    ax.text(
        -3.8, largo / 2, "HILO DE LA TELA (URDIMBRE 0°)",
        rotation=90, va='center', ha='center',
        fontsize=8, fontweight='bold', color=NARANJA
    )
    ax.grid(True, color='#CBD5E1', ls=':', lw=0.7)
    cats = set()
    for it in ubicadas:
        poly, cat, sent = it["poly"], it["cat"], it["sentido"]
        cats.add(cat)
        fill_c, edge_c = COLORES.get(cat, COLORES["Bolsillo / Puño"])
        x, y = poly.exterior.xy
        ax.fill(
            x, y, facecolor=fill_c, alpha=0.82,
            edgecolor=edge_c, lw=1.3, zorder=3
        )
        cx, cy = poly.centroid.x, poly.centroid.y
        mx, my, xx, xy = poly.bounds
        ap, lp = xx - mx, xy - my
        if sent == "Al Hilo (0°)" and lp > 10:
            fl = min(lp * 0.25, 9)
            ax.annotate(
                '', xy=(cx, cy + fl), xytext=(cx, cy - fl),
                arrowprops=dict(arrowstyle="<->", color='white', lw=1),
                zorder=4
            )
        elif sent == "Al Través (90°)" and ap > 10:
            fl = min(ap * 0.25, 9)
            ax.annotate(
                '', xy=(cx + fl, cy), xytext=(cx - fl, cy),
                arrowprops=dict(arrowstyle="<->", color='#FEF08A', lw=1.1),
                zorder=4
            )
        if ap > 13:
            tag = "HILO" if sent == "Al Hilo (0°)" else "TRAV"
            ax.text(
                cx + 1.5, cy, f"{cat[:4].upper()} ({tag})
{ap:.0f}x{lp:.0f}",
                fontsize=6.2, fontweight='bold', color='white',
                va='center', zorder=5
            )
    parches = [
        mpatches.Patch(color=COLORES[c][0], label=c)
        for c in COLORES if c in cats
    ]
    ax.legend(
        handles=parches, loc='upper center',
        bbox_to_anchor=(0.5, -0.05), ncol=3, fontsize=9
    )
    efic = (area_neta / (ancho_util * largo) * 100) if largo > 0 else 0
    ax.set_title(
        f"PLANO DE CORTE - WALDY UNIFORMES
"
        f"Ancho: {ancho_util:.1f} cm | Largo: {largo/100:.2f} m | "
        f"Aprovechamiento: {efic:.1f}%",
        fontsize=11, fontweight='bold', color=OSCURO
    )
    ax.set_xlabel("Ancho Tela - Trama (cm)")
    ax.set_ylabel("Largo de Tendido - Urdimbre (cm)")
    ax.set_xlim(-6, ancho_util + 5)
    ax.set_ylim(-5, largo + 8)
    ax.set_aspect('equal')
    plt.tight_layout()
    return fig, largo, efic

def exportar_archivos(fig, ubicadas, ancho, largo):
    buf = io.BytesIO()
    fig.savefig(buf, format="pdf", bbox_inches="tight")
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (ancho, 0), (ancho, largo), (0, largo)], close=True)
    for it in ubicadas:
        msp.add_lwpolyline(list(it["poly"].exterior.coords), close=True)
    s = io.StringIO()
    doc.write(s)
    return buf.getvalue(), s.getvalue().encode('utf-8')

encabezado()
rc = st.session_state.rc
col1, col2 = st.columns([1.2, 2.05], gap="large")

with col1:
    st.subheader("1. Configurar Prendas y Piezas")
    t1, t2 = st.tabs(["👕 Catálogo Waldy", "📄 Molde PDF"])
    with t1:
        pr = st.selectbox("Prenda:", list(CATALOGO.keys()), key=f"p_{rc}")
        ca, cb = st.columns(2)
        ta = ca.selectbox("Talla:", list(TALLAS.keys()), index=6, key=f"t_{rc}")
        cn = cb.number_input("Cantidad:", 1, 200, 2, key=f"c_{rc}")
        sentido_pr = st.radio(
            "Dirección de corte:",
            ["Al Hilo (0°)", "Al Través (90°)"],
            horizontal=True, key=f"sent_{rc}"
        )
        tipo_act = CATALOGO[pr][2]
        lista_pz = PIEZAS_TIPO[tipo_act]
        st.markdown("**Selecciona las piezas a cortar:**")
        cols_pz = st.columns(2)
        pz_elegidas = [
            nom for idx, nom in enumerate(lista_pz)
            if cols_pz[idx % 2].checkbox(
                nom, value=True, key=f"chk_{rc}_{tipo_act}_{idx}"
            )
        ]
        b_add, b_ver = st.columns(2)
        if b_add.button("➕ Agregar Orden", use_container_width=True):
            if pz_elegidas:
                st.session_state.orden_corte.append({
                    "tipo": "cat", "pr": pr, "ta": ta, "cn": cn,
                    "piezas": pz_elegidas, "sentido": sentido_pr
                })
                st.toast(f"Agregado ({sentido_pr})", icon="✅")
            else:
                st.warning("Marca al menos una pieza.")
        if b_ver.button(
            "👁️ Visualizar prenda terminada", use_container_width=True
        ):
            st.session_state.ver_prenda = True

    with t2:
        pdf_up = st.file_uploader("Subir PDF:", type=["pdf"], key=f"f_{rc}")
        cn_pdf = st.number_input("Copias PDF:", 1, 100, 1, key=f"cp_{rc}")
        sentido_pdf = st.radio(
            "Dirección PDF:",
            ["Al Hilo (0°)", "Al Través (90°)"],
            horizontal=True, key=f"sent_pdf_{rc}"
        )
        if st.button("➕ Agregar PDF", use_container_width=True) and pdf_up:
            st.session_state.orden_corte.append({
                "tipo": "pdf", "arch": pdf_up, "nom": pdf_up.name,
                "cn": cn_pdf, "sentido": sentido_pdf
            })

    if st.session_state.orden_corte:
        st.markdown("---")
        st.markdown("**📋 Lote en Mesa:**")
        for i, it in enumerate(st.session_state.orden_corte):
            if it["tipo"] == "cat":
                nom_p = it['pr'].split(' - ')[1]
                pzs = ', '.join(it['piezas'])
                txt = (
                    f"**{it['cn']}x {nom_p} ({it['ta']})** "
                    f"[{it['sentido']}]

*Piezas:* {pzs}"
                )
            else:
                txt = f"**{it['cn']}x PDF: {it['nom']}** [{it['sentido']}]"
            x1, x2 = st.columns([4.5, 1])
            x1.markdown(txt)
            if x2.button("🗑️", key=f"d_{rc}_{i}"):
                st.session_state.orden_corte.pop(i)
                st.rerun()

    st.markdown("---")
    st.subheader("2. Parámetros de Tela")
    ancho_t = st.number_input(
        "Ancho útil (cm):", 60.0, 300.0, 150.0, key=f"a_{rc}"
    )
    cm1, cm2 = st.columns(2)
    margen_t = cm1.number_input(
        "Margen (cm):", 0.0, 3.0, 0.8, key=f"m_{rc}"
    )
    paso_t = cm2.selectbox(
        "Precisión:", [1.0, 2.0, 3.0], index=1, key=f"s_{rc}"
    )
    calc = st.button("🚀 GENERAR PLANO DE CORTE", use_container_width=True)

with col2:
    if st.session_state.ver_prenda and not calc:
        st.subheader("👁️ Vista Previa de Prenda Terminada")
        fig_p, notas_conf = dibujar_prenda(pr)
        c_img, c_esp = st.columns([1.3, 1])
        c_img.pyplot(fig_p, use_container_width=True)
        with c_esp:
            st.markdown(f"### {pr.split(' - ')[1]}")
            st.success(f"**Acabados de Confección:**

{notas_conf}")
            st.info("**Piezas del molde:**

" + ", ".join(lista_pz))
            if st.button("❌ Cerrar vista previa"):
                st.session_state.ver_prenda = False
                st.rerun()
        st.markdown("---")

    st.subheader("3. Plano de Corte y Descarga")
    if calc:
        st.session_state.ver_prenda = False
        if not st.session_state.orden_corte:
            st.warning("Agrega al menos una prenda o PDF.")
        else:
            piezas = []
            for it in st.session_state.orden_corte:
                if it["tipo"] == "cat":
                    piezas.extend(crear_piezas(
                        it["pr"], it["ta"], it["cn"],
                        it["piezas"], it["sentido"]
                    ))
                else:
                    it["arch"].seek(0)
                    piezas.extend(
                        leer_pdf(it["arch"], it["sentido"]) * it["cn"]
                    )
            ubicadas, area_n, desc = anidar_piezas(
                piezas, ancho_t, margen_t, paso_t
            )
            if desc > 0:
                st.error(
                    f"⚠️ {desc} pieza(s) superan el ancho de "
                    f"{ancho_t} cm en esa dirección."
                )
            if ubicadas:
                fig, largo_f, efic_f = dibujar_plano(
                    ubicadas, ancho_t, area_n
                )
                m1, m2, m3 = st.columns(3)
                m1.metric("Metros Tela", f"{largo_f/100:.2f} m")
                m2.metric("Aprovechamiento", f"{efic_f:.1f} %")
                m3.metric("Total Piezas", f"{len(ubicadas)} uds")
                pdf_b, dxf_b = exportar_archivos(
                    fig, ubicadas, ancho_t, largo_f
                )
                b1, b2 = st.columns(2)
                b1.download_button(
                    "📥 Descargar PDF", pdf_b,
                    "Plano_Waldy.pdf", "application/pdf",
                    use_container_width=True
                )
                b2.download_button(
                    "📐 Descargar DXF", dxf_b,
                    "Trazo_Waldy.dxf", "application/dxf",
                    use_container_width=True
                )
                st.pyplot(fig, use_container_width=True)
    else:
        st.info(
            "👈 Elige la prenda, presiona **👁️ Visualizar prenda terminada** "
            "para revisar su confección, marca las piezas a cortar y "
            "agrégalas al lote."
        )
