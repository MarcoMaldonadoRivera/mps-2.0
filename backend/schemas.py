"""
================================================================
MPS 2.0 — Esquemas Pydantic (DTOs)
Archivo: schemas.py
Propósito: Definir los modelos de validación de datos para
           recibir del frontend (Create) y devolver como
           respuesta (Response). Pydantic valida automáticamente
           los tipos, campos obligatorios y formatos.
================================================================
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


# ================================================================
# ENUMS COMPARTIDOS
# ================================================================

class EstadoCliente(str, Enum):
    activo = "activo"
    inactivo = "inactivo"

class TipoConexion(str, Enum):
    USB = "USB"
    LAN = "LAN"
    WiFi = "Wi-Fi"
    USBLAN = "USB-LAN"

class EstadoImpresora(str, Enum):
    Activo = "Activo"
    EnReparacion = "En Reparación"
    DeBaja = "De Baja"

class MotivoVisita(str, Enum):
    Preventiva = "Preventiva"
    Correctiva = "Correctiva"


# ================================================================
# ESQUEMAS DE CLIENTE
# ================================================================

class ClienteCreate(BaseModel):
    """Esquema para recibir datos de un nuevo cliente desde el frontend.
    El RUT acepta desde 7 caracteres (formato simple: 12345678)
    hasta 12 con formato (12.345.678-9)."""
    rut: str = Field(..., min_length=7, max_length=12, description="RUT chileno (7-12 caracteres)")
    razon_social: str = Field(..., min_length=2, max_length=150)
    direccion: Optional[str] = Field(None, max_length=200)
    telefono: Optional[str] = Field(None, max_length=20)
    contacto: str = Field(..., min_length=2, max_length=100)
    email_contacto: Optional[str] = Field(None, max_length=100)

class ClienteUpdate(BaseModel):
    """Esquema para actualizar parcialmente un cliente existente."""
    razon_social: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    contacto: Optional[str] = None
    email_contacto: Optional[str] = None
    estado: Optional[EstadoCliente] = None

class ClienteResponse(BaseModel):
    """Esquema de respuesta con todos los datos de un cliente."""
    ID_cliente: int
    rut: str
    razon_social: str
    direccion: Optional[str]
    telefono: Optional[str]
    contacto: str
    email_contacto: Optional[str]
    estado: str
    fecha_creacion: Optional[datetime]
    fecha_actualizacion: Optional[datetime]

    class Config:
        from_attributes = True  # Permite convertir desde objetos SQLAlchemy


# ================================================================
# ESQUEMAS DE IMPRESORA
# ================================================================

class ImpresoraCreate(BaseModel):
    """Esquema para registrar una nueva impresora en el sistema."""
    ID_cliente: int
    ID_departamento: Optional[int] = None
    num_serie: str = Field(..., min_length=1, max_length=50)
    marca: str = Field(..., min_length=1, max_length=50)
    modelo: str = Field(..., min_length=1, max_length=100)
    tipo_conexion: TipoConexion = TipoConexion.LAN
    ip: Optional[str] = Field(None, max_length=15)
    mac: Optional[str] = Field(None, max_length=17)
    firmware: Optional[str] = Field(None, max_length=30)
    fecha_compra: Optional[date] = None
    termino_garantia: Optional[date] = None
    ubicacion: Optional[str] = Field(None, max_length=150)
    estado_actual: EstadoImpresora = EstadoImpresora.Activo

class ImpresoraResponse(BaseModel):
    """Esquema de respuesta con todos los datos de una impresora."""
    ID_impresora: int
    ID_cliente: int
    ID_departamento: Optional[int]
    num_serie: str
    marca: str
    modelo: str
    tipo_conexion: str
    ip: Optional[str]
    mac: Optional[str]
    firmware: Optional[str]
    fecha_compra: Optional[date]
    termino_garantia: Optional[date]
    ubicacion: Optional[str]
    estado_actual: str
    fecha_creacion: Optional[datetime]

    class Config:
        from_attributes = True


# ================================================================
# ESQUEMAS DE CONTADOR
# ================================================================

class ContadorCreate(BaseModel):
    """
    Esquema para registrar un contador mensual.
    El campo 'paginas_mes' se calcula automáticamente en el endpoint
    antes de guardar en la base de datos.
    """
    ID_impresora: int
    ID_usuario: int
    fecha_lectura: date
    contador_inicial: int = Field(..., ge=0, description="Lectura del mes anterior")
    contador_mensual: int = Field(..., ge=0, description="Lectura actual del equipo")

class ContadorResponse(BaseModel):
    """
    Esquema de respuesta que incluye la diferencia de páginas
    calculada automáticamente por el backend.
    """
    ID_contador: int
    ID_impresora: int
    ID_usuario: int
    fecha_lectura: date
    contador_inicial: int
    contador_mensual: int
    paginas_mes: int  # Calculado automáticamente: contador_mensual - contador_inicial

    class Config:
        from_attributes = True


# ================================================================
# ESQUEMAS DE VISITA TÉCNICA
# ================================================================

class VisitaCreate(BaseModel):
    """Esquema para registrar una nueva visita técnica."""
    ID_impresora: int
    ID_usuario: int
    fecha_visita: date
    motivo: MotivoVisita = MotivoVisita.Preventiva
    reporte_tecnico: str = Field(..., min_length=5, description="Descripción detallada")
    costo_visita: Decimal = Field(default=Decimal("0.00"), ge=0)
    aplica_garantia: bool = False

class VisitaResponse(BaseModel):
    """Esquema de respuesta con los datos de una visita técnica."""
    ID_visita: int
    ID_impresora: int
    ID_usuario: int
    fecha_visita: date
    motivo: str
    reporte_tecnico: str
    costo_visita: Decimal
    aplica_garantia: int
    fecha_creacion: Optional[datetime]

    class Config:
        from_attributes = True


# ================================================================
# ESQUEMAS DE AUTENTICACIÓN
# ================================================================

class LoginRequest(BaseModel):
    """Datos para iniciar sesión."""
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=4)

class LoginResponse(BaseModel):
    """Respuesta al login exitoso."""
    ID_usuario: int
    nombre: str
    email: str
    rol: str
    ID_cliente: Optional[int] = None


# ================================================================
# ESQUEMAS DE USUARIO
# ================================================================

class UsuarioCreate(BaseModel):
    """Esquema para crear un nuevo usuario."""
    ID_cliente: Optional[int] = None
    ID_rol: int
    nombre: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=4, max_length=255)
    estado: str = Field(default="activo", pattern="^(activo|inactivo|bloqueado)$")

class UsuarioUpdate(BaseModel):
    """Esquema para actualizar un usuario existente."""
    ID_cliente: Optional[int] = None
    ID_rol: Optional[int] = None
    nombre: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    estado: Optional[str] = None

class UsuarioResponse(BaseModel):
    """Esquema de respuesta con los datos de un usuario.
    NO incluye el campo password por seguridad."""
    ID_usuario: int
    ID_cliente: Optional[int]
    ID_rol: int
    nombre: str
    email: str
    estado: str
    ultimo_acceso: Optional[datetime]
    fecha_creacion: Optional[datetime]

    class Config:
        from_attributes = True


# ================================================================
# ESQUEMAS GENÉRICOS DE RESPUESTA
# ================================================================

class PaginatedResponse(BaseModel):
    """Respuesta paginada genérica para listados."""
    total: int
    page: int
    per_page: int
    data: list

class MessageResponse(BaseModel):
    """Respuesta simple con mensaje de éxito/error."""
    success: bool
    message: str
    data: Optional[dict] = None
