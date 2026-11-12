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
    "Espalda": {"fill": "#E9531E", "edge": "#9A3412"},          # Naranja Waldy
    "Delantero": {"fill": "#138A36", "edge": "#064E3B"},        # Verde Waldy
    "Manga": {"fill": "#F59E0B", "edge": "#92400E"},            # Ámbar industrial
    "Cuello / Pretina": {"fill": "#0284C7", "edge": "#075985"}, # Azul técnico
    "Bolsillo / Detalle": {"fill": "#64748B", "edge": "#1E293B"},# Gris acero
    "Molde PDF": {"fill": "#138A36", "edge": "#E9531E"}         # Combinación corporativa
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
                st.markdown(f"""
                <svg viewBox="0 0 420 265" xmlns="http://www.w3.org/2000/svg" style="width:100%; max-width:220px; display:block; margin:auto;">
                  <rect width="420" height="265" fill="#F8F9FA" rx="6"/>
                  <path d="M22,22 C22,12 38,12 38,22 L38,85 C38,95 52,95 52,85 L52,55 C52,45 68,45 68,55 L68,85 C68,95 82,95 82,85 L82,22 C82,12 98,12 98,22 L98,88 C98,112 72,118 60,104 C48,118 22,112 22,88 Z" fill="{COLOR_NARANJA_WALDY}"/>
                  <path d="M158,42 C130,42 110,60 110,80 C110,100 130,115 158,115 L164,115 L164,42 Z M148,96 C134,96 126,88 126,79 C126,70 134,61 148,61 L148,96 Z" fill="{COLOR_NARANJA_WALDY}"/>
                  <rect x="176" y="42" width="17" height="73" rx="8" fill="{COLOR_NARANJA_WALDY}"/>
                  <path d="M254,14 L254,42 L248,42 C220,42 204,58 204,79 C204,100 220,115 248,115 L270,115 L270,14 C270,6 254,6 254,14 Z M254,96 L248,96 C232,96 221,89 221,79 C221,69 232,61 248,61 L254,61 Z" fill="{COLOR_NARANJA_WALDY}"/>
                  <path d="M282,48 L282,85 C282,106 298,116 320,116 L326,116 L326,48 C326,40 310,40 310,48 L310,96 C302,96 298,91 298,83 L298,48 C298,40 282,40 282,48 Z" fill="{COLOR_NARANJA_WALDY}"/>
                  <rect x="333" y="42" width="17" height="73" rx="4" fill="{COLOR_NARANJA_WALDY}"/>
                  <rect x="333" y="123" width="17" height="22" rx="2" fill="{COLOR_NARANJA_WALDY}"/>
                  <path d="M324,123 L26,123 C20,123 16,127 16,133 L16,240 C16,246 20,250 26,250 L340,250 C346,250 350,246 350,240 L350,153 L327,153 L327,227 L39,227 L39,146 L324,146 Z" fill="{COLOR_VERDE_WALDY}"/>
                  <text x="183" y="207" font-family="Arial Narrow, Impact, sans-serif" font-weight="900" font-size="52" fill="{COLOR_NARANJA_WALDY}" text-anchor="middle" letter-spacing="1">UNIFORMES</text>
                </svg>
                """, unsafe_allow_html=True)
                
        with col_titulo:
            st.markdown(f"<h1 style='color:{COLOR_OSCURO}; margin-bottom:0; font-size:26px;'>Módulo CAD/CAM de Patronaje y Corte Textil</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:{COLOR_VERDE_WALDY}; font-weight:700; font-size:15px; margin-top:4px;'>Línea Escolar y Dotación Empresarial • Tendido Estrictamente al Hilo de Tela (Urdimbre)</p>", unsafe_allow_html=True)
            
        with col_reset:
            if st.button("🔄 Reiniciar Todo", use_container_width=True, help="Borrar lote acumulado, parámetros y reiniciar"):
                reiniciar_sistema()
                st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)

