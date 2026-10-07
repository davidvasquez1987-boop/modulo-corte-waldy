import streamlit as st
import ezdxf
import fitz  # PyMuPDF para leer vectores de archivos PDF
from shapely.geometry import Polygon
from shapely.affinity import translate
import matplotlib.pyplot as plt

# --- 1. LECTOR DE MOLDES DESDE PDF VECTORIAL ---
def extraer_poligonos_desde_pdf(archivo_pdf):
    poligonos = []
    # Abrir el PDF desde el archivo cargado en memoria de Streamlit
    doc = fitz.open(stream=archivo_pdf.read(), filetype="pdf")
    
    for pagina in doc:
        # Extraer las rutas vectoriales del PDF
        lista_dibujos = pagina.get_drawings()
        for dibujo in lista_dibujos:
            puntos = []
            for item in dibujo["items"]:
                if item[0] == "l":  # Línea recta
                    puntos.append((item[1].x, item[1].y))
                    puntos.append((item[2].x, item[2].y))
                elif item[0] == "re": # Rectángulo
                    r = item[1]
                    puntos.extend([(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1)])
            
            if len(puntos) > 2:
                # Limpiar puntos duplicados y crear polígono
                puntos_unicos = list(dict.fromkeys(puntos))
                if len(puntos_unicos) > 2:
                    poly = Polygon(puntos_unicos)
                    if poly.is_valid and poly.area > 100: # Filtrar elementos muy pequeños
                        poligonos.append(poly)
                        
    return poligonos

# --- 2. GENERADOR MATEMÁTICO DINÁMICO (CATÁLOGO WLDY) ---
def generar_moldes_dinamicos(tipo_prenda, talla, cantidad):
    doc = ezdxf.new('R2000')
    msp = doc.modelspace()
    
    tabla_medidas = {
        "Chaqueta de Invierno": {
            "S": {"cuerpo": (55, 65), "manga": (22, 58), "cuello": (40, 8)},
            "M": {"cuerpo": (58, 68), "manga": (24, 60), "cuello": (42, 8)},
            "L": {"cuerpo": (61, 71), "manga": (26, 62), "cuello": (44, 9)},
            "XL": {"cuerpo": (64, 74), "manga": (28, 64), "cuello": (46, 9)}
        },
        "Chaqueta Impermeable (Seguridad)": {
            "S": {"cuerpo": (56, 66), "manga": (23, 59), "cuello": (41, 8)},
            "M": {"cuerpo": (59, 69), "manga": (25, 61), "cuello": (43, 8)},
            "L": {"cuerpo": (62, 72), "manga": (27, 63), "cuello": (45, 9)},
            "XL": {"cuerpo": (65, 75), "manga": (29, 65), "cuello": (47, 9)}
        },
        "Chaleco Reflectivo": {
            "S": {"cuerpo": (52, 60), "manga": (15, 30), "cuello": (38, 6)},
            "M": {"cuerpo": (55, 63), "manga": (15, 30), "cuello": (40, 6)},
            "L": {"cuerpo": (58, 66), "manga": (15, 30), "cuello": (42, 7)},
            "XL": {"cuerpo": (61, 69), "manga": (15, 30), "cuello": (44, 7)}
        },
        "Camisa Casual / Empresarial": {
            "S": {"cuerpo": (50, 62), "manga": (20, 56), "cuello": (38, 7)},
            "M": {"cuerpo": (53, 65), "manga": (22, 58), "cuello": (40, 7)},
            "L": {"cuerpo": (56, 68), "manga": (24, 60), "cuello": (42, 8)},
            "XL": {"cuerpo": (59, 71), "manga": (26, 62), "cuello": (44, 8)}
        },
        "Camiseta Polo / Piqué": {
            "S": {"cuerpo": (48, 60), "manga": (18, 24), "cuello": (38, 6)},
            "M": {"cuerpo": (51, 63), "manga": (19, 25), "cuello": (40, 6)},
            "L": {"cuerpo": (54, 66), "manga": (20, 26), "cuello": (42, 7)},
            "XL": {"cuerpo": (57, 69), "manga": (21, 27), "cuello": (44, 7)}
        },
        "Pantalón Gabardina Industrial": {
            "S": {"cuerpo": (45, 98), "manga": (32, 95), "cuello": (25, 12)},
            "M": {"cuerpo": (48, 100), "manga": (34, 97), "cuello": (27, 12)},
            "L": {"cuerpo": (51, 102), "manga": (36, 99), "cuello": (29, 13)},
            "XL": {"cuerpo": (54, 104), "manga": (38, 101), "cuello": (31, 13)}
        }
    }
    
    medidas = tabla_medidas[tipo_prenda][talla]
    c_w, c_h = medidas["cuerpo"]
    m_w, m_h = medidas["manga"]
    cu_w, cu_h = medidas["cuello"]
    
    for _ in range(cantidad):
        msp.add_lwpolyline([(0,0), (c_w,0), (c_w,c_h), (0,c_h)], close=True)
        msp.add_lwpolyline([(0,0), (c_w/2,0), (c_w/2,c_h*0.7), (c_w/3,c_h*0.85), (0,c_h)], close=True)
        msp.add_lwpolyline([(0,0), (c_w/2,0), (c_w/2,c_h), (c_w/3,c_h*0.85), (0,c_h*0.7)], close=True)
        msp.add_lwpolyline([(0,0), (m_w,0), (m_w,m_h), (0,m_h)], close=True)
        msp.add_lwpolyline([(0,0), (m_w,0), (m_w,m_h), (0,m_h)], close=True)
        msp.add_lwpolyline([(0,0), (cu_w,0), (cu_w,cu_h), (0,cu_h)], close=True)
        
    return msp

