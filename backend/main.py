"""
================================================================
MPS 2.0 — Aplicación Principal FastAPI
Archivo: main.py
Propósito: Archivo central del backend API. Incluye:
           - Inicialización de FastAPI
           - Configuración de CORS
           - Rutas API REST para clientes, impresoras y contadores
           - Lógica de cálculo automático de páginas del mes
================================================================
"""

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import os
import hashlib

# Importaciones de módulos internos del proyecto
from database import engine, get_db, Base
from models import Cliente, Impresora, HistorialContador, VisitaTecnica, Usuario, Rol
from schemas import (
    ClienteCreate, ClienteUpdate, ClienteResponse,
    ImpresoraCreate, ImpresoraResponse,
    ContadorCreate, ContadorResponse,
    VisitaCreate, VisitaResponse,
    MessageResponse,
    LoginRequest, LoginResponse,
    UsuarioCreate, UsuarioUpdate, UsuarioResponse
)


# ================================================================
# INICIALIZACIÓN DE LA APLICACIÓN FASTAPI
# ================================================================
app = FastAPI(
    title="MPS 2.0 API",
    description="API REST para el Sistema de Gestión de Impresión MPS 2.0",
    version="2.0.0",
    docs_url="/docs",       # Swagger UI: http://localhost:8000/docs
    redoc_url="/redoc"      # ReDoc: http://localhost:8000/redoc
)


# ================================================================
# CONFIGURACIÓN DE CORS (Cross-Origin Resource Sharing)
# Permite que el frontend HTML/JS local pueda hacer peticiones
# al backend sin ser bloqueado por la política del navegador.
# En desarrollo: permite todos los orígenes (*).
# En producción: restringir a dominios específicos.
# ================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # Permitir todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],         # Permitir todos los métodos (GET, POST, PUT, DELETE)
    allow_headers=["*"],         # Permitir todos los headers
)


# ================================================================
# EVENTO DE ARRANQUE: Crear tablas si no existen
# (Solo en desarrollo — en producción usar migraciones Alembic)
# ================================================================
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    print("✅ MPS 2.0 API iniciada correctamente")
    print("🌐 Frontend: http://localhost:8000")
    print("📖 Documentación API: http://localhost:8000/docs")


# ================================================================
# ARCHIVOS ESTÁTICOS DEL FRONTEND
# Monta los directorios js/ y css/ para que el navegador pueda
# cargar los scripts y estilos del frontend.
# ================================================================
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..")

if os.path.isdir(os.path.join(STATIC_DIR, "js")):
    app.mount("/js", StaticFiles(directory=os.path.join(STATIC_DIR, "js")), name="js")

if os.path.isdir(os.path.join(STATIC_DIR, "css")):
    app.mount("/css", StaticFiles(directory=os.path.join(STATIC_DIR, "css")), name="css")


# ================================================================
# ENDPOINT: Health Check
# ================================================================
@app.get("/", tags=["Sistema"])
def root():
    """
    Página principal — Sirve el frontend HTML del sistema MPS 2.0.
    """
    index_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"system": "MPS 2.0", "status": "online", "docs": "http://localhost:8000/docs"}


@app.get("/login", tags=["Sistema"])
def login_page():
    """Sirve la página de inicio de sesión."""
    login_path = os.path.join(os.path.dirname(__file__), "..", "login.html")
    if os.path.exists(login_path):
        return FileResponse(login_path, media_type="text/html")
    return HTTPException(status_code=404, detail="Login page not found")


# ================================================================
# ENDPOINTS DE AUTENTICACIÓN
# ================================================================

