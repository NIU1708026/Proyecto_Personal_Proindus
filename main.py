from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select, func
from datetime import datetime, timedelta
from database import get_session, engine
from models import Cliente, Presupuesto, LineaPresupuesto
from schemas import ClienteCreate, PresupuestoCreate, PresupuestoRead, LineaRead
from decimal import Decimal
from typing import List, Optional


app = FastAPI(title="Proindus SL")

@app.post("/clientes/", response_model=Cliente)
def crear_cliente(cliente_data: ClienteCreate, session: Session = Depends(get_session)):
    nuevo_cliente = Cliente(**cliente_data.model_dump())
    session.add(nuevo_cliente)
    session.commit()
    session.refresh(nuevo_cliente)
    return nuevo_cliente

# En main.py, usando el modelo de la tabla directamente:
@app.get("/clientes/", response_model=List[Cliente])
def listar_clientes(session: Session = Depends(get_session)):
    # select(Cliente) le dice a la DB: "Trae todo lo de la tabla Cliente"
    statement = select(Cliente)
    clientes = session.exec(statement).all()
    return clientes


@app.post("/presupuestos/pro")
def crear_presupuesto_completo(datos: PresupuestoCreate, session: Session = Depends(get_session)):
    # 1. Validar Cliente
    cliente = session.get(Cliente, datos.cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # 2. Lógica de Referencia: [Codigo]-[Secuencia]-[Mes]-[Año] [cite: 103]
    count_statement = select(func.count(Presupuesto.id)).where(Presupuesto.cliente_id == cliente.id)
    secuencia = session.exec(count_statement).one() + 1
    ahora = datetime.now()
    ref_generada = f"{cliente.codigo_interno}-{secuencia}-{ahora.month}-{ahora.year}"

    # 3. Lógica de Fechas
    fecha_hoy = ahora.date()
    fecha_vencimiento = datos.vencimiento or (fecha_hoy + timedelta(days=30))

    # 4. Crear el Presupuesto (Transacción Atómica)
    nuevo_p = Presupuesto(
        referencia=ref_generada,
        fecha=fecha_hoy,
        vencimiento=fecha_vencimiento,
        cliente_id=cliente.id
    )

    for l in datos.lineas:
        nueva_linea = LineaPresupuesto(
            concepto=l.concepto,
            cantidad=l.cantidad,
            precio_unitario=l.precio_unitario,
            iva_porcentaje=l.iva_porcentaje,
            presupuesto=nuevo_p # Vinculación automática
        )
        nuevo_p.lineas.append(nueva_linea)

    session.add(nuevo_p)
    session.commit()
    session.refresh(nuevo_p)

    return {
        "id": nuevo_p.id,
        "status": "success",
        "referencia": nuevo_p.referencia,
        "total_final": nuevo_p.total_final # Propiedad calculada en el modelo
    }



@app.get("/presupuestos/", response_model=List[PresupuestoRead])
def listar_todos_los_presupuestos(session: Session = Depends(get_session)):
    """Devuelve todos los presupuestos ordenados por fecha de creación"""
    # Usamos .order_by para que los últimos aparezcan primero
    statement = select(Presupuesto).order_by(Presupuesto.id.desc())
    resultados = session.exec(statement).all()
    return resultados


@app.get("/presupuestos/{referencia}", response_model=PresupuestoRead)
def obtener_presupuesto_por_referencia(referencia: str, session: Session = Depends(get_session)):
    """Busca un presupuesto específico por su código (ej: P00253-1-3-2026)"""
    statement = select(Presupuesto).where(Presupuesto.referencia == referencia)
    presupuesto = session.exec(statement).first()
    
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        
    return presupuesto


from fastapi.responses import StreamingResponse
from pdf import generar_pdf_binario

@app.get("/presupuestos/{presupuesto_id}/pdf")
def descargar_pdf(presupuesto_id: int, session: Session = Depends(get_session)):
    # Buscar el presupuesto con sus relaciones cargadas
    p = session.get(Presupuesto, presupuesto_id)
    if not p:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    
    # Generar el PDF
    pdf_stream = generar_pdf_binario(p)
    
    # Retornar como archivo descargable
    nombre_archivo = f"Presupuesto_{p.referencia}.pdf"
    return StreamingResponse(
        pdf_stream, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
    )