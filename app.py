import streamlit as st
import requests
from datetime import date
import pandas as pd

# 1. Configuración de Marca y Estilo
st.set_page_config(page_title="PROINDUS | Gestión", page_icon="🏗️", layout="wide")

# CSS para inyectar un diseño blanco, limpio y profesional
# CSS para una legibilidad perfecta (Versión 2.0)
st.markdown("""
    <style>
    /* 1. Fondo general blanco */
    .main { background-color: #ffffff !important; }
    .stApp { background-color: #ffffff !important; }
    
    /* 2. Títulos y Etiquetas */
    h1 { color: #1a4a7c !important; font-weight: 800 !important; }
    h2, h3 { color: #2c3e50 !important; font-weight: 700 !important; margin-top: 20px !important; }
    label { color: #212529 !important; font-weight: 600 !important; font-size: 1rem !important; }

    /* 3. CORRECCIÓN: "Añadir Concepto" siempre en Negro */
    [data-testid="stExpander"] details summary p {
        color: #000000 !important;
        font-weight: white !important;
    }
    [data-testid="stExpander"] svg {
        fill: #000000 !important;
    }

    /* 4. CORRECCIÓN: Facturas y Presupuestos en Negro (No blanco) */
    [data-testid="stVerticalBlock"] p, 
    [data-testid="stVerticalBlock"] span,
    [data-testid="stCaptionContainer"] {
        color: #000000 !important;
        font-weight: 500 !important;
    }
    /* Forzamos que las referencias en negrita sean negras */
    strong { color: #000000 !important; }

    /* 5. Pestañas (Tabs) */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 2px solid #f0f2f6; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: transparent; 
        color: #95a5a6 !important; font-weight: 600; 
    }
    .stTabs [aria-selected="true"] { 
        color: #1a4a7c !important; 
        border-bottom: 3px solid #1a4a7c !important; 
    }

    /* 6. Métricas */
    [data-testid="stMetricValue"] { color: #1a4a7c !important; font-weight: 700 !important; }
    div[data-testid="metric-container"] {
        background-color: #f8fafd; border: 1px solid #e1e8f0; border-radius: 12px;
    }

    /* 7. Inputs y Botones */
    input, textarea { color: #000000 !important; background-color: #ffffff !important; }
    .stButton>button {
        border-radius: 8px; border: none; padding: 12px 28px;
        background-color: #1a4a7c; color: white !important;
        font-weight: 700; width: 100%;
    }
    .stButton>button:hover { background-color: #2c3e50; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

API_URL = "https://proyecto-personal-proindus.onrender.com"
#API_URL = "http://127.0.0.1:8000"

# --- FUNCIONES DE CARGA ---
def get_data(endpoint, params=None):
    try:
        r = requests.get(f"{API_URL}/{endpoint}", params=params)
        return r.json() if r.status_code == 200 else []
    except: return []

# --- CABECERA CON MÉTRICAS ---
st.title("🏗️ Panel de Control PROINDUS")
st.write("Bienvenida, aquí tienes el resumen de **Proindus Inversiones Industriales SL**.")

historial_total = get_data("presupuestos/")
pendientes = [p for p in historial_total if p['facturado'] != "Facturado"]
facturadas = [p for p in historial_total if p['facturado'] == "Facturado"]

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Presupuestos Hoy", len(pendientes))
with m2: st.metric("Facturas del Mes", len(facturadas))
with m3: 
    total_pend = sum(float(p['total_final']) for p in pendientes)
    st.metric("Por Facturar", f"{total_pend:,.2f}€")
with m4:
    total_fac = sum(float(f['total_final']) for f in facturadas)
    st.metric("Total Facturado", f"{total_fac:,.2f}€")

st.divider()

# --- NAVEGACIÓN POR PESTAÑAS ---
t_cli, t_nuevo, t_pres, t_fac = st.tabs([
    "👤 CLIENTES", "📝 NUEVO DOCUMENTO", "📂 PRESUPUESTOS", "🧾 FACTURAS"
])

# 1. CLIENTES (Limpio y ordenado)
with t_cli:
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        st.subheader("Registrar Nuevo")
        with st.form("f_cli", clear_on_submit=True):
            n = st.text_input("Nombre / Empresa")
            c = st.text_input("Código (Ej: P00253)")
            d = st.text_input("NIF / CIF")
            e = st.text_input("Email")
            dir_f = st.text_input("Dirección")
            if st.form_submit_button("Añadir Cliente"):
                requests.post(f"{API_URL}/clientes/", json={"codigo_interno":c, "nombre_completo":n, "nif_cif":d, "direccion":dir_f, "email":e})
                st.rerun()
    with col_c2:
        st.subheader("Lista de Contactos")
        list_c = get_data("clientes/")
        if list_c:
            df_c = pd.DataFrame(list_c)[['codigo_interno', 'nombre_completo', 'nif_cif']]
            st.dataframe(df_c, use_container_width=True, hide_index=True)

# 2. NUEVO PRESUPUESTO (Paso a paso)
with t_nuevo:
    st.subheader("Crear Propuesta para Cliente")
    list_c = get_data("clientes/")
    if not list_c:
        st.info("Añade un cliente para empezar.")
    else:
        # Selección de Cliente con búsqueda
        dict_c = {f"{cl['codigo_interno']} - {cl['nombre_completo']}": cl['id'] for cl in list_c}
        c_sel = st.selectbox("¿Para quién es el presupuesto?", options=list(dict_c.keys()))
        
        with st.container(border=True):
            c_a, c_b = st.columns(2)
            with c_a:
                obj = st.text_input("Asunto / Proyecto", placeholder="Ej: Restauración de vigas - Simon")
                fecha_doc = st.date_input("Fecha del Documento", date.today())
                venc = st.date_input("Fecha de Vencimiento", date.today() + pd.Timedelta(days=30))
            with c_b:
                cond = st.text_area("Cláusulas Especiales", value="60% de Anticipo a la aceptación / 40% a la finalización.")

        st.markdown("### 🛠️ Detalles del Trabajo")
        if 'lineas' not in st.session_state: st.session_state.lineas = []
        
        with st.expander("➕ Añadir Concepto (Haz clic aquí)"):
            t_con = st.text_input("Título corto (Ej: Decapado)")
            m_tec = st.text_area("Memoria Técnica (Detalla m2, materiales...)", height=100)
            l1, l2, l3 = st.columns(3)
            with l1: p_u = st.number_input("Precio (€)", min_value=0.0)
            with l2: can = st.number_input("Cantidad", min_value=1.0, value=1.0)
            with l3: i_p = st.selectbox("IVA", [0.21, 0.10], format_func=lambda x: f"{int(x*100)}%")
            
            if st.button("Añadir a la lista"):
                st.session_state.lineas.append({"titulo_concepto":t_con, "descripcion_detallada":m_tec, "cantidad":can, "precio_unitario":p_u, "iva_porcentaje":i_p})
                st.rerun()

        if st.session_state.lineas:
            st.table(pd.DataFrame(st.session_state.lineas)[['titulo_concepto', 'precio_unitario']])
            if st.button("🚀 GENERAR Y GUARDAR"):
                payload = {"cliente_id": dict_c[c_sel], "fecha": str(fecha_doc), "vencimiento": str(venc), "objeto_proyecto": obj, "clausulas_condiciones": cond, "lineas": st.session_state.lineas}
                res = requests.post(f"{API_URL}/presupuestos/pro", json=payload)
                if res.status_code == 200:
                    st.session_state.lineas = []
                    st.success("¡Presupuesto creado!")
                    st.rerun()

# 3. HISTORIAL DE PRESUPUESTOS (Visual)
with t_pres:
    st.subheader("Bandeja de Presupuestos Activos")
    b_p = st.text_input("🔍 Filtrar presupuestos...", key="bp")
    
    # 1. Obtenemos los datos (solo los que no están facturados)
    all_p = get_data("presupuestos/", {"search": b_p})
    pre_list = [p for p in all_p if p['facturado'] != "Facturado"]
    
    if pre_list:
        df_p = pd.DataFrame(pre_list)
        
        # 2. Configuración de la Tabla Profesional
        st.dataframe(
            df_p,
            column_order=("fecha", "referencia", "cliente_nombre", "objeto_proyecto", "base_imponible", "total_iva", "total_final"),
            column_config={
                "fecha": st.column_config.DateColumn("Fecha"),
                "referencia": "Nº Presu",
                "cliente_nombre": "Cliente",
                "objeto_proyecto": "Descripción/Proyecto",
                "base_imponible": st.column_config.NumberColumn("Subtotal", format="%.2f €"),
                "total_iva": st.column_config.NumberColumn("IVA", format="%.2f €"),
                "total_final": st.column_config.NumberColumn("Total", format="%.2f €"),
            },
            hide_index=True,
            use_container_width=True
        )

        st.divider()
        
        # 3. Acciones rápidas (Selección por referencia)
        st.caption("Selecciona un presupuesto para gestionar:")
        sel_ref = st.selectbox("Elegir documento", [p['referencia'] for p in pre_list], key="sel_p_table")
        p_sel = next(p for p in pre_list if p['referencia'] == sel_ref)
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            pdf_p = requests.get(f"{API_URL}/presupuestos/{p_sel['id']}/pdf").content
            st.download_button(f"📥 Descargar PDF {sel_ref}", data=pdf_p, file_name=f"{sel_ref}.pdf")
        
        with col_p2:
            # Botón para convertir en Factura directamente
            if st.button(f"🧾 Convertir {sel_ref} en Factura Real"):
                res = requests.post(f"{API_URL}/presupuestos/{p_sel['id']}/facturar")
                if res.status_code == 200:
                    st.success(f"¡{sel_ref} ha pasado a ser Factura!")
                    st.rerun()
    else:
        st.info("No hay presupuestos pendientes que coincidan con la búsqueda.")


# 4. LIBRO DE FACTURAS (Elegante)
with t_fac:
    st.subheader("Listado Maestro de Facturas")
    b_f = st.text_input("🔍 Filtro rápido (Cliente o Nº)...", key="bf")
    fac_list = get_data("facturas/", {"search": b_f})

    if fac_list:
        # 1. Convertimos a DataFrame para Streamlit
        df_f = pd.DataFrame(fac_list)
        
        # 2. Mostramos la tabla configurada
        st.dataframe(
            df_f,
            column_order=("fecha_emision", "referencia", "cliente_nombre", "base_imponible", "total_iva", "total_final", "estado_pago"),
            column_config={
                "presupuesto_id": None,
                "fecha_emision": st.column_config.DateColumn("Fecha"),
                "referencia": "Nº Factura",
                "cliente_nombre": "Cliente",
                "base_imponible": st.column_config.NumberColumn("Subtotal", format="%.2f €"),
                "total_iva": st.column_config.NumberColumn("IVA", format="%.2f €"),
                "total_final": st.column_config.NumberColumn("Total", format="%.2f €"),
                "estado_pago": st.column_config.SelectboxColumn("Estado", options=["PENDIENTE", "COBRADA"])
            },
            hide_index=True,
            use_container_width=True
        )

        # 3. Acciones (PDF y Cobro)
        st.divider()
        st.caption("Selecciona una factura para gestionar:")
        c_sel = st.selectbox("Elegir factura para descargar o cobrar", 
                             options=[f['referencia'] for f in fac_list], 
                             key="sel_f")
        
        # Buscamos los datos de la seleccionada
        f_sel = next(f for f in fac_list if f['referencia'] == c_sel)
        col_a, col_b = st.columns(2)
        with col_a:
            pdf_f = requests.get(f"{API_URL}/presupuestos/{f_sel['presupuesto_id']}/pdf").content
            st.download_button(f"📥 Descargar PDF {c_sel}", data=pdf_f, file_name=f"{c_sel}.pdf")
        with col_b:
            if f_sel['estado_pago'] == "PENDIENTE":
                if st.button(f"💰 Marcar {c_sel} como Cobrada"):
                    requests.post(f"{API_URL}/facturas/{f_sel['id']}/cobrar")
                    st.rerun()