# --- 1. CATÁLOGO DE PRENDAS (ESCOLAR Y EMPRESARIAL) ---
# Nota técnica: Todas las piezas se construyen con X = Ancho (Trama) e Y = Largo (Hilo/Urdimbre)
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
    """
    Genera polígonos anatómicos orientados estrictamente AL HILO DE LA TELA:
    Eje X = Ancho (Trama) | Eje Y = Largo vertical de la prenda (Urdimbre / Hilo).
    """
    info = CATALOGO_PRENDAS[prenda_nombre]
    factor = FACTORES_TALLA[talla]
    w = info["base_w"] * factor
    h = info["base_h"] * factor
    tipo = info["tipo"]
    
    piezas_orden = []
    
    for idx in range(1, cantidad + 1):
        etiqueta_base = f"{prenda_nombre.split(' - ')[1]} ({talla}) #{idx}"
        
        if tipo in ["superior_manga_larga", "superior_manga_corta", "chaqueta"]:
            # 1. Espalda (Largo H en Y al hilo)
            espalda = Polygon([
                (0, 0), (w, 0), (w, h * 0.65), (w * 0.85, h * 0.72),
                (w * 0.82, h * 0.95), (w * 0.65, h), (w * 0.35, h),
                (w * 0.18, h * 0.95), (w * 0.15, h * 0.72), (0, h * 0.65)
            ])
            piezas_orden.append({"poly": espalda, "categoria": "Espalda", "nombre": f"Espalda {etiqueta_base}"})
            
            # 2. Delanteros Izq/Der (Largo H en Y al hilo)
            for lado in ["Izq", "Der"]:
                delantero = Polygon([
                    (0, 0), (w * 0.52, 0), (w * 0.52, h * 0.86),
                    (w * 0.35, h * 0.98), (w * 0.15, h * 0.72), (0, h * 0.65)
                ])
                piezas_orden.append({"poly": delantero, "categoria": "Delantero", "nombre": f"Delantero {lado} {etiqueta_base}"})
            
            # 3. Mangas Izq/Der (Largo de manga en Y al hilo)
            largo_m = h * 0.85 if tipo != "superior_manga_corta" else h * 0.38
            ancho_m = w * 0.44
            for m_lado in ["Izq", "Der"]:
                manga = Polygon([
                    (ancho_m * 0.15, 0), (ancho_m * 0.85, 0),
                    (ancho_m, largo_m * 0.75), (ancho_m * 0.5, largo_m),
                    (0, largo_m * 0.75)
                ])
                piezas_orden.append({"poly": manga, "categoria": "Manga", "nombre": f"Manga {m_lado} {etiqueta_base}"})
            
            # 4. Cuello (Pieza longitudinal en Y al hilo para evitar deformación)
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
            # Piernas Delanteras y Traseras (Largo pierna H en Y al hilo)
            for pierna in ["Izq", "Der"]:
                del_p = Polygon([(w*0.15, 0), (w*0.65, 0), (w*0.85, h*0.72), (w, h*0.76), (w*0.92, h), (w*0.1, h)])
                tras_p = Polygon([(w*0.12, 0), (w*0.72, 0), (w*0.95, h*0.70), (w*1.12, h*0.75), (w*0.98, h*1.03), (w*0.08, h)])
                piezas_orden.append({"poly": del_p, "categoria": "Delantero", "nombre": f"Pierna Del {pierna} {etiqueta_base}"})
                piezas_orden.append({"poly": tras_p, "categoria": "Espalda", "nombre": f"Pierna Tras {pierna} {etiqueta_base}"})
            # Pretina orientada verticalmente en Y al hilo
            pretina = Polygon([(0, 0), (9.0, 0), (9.0, w * 2.0), (0, w * 2.0)])
            piezas_orden.append({"poly": pretina, "categoria": "Cuello / Pretina", "nombre": f"Pretina {etiqueta_base}"})

        elif tipo == "falda":
            paño_del = Polygon([(0, 0), (w * 1.35, 0), (w * 1.15, h), (w * 0.2, h)])
            paño_tras = Polygon([(0, 0), (w * 1.35, 0), (w * 1.15, h), (w * 0.2, h)])
            pretina = Polygon([(0, 0), (8.5, 0), (8.5, w * 1.85), (0, w * 1.85)])
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

# --- 2. EXTRACCIÓN DESDE PDF EXTERNO (RESPETANDO ORIENTACIÓN AL HILO) ---
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

