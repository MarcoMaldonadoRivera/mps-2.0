"""
================================================================
MPS 2.0 — Modelos de SQLAlchemy
Archivo: models.py
Propósito: Definir los modelos ORM que mapean las tablas de la
           base de datos `mps2.0` a objetos Python.
================================================================
"""

from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Enum, ForeignKey,
    DECIMAL, SmallInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


# ================================================================
# MODELO: CLIENTE
# Almacena los datos de cada PYME registrada en el sistema.
# Un cliente puede tener múltiples impresoras, departamentos
# y usuarios asociados.
# ================================================================
class Cliente(Base):
    __tablename__ = "clientes"

    ID_cliente = Column(Integer, primary_key=True, autoincrement=True)
    rut = Column(String(12), unique=True, nullable=False, comment="RUT chileno XX.XXX.XXX-X")
    razon_social = Column(String(150), nullable=False)
    direccion = Column(String(200), nullable=True)
    telefono = Column(String(20), nullable=True)
    contacto = Column(String(100), nullable=False, comment="Nombre del contacto administrativo")
    email_contacto = Column(String(100), nullable=True)
    estado = Column(Enum("activo", "inactivo"), default="activo", nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relaciones: un cliente tiene Many departamentos, impresoras, usuarios
    departamentos = relationship("Departamento", back_populates="cliente", cascade="all, delete-orphan")
    impresoras = relationship("Impresora", back_populates="cliente", cascade="all, delete-orphan")
    usuarios = relationship("Usuario", back_populates="cliente")


# ================================================================
# MODELO: ROL
# Roles de acceso del sistema (Gerente, Técnico, etc.)
# ================================================================
class Rol(Base):
    __tablename__ = "roles"

    ID_rol = Column(Integer, primary_key=True, autoincrement=True)
    nombre_rol = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String(200), nullable=True)

    usuarios = relationship("Usuario", back_populates="rol")


# ================================================================
# MODELO: USUARIO
# Usuarios del sistema con autenticación por contraseña hasheada.
# ================================================================
class Usuario(Base):
    __tablename__ = "usuarios"

    ID_usuario = Column(Integer, primary_key=True, autoincrement=True)
    ID_cliente = Column(Integer, ForeignKey("clientes.ID_cliente", ondelete="SET NULL"), nullable=True)
    ID_rol = Column(Integer, ForeignKey("roles.ID_rol", ondelete="RESTRICT"), nullable=False)
    nombre = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(255), nullable=False, comment="Hash bcrypt")
    estado = Column(Enum("activo", "inactivo", "bloqueado"), default="activo", nullable=False)
    ultimo_acceso = Column(DateTime, nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.now())

    # Relaciones
    cliente = relationship("Cliente", back_populates="usuarios")
    rol = relationship("Rol", back_populates="usuarios")
    contadores = relationship("HistorialContador", back_populates="usuario")
    visitas = relationship("VisitaTecnica", back_populates="usuario")
    cambios_suministros = relationship("CambioSuministro", back_populates="usuario")


# ================================================================
# MODELO: DEPARTAMENTO
# Organiza impresoras por área dentro de cada cliente.
# ================================================================
class Departamento(Base):
    __tablename__ = "departamentos"

    ID_departamento = Column(Integer, primary_key=True, autoincrement=True)
    ID_cliente = Column(Integer, ForeignKey("clientes.ID_cliente", ondelete="CASCADE"), nullable=False)
    nombre_departamento = Column(String(100), nullable=False)

    # Relaciones
    cliente = relationship("Cliente", back_populates="departamentos")
    impresoras = relationship("Impresora", back_populates="departamento")


