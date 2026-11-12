import streamlit as st
import ezdxf
import fitz
import numpy as np
from shapely.geometry import Polygon
from shapely.affinity import translate, rotate
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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

st.markdown(
    "<style>"
    f".main {{ background-color: {FONDO}; }}"
    f".stButton>button {{ background-color: {NARANJA}; color: white; "
    "font-weight: bold; border-radius: 8px; border: none; }}"
    f".stButton>button:hover {{ background-color: {VERDE}; color: white; }}"
    "</style>",
    unsafe_allow_html=True
)

if "orden_corte" not in st.session_state:
    st.session_state.orden_corte = []
if "rc" not in st.session_state:
    st.session_state.rc = 0

def reiniciar():
    st.session_state.orden_corte = []
    st.session_state.rc += 1

def svg_logo():
    s = [
        '<svg viewBox="0 0 420 265" xmlns="http://www.w3.org/2000/svg" ',
        'style="width:100%;max-width:210px;display:block;margin:auto;">',
        '<rect width="420" height="265" fill="#F8F9FA" rx="6"/>',
        f'<path d="M22,22 C22,12 38,12 38,22 L38,85 C38,95 52,95 52,85 ',
        'L52,55 C52,45 68,45 68,55 L68,85 C68,95 82,95 82,85 L82,22 ',
        'C82,12 98,12 98,22 L98,88 C98,112 72,118 60,104 ',
        f'C48,118 22,112 22,88 Z" fill="{NARANJA}"/>',
        f'<path d="M158,42 C130,42 110,60 110,80 C110,100 130,115 158,115 ',
        'L164,115 L164,42 Z M148,96 C134,96 126,88 126,79 ',
        f'C126,70 134,61 148,61 L148,96 Z" fill="{NARANJA}"/>',
        f'<rect x="176" y="42" width="17" height="73" rx="8" fill="{NARANJA}"/>',
        f'<path d="M254,14 L254,42 L248,42 C220,42 204,58 204,79 ',
        'C204,100 220,115 248,115 L270,115 L270,14 C270,6 254,6 254,14 Z ',
        'M254,96 L248,96 C232,96 221,89 221,79 C221,69 232,61 248,61 ',
        f'L254,61 Z" fill="{NARANJA}"/>',
        f'<path d="M282,48 L282,85 C282,106 298,116 320,116 L326,116 ',
        'L326,48 C326,40 310,40 310,48 L310,96 C302,96 298,91 298,83 ',
        f'L298,48 C298,40 282,40 282,48 Z" fill="{NARANJA}"/>',
        f'<rect x="333" y="42" width="17" height="73" rx="4" fill="{NARANJA}"/>',
        f'<rect x="333" y="123" width="17" height="22" rx="2" fill="{NARANJA}"/>',
        f'<path d="M324,123 L26,123 C20,123 16,127 16,133 L16,240 ',
        'C16,246 20,250 26,250 L340,250 C346,250 350,246 350,240 L350,153 ',
        f'L327,153 L327,227 L39,227 L39,146 L324,146 Z" fill="{VERDE}"/>',
        '<text x="183" y="207" font-family="Arial Narrow, Impact, sans-serif" ',
        f'font-weight="900" font-size="52" fill="{NARANJA}" ',
        'text-anchor="middle" letter-spacing="1">UNIFORMES</text></svg>'
    ]
    return "".join(s)

def encabezado():
    c1, c2, c3 = st.columns([1.3, 3.7, 1.1], vertical_alignment="center")
    with c1:
        rutas = [
            "logo_waldy.jpeg", "logo_waldy.jpg", "logo_waldy.png",
            "WhatsApp Image 2026-11-08 at 6.57.34 PM.jpeg"
        ]
        encontrado = next((r for r in rutas if os.path.exists(r)), None)
        if encontrado:
            st.image(Image.open(encontrado), use_container_width=True)
        else:
            st.markdown(svg_logo(), unsafe_allow_html=True)
    with c2:
        st.markdown(
            f"<h2 style='color:{OSCURO};margin:0;'>"
            "Módulo CAD/CAM de Corte Textil - Waldy Uniformes</h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='color:{VERDE};font-weight:700;margin:0;'>"
            "Control por Pieza • Corte Al Hilo o Al Través por Prenda</p>",
            unsafe_allow_html=True
        )
    with c3:
        if st.button("🔄 Reiniciar Todo", use_container_width=True):
            reiniciar()
            st.rerun()
    st.markdown("---")

