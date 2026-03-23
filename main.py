from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import Session, select, func, or_, and_
from typing import List, Optional
from datetime import date
from database import engine, get_session
from models import Cliente, Presupuesto, LineaPresupuesto, Factura, EstadoPresupuesto, EstadoFacturado
from schemas import (
    PresupuestoCreate, PresupuestoRead, PresupuestoUpdate,
    LineaCreate, FacturaRead
)
from pdf import generar_pdf_binario # Tu función de WeasyPrint
from fastapi.responses import StreamingResponse

app = FastAPI(title="PROINDUS API v2")

# --- 1. GESTIÓN DE CLIENTES ---

@app.post("/clientes/", response_model=Cliente)
def crear_cliente(cliente: Cliente, session: Session = Depends(get_session)):
    session.add(cliente)
    session.commit()
    session.refresh(cliente)
    return cliente

@app.get("/clientes/", response_model=List[Cliente])
def listar_clientes(session: Session = Depends(get_session)):
    return session.exec(select(Cliente)).all()

# --- 2. GESTIÓN DE PRESUPUESTOS (P) ---

@app.post("/presupuestos/pro")
def crear_presupuesto_completo(datos: PresupuestoCreate, session: Session = Depends(get_session)):
    # 1. Generar Referencia automática P00...
    cliente = session.get(Cliente, datos.cliente_id)
    hoy = date.today()
    referencia = f"P{cliente.codigo_interno}-{hoy.day}-{hoy.month}-{hoy.year}"
    
    # 2. Crear cabecera
    nuevo_p = Presupuesto(
        referencia=referencia,
        vencimiento=datos.vencimiento,
        objeto_proyecto=datos.objeto_proyecto,
        clausulas_condiciones=datos.clausulas_condiciones,
        cliente_id=datos.cliente_id,
        estado=EstadoPresupuesto.PENDIENTE
    )
    session.add(nuevo_p)
    session.commit()
    session.refresh(nuevo_p)

    # 3. Añadir líneas con doble descripción
    for l in datos.lineas:
        nueva_l = LineaPresupuesto(
            titulo_concepto=l.titulo_concepto,
            descripcion_detallada=l.descripcion_detallada,
            cantidad=l.cantidad,
            precio_unitario=l.precio_unitario,
            iva_porcentaje=l.iva_porcentaje,
            presupuesto_id=nuevo_p.id
        )
        session.add(nueva_l)
    
    session.commit()
    session.refresh(nuevo_p)
    return {"id": nuevo_p.id, "referencia": nuevo_p.referencia}

@app.get("/presupuestos/", response_model=List[PresupuestoRead])
def listar_presupuestos(
    search: Optional[str] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    session: Session = Depends(get_session)
):
    """Listado con filtros de búsqueda y fechas (Estilo Holded)"""
    statement = select(Presupuesto).join(Cliente)
    
    filtros = []
    if search:
        filtros.append(or_(
            Presupuesto.referencia.contains(search),
            Presupuesto.objeto_proyecto.contains(search),
            Cliente.nombre_completo.contains(search)
        ))
    if desde:
        filtros.append(Presupuesto.fecha >= desde)
    if hasta:
        filtros.append(Presupuesto.fecha <= hasta)
    
    if filtros:
        statement = statement.where(and_(*filtros))
        
    return session.exec(statement.order_by(Presupuesto.id.desc())).all()

# --- 3. EL "BOTÓN MÁGICO": CONVERTIR P EN F ---

@app.post("/presupuestos/{id}/facturar")
def generar_factura(id: int, session: Session = Depends(get_session)):
    p = session.get(Presupuesto, id)
    if not p: raise HTTPException(status_code=404)
    if p.facturado == EstadoFacturado.FACTURADO: raise HTTPException(status_code=400, detail="Ya facturado")

    # Transformar Referencia P -> F
    ref_factura = p.referencia.replace("P", "F", 1)
    
    nueva_f = Factura(
        referencia=ref_factura,
        presupuesto_id=p.id,
        total_final=p.total_final
    )
    
    p.estado = EstadoPresupuesto.ACEPTADO
    p.facturado = EstadoFacturado.FACTURADO
    
    session.add(nueva_f)
    session.add(p)
    session.commit()

    session.refresh(nueva_f)
    session.refresh(p)

    return {
        "id": nueva_f.id, 
        "referencia": ref_factura,
        "estado_presupuesto": p.estado,
        "estado_facturacion": p.facturado
    }

# --- 4. GENERACIÓN DE PDF DINÁMICO ---

@app.get("/presupuestos/{id}/pdf")
def descargar_pdf(id: int, session: Session = Depends(get_session)):
    p = session.get(Presupuesto, id)
    if not p: raise HTTPException(status_code=404)
    
    # Decidimos el título del PDF según el estado
    tipo_doc = "FACTURA" if p.facturado == EstadoFacturado.FACTURADO else "PRESUPUESTO"
    
    # Llamamos a tu función de WeasyPrint pasando el objeto presupuesto
    # (Asegúrate de que tu función generar_pdf_binario acepte el parámetro 'tipo')
    pdf_stream = generar_pdf_binario(p, tipo=tipo_doc)
    
    return StreamingResponse(
        pdf_stream, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={p.referencia}.pdf"}
    )