from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List, Optional
from datetime import date

# --- SCHEMAS DE CLIENTE ---
class ClienteBase(BaseModel):
    codigo_interno: str # Ej: "P00253"
    nombre_completo: str
    nif_cif: str
    direccion: str
    email: str

class ClienteCreate(ClienteBase):
    pass

# --- SCHEMAS DE LÍNEAS ---
class LineaCreate(BaseModel):
    concepto: str # Ej: "Lijado de vigas de madera"
    cantidad: Decimal = Decimal("1.0")
    precio_unitario: Decimal
    iva_porcentaje: Decimal = Decimal("0.10") # 10% por defecto para reformas

# --- SCHEMAS DE PRESUPUESTO ---
class PresupuestoCreate(BaseModel):
    cliente_id: int
    vencimiento: Optional[date] = None # Si no lo pone, calcularemos +30 días
    lineas: List[LineaCreate]

# --- SCHEMAS DE LECTURA (Para ver los totales) ---

class LineaRead(BaseModel):
    id: int
    concepto: str
    cantidad: Decimal
    precio_unitario: Decimal
    iva_porcentaje: Decimal
    subtotal: Decimal # Campo calculado
    iva_importe: Decimal # Campo calculado

class PresupuestoRead(BaseModel):
    id: int
    referencia: str
    fecha: date
    vencimiento: date
    cliente_id: int
    base_imponible: Decimal # Campo calculado
    total_iva: Decimal      # Campo calculado
    total_final: Decimal    # Campo calculado
    lineas: List[LineaRead]  