from sqlmodel import Session, select
from database import engine
from models import Cliente, Presupuesto, LineaPresupuesto, EstadoPresupuesto
from datetime import date, timedelta
from decimal import Decimal

def seed_test_data():
    with Session(engine) as session:
        print("🚀 Iniciando carga de datos de prueba para PROINDUS...")

        # 1. CREAR CLIENTES REALES
        cliente_simon = Cliente(
            codigo_interno="P00253",
            nombre_completo="Simon Anthony Earley",
            nif_cif="Y9303232E",
            direccion="Calle Taco 7, Sitges, Barcelona",
            email="proyectos@proindus.es"
        ) # [cite: 4, 7, 15]

        cliente_vaghinak = Cliente(
            codigo_interno="E260013",
            nombre_completo="Vaghinak Arakelyan",
            nif_cif="X7845386V",
            direccion="C. Industria 89, Barcelona",
            email="info@proindus.es"
        ) # [cite: 30, 33, 36]

        session.add(cliente_simon)
        session.add(cliente_vaghinak)
        session.commit()
        session.refresh(cliente_simon)
        session.refresh(cliente_vaghinak)

        # 2. PRESUPUESTO SIMON (Caso Vigas - IVA 10%)
        p_simon = Presupuesto(
            referencia=f"P{cliente_simon.codigo_interno}-16-3-2026",
            vencimiento=date(2026, 4, 15),
            objeto_proyecto="Restauración de vigas y rejas",
            clausulas_condiciones="Pago por transferencia bancaria tras finalización.",
            cliente_id=cliente_simon.id,
            estado=EstadoPresupuesto.PENDIENTE
        ) # [cite: 15, 21]
        session.add(p_simon)
        session.commit()

        # Líneas para Simon
        l1_s = LineaPresupuesto(
            titulo_concepto="Lijado y decapado de madera",
            descripcion_detallada="Lijado manual y mecánico de 7 vigas (baño, escalera y cambiador).",
            cantidad=Decimal("1"),
            precio_unitario=Decimal("850.00"),
            iva_porcentaje=Decimal("0.10"),
            presupuesto_id=p_simon.id
        ) # [cite: 2]
        session.add(l1_s)

        # 3. PRESUPUESTO VAGHINAK (Caso Chorreado - IVA 21%)
        p_vaghinak = Presupuesto(
            referencia=f"P{cliente_vaghinak.codigo_interno}-02-1-2026",
            vencimiento=date(2026, 2, 1),
            objeto_proyecto="Decapado mediante sistema de chorreado",
            clausulas_condiciones=(
                "- 60% de Anticipo: A la aceptación para gestión de tasas y maquinaria.\n"
                "- 40% Restante: A la finalización de los trabajos."
            ),
            cliente_id=cliente_vaghinak.id,
            estado=EstadoPresupuesto.PENDIENTE
        ) # [cite: 30, 37]
        session.add(p_vaghinak)
        session.commit()

        # Líneas para Vaghinak (Múltiples líneas)
        l1_v = LineaPresupuesto(
            titulo_concepto="Servicio de decapado y limpieza",
            descripcion_detallada="Tratamiento de vigas y bovedillas mediante vidrio micronizado ecológico.",
            cantidad=Decimal("1"),
            precio_unitario=Decimal("3500.00"),
            iva_porcentaje=Decimal("0.21"),
            presupuesto_id=p_vaghinak.id
        ) # 
        
        l2_v = LineaPresupuesto(
            titulo_concepto="Gestión de residuos y protección",
            descripcion_detallada="Recogida de abrasivo y protección de paramentos verticales.",
            cantidad=Decimal("1"),
            precio_unitario=Decimal("150.00"),
            iva_porcentaje=Decimal("0.21"),
            presupuesto_id=p_vaghinak.id
        )
        
        session.add(l1_v)
        session.add(l2_v)
        
        session.commit()
        print("✅ Datos cargados con éxito. Proindus está listo para pruebas.")

if __name__ == "__main__":
    seed_test_data()