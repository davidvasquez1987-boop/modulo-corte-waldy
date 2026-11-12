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
                    pts.extend([(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1)])
        if len(pts) > 4:
            unicos = list(dict.fromkeys([(round(p[0]/28.35, 1), round(p[1]/28.35, 1)) for p in pts]))
            if len(unicos) > 3:
                try:
                    poly = Polygon(unicos).simplify(0.4, preserve_topology=True)
                    if poly.is_valid and not poly.is_empty and poly.area > 5:
                        res.append({"poly": rotar_sentido(poly, sentido), "cat": "Molde PDF", "sentido": sentido})
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
        proc.append({"poly": pm, "cat": it["cat"], "sentido": it["sentido"], "area": pm.area})
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
                    ubicadas.append({"poly": cand, "cat": it["cat"], "sentido": it["sentido"]})
                    ok = True
                    break
                x += paso
            y += paso
        barra.progress((idx + 1) / len(proc))
    barra.empty()
    return ubicadas, area_neta, desc

def dibujar_plano(ubicadas, ancho_util, area_neta):
    largo = max((u["poly"].bounds[3] for u in ubicadas), default=10.0)
    fig, ax = plt.subplots(figsize=(10, max(6.5, min(18.0, (largo / ancho_util) * 8.0))), dpi=150)
    ax.add_patch(plt.Rectangle((0, 0), ancho_util, largo + 5, fill=True, facecolor='#F1F5F9', edgecolor=OSCURO, lw=2, ls='--'))
    ax.annotate('', xy=(-2.5, largo), xytext=(-2.5, 0), arrowprops=dict(arrowstyle="<->", color=NARANJA, lw=2))
    ax.text(-3.8, largo/2, "HILO DE LA TELA (URDIMBRE 0°)", rotation=90, va='center', ha='center', fontsize=8, fontweight='bold', color=NARANJA)
    ax.grid(True, color='#CBD5E1', ls=':', lw=0.7)
    cats = set()
    for it in ubicadas:
        poly, cat, sent = it["poly"], it["cat"], it["sentido"]
        cats.add(cat)
        fill_c, edge_c = COLORES.get(cat, COLORES["Bolsillo / Puño"])
        x, y = poly.exterior.xy
        ax.fill(x, y, facecolor=fill_c, alpha=0.82, edgecolor=edge_c, lw=1.3, zorder=3)
        cx, cy = poly.centroid.x, poly.centroid.y
        mx, my, xx, xy = poly.bounds
        ap, lp = xx - mx, xy - my
        if sent == "Al Hilo (0°)" and lp > 10:
            fl = min(lp * 0.25, 9)
            ax.annotate('', xy=(cx, cy + fl), xytext=(cx, cy - fl), arrowprops=dict(arrowstyle="<->", color='white', lw=1), zorder=4)
        elif sent == "Al Través (90°)" and ap > 10:
            fl = min(ap * 0.25, 9)
            ax.annotate('', xy=(cx + fl, cy), xytext=(cx - fl, cy), arrowprops=dict(arrowstyle="<->", color='#FEF08A', lw=1.1), zorder=4)
        if ap > 13:
            tag = "HILO" if sent == "Al Hilo (0°)" else "TRAV"
            ax.text(cx + 1.5, cy, f"{cat[:4].upper()} ({tag})\n{ap:.0f}x{lp:.0f}", fontsize=6.2, fontweight='bold', color='white', va='center', zorder=5)
    parches = [mpatches.Patch(color=COLORES[c][0], label=c) for c in COLORES if c in cats]
    ax.legend(handles=parches, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3, fontsize=9)
    efic = (area_neta / (ancho_util * largo) * 100) if largo > 0 else 0
    ax.set_title(f"PLANO DE CORTE - WALDY UNIFORMES\nAncho: {ancho_util:.1f} cm | Largo: {largo/100:.2f} m | Aprovechamiento: {efic:.1f}%", fontsize=11, fontweight='bold', color=OSCURO)
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
    msp.add_lwpolyline([(0,0),(ancho,0),(ancho,largo),(0,largo)], close=True)
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
        sentido_pr = st.radio("Dirección de corte:", ["Al Hilo (0°)", "Al Través (90°)"], horizontal=True, key=f"sent_{rc}")
        tipo_act = CATALOGO[pr][2]
        lista_pz = PIEZAS_TIPO[tipo_act]
        st.markdown("**Selecciona las piezas a cortar:**")
        cols_pz = st.columns(2)
        pz_elegidas = [nom for idx, nom in enumerate(lista_pz) if cols_pz[idx % 2].checkbox(nom, value=True, key=f"chk_{rc}_{tipo_act}_{idx}")]
        b_add, b_ver = st.columns(2)
        if b_add.button("➕ Agregar Orden", use_container_width=True):
            if pz_elegidas:
                st.session_state.orden_corte.append({"tipo": "cat", "pr": pr, "ta": ta, "cn": cn, "piezas": pz_elegidas, "sentido": sentido_pr})
                st.toast(f"Agregado ({sentido_pr})", icon="✅")
            else:
                st.warning("Marca al menos una pieza.")
        if b_ver.button("👁️ Visualizar prenda terminada", use_container_width=True):
            st.session_state.ver_prenda = True
    with t2:
        pdf_up = st.file_uploader("Subir PDF:", type=["pdf"], key=f"f_{rc}")
        cn_pdf = st.number_input("Copias PDF:", 1, 100, 1, key=f"cp_{rc}")
        sentido_pdf = st.radio("Dirección PDF:", ["Al Hilo (0°)", "Al Través (90°)"], horizontal=True, key=f"sent_pdf_{rc}")
        if st.button("➕ Agregar PDF", use_container_width=True) and pdf_up:
            st.session_state.orden_corte.append({"tipo": "pdf", "arch": pdf_up, "nom": pdf_up.name, "cn": cn_pdf, "sentido": sentido_pdf})

    if st.session_state.orden_corte:
        st.markdown("---")
        st.markdown("**📋 Lote en Mesa:**")
        for i, it in enumerate(st.session_state.orden_corte):
            txt = f"**{it['cn']}x {it['pr'].split(' - ')[1]} ({it['ta']})** [{it['sentido']}]\n\n*Piezas:* {', '.join(it['piezas'])}" if it["tipo"] == "cat" else f"**{it['cn']}x PDF: {it['nom']}** [{it['sentido']}]"
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
    if st.session_state.ver_prenda and not calc:
        st.subheader("👁️ Vista Previa de Prenda Terminada")
        fig_p, notas_conf = dibujar_prenda(pr)
        c_img, c_esp = st.columns([1.3, 1])
        c_img.pyplot(fig_p, use_container_width=True)
        with c_esp:
            st.markdown(f"### {pr.split(' - ')[1]}")
            st.success(f"**Acabados de Confección:**\n\n{notas_conf}")
            st.info("**Piezas del molde:**\n\n" + ", ".join(lista_pz))
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
                    piezas.extend(crear_piezas(it["pr"], it["ta"], it["cn"], it["piezas"], it["sentido"]))
                else:
                    it["arch"].seek(0)
                    piezas.extend(leer_pdf(it["arch"], it["sentido"]) * it["cn"])
            ubicadas, area_n, desc = anidar_piezas(piezas, ancho_t, margen_t, paso_t)
            if desc > 0:
                st.error(f"⚠️ {desc} pieza(s) superan el ancho de {ancho_t} cm en esa dirección.")
            if ubicadas:
                fig, largo_f, efic_f = dibujar_plano(ubicadas, ancho_t, area_n)
                m1, m2, m3 = st.columns(3)
                m1.metric("Metros Tela", f"{largo_f/100:.2f} m")
                m2.metric("Aprovechamiento", f"{efic_f:.1f} %")
                m3.metric("Total Piezas", f"{len(ubicadas)} uds")
                pdf_b, dxf_b = exportar_archivos(fig, ubicadas, ancho_t, largo_f)
                b1, b2 = st.columns(2)
                b1.download_button("📥 Descargar PDF", pdf_b, "Plano_Waldy.pdf", "application/pdf", use_container_width=True)
                b2.download_button("📐 Descargar DXF", dxf_b, "Trazo_Waldy.dxf", "application/dxf", use_container_width=True)
                st.pyplot(fig, use_container_width=True)
    else:
        st.info("👈 Elige la prenda, presiona **👁️ Visualizar prenda terminada** para revisar su confección, marca las piezas a cortar y agrégalas al lote.")