def extraer_poligonos_desde_msp(msp):
    poligonos = []
    for entidad in msp.query('LWPOLYLINE'):
        puntos = entidad.get_points('xy')
        if len(puntos) > 2:
            poly = Polygon(puntos)
            if poly.is_valid:
                poligonos.append(poly)
    return poligonos

def aplicar_margen(poligonos, margen_cm):
    return [pieza.buffer(margen_cm, join_style=2) for pieza in poligonos]

def optimizacion_geometrica(piezas, ancho_util, paso_cm):
    piezas.sort(key=lambda p: p.area, reverse=True)
    piezas_ubicadas = []
    
    progress_bar = st.progress(0)
    total_piezas = len(piezas)

    for indice, pieza in enumerate(piezas):
        minx, miny, maxx, maxy = pieza.bounds
        pieza_centrada = translate(pieza, xoff=-minx, yoff=-miny)
        ubicado = False
        x_actual = 0.0
        y_actual = 0.0
        
        while not ubicado:
            candidato = translate(pieza_centrada, xoff=x_actual, yoff=y_actual)
            _, _, c_maxx, _ = candidato.bounds
            
            if c_maxx > ancho_util:
                x_actual = 0.0
                y_actual += paso_cm
                continue
                
            colision = any(candidato.intersects(p_fija) for p_fija in piezas_ubicadas)
            
            if not colision:
                piezas_ubicadas.append(candidato)
                ubicado = True
            else:
                x_actual += paso_cm
        
        progress_bar.progress((indice + 1) / total_piezas)
        
    return piezas_ubicadas

def visualizar_mesa_corte(piezas_ubicadas, ancho_util):
    fig, ax = plt.subplots(figsize=(8, 12))
    largo_consumido = 0
    for pieza in piezas_ubicadas:
        x, y = pieza.exterior.xy
        ax.plot(x, y, color='#2c3e50', linewidth=1.5, zorder=2)
        ax.fill(x, y, alpha=0.4, color='#3498db')
        _, _, _, maxy = pieza.bounds
        if maxy > largo_consumido:
            largo_consumido = maxy
            
    ax.plot([0, ancho_util, ancho_util, 0, 0], [0, 0, largo_consumido + 10, largo_consumido + 10, 0], color='#e74c3c', linestyle='--', label='Borde Textil')
    plt.title(f"Módulo CAD/CAM - Ancho: {ancho_util}cm | Largo consumido: {largo_consumido:.2f}cm")
    plt.axis('equal')
    plt.xlim(-10, ancho_util + 10)
    plt.ylim(-10, largo_consumido + 20)
    return fig, largo_consumido

