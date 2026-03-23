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

API_URL = "http://127.0.0.1:8000"

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
                payload = {"cliente_id": dict_c[c_sel], "vencimiento": str(venc), "objeto_proyecto": obj, "clausulas_condiciones": cond, "lineas": st.session_state.lineas}
                res = requests.post(f"{API_URL}/presupuestos/pro", json=payload)
                if res.status_code == 200:
                    st.session_state.lineas = []
                    st.success("¡Presupuesto creado!")
                    st.rerun()

# 3. HISTORIAL DE PRESUPUESTOS (Visual)
with t_pres:
    st.subheader("Presupuestos Pendientes de Cobro")
    b_p = st.text_input("🔍 Buscar por cliente o código...", key="bp")
    pre_list = [p for p in get_data("presupuestos/", {"search": b_p}) if p['facturado'] != "Facturado"]
    
    for p in pre_list:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{p['referencia']}** | {p['objeto_proyecto']}")
                st.caption(f"Vence el {p['vencimiento']}")
            with col2:
                st.write(f"### {float(p['total_final']):,.2f}€")
            with col3:
                pdf = requests.get(f"{API_URL}/presupuestos/{p['id']}/pdf").content
                st.download_button("📥 PDF", data=pdf, file_name=f"{p['referencia']}.pdf", key=f"d_p_{p['id']}")
                if st.button("🧾 FACTURAR", key=f"f_p_{p['id']}"):
                    requests.post(f"{API_URL}/presupuestos/{p['id']}/facturar")
                    st.rerun()

# 4. LIBRO DE FACTURAS (Elegante)
with t_fac:
    st.subheader("Registro Legal de Facturas")
    b_f = st.text_input("🔍 Buscar en el archivo...", key="bf")
    fac_list = [f for f in get_data("presupuestos/", {"search": b_f}) if f['facturado'] == "Facturado"]
    
    for f in fac_list:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{f['referencia']}** ✅")
                st.write(f"Emitida el {f['fecha']}")
            with col2:
                st.write(f"### {float(f['total_final']):,.2f}€")
            with col3:
                pdf_f = requests.get(f"{API_URL}/presupuestos/{f['id']}/pdf").content
                st.download_button("📥 DESCARGAR", data=pdf_f, file_name=f"{f['referencia']}.pdf", key=f"d_f_{f['id']}")