# ================================================================
# MODELO: IMPRESORA
# Inventario completo del parque de impresoras.
# Incluye datos de red (IP, MAC), firmware, garantía y estado.
# ================================================================
class Impresora(Base):
    __tablename__ = "impresoras"

    ID_impresora = Column(Integer, primary_key=True, autoincrement=True)
    ID_cliente = Column(Integer, ForeignKey("clientes.ID_cliente", ondelete="CASCADE"), nullable=False)
    ID_departamento = Column(Integer, ForeignKey("departamentos.ID_departamento", ondelete="SET NULL"), nullable=True)
    num_serie = Column(String(50), unique=True, nullable=False, comment="Número de serie único")
    marca = Column(String(50), nullable=False)
    modelo = Column(String(100), nullable=False)
    tipo_conexion = Column(Enum("USB", "LAN", "Wi-Fi", "USB-LAN"), default="LAN", nullable=False)
    ip = Column(String(15), nullable=True, comment="Dirección IPv4")
    mac = Column(String(17), nullable=True, comment="Dirección MAC")
    firmware = Column(String(30), nullable=True, comment="Versión de firmware")
    fecha_compra = Column(Date, nullable=True)
    termino_garantia = Column(Date, nullable=True, comment="Fecha fin de garantía")
    ubicacion = Column(String(150), nullable=True)
    estado_actual = Column(Enum("Activo", "En Reparación", "De Baja"), default="Activo", nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relaciones
    cliente = relationship("Cliente", back_populates="impresoras")
    departamento = relationship("Departamento", back_populates="impresoras")
    contadores = relationship("HistorialContador", back_populates="impresora", cascade="all, delete-orphan")
    visitas = relationship("VisitaTecnica", back_populates="impresora", cascade="all, delete-orphan")
    cambios_suministros = relationship("CambioSuministro", back_populates="impresora", cascade="all, delete-orphan")


# ================================================================
# MODELO: SUMINISTRO
# Catálogo de consumibles (tóner, drums, fusores, kits).
# ================================================================
class Suministro(Base):
    __tablename__ = "suministros"

    ID_suministro = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(Enum("Tóner", "Drum", "Fusor", "Kit Mantención", "Tinta", "Otro"), nullable=False)
    modelo_codigo = Column(String(80), nullable=False)
    color = Column(String(20), nullable=True)
    rendimiento_estimado = Column(Integer, nullable=True, comment="Páginas estimadas de vida útil")
    costo_unitario = Column(DECIMAL(10, 2), default=0.00, nullable=False, comment="Costo en CLP")
    stock_actual = Column(Integer, default=0, nullable=False)
    stock_minimo = Column(Integer, default=2, nullable=False)
    estado = Column(Enum("activo", "descontinuado"), default="activo", nullable=False)

    cambios = relationship("CambioSuministro", back_populates="suministro")


# ================================================================
# MODELO: CAMBIO DE SUMINISTRO
# Registro de cada cambio de consumible en una impresora.
# ================================================================
class CambioSuministro(Base):
    __tablename__ = "cambio_suministros"

    ID_cambio = Column(Integer, primary_key=True, autoincrement=True)
    ID_impresora = Column(Integer, ForeignKey("impresoras.ID_impresora", ondelete="CASCADE"), nullable=False)
    ID_suministro = Column(Integer, ForeignKey("suministros.ID_suministro", ondelete="RESTRICT"), nullable=False)
    ID_usuario = Column(Integer, ForeignKey("usuarios.ID_usuario", ondelete="RESTRICT"), nullable=False)
    fecha_cambio = Column(DateTime, server_default=func.now())
    nivel_anterior = Column(Integer, nullable=True, comment="Nivel % anterior")
    contador_cambio = Column(Integer, nullable=True, comment="Contador al momento del cambio")
    observaciones = Column(String(300), nullable=True)

    # Relaciones
    impresora = relationship("Impresora", back_populates="cambios_suministros")
    suministro = relationship("Suministro", back_populates="cambios")
    usuario = relationship("Usuario", back_populates="cambios_suministros")


# ================================================================
# MODELO: HISTORIAL DE CONTADORES
# Registro mensual de lecturas de contador de cada impresora.
# La lógica de cálculo de páginas del mes está en main.py.
# ================================================================
class HistorialContador(Base):
    __tablename__ = "historial_contadores"

    ID_contador = Column(Integer, primary_key=True, autoincrement=True)
    ID_impresora = Column(Integer, ForeignKey("impresoras.ID_impresora", ondelete="CASCADE"), nullable=False)
    ID_usuario = Column(Integer, ForeignKey("usuarios.ID_usuario", ondelete="RESTRICT"), nullable=False)
    fecha_lectura = Column(Date, nullable=False)
    contador_inicial = Column(Integer, default=0, nullable=False, comment="Lectura mes anterior")
    contador_mensual = Column(Integer, default=0, nullable=False, comment="Lectura actual")
    paginas_mes = Column(Integer, default=0, nullable=False, comment="Diferencia calculada")

    # Relaciones
    impresora = relationship("Impresora", back_populates="contadores")
    usuario = relationship("Usuario", back_populates="contadores")


# ================================================================
# MODELO: VISITA TÉCNICA
# Registro de cada visita preventiva o correctiva.
# ================================================================
class VisitaTecnica(Base):
    __tablename__ = "visitas_tecnicas"

    ID_visita = Column(Integer, primary_key=True, autoincrement=True)
    ID_impresora = Column(Integer, ForeignKey("impresoras.ID_impresora", ondelete="CASCADE"), nullable=False)
    ID_usuario = Column(Integer, ForeignKey("usuarios.ID_usuario", ondelete="RESTRICT"), nullable=False)
    fecha_visita = Column(Date, nullable=False)
    motivo = Column(Enum("Preventiva", "Correctiva"), default="Preventiva", nullable=False)
    reporte_tecnico = Column(Text, nullable=False)
    costo_visita = Column(DECIMAL(10, 2), default=0.00, nullable=False, comment="Costo en CLP")
    aplica_garantia = Column(SmallInteger, default=0, nullable=False, comment="1 = cubierto por garantía")
    fecha_creacion = Column(DateTime, server_default=func.now())

    # Relaciones
    impresora = relationship("Impresora", back_populates="visitas")
    usuario = relationship("Usuario", back_populates="visitas")
    costos_adicionales = relationship("CostoAdicionalVisita", back_populates="visita", cascade="all, delete-orphan")


# ================================================================
# MODELO: COSTO ADICIONAL POR VISITA
# Desglose de piezas, insumos y horas extra por visita.
# ================================================================
class CostoAdicionalVisita(Base):
    __tablename__ = "costos_adicionales_visita"

    ID_costo_adicional = Column(Integer, primary_key=True, autoincrement=True)
    ID_visita = Column(Integer, ForeignKey("visitas_tecnicas.ID_visita", ondelete="CASCADE"), nullable=False)
    ID_suministro = Column(Integer, ForeignKey("suministros.ID_suministro", ondelete="SET NULL"), nullable=True)
    descripcion = Column(String(200), nullable=False)
    cantidad = Column(Integer, default=1, nullable=False)
    costo_momento = Column(DECIMAL(10, 2), default=0.00, nullable=False, comment="Costo unitario al momento")

    # Relaciones
    visita = relationship("VisitaTecnica", back_populates="costos_adicionales")
    suministro = relationship("Suministro")