# --- 3. DISEÑO DE LA INTERFAZ WEB ---
st.set_page_config(page_title="Módulo de Corte - Waldy", layout="wide")
st.title("✂️ Panel de Producción y Anidado - Waldy Uniformes")
st.markdown("Calcula el consumo textil mediante catálogo estándar o cargando moldes personalizados en PDF.")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("📋 Origen del Molde")
    
    # Opción para elegir entre catálogo o archivo PDF externo
    modo_fuente = st.radio("Seleccionar fuente de moldes:", ["Catálogo Estándar Waldy", "Subir Molde Externo (PDF)"])
    
    piezas_base = []
    
    if modo_fuente == "Subir Molde Externo (PDF)":
        archivo_pdf_subido = st.file_uploader("Cargar archivo PDF de patrones", type=["pdf"])
        cantidad_pdf = st.number_input("Multiplicar este molde por cuántas unidades", min_value=1, value=1, step=1)
    else:
        tipo_prenda = st.selectbox(
            "Tipo de Prenda", 
            [
                "Chaqueta de Invierno", 
                "Chaqueta Impermeable (Seguridad)", 
                "Chaleco Reflectivo", 
                "Camisa Casual / Empresarial", 
                "Camiseta Polo / Piqué", 
                "Pantalón Gabardina Industrial"
            ]
        )
        talla = st.selectbox("Talla", ["S", "M", "L", "XL"])
        cantidad = st.number_input("Cantidad de prendas", min_value=1, value=5, step=1)
    
    st.markdown("---")
    st.header("⚙️ Parámetros de Tela")
    ancho_tela = st.number_input("Ancho útil de la tela (cm)", min_value=50.0, value=150.0, step=1.0)
    margen = st.number_input("Margen de costura (cm)", min_value=0.0, value=1.0, step=0.1)
    paso = st.slider("Precisión de encaje", min_value=1.0, max_value=5.0, value=2.0, step=0.5)
    
    iniciar = st.button("🚀 Calcular Trazo y Tela", use_container_width=True)

with col2:
    st.header("📊 Resultados del Sistema")
    if iniciar:
        if modo_fuente == "Subir Molde Externo (PDF)":
            if archivo_pdf_subido is not None:
                st.info("Leyendo vectores geométricos del PDF...")
                piezas_individuales = extraer_poligonos_desde_pdf(archivo_pdf_subido)
                # Multiplicar por la cantidad solicitada
                piezas_base = piezas_individuales * cantidad_pdf
                st.success(f"Se extrajeron y multiplicaron {len(piezas_base)} piezas del PDF.")
            else:
                st.error("Por favor, sube un archivo PDF antes de calcular.")
                st.stop()
        else:
            st.info(f"Generando moldes virtuales para {cantidad} unidades de {tipo_prenda} (Talla {talla})...")
            msp_generado = generar_moldes_dinamicos(tipo_prenda, talla, cantidad)
            piezas_base = extraer_poligonos_desde_msp(msp_generado)
            st.success(f"Se estructuraron {len(piezas_base)} piezas vectoriales correctamente.")
        
        if piezas_base:
            st.warning("Calculando optimización geométrica y colisiones en la mesa de corte...")
            piezas_expandidas = aplicar_margen(piezas_base, margen)
            piezas_optimizadas = optimizacion_geometrica(piezas_expandidas, ancho_tela, paso)
            
            fig, largo_total = visualizar_mesa_corte(piezas_optimizadas, ancho_tela)
            metros_totales = largo_total / 100
            
            st.markdown("### 🧵 Resumen de Consumo para Compra")
            st.metric(label="Largo Total de Textil Requerido", value=f"{metros_totales:.2f} Metros", delta=f"{largo_total:.1f} cm")
            
            st.pyplot(fig)
    else:
        st.info("👈 Selecciona si usarás el catálogo o un PDF en el panel izquierdo y presiona el botón para calcular.")
