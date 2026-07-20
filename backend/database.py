"""
================================================================
MPS 2.0 — Configuración de Base de Datos
Archivo: database.py
Propósito: Configurar la conexión a MySQL usando SQLAlchemy
           y proveer la sesión de base de datos para dependency injection.
================================================================
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ================================================================
# CREDENCIALES DE BASE DE DATOS
# En producción, estas variables deben leerse desde variables
# de entorno (os.environ) o un archivo de configuración .env
# ================================================================
DB_USER     = "sql10833431"
DB_PASSWORD = "BmxHX131AJ"
DB_HOST     = "sql10.freesqldatabase.com"
DB_PORT     = "3306"
DB_NAME     = "sql10833431"

# ================================================================
# URL DE CONEXIÓN
# Formato: mysql+pymysql://usuario:clave@host:puerto/base_de_datos
# ================================================================
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ================================================================
# MOTOR DE SQLALCHEMY (engine)
# - pool_pre_ping=True: Verifica la conexión antes de usarla
#                       (evita errores de conexiones muertas)
# - pool_recycle=3600: Recicla conexiones cada hora
# ================================================================
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # True para depuración SQL (muestra queries en consola)
)

# ================================================================
# SESIÓN DE BASE DE DATOS
# cada petición HTTP obtiene su propia sesión independiente
# ================================================================
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ================================================================
# BASE PARA MODELOS
# Todas las tablas heredan de esta base
# ================================================================
Base = declarative_base()


def get_db():
    """
    Generador de dependencia para FastAPI.
    Crea una sesión de BD por cada petición y la cierra al finalizar.
    Se usa como: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()