# --- 3. MOTOR DE ANIDADO ESTRICTO AL HILO DE LA TELA (SIN ROTACIÓN AL TRAVÉS) ---
def ejecutar_nesting_al_hilo(lista_piezas, ancho_util, margen_cm, paso_cm):
    """
    Optimiza el encaje de piezas desplazando únicamente en X e Y (0 grados).
    PROHIBIDA la rotación a 90 grados para garantizar que ninguna prenda se corte al través.
    """
    piezas_procesadas = []
    area_neta_piezas = 0.0
    piezas_descartadas = 0
    
    for item in lista_piezas:
        poly_margen = item["poly"].buffer(margen_cm, join_style=2)
        minx, miny, maxx, maxy = poly_margen.bounds
        if (maxx - minx) > ancho_util:
            piezas_descartadas += 1
            continue
        area_neta_piezas += poly_margen.area
        piezas_procesadas.append({
            "poly": poly_margen,
            "categoria": item["categoria"],
            "nombre": item["nombre"],
            "area": poly_margen.area
        })
    
    # Ordenar de mayor a menor área para compactar mejor el tendido al hilo
    piezas_procesadas.sort(key=lambda x: x["area"], reverse=True)
    
    ubicadas = []
    barra = st.progress(0)
    total = len(piezas_procesadas)
    
    for i, item in enumerate(piezas_procesadas):
        poly_base = item["poly"]
        minx, miny, maxx, maxy = poly_base.bounds
        ancho_pieza = maxx - minx
        pieza_norm = translate(poly_base, xoff=-minx, yoff=-miny)
        
        y_actual = 0.0
        encontrado = False
        
        while not encontrado:
            x_actual = 0.0
            while x_actual + ancho_pieza <= ancho_util:
                candidato = translate(pieza_norm, xoff=x_actual, yoff=y_actual)
                if not any(candidato.intersects(u["poly"]) for u in ubicadas):
                    ubicadas.append({
                        "poly": candidato,
                        "categoria": item["categoria"],
                        "nombre": item["nombre"]
                    })
                    encontrado = True
                    break
                x_actual += paso_cm
            y_actual += paso_cm
            
        barra.progress((i + 1) / total)
        
    barra.empty()
    return ubicadas, area_neta_piezas, piezas_descartadas

# --- 4. VISUALIZACIÓN INDUSTRIAL CON FLECHAS DE HILO Y EXPORTACIÓN ---
def generar_plano_corte(ubicadas, ancho_util, area_neta):
    largo_max = max((u["poly"].bounds[3] for u in ubicadas), default=10.0)
    proporcion = max(6.5, min(18.0, (largo_max / ancho_util) * 8.0))
    
    fig, ax = plt.subplots(figsize=(10, proporcion), dpi=150)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#FAFAFA')
    
    # Dibujar rollo de tela
    ax.add_patch(plt.Rectangle((0, 0), ancho_util, largo_max + 5, fill=True, facecolor='#F1F5F9', edgecolor=COLOR_OSCURO, linewidth=2, linestyle='--'))
    
    # Flechas laterales indicando el sentido del HILO DE LA TELA (Urdimbre)
    ax.annotate('', xy=(-2.5, largo_max), xytext=(-2.5, 0),
                arrowprops=dict(arrowstyle="<->", color=COLOR_NARANJA_WALDY, lw=2))
    ax.text(-3.8, largo_max / 2, "SENTIDO DEL HILO DE LA TELA (URDIMBRE)", rotation=90,
            va='center', ha='center', fontsize=8, fontweight='bold', color=COLOR_NARANJA_WALDY)
    
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
        ax.fill(x, y, facecolor=estilo["fill"], alpha=0.80, edgecolor=estilo["edge"], linewidth=1.3, zorder=3)
        
        # Etiqueta y línea de aplome/hilo interna en cada pieza
        cx, cy = poly.centroid.x, poly.centroid.y
        minx, miny, maxx, maxy = poly.bounds
        ancho_p = maxx - minx
        largo_p = maxy - miny
        
        if ancho_p > 7 and largo_p > 12:
            # Línea vertical interna que marca el hilo en el molde
            flecha_len = min(largo_p * 0.25, 10)
            ax.annotate('', xy=(cx, cy + flecha_len), xytext=(cx, cy - flecha_len),
                        arrowprops=dict(arrowstyle="<->", color='white', lw=0.9, alpha=0.85), zorder=4)
            
        if ancho_p > 13:
            ax.text(cx + 1.5, cy, f"{cat[:4].upper()}\n{ancho_p:.0f}x{largo_p:.0f}", fontsize=6.5, fontweight='bold',
                    color='white', ha='left', va='center', zorder=5)

    # Leyenda de clasificación por colores
    parches_leyenda = [
        mpatches.Patch(color=COLORES_PIEZAS[c]["fill"], label=c)
        for c in COLORES_PIEZAS if c in categorias_presentes
    ]
    ax.legend(handles=parches_leyenda, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3, frameon=True, fontsize=9)
    
    area_tela_total = ancho_util * largo_max
    eficiencia = (area_neta / area_tela_total * 100) if area_tela_total > 0 else 0
    
    ax.set_title(
        f"PLANO DE CORTE AL HILO - WALDY UNIFORMES\n"
        f"Ancho Útil: {ancho_util:.1f} cm | Largo Total: {largo_max:.1f} cm ({largo_max/100:.2f} m) | Aprovechamiento: {eficiencia:.1f}%",
        fontsize=11, fontweight='bold', color=COLOR_OSCURO, pad=14
    )
    ax.set_xlabel("Ancho del Rollo Textil - Trama (cm)", fontsize=9, fontweight='bold', color=COLOR_OSCURO)
    ax.set_ylabel("Largo de Tendido - Al Hilo (cm)", fontsize=9, fontweight='bold', color=COLOR_OSCURO)
    ax.set_xlim(-6, ancho_util + 5)
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
    msp.add_lwpolyline([(0, 0), (ancho_util, 0), (ancho_util, largo_max), (0, largo_max)], close=True)
    for item in ubicadas:
        coords = list(item["poly"].exterior.coords)
        msp.add_lwpolyline(coords, close=True)
    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode('utf-8')