CATALOGO = {
    "🏫 Escolar - Camisa / Blusa Colegial": (46, 58, "sup_larga"),
    "🏫 Escolar - Camiseta Polo Institucional": (45, 56, "sup_corta"),
    "🏫 Escolar - Chaqueta Sudadera": (50, 60, "chaqueta"),
    "🏫 Escolar - Pantalón Sudadera": (36, 88, "pantalon"),
    "🏫 Escolar - Pantalón Clásico / Diario": (38, 92, "pantalon"),
    "🏫 Escolar - Jardinera / Falda Tableada": (44, 52, "falda"),
    "🏢 Empresarial - Camisa Oxford Manga Larga": (52, 68, "sup_larga"),
    "🏢 Empresarial - Camiseta Polo Piqué": (50, 65, "sup_corta"),
    "🏢 Empresarial - Chaqueta Impermeable": (56, 70, "chaqueta"),
    "🏢 Empresarial - Chaleco Reflectivo": (53, 63, "chaleco"),
    "🏢 Empresarial - Pantalón Drill / Gabardina": (44, 100, "pantalon"),
    "🏢 Empresarial - Overol Enterizo": (55, 145, "overol"),
}

PIEZAS_POR_TIPO = {
    "sup_larga": ["Espalda", "Delanteros (x2)", "Mangas (x2)",
                  "Cuello", "Puños (x2)", "Bolsillo"],
    "sup_corta": ["Espalda", "Delanteros (x2)", "Mangas (x2)",
                  "Cuello", "Bolsillo"],
    "chaqueta": ["Espalda", "Delanteros (x2)", "Mangas (x2)",
                 "Cuello", "Puños (x2)", "Bolsillos (x2)"],
    "chaleco": ["Espalda", "Delanteros (x2)", "Cuello", "Bolsillos (x2)"],
    "pantalon": ["Piernas Delanteras (x2)", "Piernas Traseras (x2)",
                 "Pretina", "Bolsillos (x2)"],
    "falda": ["Paño Delantero", "Paño Trasero", "Pretina", "Bolsillo"],
    "overol": ["Cuerpo Delantero (x2)", "Cuerpo Trasero (x2)",
               "Mangas (x2)", "Cuello", "Bolsillos (x2)"]
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
            esp = Polygon([
                (0, 0), (w, 0), (w, h * 0.65), (w * 0.82, h * 0.95),
                (w * 0.65, h), (w * 0.35, h), (w * 0.18, h * 0.95),
                (0, h * 0.65)
            ])
            res.append({
                "poly": aplicar_sentido(esp, sentido),
                "cat": "Espalda", "sentido": sentido
            })

        if "Delanteros (x2)" in piezas_sel:
            for _ in range(2):
                d = Polygon([
                    (0, 0), (w * 0.52, 0), (w * 0.52, h * 0.86),
                    (w * 0.35, h * 0.98), (0, h * 0.65)
                ])
                res.append({
                    "poly": aplicar_sentido(d, sentido),
                    "cat": "Delantero", "sentido": sentido
                })

        if "Mangas (x2)" in piezas_sel:
            lm = h * 0.85 if tipo != "sup_corta" else h * 0.38
            if tipo == "overol":
                lm = h * 0.34
            am = w * 0.44
            for _ in range(2):
                m = Polygon([
                    (am * 0.15, 0), (am * 0.85, 0), (am, lm * 0.75),
                    (am * 0.5, lm), (0, lm * 0.75)
                ])
                res.append({
                    "poly": aplicar_sentido(m, sentido),
                    "cat": "Manga", "sentido": sentido
                })

        if "Cuello" in piezas_sel:
            c = Polygon([(0, 0), (7.5, 0), (7.5, w * 0.76), (0, w * 0.76)])
            res.append({
                "poly": aplicar_sentido(c, sentido),
                "cat": "Cuello / Pretina", "sentido": sentido
            })

        if "Puños (x2)" in piezas_sel:
            for _ in range(2):
                pu = Polygon([(0, 0), (7.0, 0), (7.0, 23.0), (0, 23.0)])
                res.append({
                    "poly": aplicar_sentido(pu, sentido),
                    "cat": "Bolsillo / Puño", "sentido": sentido
                })

        if "Bolsillo" in piezas_sel:
            bo = Polygon([(0, 0), (13.0, 0), (13.0, 15.0), (0, 15.0)])
            res.append({
                "poly": aplicar_sentido(bo, sentido),
                "cat": "Bolsillo / Puño", "sentido": sentido
            })

        if "Bolsillos (x2)" in piezas_sel:
            for _ in range(2):
                bo = Polygon([(0, 0), (15.0, 0), (15.0, 17.0), (0, 17.0)])
                res.append({
                    "poly": aplicar_sentido(bo, sentido),
                    "cat": "Bolsillo / Puño", "sentido": sentido
                })

        if "Piernas Delanteras (x2)" in piezas_sel:
            for _ in range(2):
                dp = Polygon([
                    (w * 0.15, 0), (w * 0.65, 0), (w * 0.85, h * 0.72),
                    (w, h * 0.76), (w * 0.92, h), (w * 0.1, h)
                ])
                res.append({
                    "poly": aplicar_sentido(dp, sentido),
                    "cat": "Delantero", "sentido": sentido
                })

        if "Piernas Traseras (x2)" in piezas_sel:
            for _ in range(2):
                tp = Polygon([
                    (w * 0.12, 0), (w * 0.72, 0), (w * 0.95, h * 0.70),
                    (w * 1.12, h * 0.75), (w * 0.98, h * 1.03), (w * 0.08, h)
                ])
                res.append({
                    "poly": aplicar_sentido(tp, sentido),
                    "cat": "Espalda", "sentido": sentido
                })

        if "Pretina" in piezas_sel:
            pr = Polygon([(0, 0), (9.0, 0), (9.0, w * 2.0), (0, w * 2.0)])
            res.append({
                "poly": aplicar_sentido(pr, sentido),
                "cat": "Cuello / Pretina", "sentido": sentido
            })

        if "Paño Delantero" in piezas_sel:
            pa = Polygon([(0, 0), (w * 1.35, 0), (w * 1.15, h), (w * 0.2, h)])
            res.append({
                "poly": aplicar_sentido(pa, sentido),
                "cat": "Delantero", "sentido": sentido
            })

        if "Paño Trasero" in piezas_sel:
            pa = Polygon([(0, 0), (w * 1.35, 0), (w * 1.15, h), (w * 0.2, h)])
            res.append({
                "poly": aplicar_sentido(pa, sentido),
                "cat": "Espalda", "sentido": sentido
            })

        if "Cuerpo Delantero (x2)" in piezas_sel:
            for _ in range(2):
                cd = Polygon([
                    (w * 0.1, 0), (w * 0.55, 0), (w * 0.65, h * 0.48),
                    (w * 0.65, h * 0.90), (w * 0.4, h), (0, h * 0.75)
                ])
                res.append({
                    "poly": aplicar_sentido(cd, sentido),
                    "cat": "Delantero", "sentido": sentido
                })

        if "Cuerpo Trasero (x2)" in piezas_sel:
            for _ in range(2):
                ct = Polygon([
                    (w * 0.1, 0), (w * 0.60, 0), (w * 0.72, h * 0.48),
                    (w * 0.68, h * 0.96), (w * 0.35, h), (0, h * 0.78)
                ])
                res.append({
                    "poly": aplicar_sentido(ct, sentido),
                    "cat": "Espalda", "sentido": sentido
                })

    return res

def leer_pdf(archivo, sentido):
    res = []
    doc = fitz.open(stream=archivo.read(), filetype="pdf")
    for pag in doc:
        pts = []
        for path in pag.get_drawings():
            for it in path.get("items", []):
                if it[0] == 'l':
                    pts.extend([(it[1].x, it[1].y), (it[2].x, it[2].y)])
                elif it[0] == 'c':
                    pts.extend([(it[1].x, it[1].y), (it[3].x, it[3].y)])
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
                            "poly": aplicar_sentido(poly, sentido),
                            "cat": "Molde PDF", "sentido": sentido
                        })
                except Exception:
                    pass
    return res

