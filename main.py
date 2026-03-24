from fastapi import FastAPI, Depends, HTTPException, Query
from decimal import Decimal
from sqlmodel import Session, select, func, or_, and_
from typing import List, Optional
from datetime import date
from database import engine, get_session
from models import Cliente, Presupuesto, LineaPresupuesto, Factura, EstadoPresupuesto, EstadoFacturado, EstadoPago
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

    count_statement = select(func.count(Presupuesto.id)).where(Presupuesto.cliente_id == cliente.id)
    secuencia = session.exec(count_statement).one() + 1

    fecha_final = datos.fecha or date.today()
    referencia = f"P{cliente.codigo_interno}-{secuencia}-{fecha_final.month}-{fecha_final.year}"
    
    # 2. Crear cabecera
    nuevo_p = Presupuesto(
        referencia=referencia,
        fecha = fecha_final,
        vencimiento=datos.vencimiento,
        objeto_proyecto=datos.objeto_proyecto,
        clausulas_condiciones=datos.clausulas_condiciones,
        cliente_id=datos.cliente_id,
        estado=EstadoPresupuesto.PENDIENTE,
        facturado=EstadoFacturado.PENDIENTE
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
    session: Session = Depends(get_session)
):
    # Unimos con Cliente para tener acceso a su nombre
    statement = select(Presupuesto).join(Cliente)
    
    if search:
        statement = statement.where(or_(
            Presupuesto.referencia.contains(search),
            Presupuesto.objeto_proyecto.contains(search),
            Cliente.nombre_completo.contains(search)
        ))
        
    resultados = session.exec(statement.order_by(Presupuesto.id.desc())).all()
    
    # Mapeamos manualmente para incluir el nombre del cliente
    return [
        PresupuestoRead(
            **p.model_dump(),
            cliente_nombre=p.cliente.nombre_completo,
            base_imponible=p.base_imponible,
            total_iva=p.total_iva,
            total_final=p.total_final
        ) for p in resultados
    ]

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
        total_final=p.total_final,
        estado_pago=EstadoPago.PENDIENTE
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


# Añade esto en main.py para gestionar el cobro
@app.post("/facturas/{id}/cobrar")
def marcar_factura_cobrada(id: int, session: Session = Depends(get_session)):
    factura = session.get(Factura, id)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    factura.estado_pago = EstadoPago.COBRADA
    session.add(factura)
    session.commit()
    return {"status": "ok", "referencia": factura.referencia}



@app.get("/facturas/", response_model=List[FacturaRead])
def listar_facturas(search: Optional[str] = None, session: Session = Depends(get_session)):
    statement = select(Factura).join(Presupuesto).join(Cliente)
    if search:
        statement = statement.where(or_(
            Factura.referencia.contains(search),
            Cliente.nombre_completo.contains(search)
        ))
    
    resultados = session.exec(statement).all()
    
    # Mapeamos los datos del presupuesto y cliente al esquema de la factura
    facturas_finales = []
    for f in resultados:
        # Extraemos los datos a un diccionario
        datos_factura = f.model_dump()
        
        # Corregimos el total si es None (para facturas viejas)
        if datos_factura.get("total_final") is None:
            datos_factura["total_final"] = 0
            
        # Añadimos los campos calculados que no están en la tabla Factura
        facturas_finales.append(
            FacturaRead(
                **datos_factura,
                base_imponible=f.presupuesto.base_imponible,
                total_iva=f.presupuesto.total_iva,
                cliente_nombre=f.presupuesto.cliente.nombre_completo
            )
        )
        
    return facturas_finales