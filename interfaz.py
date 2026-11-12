import streamlit as st
import ezdxf
import fitz  # PyMuPDF
import numpy as np
from shapely.geometry import Polygon
from shapely.affinity import translate, rotate
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
    "Espalda": {"fill": "#E9531E", "edge": "#9A3412"},      # Naranja Waldy
    "Delantero": {"fill": "#138A36", "edge": "#064E3B"},    # Verde Waldy
    "Manga": {"fill": "#F59E0B", "edge": "#92400E"},        # Ámbar industrial
    "Cuello / Pretina": {"fill": "#0284C7", "edge": "#075985"}, # Azul técnico
    "Bolsillo / Detalle": {"fill": "#64748B", "edge": "#1E293B"}, # Gris acero
    "Molde PDF": {"fill": "#138A36", "edge": "#E9531E"}     # Combinación corporativa
}

# --- CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS ---
st.set_page_config(
    page_title="CAD/CAM Corte Industrial | Waldy Uniformes",
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
        padding: 0.6rem 1.2rem;
        font-size: 16px;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        background-color: {COLOR_VERDE_WALDY};
        color: white;
    }}
    .header-box {{
        background-color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        border-left: 8px solid {COLOR_NARANJA_WALDY};
        border-bottom: 3px solid {COLOR_VERDE_WALDY};
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
    }}
    .metric-card {{
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        border-top: 4px solid {COLOR_VERDE_WALDY};
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }}
</style>
""", unsafe_allow_html=True)

# --- ENCABEZADO CORPORATIVO CON LOGO ---
def mostrar_encabezado():
    with st.container():
        st.markdown('<div class="header-box">', unsafe_allow_html=True)
        col_logo, col_titulo = st.columns([1.2, 4])
        
        with col_logo:
            # Busca automáticamente el archivo del logo en la carpeta del proyecto
            rutas_posibles = [
                "logo_waldy.png", 
                "logo_waldy.jpg", 
                "logo_waldy.jpeg",
                "WhatsApp Image 2026-11-08 at 6.57.34 PM.jpeg"
            ]
            logo_cargado = False
            for ruta in rutas_posibles:
                if os.path.exists(ruta):
                    img = Image.open(ruta)
                    st.image(img, use_container_width=True)
                    logo_cargado = True
                    break
            if not logo_cargado:
                # Respaldo vectorial tipográfico si no encuentra el archivo de imagen
                st.markdown(f"""
                <div style="text-align:center; font-family:sans-serif;">
                    <span style="color:{COLOR_NARANJA_WALDY}; font-size:36px; font-weight:900; letter-spacing:-1px;">Waldy</span><br>
                    <span style="color:{COLOR_VERDE_WALDY}; font-size:14px; font-weight:800; border:2px solid {COLOR_VERDE_WALDY}; padding:2px 8px; border-radius:4px;">UNIFORMES</span>
                </div>
                """, unsafe_allow_html=True)
                
        with col_titulo:
            st.markdown(f"<h1 style='color:{COLOR_OSCURO}; margin-bottom:0;'>Sistema CAD/CAM de Patronaje y Optimización de Corte</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:{COLOR_VERDE_WALDY}; font-weight:600; font-size:16px; margin-top:4px;'>Gestión Industrial de Tendido Textil • Línea Escolar y Dotación Empresarial</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- 1. CATÁLOGO AMPLIADO (ESCOLAR Y EMPRESARIAL) ---
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

def generar_geometria_anatomica(prenda_nombre, talla, cantidad):
    """Genera polígonos anatómicos reales clasificados por pieza y color."""
    info = CATALOGO_PRENDAS[prenda_nombre]
    factor = FACTORES_TALLA[talla]
    w = info["base_w"] * factor
    h = info["base_h"] * factor
    tipo = info["tipo"]
    
    piezas_orden = []
    
    for idx in range(1, cantidad + 1):
        etiqueta_base = f"{prenda_nombre.split(' - ')[1]} ({talla}) #{idx}"
        
        if tipo in ["superior_manga_larga", "superior_manga_corta", "chaqueta"]:
            # 1. Espalda con caída de hombro y curva de sisa
            espalda = Polygon([
                (0, 0), (w, 0), (w, h * 0.65), (w * 0.85, h * 0.72),
                (w * 0.82, h * 0.95), (w * 0.65, h), (w * 0.35, h),
                (w * 0.18, h * 0.95), (w * 0.15, h * 0.72), (0, h * 0.65)
            ])
            piezas_orden.append({"poly": espalda, "categoria": "Espalda", "nombre": f"Espalda {etiqueta_base}"})
            
            # 2. Delanteros (Izquierdo y Derecho con escote pronunciado)
            for lado in ["Izq", "Der"]:
                delantero = Polygon([
                    (0, 0), (w * 0.52, 0), (w * 0.52, h * 0.86),
                    (w * 0.35, h * 0.98), (w * 0.15, h * 0.72), (0, h * 0.65)
                ])
                piezas_orden.append({"poly": delantero, "categoria": "Delantero", "nombre": f"Delantero {lado} {etiqueta_base}"})
            
            # 3. Mangas (x2) con copa anatómica
            largo_m = h * 0.85 if tipo != "superior_manga_corta" else h * 0.38
            ancho_m = w * 0.44
            for m_lado in ["Izq", "Der"]:
                manga = Polygon([
                    (ancho_m * 0.15, 0), (ancho_m * 0.85, 0),
                    (ancho_m, largo_m * 0.75), (ancho_m * 0.5, largo_m),
                    (0, largo_m * 0.75)
                ])
                piezas_orden.append({"poly": manga, "categoria": "Manga", "nombre": f"Manga {m_lado} {etiqueta_base}"})
            
            # 4. Cuello
            cuello = Polygon([(0, 0), (w * 0.78, 0), (w * 0.74, 7.5), (w * 0.04, 7.5)])
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
            # Delanteros x2 y Traseros x2 con tiro anatómico
            for pierna in ["Izq", "Der"]:
                del_p = Polygon([(w*0.15, 0), (w*0.65, 0), (w*0.85, h*0.72), (w, h*0.76), (w*0.92, h), (w*0.1, h)])
                tras_p = Polygon([(w*0.12, 0), (w*0.72, 0), (w*0.95, h*0.70), (w*1.12, h*0.75), (w*0.98, h*1.03), (w*0.08, h)])
                piezas_orden.append({"poly": del_p, "categoria": "Delantero", "nombre": f"Pierna Del {pierna} {etiqueta_base}"})
                piezas_orden.append({"poly": tras_p, "categoria": "Espalda", "nombre": f"Pierna Tras {pierna} {etiqueta_base}"})
            pretina = Polygon([(0, 0), (w * 2.1, 0), (w * 2.1, 9.0), (0, 9.0)])
            piezas_orden.append({"poly": pretina, "categoria": "Cuello / Pretina", "nombre": f"Pretina {etiqueta_base}"})

        elif tipo == "falda":
            paño_del = Polygon([(0, 0), (w * 1.35, 0), (w * 1.15, h), (w * 0.2, h)])
            paño_tras = Polygon([(0, 0), (w * 1.35, 0), (w * 1.15, h), (w * 0.2, h)])
            pretina = Polygon([(0, 0), (w * 1.9, 0), (w * 1.9, 8.5), (0, 8.5)])
            piezas_orden.append({"poly": paño_del, "categoria": "Delantero", "nombre": f"Paño Del {etiqueta_base}"})
            piezas_orden.append({"poly": paño_tras, "categoria": "Espalda", "nombre": f"Paño Tras {etiqueta_base}"})
            piezas_orden.append({"poly": pretina, "categoria": "Cuello / Pretina", "nombre": f"Pretina {etiqueta_base}"})

        elif tipo == "overol":
            for lado in ["Izq", "Der"]:
                cuerpo_del = Polygon([(w*0.1, 0), (w*0.55, 0), (w*0.65, h*0.48), (w*0.65, h*0.90), (w*0.4, h), (w*0.15, h*0.82), (0, h*0.75)])
                cuerpo_tras = Polygon([(w*0.1, 0), (w*0.60, 0), (w*0.72, h*0.48), (w*0.68, h*0.96), (w*0.35, h), (0, h*0.78)])
                manga = Polygon([(w*0.08, 0), (w*0.42, 0), (w*0.48, h*0.32), (w*0.24, h*0.42), (0, h*0.32)])
                piezas_orden.append({"poly": cuerpo_del, "categoria": "Delantero", "nombre": f"Cuerpo Del {lado} {etiqueta_base}"})
                piezas_orden.append({"poly": cuerpo_tras, "categoria": "Espalda", "nombre": f"Cuerpo Tras {lado} {etiqueta_base}"})
                piezas_orden.append({"poly": manga, "categoria": "Manga", "nombre": f"Manga {lado} {etiqueta_base}"})

    return piezas_orden

# --- 2. EXTRACCIÓN DESDE PDF EXTERNO ---
def extraer_poligonos_desde_pdf(archivo_pdf):
    piezas_pdf = []
    doc = fitz.open(stream=archivo_pdf.read(), filetype="pdf")
    for idx_pag, pagina in enumerate(doc):
        paths = pagina.get_drawings()
        puntos_pagina = []
        for path in paths:
            for item in path.get("items", []):
                if item[0] == 'l':
                    puntos_pagina.extend([(item[1].x, item[1].y), (item[2].x, item[2].y)])
                elif item[0] == 'c':
                    puntos_pagina.extend([(item[1].x, item[1].y), (item[3].x, item[3].y)])
                elif item[0] == 're':
                    r = item[1]
                    puntos_pagina.extend([(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1)])
        if len(puntos_pagina) > 4:
            puntos_cm = [(round(p[0] / 28.35, 1), round(p[1] / 28.35, 1)) for p in puntos_pagina]
            puntos_unicos = list(dict.fromkeys(puntos_cm))
            if len(puntos_unicos) > 3:
                try:
                    poly = Polygon(puntos_unicos).simplify(0.4, preserve_topology=True)
                    if poly.is_valid and not poly.is_empty and poly.area > 5:
                        piezas_pdf.append({"poly": poly, "categoria": "Molde PDF", "nombre": f"Pieza PDF Pág {idx_pag+1}"})
                except Exception:
                    pass
    return piezas_pdf

# --- 3. MOTOR DE ANIDADO GEOMÉTRICO CON ROTACIÓN Y EFICIENCIA ---
def ejecutar_nesting_profesional(lista_piezas, ancho_util, margen_cm, paso_cm, permitir_rotacion=True):
    # Aplicar margen de costura
    piezas_procesadas = []
    area_neta_piezas = 0.0
    
    for item in lista_piezas:
        poly_margen = item["poly"].buffer(margen_cm, join_style=2)
        area_neta_piezas += poly_margen.area
        piezas_procesadas.append({
            "poly": poly_margen,
            "categoria": item["categoria"],
            "nombre": item["nombre"],
            "area": poly_margen.area
        })
    
    # Ordenar de mayor a menor área (estrategia Best-Fit Decreasing)
    piezas_procesadas.sort(key=lambda x: x["area"], reverse=True)
    
    ubicadas = []
    barra = st.progress(0)
    total = len(piezas_procesadas)
    
    for i, item in enumerate(piezas_procesadas):
        poly_base = item["poly"]
        orientaciones = [poly_base]
        if permitir_rotacion:
            orientaciones.append(rotate(poly_base, 90, origin='centroid'))
            
        mejor_candidato = None
        mejor_y = float('inf')
        mejor_x = float('inf')
        
        for orient in orientaciones:
            minx, miny, maxx, maxy = orient.bounds
            if (maxx - minx) > ancho_util:
                continue
            pieza_norm = translate(orient, xoff=-minx, yoff=-miny)
            
            y_actual = 0.0
            encontrado = False
            while not encontrado:
                x_actual = 0.0
                while x_actual + (maxx - minx) <= ancho_util:
                    candidato = translate(pieza_norm, xoff=x_actual, yoff=y_actual)
                    if not any(candidato.intersects(u["poly"]) for u in ubicadas):
                        # Priorizar menor altura Y y luego menor X
                        if (y_actual < mejor_y) or (y_actual == mejor_y and x_actual < mejor_x):
                            mejor_y = y_actual
                            mejor_x = x_actual
                            mejor_candidato = candidato
                        encontrado = True
                        break
                    x_actual += paso_cm
                y_actual += paso_cm
                
        if mejor_candidato is not None:
            ubicadas.append({
                "poly": mejor_candidato,
                "categoria": item["categoria"],
                "nombre": item["nombre"]
            })
        barra.progress((i + 1) / total)
        
    barra.empty()
    return ubicadas, area_neta_piezas

# --- 4. VISUALIZACIÓN INDUSTRIAL Y EXPORTACIÓN ---
def generar_plano_corte(ubicadas, ancho_util, area_neta):
    largo_max = max((u["poly"].bounds[3] for u in ubicadas), default=10.0)
    proporcion = max(6.0, min(18.0, (largo_max / ancho_util) * 8.0))
    
    fig, ax = plt.subplots(figsize=(10, proporcion), dpi=150)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#FAFAFA')
    
    # Dibujar mesa / rollo de tela
    ax.add_patch(plt.Rectangle((0, 0), ancho_util, largo_max + 5, fill=True, facecolor='#F1F5F9', edgecolor=COLOR_OSCURO, linewidth=2, linestyle='--'))
    
    # Cuadrícula técnica cada 10 cm
    ax.set_xticks(np.arange(0, ancho_util + 10, 10))
    ax.set_yticks(np.arange(0, largo_max + 15, 10))
    ax.grid(True, which='both', color='#CBD5E1', linestyle=':', linewidth=0.7)
    
    categorias_presentes = set()
    
    for item in ubicadas:
        poly = item["poly"]
        cat = item["categoria"]
        categorias_presentes.add(cat)
        estilo = COLORES_PIEZAS.get(cat, COLORES_PIEZAS["Bolsillo / Detalle"])
        
        x, y = poly.exterior.xy
        ax.fill(x, y, facecolor=estilo["fill"], alpha=0.78, edgecolor=estilo["edge"], linewidth=1.3, zorder=3)
        
        # Etiqueta interna en el centroide de cada pieza
        cx, cy = poly.centroid.x, poly.centroid.y
        minx, miny, maxx, maxy = poly.bounds
        ancho_p = maxx - minx
        if ancho_p > 12:
            ax.text(cx, cy, f"{cat[:4].upper()}\n{ancho_p:.0f}x{maxy-miny:.0f}", fontsize=6.5, fontweight='bold',
                    color='white', ha='center', va='center', zorder=4)

    # Leyenda de clasificación por colores
    parches_leyenda = [
        mpatches.Patch(color=COLORES_PIEZAS[c]["fill"], label=c)
        for c in COLORES_PIEZAS if c in categorias_presentes
    ]
    ax.legend(handles=parches_leyenda, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3, frameon=True, fontsize=9)
    
    area_tela_total = ancho_util * largo_max
    eficiencia = (area_neta / area_tela_total * 100) if area_tela_total > 0 else 0
    
    ax.set_title(
        f"PLANO DE CORTE INDUSTRIAL - WALDY UNIFORMES\n"
        f"Ancho Útil: {ancho_util:.1f} cm | Largo Total: {largo_max:.1f} cm ({largo_max/100:.2f} m) | Aprovechamiento: {eficiencia:.1f}%",
        fontsize=11, fontweight='bold', color=COLOR_OSCURO, pad=14
    )
    ax.set_xlabel("Ancho del Rollo Textil (cm)", fontsize=9, fontweight='bold', color=COLOR_OSCURO)
    ax.set_ylabel("Largo de Tendido (cm)", fontsize=9, fontweight='bold', color=COLOR_OSCURO)
    ax.set_xlim(-5, ancho_util + 5)
    ax.set_ylim(-5, largo_max + 8)
    ax.set_aspect('equal')
    plt.tight_layout()
    
    return fig, largo_max, eficiencia

def exportar_pdf_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="pdf", bbox_inches="tight")
    buf.seek(0)
    return buf.getvalue()

def exportar_dxf_bytes(ubicadas, ancho_util, largo_max):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    # Dibujar marco de tela
    msp.add_lwpolyline([(0, 0), (ancho_util, 0), (ancho_util, largo_max), (0, largo_max)], close=True)
    for item in ubicadas:
        coords = list(item["poly"].exterior.coords)
        msp.add_lwpolyline(coords, close=True)
    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode('utf-8')

# --- 5. INTERFAZ DE USUARIO INTUITIVA ---
mostrar_encabezado()

# Inicializar lista de orden de producción en sesión
if "orden_corte" not in st.session_state:
    st.session_state.orden_corte = []

col_izq, col_der = st.columns([1.15, 2.1], gap="large")

with col_izq:
    st.markdown(f"<h3 style='color:{COLOR_NARANJA_WALDY};'>1. Configurar Orden de Corte</h3>", unsafe_allow_html=True)
    
    pestana_cat, pestana_pdf = st.tabs(["👕 Catálogo Waldy", "📄 Subir Molde PDF"])
    
    with pestana_cat:
        prenda_sel = st.selectbox("Selecciona la Prenda:", list(CATALOGO_PRENDAS.keys()))
        c_talla, c_cant = st.columns(2)
        with c_talla:
            talla_sel = st.selectbox("Talla:", list(FACTORES_TALLA.keys()), index=6)
        with c_cant:
            cant_sel = st.number_input("Cantidad:", min_value=1, max_value=200, value=4, step=1)
            
        if st.button("➕ Agregar a la Orden de Tendido", use_container_width=True):
            st.session_state.orden_corte.append({
                "origen": "catalogo",
                "prenda": prenda_sel,
                "talla": talla_sel,
                "cantidad": cant_sel
            })
            st.toast(f"Agregado: {cant_sel}x {prenda_sel.split(' - ')[1]} ({talla_sel})", icon="✅")

    with pestana_pdf:
        archivo_pdf = st.file_uploader("Cargar archivo vectorial PDF:", type=["pdf"])
        cant_pdf = st.number_input("Copias a tender del PDF:", min_value=1, max_value=100, value=1)
        if st.button("➕ Agregar PDF a la Orden", use_container_width=True):
            if archivo_pdf is not None:
                st.session_state.orden_corte.append({
                    "origen": "pdf",
                    "archivo": archivo_pdf,
                    "nombre": archivo_pdf.name,
                    "cantidad": cant_pdf
                })
                st.toast(f"PDF '{archivo_pdf.name}' agregado.", icon="📄")
            else:
                st.warning("Sube primero un archivo PDF.")

    # Mostrar resumen de la orden acumulada (permite mezclar tallas y prendas en un mismo tendido)
    if st.session_state.orden_corte:
        st.markdown("---")
        st.markdown(f"<h4 style='color:{COLOR_VERDE_WALDY};'>📋 Lote Acumulado en Mesa</h4>", unsafe_allow_html=True)
        for idx, item in enumerate(st.session_state.orden_corte):
            desc = f"**{item['cantidad']}x** {item['prenda'].split(' - ')[1]} (Talla {item['talla']})" if item["origen"] == "catalogo" else f"**{item['cantidad']}x** PDF: {item['nombre']}"
            c_txt, c_del = st.columns([4, 1])
            c_txt.markdown(desc)
            if c_del.button("🗑️", key=f"del_{idx}", help="Eliminar ítem"):
                st.session_state.orden_corte.pop(idx)
                st.rerun()
        if st.button("🧹 Vaciar Todo el Lote", use_container_width=True):
            st.session_state.orden_corte = []
            st.rerun()

    st.markdown("---")
    st.markdown(f"<h3 style='color:{COLOR_NARANJA_WALDY};'>2. Parámetros del Rollo Textil</h3>", unsafe_allow_html=True)
    ancho_tela = st.number_input("Ancho útil de tela (cm):", min_value=60.0, max_value=300.0, value=150.0, step=1.0)
    col_m, col_p = st.columns(2)
    with col_m:
        margen = st.number_input("Margen costura (cm):", min_value=0.0, max_value=3.0, value=0.8, step=0.1)
    with col_p:
        paso = st.selectbox("Precisión encaje:", [1.0, 2.0, 3.0], index=1, help="Menor valor = mayor precisión de encaje")
    rotacion_activa = st.checkbox("Permitir rotación 90° (Optimizar ahorro)", value=True)
    
    calcular = st.button("🚀 GENERAR PLANO DE CORTE OPTIMIZADO", use_container_width=True)

with col_der:
    st.markdown(f"<h3 style='color:{COLOR_VERDE_WALDY};'>3. Visualización y Descarga del Plano</h3>", unsafe_allow_html=True)
    
    if calcular:
        if not st.session_state.orden_corte:
            st.warning("⚠️ Agrega al menos una prenda o molde PDF en el panel izquierdo antes de calcular.")
        else:
            todas_las_piezas = []
            for item in st.session_state.orden_corte:
                if item["origen"] == "catalogo":
                    todas_las_piezas.extend(generar_geometria_anatomica(item["prenda"], item["talla"], item["cantidad"]))
                else:
                    item["archivo"].seek(0)
                    piezas_ext = extraer_poligonos_desde_pdf(item["archivo"])
                    todas_las_piezas.extend(piezas_ext * item["cantidad"])
            
            if not todas_las_piezas:
                st.error("No se pudieron procesar piezas válidas para el corte.")
            else:
                with st.spinner("Optimizando geometrías en mesa de corte Waldy..."):
                    ubicadas, area_neta = ejecutar_nesting_profesional(
                        todas_las_piezas, ancho_tela, margen, paso, rotacion_activa
                    )
                    fig, largo_final, eficiencia = generar_plano_corte(ubicadas, ancho_tela, area_neta)
                
                # Tarjetas de métricas industriales
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Metros Requeridos", f"{largo_final / 100:.2f} m", f"{largo_final:.1f} cm")
                m2.metric("Aprovechamiento", f"{eficiencia:.1f} %", f"Merma: {100 - eficiencia:.1f}%")
                m3.metric("Total Piezas", f"{len(ubicadas)} uds", "Clasificadas")
                m4.metric("Ancho de Rollo", f"{ancho_tela:.0f} cm", f"Margen: {margen} cm")
                
                st.markdown("---")
                
                # Botones de descarga profesional
                d1, d2 = st.columns(2)
                pdf_bytes = exportar_pdf_bytes(fig)
                dxf_bytes = exportar_dxf_bytes(ubicadas, ancho_tela, largo_final)
                
                with d1:
                    st.download_button(
                        label="📥 Descargar Plano Final en PDF (Impresión / Plotter)",
                        data=pdf_bytes,
                        file_name="Plano_Corte_Waldy_Uniformes.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                with d2:
                    st.download_button(
                        label="📐 Descargar Vectores CAD (.DXF)",
                        data=dxf_bytes,
                        file_name="Trazo_CAD_Waldy_Uniformes.dxf",
                        mime="application/dxf",
                        use_container_width=True
                    )
                
                st.pyplot(fig, use_container_width=True)
    else:
        st.info(
            "👈 **Instrucciones rápidas:**\n"
            "1. Selecciona las prendas escolares o empresariales (puedes combinar varias tallas y referencias en un mismo tendido) y haz clic en **Agregar a la Orden**.\n"
            "2. Ajusta el ancho de la tela y presiona **GENERAR PLANO DE CORTE OPTIMIZADO**.\n"
            "3. Revisa la clasificación por colores y descarga tu plano final en **PDF** o **DXF**."
        )
