from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from decimal import Decimal
from models import EstadoPresupuesto, EstadoFacturado

# --- 1. ESQUEMAS PARA LAS LÍNEAS (Concepto vs Detalles) ---

class LineaBase(BaseModel):
    titulo_concepto: str = Field(..., example="Servicio de decapado y limpieza")
    descripcion_detallada: str = Field(..., example="Uso de vidrio micronizado ecológico...")
    cantidad: Decimal = Field(default=1.0)
    precio_unitario: Decimal
    iva_porcentaje: Decimal = Field(default=Decimal("0.21")) # 21% por defecto 

class LineaCreate(LineaBase):
    pass

class LineaRead(LineaBase):
    id: int
    subtotal: Decimal
    iva_importe: Decimal

    class Config:
        from_attributes = True

# --- 2. ESQUEMAS PARA EL PRESUPUESTO (Editable) ---

class PresupuestoBase(BaseModel):
    objeto_proyecto: str = Field(..., example="Reforma Calle Industria")
    vencimiento: date
    clausulas_condiciones: Optional[str] = "60% de Anticipo / 40% a la finalización." # 
    estado: EstadoPresupuesto = EstadoPresupuesto.PENDIENTE
    facturado: EstadoFacturado = EstadoFacturado.PENDIENTE

class PresupuestoCreate(PresupuestoBase):
    cliente_id: int
    lineas: List[LineaCreate]

class PresupuestoUpdate(BaseModel):
    """Para permitir a tu madre editar borradores"""
    objeto_proyecto: Optional[str] = None
    vencimiento: Optional[date] = None
    clausulas_condiciones: Optional[str] = None
    estado: Optional[EstadoPresupuesto] = None
    lineas: Optional[List[LineaCreate]] = None

class PresupuestoRead(PresupuestoBase):
    id: int
    referencia: str
    fecha: date
    cliente_id: int
    base_imponible: Decimal
    total_iva: Decimal
    total_final: Decimal
    facturado: EstadoFacturado
    lineas: List[LineaRead]

    class Config:
        from_attributes = True

# --- 3. ESQUEMAS PARA LAS FACTURAS (Finales) ---

class FacturaRead(BaseModel):
    id: int
    referencia: str # Empezará con "F"
    fecha_emision: date
    presupuesto_id: int
    total_final: Decimal

    class Config:
        from_attributes = True