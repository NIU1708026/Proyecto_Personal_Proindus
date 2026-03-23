from sqlmodel import Session, select, func
from database import engine
from models import Cliente, Presupuesto, LineaPresupuesto
from decimal import Decimal
from datetime import date, datetime, timedelta

def insertar_datos():
    with Session(engine) as session:
        # 1. CREACIÓN DE CLIENTES
        # Datos extraídos del presupuesto de Sitges [cite: 92, 94, 95]
        c1 = Cliente(
            codigo_interno="P00253",
            nombre_completo="Simon Anthony Earley",
            nif_cif="Y9303232E",
            direccion="Calle Taco 7, Sitges (08870)",
            email="proyectos@proindus.es"
        )
        # Datos extraídos del presupuesto de Barcelona [cite: 8, 10]
        c2 = Cliente(
            codigo_interno="P00458",
            nombre_completo="Presidente Comunidad Sr. Jorge",
            nif_cif="NIF-COMUNIDAD-99",
            direccion="Calle Mercaderes 10, Barcelona",
            email="comunidad@ejemplo.com"
        )
        c3 = Cliente(
            codigo_interno="P00500",
            nombre_completo="Jose Prueba",
            nif_cif="12345678Z",
            direccion="Calle Falsa 123",
            email="jose@prueba.com"
        )

        session.add_all([c1, c2, c3])
        session.commit()
        
        for c in [c1, c2, c3]:
            session.refresh(c)

        # 2. CREACIÓN DE PRESUPUESTOS CON LÓGICA DE REFERENCIA
        ahora = datetime.now()
        mes_año = ahora.strftime("%m-%Y")

        # Presupuesto 1: Simon (Lijado de vigas) [cite: 90, 109]
        p1 = Presupuesto(
            referencia=f"{c1.codigo_interno}-1-{mes_año}",
            vencimiento=date.today() + timedelta(days=30),
            cliente_id=c1.id
        )
        l1 = LineaPresupuesto(
            concepto="Lijado manual y mecánico de vigas de madera y rejas",
            cantidad=Decimal("1"),
            precio_unitario=Decimal("850.00"),
            iva_porcentaje=Decimal("0.10"), # IVA 10% según Holded 
            presupuesto=p1
        )

        # Presupuesto 2: Sr. Jorge (Tratamiento Integral) [cite: 9, 35, 65]
        p2 = Presupuesto(
            referencia=f"{c2.codigo_interno}-1-{mes_año}",
            vencimiento=date.today() + timedelta(days=30),
            cliente_id=c2.id
        )
        l2 = LineaPresupuesto(
            concepto="Tratamiento Integral de Paramentos Verticales (320m2)",
            cantidad=Decimal("1"),
            precio_unitario=Decimal("9310.00"),
            iva_porcentaje=Decimal("0.21"),
            presupuesto=p2
        )

        # Presupuesto 3: Jose (Segunda obra para probar secuencia)
        p3 = Presupuesto(
            referencia=f"{c1.codigo_interno}-2-{mes_año}", # Es el segundo para Simon
            vencimiento=date.today() + timedelta(days=30),
            cliente_id=c1.id
        )
        l3 = LineaPresupuesto(
            concepto="Pintura de escalera interior",
            cantidad=Decimal("1"),
            precio_unitario=Decimal("450.00"),
            iva_porcentaje=Decimal("0.10"),
            presupuesto=p3
        )

        session.add_all([p1, p2, p3])
        session.commit()
        print("✅ 3 Clientes y 3 Presupuestos insertados correctamente.")

if __name__ == "__main__":
    insertar_datos()