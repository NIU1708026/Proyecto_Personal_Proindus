from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from decimal import Decimal
from datetime import date
from enum import Enum

# --- 1. ESTADOS DEL DOCUMENTO ---
class EstadoPresupuesto(str, Enum):
    PENDIENTE = "Pendiente" # El amarillo de Holded
    ACEPTADO = "Aceptado"   # El verde de Holded
    RECHAZADO = "Rechazado"

class EstadoFacturado(str, Enum):
    PENDIENTE = "Pendiente" # El amarillo de Holded
    FACTURADO = "Facturado"   # El verde de Holded
    PARCIALMENTE = "Parcialmente"

# --- 2. CLIENTE ---
class Cliente(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo_interno: str = Field(index=True, unique=True) # Ej: "P00253" [cite: 89, 103]
    nombre_completo: str # [cite: 92, 121]
    nif_cif: str # [cite: 95, 124]
    direccion: str # [cite: 93, 122]
    email: str # [cite: 96, 120]
    
    presupuestos: List["Presupuesto"] = Relationship(back_populates="cliente")

# --- 3. LÍNEAS DE DETALLE (Concepto vs Descripción) ---
class LineaPresupuesto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo_concepto: str # Ej: "Servicio de decapado y limpieza" 
    descripcion_detallada: str # Los bullets técnicos (madera, rejas, etc.) 
    cantidad: Decimal = Field(default=1, max_digits=10, decimal_places=2)
    precio_unitario: Decimal = Field(max_digits=10, decimal_places=2)
    iva_porcentaje: Decimal = Field(default=Decimal("0.21")) # 21% para industria o 10% vivienda 
    
    presupuesto_id: int = Field(foreign_key="presupuesto.id")
    presupuesto: Optional["Presupuesto"] = Relationship(back_populates="lineas")

    @property
    def subtotal(self) -> Decimal:
        return self.cantidad * self.precio_unitario

    @property
    def iva_importe(self) -> Decimal:
        return self.subtotal * self.iva_porcentaje

# --- 4. PRESUPUESTO (Documento Editable) ---
class Presupuesto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    referencia: str = Field(index=True, unique=True) # "P" + Código 
    fecha: date = Field(default_factory=date.today) # [cite: 103, 118]
    vencimiento: date # [cite: 103, 118]
    
    # Identificación rápida para el historial
    objeto_proyecto: str # Título breve (Ej: "Reforma Calle Mercaderes")
    
    # Cláusulas específicas (Permisos, 60/40, logística)
    clausulas_condiciones: Optional[str] = Field(default="60% de Anticipo a la aceptación / 40% a la finalización.") # [cite: 125, 134]
    
    estado: EstadoPresupuesto = Field(default=EstadoPresupuesto.PENDIENTE)
    facturado: EstadoFacturado = Field(default=EstadoFacturado.PENDIENTE)
    
    cliente_id: int = Field(foreign_key="cliente.id")
    cliente: Optional[Cliente] = Relationship(back_populates="presupuestos")
    lineas: List[LineaPresupuesto] = Relationship(back_populates="presupuesto")
    factura: Optional["Factura"] = Relationship(back_populates="presupuesto")

    # Propiedades calculadas
    @property
    def base_imponible(self) -> Decimal:
        return sum(l.subtotal for l in self.lineas)

    @property
    def total_iva(self) -> Decimal:
        return sum(l.iva_importe for l in self.lineas)

    @property
    def total_final(self) -> Decimal:
        return self.base_imponible + self.total_iva

# --- 5. FACTURA (Documento Legal Final) ---
class Factura(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    referencia: str = Field(index=True, unique=True) # "F" + Código [cite: 103]
    fecha_emision: date = Field(default_factory=date.today)
    
    presupuesto_id: int = Field(foreign_key="presupuesto.id")
    presupuesto: Optional[Presupuesto] = Relationship(back_populates="factura")
    
    # Datos inmutables de Proindus para la factura [cite: 112, 115, 116, 130]
    emisor_nif: str = "B19417401"
    emisor_direccion: str = "Avenida Meridiana 325 Bajo 2, Barcelona"
    emisor_iban: str = "ES40 0049 3073 0724 1422 5620"