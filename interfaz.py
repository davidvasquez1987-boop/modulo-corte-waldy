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

def reiniciar():
    st.session_state.orden_corte = []
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
            "margin:0;'>Waldy Uniformes • Control por Pieza "
            "y Corte Al Hilo o Al Través</p>"
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
            for _ in range(2):
                pts = [
                    (am * 0.15, 0), (am * 0.85, 0),
                    (am, lm * 0.75), (am * 0.5, lm),
                    (0, lm * 0.75)
                ]
                res.append({
                    "poly": aplicar_sentido(Polygon(pts), sentido),
                    "cat": "Manga", "sentido": sentido
                })

        if "Cuello" in piezas_sel:
            pts = [
                (0, 0), (7.5, 0),
                (7.5, w * 0.76), (0, w * 0.76)
            ]
            res.append({
                "poly": aplicar_sentido(Polygon(pts), sentido),
                "cat": "Cuello / Pretina", "sentido": sentido
            })

        if "Puños (x2)" in piezas_sel:
            for _ in range(2):
                pts = [(0, 0), (7.0, 0), (7.0, 23.0), (0, 23.0)]
                res.append({
                    "poly": aplicar_sentido(Polygon(pts), sentido),
                    "cat": "Bolsillo / Puño", "sentido": sentido
                })

        if "Bolsillo" in piezas_sel:
            pts = [(0, 0), (13.0, 0), (13.0, 15.0), (0, 15.0)]
            res.append({
                "poly": aplicar_sentido(Polygon(pts), sentido),
                "cat": "Bolsillo / Puño", "sentido": sentido
            })

        if "Bolsillos (x2)" in piezas_sel:
            for _ in range(2):
                pts = [(0, 0), (15.0, 0), (15.0, 17.0), (0, 17.0)]
                res.append({
                    "poly": aplicar_sentido(Polygon(pts), sentido),
                    "cat": "Bolsillo / Puño", "sentido": sentido
                })

        if "Piernas Delanteras (x2)" in piezas_sel:
            for _ in range(2):
                pts = [
                    (w * 0.15, 0), (w * 0.65, 0),
                    (w * 0.85, h * 0.72), (w, h * 0.76),
                    (w * 0.92, h), (w * 0.1, h)
                ]
                res.append({
                    "poly": aplicar_sentido(Polygon(pts), sentido),
                    "cat": "Delantero", "sentido": sentido
                })

        if "Piernas Traseras (x2)" in piezas_sel:
            for _ in range(2):
                pts = [
                    (w * 0.12, 0), (w * 0.72, 0),
                    (w * 0.95, h * 0.70), (w * 1.12, h * 0.75),
                    (w * 0.98, h * 1.03), (w * 0.08, h)
                ]
                res.append({
                    "poly": aplicar_sentido(Polygon(pts), sentido),
                    "cat": "Espalda", "sentido": sentido
                })

        if "Pretina" in piezas_sel:
            pts = [(0, 0), (9.0, 0), (9.0, w * 2.0), (0, w * 2.0)]
            res.append({
                "poly": aplicar_sentido(Polygon(pts), sentido),
                "cat": "Cuello / Pretina", "sentido": sentido
            })

        if "Paño Delantero" in piezas_sel:
            pts = [
                (0, 0), (w * 1.35, 0),
                (w * 1.15, h), (w * 0.2, h)
            ]
            res.append({
                "poly": aplicar_sentido(Polygon(pts), sentido),
                "cat": "Delantero", "sentido": sentido
            })

        if "Paño Trasero" in piezas_sel:
            pts = [
                (0, 0), (w * 1.35, 0),
                (w * 1.15, h), (w * 0.2, h)
            ]
            res.append({
                "poly": aplicar_sentido(Polygon(pts), sentido),
                "cat": "Espalda", "sentido": sentido
            })

        if "Cuerpo Delantero (x2)" in piezas_sel:
            for _ in range(2):
                pts = [
                    (w * 0.1, 0), (w * 0.55, 0),
                    (w * 0.65, h * 0.48), (w * 0.65, h * 0.90),
                    (w * 0.4, h), (0, h * 0.75)
                ]
                res.append({
                    "poly": aplicar_sentido(Polygon(pts), sentido),
                    "cat": "Delantero", "sentido": sentido
                })

        if "Cuerpo Trasero (x2)" in piezas_sel:
            for _ in range(2):
                pts = [
                    (w * 0.1, 0), (w * 0.60, 0),
                    (w * 0.72, h * 0.48), (w * 0.68, h * 0.96),
                    (w * 0.35, h), (0, h * 0.78)
                ]
                res.append({
                    "poly": aplicar_sentido(Polygon(pts), sentido),
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
                    pts.append((it[1].x, it[1].y))
                    pts.append((it[2].x, it[2].y))
                elif it[0] == 'c':
                    pts.append((it[1].x, it[1].y))
                    pts.append((it[3].x, it[3].y))
                elif it[0] == 're':
                    r = it[1]
                    pts.extend([
                        (r.x0, r.y0), (r.x1, r.y0),
                        (r.x1, r.y1), (r.x0, r.y1)
                    ])
        if len(pts) > 4:
            cm = [
                (round(p[0] / 28.35, 1), round(p[1] / 28.35, 1))
                for p in pts
            ]
            unicos = list(dict.fromkeys(cm))
            if len(unicos) > 3:
                try:
                    poly = Polygon(unicos).simplify(
                        0.4, preserve_topology=True
                    )
                    if poly.is_valid and not poly.is_empty:
                        if poly.area > 5:
                            res.append({
                                "poly": aplicar_sentido(poly, sentido),
                                "cat": "Molde PDF",
                                "sentido": sentido
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
        facecolor='#F1F5F9', edgecolor=OSCURO,
        linewidth=2, linestyle='--'
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
        est = COLORES.get(cat, COLORES["Bolsillo / Puño"])
        x, y = poly.exterior.xy
        ax.fill(
            x, y, facecolor=est["fill"], alpha=0.82,
            edgecolor=est["edge"], linewidth=1.3, zorder=3
        )

        cx, cy = poly.centroid.x, poly.centroid.y
        minx, miny, maxx, maxy = poly.bounds
        ap, lp = maxx - minx, maxy - miny

        if sent == "Al Hilo (0°)" and lp > 10:
            fl = min(lp * 0.25, 9)
            ax.annotate(
                '', xy=(cx, cy + fl), xytext=(cx, cy - fl),
                arrowprops=dict(
                    arrowstyle="<->", color='white', lw=1.0
                ),
                zorder=4
            )
        elif sent == "Al Través (90°)" and ap > 10:
            fl = min(ap * 0.25, 9)
            ax.annotate(
                '', xy=(cx + fl, cy), xytext=(cx - fl, cy),
                arrowprops=dict(
                    arrowstyle="<->", color='#FEF08A', lw=1.1
                ),
                zorder=4
            )

        if ap > 13:
            tag = "HILO" if sent == "Al Hilo (0°)" else "TRAV"
            lbl = f"{cat[:4].upper()} ({tag})\n{ap:.0f}x{lp:.0f}"
            ax.text(
                cx + 1.5, cy, lbl,
                fontsize=6.2, fontweight='bold', color='white',
                ha='left', va='center', zorder=5
            )

    parches = [
        mpatches.Patch(color=COLORES[c]["fill"], label=c)
        for c in COLORES if c in cats
    ]
    ax.legend(
        handles=parches, loc='upper center',
        bbox_to_anchor=(0.5, -0.05), ncol=3, fontsize=9
    )

    efic = (area_neta / (ancho_util * largo) * 100) if largo > 0 else 0
    titulo = (
        f"PLANO DE CORTE - WALDY UNIFORMES\n"
        f"Ancho: {ancho_util:.1f} cm | Largo: {largo/100:.2f} m | "
        f"Aprovechamiento: {efic:.1f}%"
    )
    ax.set_title(titulo, fontsize=11, fontweight='bold', color=OSCURO)
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
    marco = [(0, 0), (ancho, 0), (ancho, largo), (0, largo)]
    msp.add_lwpolyline(marco, close=True)
    for it in ubicadas:
        coords = list(it["poly"].exterior.coords)
        msp.add_lwpolyline(coords, close=True)
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
        pr = st.selectbox(
            "Prenda:", list(CATALOGO.keys()), key=f"p_{rc}"
        )
        ca, cb = st.columns(2)
        ta = ca.selectbox(
            "Talla:", list(TALLAS.keys()), index=6, key=f"t_{rc}"
        )
        cn = cb.number_input(
            "Cantidad:", 1, 200, 2, key=f"c_{rc}"
        )

        sentido_pr = st.radio(
            "Dirección de corte:",
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
                chk_key = f"chk_{rc}_{tipo_act}_{idx_p}"
                if st.checkbox(nom_pz, value=True, key=chk_key):
                    pz_elegidas.append(nom_pz)

        if st.button("➕ Agregar a la Orden", use_container_width=True):
            if not pz_elegidas:
                st.warning("Marca al menos una pieza.")
            else:
                nuevo_item = {
                    "tipo": "cat",
                    "pr": pr,
                    "ta": ta,
                    "cn": cn,
                    "piezas": pz_elegidas,
                    "sentido": sentido_pr
                }
                st.session_state.orden_corte.append(nuevo_item)
                st.toast(f"Agregado ({sentido_pr})", icon="✅")

    with t2:
        pdf_up = st.file_uploader(
            "Subir PDF:", type=["pdf"], key=f"f_{rc}"
        )
        cn_pdf = st.number_input(
            "Copias PDF:", 1, 100, 1, key=f"cp_{rc}"
        )
        sentido_pdf = st.radio(
            "Dirección PDF:",
            ["Al Hilo (0°)", "Al Través (90°)"],
            horizontal=True,
            key=f"sent_pdf_{rc}"
        )
        btn_pdf = st.button(
            "➕ Agregar PDF", use_container_width=True
        )
        if btn_pdf and pdf_up:
            nuevo_pdf = {
                "tipo": "pdf",
                "arch": pdf_up,
                "nom": pdf_up.name,
                "cn": cn_pdf,
                "sentido": sentido_pdf
            }
            st.session_state.orden_corte.append(nuevo_pdf)

    if st.session_state.orden_corte:
        st.markdown("---")
        st.markdown("**📋 Lote en Mesa:**")
        for i, it in enumerate(st.session_state.orden_corte):
            if it["tipo"] == "cat":
                resumen_pz = ", ".join(it["piezas"])
                nom_c = it["pr"].split(" - ")[1]
                txt = (
                    f"**{it['cn']}x {nom_c} ({it['ta']})** "
                    f"[{it['sentido']}]\n\n*Piezas:* {resumen_pz}"
                )
            else:
                txt = (
                    f"**{it['cn']}x PDF: {it['nom']}** "
                    f"[{it['sentido']}]"
                )
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
    calc = st.button(
        "🚀 GENERAR PLANO DE CORTE", use_container_width=True
    )

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

                b1, b2 = st.columns(2)
                b1.download_button(
                    "📥 Descargar PDF", a_pdf(fig),
                    "Plano_Waldy.pdf", "application/pdf",
                    use_container_width=True
                )
                b2.download_button(
                    "📐 Descargar DXF",
                    a_dxf(ubicadas, ancho_t, largo_f),
                    "Trazo_Waldy.dxf", "application/dxf",
                    use_container_width=True
                )
                st.pyplot(fig, use_container_width=True)
    else:
        guia = (
            "👈 **Cómo usar:** Elige la prenda, selecciona **Al Hilo** "
            "o **Al Través**, marca las piezas exactas que vas a cortar "
            "(cuello, mangas, delantero, espalda, bolsillos, etc.) "
            "y agrégalas al lote."
        )
        st.info(guia)