def anidar_piezas(piezas, ancho_util, margen, paso):
    proc = []
    area_neta = 0.0
    descartadas = 0
    for it in piezas:
        pm = it["poly"].buffer(margen, join_style=2)
        minx, miny, maxx, maxy = pm.bounds
        if (maxx - minx) > ancho_util:
            descartadas += 1
            continue
        area_neta += pm.area
        proc.append({
            "poly": pm, "cat": it["cat"],
            "sentido": it["sentido"], "area": pm.area
        })

    proc.sort(key=lambda x: x["area"], reverse=True)
    ubicadas = []
    barra = st.progress(0)
    tot = len(proc)

    for i, it in enumerate(proc):
        pb = it["poly"]
        minx, miny, maxx, maxy = pb.bounds
        ap = maxx - minx
        pn = translate(pb, xoff=-minx, yoff=-miny)
        y = 0.0
        ok = False
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
        barra.progress((i + 1) / tot)
    barra.empty()
    return ubicadas, area_neta, descartadas

def dibujar_plano(ubicadas, ancho_util, area_neta):
    largo = max((u["poly"].bounds[3] for u in ubicadas), default=10.0)
    prop = max(6.5, min(18.0, (largo / ancho_util) * 8.0))
    fig, ax = plt.subplots(figsize=(10, prop), dpi=150)

    ax.add_patch(plt.Rectangle(
        (0, 0), ancho_util, largo + 5, fill=True,
        facecolor='#F1F5F9', edgecolor=OSCURO, linewidth=2, linestyle='--'
    ))
    ax.annotate(
        '', xy=(-2.5, largo), xytext=(-2.5, 0),
        arrowprops=dict(arrowstyle="<->", color=NARANJA, lw=2)
    )
    ax.text(
        -3.8, largo / 2, "HILO DE LA TELA (URDIMBRE 0°)",
        rotation=90, va='center', ha='center', fontsize=8,
        fontweight='bold', color=NARANJA
    )
    ax.grid(True, color='#CBD5E1', linestyle=':', linewidth=0.7)

    cats = set()
    for it in ubicadas:
        poly = it["poly"]
        cat = it["cat"]
        sent = it["sentido"]
        cats.add(cat)
        est = COLORES.get(cat, COLORES["Bolsillo / Detalle"])
        x, y = poly.exterior.xy
        ax.fill(x, y, facecolor=est["fill"], alpha=0.82,
                edgecolor=est["edge"], linewidth=1.3, zorder=3)

        cx, cy = poly.centroid.x, poly.centroid.y
        minx, miny, maxx, maxy = poly.bounds
        ap, lp = maxx - minx, maxy - miny

        # Flecha vertical si es Al Hilo, horizontal si es Al Través
        if sent == "Al Hilo (0°)" and lp > 10:
            fl = min(lp * 0.25, 9)
            ax.annotate(
                '', xy=(cx, cy + fl), xytext=(cx, cy - fl),
                arrowprops=dict(arrowstyle="<->", color='white', lw=1.0),
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
                cx + 1.5, cy, f"{cat[:4].upper()} ({tag})\n{ap:.0f}x{lp:.0f}",
                fontsize=6.2, fontweight='bold', color='white',
                ha='left', va='center', zorder=5
            )

    parches = [
        mpatches.Patch(color=COLORES[c]["fill"], label=c)
        for c in COLORES if c in cats
    ]
    ax.legend(handles=parches, loc='upper center',
              bbox_to_anchor=(0.5, -0.05), ncol=3, fontsize=9)

    efic = (area_neta / (ancho_util * largo) * 100) if largo > 0 else 0
    ax.set_title(
        f"PLANO DE CORTE INDUSTRIAL - WALDY UNIFORMES\n"
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

def a_pdf(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="pdf", bbox_inches="tight")
    buf.seek(0)
    return buf.getvalue()

def a_dxf(ubicadas, ancho, largo):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    msp.add_lwpolyline(
        [(0, 0), (ancho, 0), (ancho, largo), (0, largo)], close=True
    )
    for it in ubicadas:
        msp.add_lwpolyline(list(it["poly"].exterior.coords), close=True)
    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode('utf-8')

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
            "Dirección de corte para esta prenda:",
            ["Al Hilo (0°)", "Al Través (90°)"],
            horizontal=True,
            key=f"sent_{rc}"
        )

        tipo_act = CATALOGO[pr][2]
        lista_pz = PIEZAS_POR_TIPO[tipo_act]
        st.markdown("**Selecciona las piezas a cortar:**")
        cols_pz = st.columns(2)
        pz_elegidas = []
        for idx_p, nom_pz in enumerate(lista_pz):
            with cols_pz[idx_p % 2]:
                if st.checkbox(nom_pz, value=True, key=f"chk_{rc}_{tipo_act}_{idx_p}"):
                    pz_elegidas.append(nom_pz)

        if st.button("➕ Agregar Selección a la Orden", use_container_width=True):
            if not pz_elegidas:
                st.warning("Marca al menos una pieza para agregar.")
            else:
                st.session_state.orden_corte.append({
                    "tipo": "cat", "pr": pr, "ta": ta, "cn": cn,
                    "piezas": pz_elegidas, "sentido": sentido_pr
                })
                st.toast(f"Agregado ({sentido_pr})", icon="✅")

    with t2:
        pdf_up = st.file_uploader("Subir PDF:", type=["pdf"], key=f"f_{rc}")
        cn_pdf = st.number_input("Copias PDF:", 1, 100, 1, key=f"cp_{rc}")
        sentido_pdf = st.radio(
            "Dirección del molde PDF:",
            ["Al Hilo (0°)", "Al Través (90°)"],
            horizontal=True,
            key=f"sent_pdf_{rc}"
        )
        if st.button("➕ Agregar PDF a la Orden", use_container_width=True) and pdf_up:
            st.session_state.orden_corte.append({
                "tipo": "pdf", "arch": pdf_up, "nom": pdf_up.name,
                "cn": cn_pdf, "sentido": sentido_pdf
            })

    if st.session_state.orden_corte:
        st.markdown("---")
        st.markdown("**📋 Lote Acumulado en Mesa:**")
        for i, it in enumerate(st.session_state.orden_corte):
            if it["tipo"] == "cat":
                resumen_pz = ", ".join(it["piezas"])
                txt = (
                    f"**{it['cn']}x {it['pr'].split(' - ')[1]} ({it['ta']})** "
                    f"[{it['sentido']}]\n\n*Piezas:* {resumen_pz}"
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
    ancho_t = st.number_input("Ancho útil (cm):", 60.0, 300.0, 150.0, key=f"a_{rc}")
    cm1, cm2 = st.columns(2)
    margen_t = cm1.number_input("Margen (cm):", 0.0, 3.0, 0.8, key=f"m_{rc}")
    paso_t = cm2.selectbox("Precisión:", [1.0, 2.0, 3.0], index=1, key=f"s_{rc}")
    calc = st.button("🚀 GENERAR PLANO DE CORTE", use_container_width=True)

with col2:
    st.subheader("3. Plano de Corte y Descarga")
    if calc:
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
                    f"⚠️ {desc} pieza(s) superan el ancho de {ancho_t} cm "
                    "en la dirección elegida y no caben en el rollo."
                )

            if ubicadas:
                fig, largo_f, efic_f = dibujar_plano(ubicadas, ancho_t, area_n)
                m1, m2, m3 = st.columns(3)
                m1.metric("Metros Tela", f"{largo_f/100:.2f} m")
                m2.metric("Aprovechamiento", f"{efic_f:.1f} %")
                m3.metric("Total Piezas", f"{len(ubicadas)} uds")

                b1, b2 = st.columns(2)
                b1.download_button(
                    "📥 Descargar PDF", a_pdf(fig),
                    "Plano_Waldy.pdf", "application/pdf",
                    use_container_width=True
                )
                b2.download_button(
                    "📐 Descargar DXF", a_dxf(ubicadas, ancho_t, largo_f),
                    "Trazo_Waldy.dxf", "application/dxf",
                    use_container_width=True
                )
                st.pyplot(fig, use_container_width=True)
    else:
        st.info(
            "👈 **Cómo usar:** Elige la prenda, selecciona **Al Hilo** o "
            "**Al Través**, marca las piezas exactas que vas a cortar "
            "(cuello, mangas, delantero, espalda, bolsillos, etc.) y agrégalas "
            "al lote. Puedes mezclar prendas al hilo y al través en un mismo plano."
        )