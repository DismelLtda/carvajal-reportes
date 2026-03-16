#!/usr/bin/env python3
# ============================================================================
# SCRIPT DE DEBUG - PRUEBA DE DOWNLOAD_SCHEDULER
# Ejecutar en Rocky Linux para diagnosticar el error del downloader
# ============================================================================

import os
import sys
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Verifica que todas las variables de entorno estén configuradas"""
    logger.info("=" * 70)
    logger.info("REVISANDO VARIABLES DE ENTORNO")
    logger.info("=" * 70)
    
    required_vars = [
        'ENVIRONMENT',
        'DATABASE_TYPE',
        'DATABASE_URL',
        'DESCARGAS_VENTAS_DIR',
        'DESCARGAS_INVENTARIO_DIR',
        'LOGS_DIR',
        'INTERVALO_VERIFICACION'
    ]
    
    optional_vars = [
        'CORREO_REMITENTE',
        'PASSWORD_CORREO',
        'CORREO_DESTINATARIO'
    ]
    
    logger.info("\n📋 Variables requeridas:")
    for var in required_vars:
        value = os.getenv(var, 'NO CONFIGURADA')
        if value == 'NO CONFIGURADA':
            logger.error(f"  ❌ {var}: {value}")
        else:
            # Ocultar valores sensibles
            if 'PASSWORD' in var or 'PASSWORD_CORREO' in var:
                logger.info(f"  ✅ {var}: ****")
            else:
                logger.info(f"  ✅ {var}: {value}")
    
    logger.info("\n📧 Variables de correo (opcionales):")
    for var in optional_vars:
        value = os.getenv(var, 'NO CONFIGURADA')
        if 'PASSWORD' in var:
            logger.info(f"  {'✅' if value != 'NO CONFIGURADA' else '⚠️ '} {var}: **** {'[Configurado]' if value != 'NO CONFIGURADA' else '[NO CONFIGURADO]'}")
        else:
            logger.info(f"  {'✅' if value != 'NO CONFIGURADA' else '⚠️ '} {var}: {value if value != 'NO CONFIGURADA' else '[NO CONFIGURADO]'}")

def check_directories():
    """Verifica que los directorios existan"""
    logger.info("\n" + "=" * 70)
    logger.info("REVISANDO DIRECTORIOS")
    logger.info("=" * 70)
    
    dirs = [
        'DESCARGAS_VENTAS_DIR',
        'DESCARGAS_INVENTARIO_DIR',
        'LOGS_DIR'
    ]
    
    for dir_var in dirs:
        dir_path = os.getenv(dir_var)
        if dir_path:
            exists = os.path.exists(dir_path)
            status = "✅" if exists else "❌"
            logger.info(f"  {status} {dir_var}: {dir_path}")
            if exists:
                perms = oct(os.stat(dir_path).st_mode)[-3:]
                logger.info(f"      Permisos: {perms}")

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    logger.info("\n" + "=" * 70)
    logger.info("REVISANDO DEPENDENCIAS DE PYTHON")
    logger.info("=" * 70)
    
    dependencies = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'psycopg2',
        'openpyxl',
        'pandas',
        'apscheduler',
        'yagmail'
    ]
    
    for dep in dependencies:
        try:
            __import__(dep)
            logger.info(f"  ✅ {dep}")
        except ImportError:
            logger.error(f"  ❌ {dep}: NO INSTALADO")

def check_database_connection():
    """Intenta conectarse a la base de datos"""
    logger.info("\n" + "=" * 70)
    logger.info("REVISANDO CONEXIÓN A BASE DE DATOS")
    logger.info("=" * 70)
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("  ❌ DATABASE_URL no está configurado")
        return
    
    try:
        # Ocultar credenciales en el log
        safe_url = database_url.replace(':' + database_url.split(':')[2].split('@')[0], ':****')
        logger.info(f"  📍 Conectando a: {safe_url}")
        
        from sqlalchemy import create_engine, text
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"  ✅ Conexión exitosa")
    
    except Exception as e:
        logger.error(f"  ❌ Error: {str(e)}")

def check_imports():
    """Verifica que todos los imports del scheduler funcionen"""
    logger.info("\n" + "=" * 70)
    logger.info("REVISANDO IMPORTS DEL SCHEDULER")
    logger.info("=" * 70)
    
    try:
        logger.info("  Importando: src.processor.detector")
        from src.processor.detector import ReporteDetector
        logger.info("  ✅ ReporteDetector importado correctamente")
    except ImportError as e:
        logger.error(f"  ❌ Error: {str(e)}")
    
    try:
        logger.info("  Importando: src.config")
        from src.config import DESCARGAS_VENTAS_DIR, DESCARGAS_INVENTARIO_DIR
        logger.info("  ✅ Config importado correctamente")
    except ImportError as e:
        logger.error(f"  ❌ Error: {str(e)}")
    
    try:
        logger.info("  Importando: notificaciones")
        from notificaciones import enviar_notificacion_error
        logger.info("  ✅ Notificaciones importado correctamente")
    except ImportError as e:
        logger.error(f"  ❌ Error: {str(e)}")

def main():
    logger.info("\n")
    logger.info("🔍 INICIANDO DIAGNÓSTICO DEL DOWNLOADER")
    logger.info("=" * 70)
    
    check_environment_variables()
    check_directories()
    check_dependencies()
    check_imports()
    check_database_connection()
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ DIAGNÓSTICO COMPLETADO")
    logger.info("=" * 70)
    logger.info("Si ves errores ❌, revisa:")
    logger.info("  1. Variables de entorno en .env.docker.prod")
    logger.info("  2. requirements.txt - instala todas las dependencias")
    logger.info("  3. Permisos de directorios - asegúrate que sean escribibles")
    logger.info("  4. Conexión a base de datos PostgreSQL")
    logger.info("\n")

if __name__ == "__main__":
    main()