# --- 5. INTERFAZ DE USUARIO INTUITIVA ---
mostrar_encabezado()

rc = st.session_state.reset_counter
col_izq, col_der = st.columns([1.15, 2.1], gap="large")

with col_izq:
    st.markdown(f"<h3 style='color:{COLOR_NARANJA_WALDY};'>1. Configurar Orden de Corte</h3>", unsafe_allow_html=True)
    
    pestana_cat, pestana_pdf = st.tabs(["👕 Catálogo Waldy", "📄 Subir Molde PDF"])
    
    with pestana_cat:
        prenda_sel = st.selectbox("Selecciona la Prenda:", list(CATALOGO_PRENDAS.keys()), key=f"prenda_{rc}")
        c_talla, c_cant = st.columns(2)
        with c_talla:
            talla_sel = st.selectbox("Talla:", list(FACTORES_TALLA.keys()), index=6, key=f"talla_{rc}")
        with c_cant:
            cant_sel = st.number_input("Cantidad:", min_value=1, max_value=200, value=4, step=1, key=f"cant_{rc}")
            
        if st.button("➕ Agregar a la Orden de Tendido", use_container_width=True):
            st.session_state.orden_corte.append({
                "origen": "catalogo",
                "prenda": prenda_sel,
                "talla": talla_sel,
                "cantidad": cant_sel
            })
            st.toast(f"Agregado: {cant_sel}x {prenda_sel.split(' - ')[1]} ({talla_sel})", icon="✅")

    with pestana_pdf:
        archivo_pdf = st.file_uploader("Cargar archivo vectorial PDF:", type=["pdf"], key=f"pdf_{rc}")
        cant_pdf = st.number_input("Copias a tender del PDF:", min_value=1, max_value=100, value=1, key=f"cant_pdf_{rc}")
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

    # Resumen del lote acumulado
    if st.session_state.orden_corte:
        st.markdown("---")
        st.markdown(f"<h4 style='color:{COLOR_VERDE_WALDY};'>📋 Lote Acumulado en Mesa</h4>", unsafe_allow_html=True)
        for idx, item in enumerate(st.session_state.orden_corte):
            desc = f"**{item['cantidad']}x** {item['prenda'].split(' - ')[1]} (Talla {item['talla']})" if item["origen"] == "catalogo" else f"**{item['cantidad']}x** PDF: {item['nombre']}"
            c_txt, c_del = st.columns([4, 1])
            c_txt.markdown(desc)
            if c_del.button("🗑️", key=f"del_{rc}_{idx}", help="Eliminar ítem"):
                st.session_state.orden_corte.pop(idx)
                st.rerun()

    st.markdown("---")
    st.markdown(f"<h3 style='color:{COLOR_NARANJA_WALDY};'>2. Parámetros del Rollo Textil</h3>", unsafe_allow_html=True)
    ancho_tela = st.number_input("Ancho útil de tela (cm):", min_value=60.0, max_value=300.0, value=150.0, step=1.0, key=f"ancho_{rc}")
    col_m, col_p = st.columns(2)
    with col_m:
        margen = st.number_input("Margen costura (cm):", min_value=0.0, max_value=3.0, value=0.8, step=0.1, key=f"margen_{rc}")
    with col_p:
        paso = st.selectbox("Precisión encaje:", [1.0, 2.0, 3.0], index=1, key=f"paso_{rc}", help="Menor valor = mayor precisión de
