from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from decimal import Decimal
from datetime import date

class Cliente(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo_interno: str = Field(index=True, unique=True) # Ej: "P00253"
    nombre_completo: str
    nif_cif: str
    direccion: str
    email: str
    
    presupuestos: List["Presupuesto"] = Relationship(back_populates="cliente")

class Presupuesto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    referencia: str = Field(index=True, unique=True) # Ej: "P00253-6-3-2026"
    fecha: date = Field(default_factory=date.today)
    vencimiento: date
    
    cliente_id: int = Field(foreign_key="cliente.id")
    cliente: Optional[Cliente] = Relationship(back_populates="presupuestos")
    lineas: List["LineaPresupuesto"] = Relationship(back_populates="presupuesto")

    @property
    def base_imponible(self) -> Decimal:
        return sum(l.subtotal for l in self.lineas)

    @property
    def total_iva(self) -> Decimal:
        return sum(l.iva_importe for l in self.lineas)

    @property
    def total_final(self) -> Decimal:
        return self.base_imponible + self.total_iva

class LineaPresupuesto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    concepto: str # Descripción detallada del trabajo
    cantidad: Decimal = Field(default=1, max_digits=10, decimal_places=2)
    precio_unitario: Decimal = Field(max_digits=10, decimal_places=2)
    iva_porcentaje: Decimal = Field(default=Decimal("0.10")) # 10% según el PDF de Sitges
    
    presupuesto_id: int = Field(foreign_key="presupuesto.id")
    presupuesto: Optional[Presupuesto] = Relationship(back_populates="lineas")

    @property
    def subtotal(self) -> Decimal:
        return self.cantidad * self.precio_unitario

    @property
    def iva_importe(self) -> Decimal:
        return self.subtotal * self.iva_porcentaje