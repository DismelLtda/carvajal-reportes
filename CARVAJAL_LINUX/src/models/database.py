"""
🗄️ CONFIGURACIÓN DE BASE DE DATOS
Centraliza la conexión a la BD y la creación de sesiones
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import DATABASE_URL, DEBUG

# Configuración del Engine
engine = create_engine(
    DATABASE_URL, 
    echo=DEBUG, 
    # check_same_thread solo es necesario para SQLite
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """Retorna una nueva sesión de base de datos"""
    return SessionLocal()