@app.post("/api/auth/login", response_model=LoginResponse, tags=["Auth"])
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica un usuario con email y contraseña.
    Retorna los datos del usuario, su rol y el ID del cliente asociado.
    """
    usuario = db.query(Usuario).filter(Usuario.email == credentials.email).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    # Verificar contraseña (comparación directa para demo — en producción usar bcrypt)
    if usuario.password != credentials.password:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    if usuario.estado != "activo":
        raise HTTPException(status_code=403, detail="Tu cuenta está desactivada")

    # Obtener el nombre del rol
    rol = db.query(Rol).filter(Rol.ID_rol == usuario.ID_rol).first()
    nombre_rol = rol.nombre_rol if rol else "Sin rol"

    return LoginResponse(
        ID_usuario=usuario.ID_usuario,
        nombre=usuario.nombre,
        email=usuario.email,
        rol=nombre_rol,
        ID_cliente=usuario.ID_cliente
    )


# ================================================================
# ENDPOINTS DE USUARIOS (CRUD)
# ================================================================

@app.get("/api/usuarios", response_model=List[UsuarioResponse], tags=["Usuarios"])
def listar_usuarios(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db)
):
    """Lista todos los usuarios registrados en el sistema."""
    query = db.query(Usuario)
    if estado:
        query = query.filter(Usuario.estado == estado)
    usuarios = query.order_by(desc(Usuario.fecha_creacion)).all()
    return usuarios


@app.get("/api/usuarios/{id_usuario}", response_model=UsuarioResponse, tags=["Usuarios"])
def obtener_usuario(id_usuario: int, db: Session = Depends(get_db)):
    """Obtiene los datos de un usuario específico."""
    usuario = db.query(Usuario).filter(Usuario.ID_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@app.post("/api/usuarios", response_model=UsuarioResponse, status_code=201, tags=["Usuarios"])
def crear_usuario(usuario_data: UsuarioCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario en el sistema."""
    existente = db.query(Usuario).filter(Usuario.email == usuario_data.email).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"Ya existe un usuario con email {usuario_data.email}")

    nuevo_usuario = Usuario(
        ID_cliente=usuario_data.ID_cliente,
        ID_rol=usuario_data.ID_rol,
        nombre=usuario_data.nombre,
        email=usuario_data.email,
        password=usuario_data.password,  # En producción: hash bcrypt
        estado=usuario_data.estado
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@app.put("/api/usuarios/{id_usuario}", response_model=UsuarioResponse, tags=["Usuarios"])
def actualizar_usuario(
    id_usuario: int,
    usuario_data: UsuarioUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza parcialmente los datos de un usuario existente."""
    usuario = db.query(Usuario).filter(Usuario.ID_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    update_data = usuario_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(usuario, field, value)

    db.commit()
    db.refresh(usuario)
    return usuario


@app.delete("/api/usuarios/{id_usuario}", response_model=MessageResponse, tags=["Usuarios"])
def eliminar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    """Elimina un usuario del sistema."""
    usuario = db.query(Usuario).filter(Usuario.ID_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if usuario.ID_usuario == 1:
        raise HTTPException(status_code=400, detail="No se puede eliminar el usuario administrador")

    db.delete(usuario)
    db.commit()
    return MessageResponse(success=True, message="Usuario eliminado correctamente")


@app.get("/api/roles", response_model=list, tags=["Usuarios"])
def listar_roles(db: Session = Depends(get_db)):
    """Lista todos los roles disponibles."""
    roles = db.query(Rol).all()
    return [{"ID_rol": r.ID_rol, "nombre_rol": r.nombre_rol, "descripcion": r.descripcion} for r in roles]


# ================================================================
# ENDPOINTS DE CLIENTES
# ================================================================

@app.get("/api/clientes", response_model=List[ClienteResponse], tags=["Clientes"])
def listar_clientes(
    estado: Optional[str] = Query(None, description="Filtrar por estado: activo/inactivo"),
    busqueda: Optional[str] = Query(None, description="Buscar por RUT o razón social"),
    db: Session = Depends(get_db)
):
    """
    Lista todos los clientes registrados.
    Soporta filtros opcionales por estado y búsqueda por texto.
    """
    query = db.query(Cliente)

    # Filtro por estado (activo/inactivo)
    if estado:
        query = query.filter(Cliente.estado == estado)

    # Búsqueda parcial por RUT o razón social
    if busqueda:
        query = query.filter(
            (Cliente.rut.contains(busqueda)) |
            (Cliente.razon_social.contains(busqueda))
        )

    # Ordenar por fecha de creación (más recientes primero)
    clientes = query.order_by(desc(Cliente.fecha_creacion)).all()
    return clientes


@app.get("/api/clientes/{id_cliente}", response_model=ClienteResponse, tags=["Clientes"])
def obtener_cliente(id_cliente: int, db: Session = Depends(get_db)):
    """Obtiene los datos de un cliente específico por su ID."""
    cliente = db.query(Cliente).filter(Cliente.ID_cliente == id_cliente).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@app.post("/api/clientes", response_model=ClienteResponse, status_code=201, tags=["Clientes"])
def crear_cliente(cliente_data: ClienteCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo cliente en el sistema.
    Valida que el RUT no esté duplicado antes de insertar.
    """
    # Verificar que el RUT no exista
    existente = db.query(Cliente).filter(Cliente.rut == cliente_data.rut).first()
    if existente:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un cliente con RUT {cliente_data.rut}"
        )

    nuevo_cliente = Cliente(**cliente_data.model_dump())
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    return nuevo_cliente


@app.put("/api/clientes/{id_cliente}", response_model=ClienteResponse, tags=["Clientes"])
def actualizar_cliente(
    id_cliente: int,
    cliente_data: ClienteUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza parcialmente los datos de un cliente existente."""
    cliente = db.query(Cliente).filter(Cliente.ID_cliente == id_cliente).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Actualizar solo los campos enviados (no nulos)
    update_data = cliente_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cliente, field, value)

    db.commit()
    db.refresh(cliente)
    return cliente


@app.delete("/api/clientes/{id_cliente}", response_model=MessageResponse, tags=["Clientes"])
def eliminar_cliente(id_cliente: int, db: Session = Depends(get_db)):
    """Elimina un cliente y todos sus datos asociados (CASCADE)."""
    cliente = db.query(Cliente).filter(Cliente.ID_cliente == id_cliente).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    db.delete(cliente)
    db.commit()
    return MessageResponse(success=True, message="Cliente eliminado correctamente")


# ================================================================
# ENDPOINTS DE IMPRESORAS
# ================================================================

@app.get("/api/impresoras", response_model=List[ImpresoraResponse], tags=["Impresoras"])
def listar_impresoras(
    id_cliente: Optional[int] = Query(None, description="Filtrar por cliente"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db)
):
    """
    Lista todas las impresoras del parque.
    Soporta filtros por cliente y por estado del equipo.
    """
    query = db.query(Impresora)

    if id_cliente:
        query = query.filter(Impresora.ID_cliente == id_cliente)

    if estado:
        query = query.filter(Impresora.estado_actual == estado)

    impresoras = query.order_by(desc(Impresora.fecha_creacion)).all()
    return impresoras


@app.get("/api/impresoras/{id_impresora}", response_model=ImpresoraResponse, tags=["Impresoras"])
def obtener_impresora(id_impresora: int, db: Session = Depends(get_db)):
    """Obtiene los datos de una impresora específica."""
    impresora = db.query(Impresora).filter(Impresora.ID_impresora == id_impresora).first()
    if not impresora:
        raise HTTPException(status_code=404, detail="Impresora no encontrada")
    return impresora


@app.post("/api/impresoras", response_model=ImpresoraResponse, status_code=201, tags=["Impresoras"])
def crear_impresora(impresora_data: ImpresoraCreate, db: Session = Depends(get_db)):
    """
    Registra una nueva impresora en el sistema.
    Valida que el número de serie no esté duplicado.
    """
    existente = db.query(Impresora).filter(
        Impresora.num_serie == impresora_data.num_serie
    ).first()
    if existente:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe una impresora con serie {impresora_data.num_serie}"
        )

    nueva_impresora = Impresora(**impresora_data.model_dump())
    db.add(nueva_impresora)
    db.commit()
    db.refresh(nueva_impresora)
    return nueva_impresora


@app.put("/api/impresoras/{id_impresora}", response_model=ImpresoraResponse, tags=["Impresoras"])
def actualizar_impresora(
    id_impresora: int,
    impresora_data: ImpresoraCreate,
    db: Session = Depends(get_db)
):
    """Actualiza una impresora existente."""
    impresora = db.query(Impresora).filter(Impresora.ID_impresora == id_impresora).first()
    if not impresora:
        raise HTTPException(status_code=404, detail="Impresora no encontrada")

    update_data = impresora_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(impresora, field, value)

    db.commit()
    db.refresh(impresora)
    return impresora


@app.delete("/api/impresoras/{id_impresora}", response_model=MessageResponse, tags=["Impresoras"])
def eliminar_impresora(id_impresora: int, db: Session = Depends(get_db)):
    """Elimina una impresora del sistema."""
    impresora = db.query(Impresora).filter(Impresora.ID_impresora == id_impresora).first()
    if not impresora:
        raise HTTPException(status_code=404, detail="Impresora no encontrada")

    db.delete(impresora)
    db.commit()
    return MessageResponse(success=True, message="Impresora eliminada correctamente")


# ================================================================
# ENDPOINTS DE CONTADORES
# ================================================================

@app.get("/api/impresoras/{id_impresora}/contadores", response_model=List[ContadorResponse], tags=["Contadores"])
def listar_contadores(
    id_impresora: int,
    limit: int = Query(12, ge=1, le=100, description="Últimos N registros"),
    db: Session = Depends(get_db)
):
    """
    Lista el historial de contadores de una impresora específica.
    Retorna los últimos registros ordenados por fecha descendente.
    """
    contadores = (
        db.query(HistorialContador)
        .filter(HistorialContador.ID_impresora == id_impresora)
        .order_by(desc(HistorialContador.fecha_lectura))
        .limit(limit)
        .all()
    )
    return contadores


@app.post("/api/contadores", response_model=ContadorResponse, status_code=201, tags=["Contadores"])
def registrar_contador(contador_data: ContadorCreate, db: Session = Depends(get_db)):
    """
    ════════════════════════════════════════════════════════════
    LÓGICA DE CÁLCULO AUTOMÁTICO DE PÁGINAS DEL MES
    ════════════════════════════════════════════════════════════

    Este endpoint realiza los siguientes pasos:

    1. Busca el ÚLTIMO contador registrado para la impresora indicada.
    2. Si existe un contador anterior, usa su 'contador_mensual'
       como 'contador_inicial' del nuevo registro (si el frontend
       no envía un valor específico).
    3. Calcula automáticamente las páginas impresas del mes:
       paginas_mes = contador_mensual - contador_inicial
    4. Valida que el contador actual sea mayor al anterior
       (evita datos inconsistentes).
    5. Guarda el registro con la diferencia calculada.
    ════════════════════════════════════════════════════════════
    """
    # Paso 1: Buscar el último contador registrado para esta impresora
    ultimo_contador = (
        db.query(HistorialContador)
        .filter(HistorialContador.ID_impresora == contador_data.ID_impresora)
        .order_by(desc(HistorialContador.fecha_lectura))
        .first()
    )

    # Paso 2: Si el frontend no envía contador_inicial (o es 0),
    # usar el contador_mensual del último registro como base
    contador_inicial = contador_data.contador_inicial
    if contador_inicial == 0 and ultimo_contador:
        contador_inicial = ultimo_contador.contador_mensual

    # Paso 3: Calcular la diferencia de páginas del mes
    paginas_mes = contador_data.contador_mensual - contador_inicial

    # Paso 4: Validar que los datos sean coherentes
    if paginas_mes < 0:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Error en contadores: el contador actual "
                f"({contador_data.contador_mensual}) es menor que "
                f"el anterior ({contador_inicial}). "
                f"La diferencia no puede ser negativa."
            )
        )

    # Paso 5: Crear el registro con la diferencia calculada
    nuevo_contador = HistorialContador(
        ID_impresora=contador_data.ID_impresora,
        ID_usuario=contador_data.ID_usuario,
        fecha_lectura=contador_data.fecha_lectura,
        contador_inicial=contador_inicial,
        contador_mensual=contador_data.contador_mensual,
        paginas_mes=paginas_mes  # ← Calculado automáticamente
    )

    db.add(nuevo_contador)
    db.commit()
    db.refresh(nuevo_contador)

    return nuevo_contador


# ================================================================
# ENDPOINTS DE VISITAS TÉCNICAS
# ================================================================

@app.get("/api/visitas", response_model=List[VisitaResponse], tags=["Visitas Técnicas"])
def listar_visitas(
    id_impresora: Optional[int] = Query(None, description="Filtrar por impresora"),
    motivo: Optional[str] = Query(None, description="Filtrar por motivo"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista las visitas técnicas registradas, con filtros opcionales."""
    query = db.query(VisitaTecnica)

    if id_impresora:
        query = query.filter(VisitaTecnica.ID_impresora == id_impresora)
    if motivo:
        query = query.filter(VisitaTecnica.motivo == motivo)

    visitas = query.order_by(desc(VisitaTecnica.fecha_visita)).limit(limit).all()
    return visitas


@app.post("/api/visitas", response_model=VisitaResponse, status_code=201, tags=["Visitas Técnicas"])
def registrar_visita(visita_data: VisitaCreate, db: Session = Depends(get_db)):
    """Registra una nueva visita técnica en el sistema."""
    nueva_visita = VisitaTecnica(
        ID_impresora=visita_data.ID_impresora,
        ID_usuario=visita_data.ID_usuario,
        fecha_visita=visita_data.fecha_visita,
        motivo=visita_data.motivo.value,
        reporte_tecnico=visita_data.reporte_tecnico,
        costo_visita=float(visita_data.costo_visita),
        aplica_garantia=1 if visita_data.aplica_garantia else 0
    )

    db.add(nueva_visita)
    db.commit()
    db.refresh(nueva_visita)
    return nueva_visita


# ================================================================
# ENDPOINT: DASHBOARD — KPIs Resumen
# ================================================================

@app.get("/api/dashboard/stats", tags=["Dashboard"])
def obtener_estadisticas(db: Session = Depends(get_db)):
    """
    Retorna estadísticas generales para el dashboard.
    Incluye contadores de equipos, alertas de garantía y costos.
    """
    from datetime import date, timedelta

    hoy = date.today()
    hace_30_dias = hoy + timedelta(days=30)

    # Contar equipos por estado
    total_impresoras = db.query(Impresora).count()
    activas = db.query(Impresora).filter(Impresora.estado_actual == "Activo").count()
    en_reparacion = db.query(Impresora).filter(Impresora.estado_actual == "En Reparación").count()
    de_baja = db.query(Impresora).filter(Impresora.estado_actual == "De Baja").count()

    # Garantías por vencer (próximos 30 días)
    garantias_por_vencer = (
        db.query(Impresora)
        .filter(
            Impresora.termino_garantia != None,
            Impresora.termino_garantia <= hace_30_dias,
            Impresora.termino_garantia >= hoy
        )
        .count()
    )

    # Total de clientes activos
    total_clientes = db.query(Cliente).filter(Cliente.estado == "activo").count()

    # Costo total de visitas (mes actual)
    from sqlalchemy import func as sqlfunc
    costo_total = (
        db.query(sqlfunc.coalesce(sqlfunc.sum(VisitaTecnica.costo_visita), 0))
        .filter(
            VisitaTecnica.fecha_visita >= hoy.replace(day=1)
        )
        .scalar()
    )

    # Total de páginas impresas (mes actual)
    paginas_totales = (
        db.query(sqlfunc.coalesce(sqlfunc.sum(HistorialContador.paginas_mes), 0))
        .filter(
            HistorialContador.fecha_lectura >= hoy.replace(day=1)
        )
        .scalar()
    )

    return {
        "total_clientes": total_clientes,
        "total_impresoras": total_impresoras,
        "impresoras_activas": activas,
        "impresoras_en_reparacion": en_reparacion,
        "impresoras_de_baja": de_baja,
        "garantias_por_vencer": garantias_por_vencer,
        "costo_mes_actual": float(costo_total),
        "paginas_mes_actual": int(paginas_totales)
    }


# ================================================================
# EJECUCIÓN DIRECTA (desarrollo local)
# Para ejecutar: cd backend && python main.py
# ================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-recarga al detectar cambios en código
    )