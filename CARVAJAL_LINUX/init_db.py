#!/usr/bin/env python
"""
🗄️ INICIALIZADOR DE BASE DE DATOS
Crea las tablas necesarias en la BD (SQLite o PostgreSQL)
"""

import sys
import logging
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, inspect
from src.config import DATABASE_URL, DATABASE_TYPE
from src.models import Base, crear_todas_tablas, MODELOS

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def verificar_estado_bd(engine):
    """Verifica qué tablas existen en la BD"""
    
    inspector = inspect(engine)
    tablas_existentes = inspector.get_table_names()
    
    print("\n📊 Estado de tablas en BD:")
    print(f"   Total tablas encontradas: {len(tablas_existentes)}")
    
    if tablas_existentes:
        for tabla in tablas_existentes:
            print(f"   ✅ {tabla}")
    else:
        print("   (Sin tablas creadas aún)")
    
    return tablas_existentes


def crear_bd():
    """Crea todas las tablas en la BD"""
    
    print("\n" + "=" * 80)
    print("🗄️  INICIALIZADOR DE BASE DE DATOS")
    print("=" * 80)
    
    print(f"\n📌 Configuración:")
    print(f"   Tipo: {DATABASE_TYPE.upper()}")
    print(f"   URL: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else f"   URL: {DATABASE_URL}")
    
    try:
        # Crear engine
        logger.info(f"Conectando a BD ({DATABASE_TYPE})...")
        
        if DATABASE_TYPE == 'sqlite':
            # SQLite: permitir create_all sin advertencias
            engine = create_engine(DATABASE_URL, echo=False)
        else:
            # PostgreSQL: verificar pooling
            engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
        
        print("\n✅ Conectado a BD")
        
        # Verificar tablas existentes antes
        print("\n📋 Tablas ANTES de crear:")
        tablas_antes = verificar_estado_bd(engine)
        
        # Crear tablas
        print("\n⏳ Creando tablas...")
        crear_todas_tablas(engine)
        
        # Verificar tablas después
        print("\n📋 Tablas DESPUÉS de crear:")
        tablas_despues = verificar_estado_bd(engine)
        
        # Resumen
        nuevas_tablas = len(tablas_despues) - len(tablas_antes)
        print(f"\n✅ Proceso completado:")
        print(f"   Nuevas tablas: {nuevas_tablas}")
        print(f"   Total tablas: {len(tablas_despues)}/{len(MODELOS)}")
        
        # Listar modelos
        print(f"\n📊 Modelos ORM definidos ({len(MODELOS)}):")
        for modelo in MODELOS:
            print(f"   ✅ {modelo.__tablename__}")
        
        engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Error inicializando BD: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    crear_bd()
