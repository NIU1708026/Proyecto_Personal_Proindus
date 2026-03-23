import streamlit as st
import requests
from datetime import date
import pandas as pd

# Configuración de página
st.set_page_config(page_title="PROINDUS - Gestión", page_icon="🏗️", layout="wide")

# URL de tu API (Asegúrate de que coincide con el puerto de uvicorn)
API_URL = "http://127.0.0.1:8000"

st.title("🏗️ Panel de Control PROINDUS")

# --- FUNCIONES DE AYUDA ---
def obtener_lista_clientes():
    try:
        r = requests.get(f"{API_URL}/clientes/")
        return r.json() if r.status_code == 200 else []
    except:
        return []

# --- ESTADO DE LA SESIÓN (Para guardar las líneas mientras escribe) ---
if 'carrito_lineas' not in st.session_state:
    st.session_state.carrito_lineas = []

# --- PESTAÑAS ---
tab_cli, tab_pre, tab3 = st.tabs(["👤 Gestión de Clientes", "📄 Crear nuevo Presupuesto", "📊 Ver Presupuestos"])

# 1. PESTAÑA CLIENTES (Ya te funciona, la mantenemos limpia)
with tab_cli:
    st.header("Registrar Cliente")
    with st.form("nuevo_cliente"):
        c1, c2 = st.columns(2)
        with c1:
            cod = st.text_input("Código Interno (Ej: P00253)")
            nom = st.text_input("Nombre / Empresa")
            dni = st.text_input("NIF / CIF")
        with c2:
            mail = st.text_input("Email")
            dir_f = st.text_input("Dirección")
        
        if st.form_submit_button("Guardar Cliente"):
            payload = {"codigo_interno": cod, "nombre_completo": nom, "nif_cif": dni, "direccion": dir_f, "email": mail}
            res = requests.post(f"{API_URL}/clientes/", json=payload)
            if res.status_code == 200:
                st.success(f"✅ {nom} guardado correctamente.")
                st.rerun()

# 2. PESTAÑA PRESUPUESTOS (Aquí es donde estaba el fallo)
with tab_pre:
    st.header("Redactar Presupuesto")
    
    # SELECCIÓN DE CLIENTE
    lista_c = obtener_lista_clientes()
    if not lista_c:
        st.warning("⚠️ No hay clientes en la base de datos. Crea uno primero.")
    else:
        # Creamos un diccionario para que ella vea nombres pero nosotros usemos IDs
        dict_clientes = {f"{c['codigo_interno']} - {c['nombre_completo']}": c['id'] for c in lista_c}
        cliente_seleccionado = st.selectbox("Selecciona el cliente:", options=list(dict_clientes.keys()))
        id_final = dict_clientes[cliente_seleccionado]

        st.divider()

        # AGREGAR LÍNEAS
        st.subheader("Añadir Conceptos")
        with st.container(border=True):
            concepto = st.text_area("Descripción del trabajo:", placeholder="Ej: Lijado manual de 7 vigas...", height=150)
            col_a, col_b, col_c = st.columns([3, 1, 1])
            with col_a:
                p_uni = st.number_input("Precio (€)", min_value=0.0, step=10.0)
            with col_b:
                cant = st.number_input("Cantidad", min_value=1.0, value=1.0)
            with col_c:
                iva = st.selectbox("IVA", [0.10, 0.21], format_func=lambda x: f"{int(x*100)}%")

            if st.button("➕ Añadir esta línea al presupuesto"):
                if concepto and p_uni > 0:
                    nueva_linea = {
                        "concepto": concepto,
                        "cantidad": cant,
                        "precio_unitario": p_uni,
                        "iva_porcentaje": iva
                    }
                    st.session_state.carrito_lineas.append(nueva_linea)
                    st.toast("Línea añadida con éxito")
                else:
                    st.error("Escribe un concepto y un precio.")

        # TABLA DE REVISIÓN
        if st.session_state.carrito_lineas:
            st.subheader("Líneas actuales")
            df = pd.DataFrame(st.session_state.carrito_lineas)
            st.table(df)
            
            if st.button("🗑️ Borrar todas las líneas"):
                st.session_state.carrito_lineas = []
                st.rerun()

            st.divider()

            # BOTÓN FINAL: GENERAR PDF
            if st.button("🚀 GENERAR Y DESCARGAR PDF"):
                # Preparar datos para el backend
                vencimiento = date.today().replace(month=date.today().month + 1)
                payload_pro = {
                    "cliente_id": id_final,
                    "vencimiento": str(vencimiento),
                    "lineas": st.session_state.carrito_lineas
                }
                
                with st.spinner("Conectando con el servidor..."):
                    res_p = requests.post(f"{API_URL}/presupuestos/pro", json=payload_pro)
                    
                    if res_p.status_code == 200:
                        data_final = res_p.json()
                        st.success(f"✅ Presupuesto {data_final['referencia']} creado.")
                        
                        # Obtener el PDF real para descargarlo
                        pdf_res = requests.get(f"{API_URL}/presupuestos/{data_final['id']}/pdf")
                        
                        if pdf_res.status_code == 200:
                            st.download_button(
                                label="💾 GUARDAR E IMPRIMIR PDF",
                                data=pdf_res.content,
                                file_name=f"Presupuesto_{data_final['referencia']}.pdf",
                                mime="application/pdf"
                            )
                            # Limpiamos el carrito para el próximo presupuesto
                            st.session_state.carrito_lineas = []
                        else:
                            st.error("El presupuesto se guardó, pero hubo un error al generar el archivo PDF.")
                    else:
                        st.error(f"Error en el servidor: {res_p.text}")
            

# --- TAB 3: HISTORIAL DE DOCUMENTOS (CORREGIDO) ---
with tab3:
    st.header("Historial de Presupuestos y Facturas")
    st.info("Aquí puedes ver todos los documentos generados y volver a descargarlos.")

    try:
        res_historial = requests.get(f"{API_URL}/presupuestos/")
        if res_historial.status_code == 200:
            historial = res_historial.json()
            
            if not historial:
                st.write("Aún no se ha creado ningún presupuesto.")
            else:
                datos_tabla = []
                for p in historial:
                    # Convertimos el total a float() para evitar el error de formato
                    total_num = float(p['total_final']) 
                    
                    datos_tabla.append({
                        "ID": p['id'],
                        "Referencia": p['referencia'],
                        "Fecha": p['fecha'],
                        "Total (€)": f"{total_num:.2f}€" # Ahora funciona correctamente
                    })
                
                st.dataframe(pd.DataFrame(datos_tabla), use_container_width=True, hide_index=True)

                st.divider()

                st.subheader("📥 Re-descargar un documento")
                # También corregimos el formato aquí para el selector
                opciones_descarga = {
                    f"{p['referencia']} - Total: {float(p['total_final']):.2f}€": p['id'] 
                    for p in historial
                }
                
                seleccion = st.selectbox("Busca por referencia:", options=list(opciones_descarga.keys()))
                
                if seleccion:
                    id_a_descargar = opciones_descarga[seleccion]
                    ref_nombre = seleccion.split(" - ")[0]
                    
                    with st.spinner("Preparando archivo..."):
                        pdf_data = requests.get(f"{API_URL}/presupuestos/{id_a_descargar}/pdf").content
                        
                        st.download_button(
                            label=f"⬇️ Descargar PDF de {ref_nombre}",
                            data=pdf_data,
                            file_name=f"{ref_nombre}.pdf",
                            mime="application/pdf",
                            key=f"btn_historial_{id_a_descargar}"
                        )
    except Exception as e:
        st.error(f"Error de conexión con el historial: {e}")