"""
📋 CONFIGURACIÓN CENTRALIZADA DEL PROYECTO
Archivo de configuración para ambientes (dev, staging, prod)
Compatible con SQLite y PostgreSQL
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ============================================================================
# ENTORNO
# ============================================================================
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# ============================================================================
# DIRECTORIOS BASE
# ============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# BASE DE DATOS
# ============================================================================
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')

if DATABASE_TYPE == 'sqlite':
    # SQLite: Archivo local
    DATABASE_PATH = BASE_DIR / 'database' / 'reportes_ventas.db'
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    DB_ECHO = DEBUG  # Mostrar SQL en logs si DEBUG=True
else:
    # PostgreSQL: Servidor remoto
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost:5432/reportes_ventas'
    )
    DB_ECHO = DEBUG

print(f"🗄️  DATABASE: {DATABASE_TYPE.upper()} ({ENVIRONMENT})")
if DATABASE_TYPE == 'sqlite':
    print(f"   Archivo: {DATABASE_PATH}")
else:
    print(f"   Host: {DATABASE_URL.split('@')[1].split('/')[0] if '@' in DATABASE_URL else 'N/A'}")

# ============================================================================
# DIRECTORIOS DE DESCARGAS (Usar variables de entorno si están disponibles)
# ============================================================================
# Directorio base para descargas si no se especifican rutas individuales
DESCARGAS_DIR = Path(os.getenv('DESCARGAS_DIR', BASE_DIR / 'descargas_reportes'))

# Rutas específicas por tipo de reporte
DESCARGAS_VENTAS_DIR = Path(os.getenv('DESCARGAS_VENTAS_DIR', DESCARGAS_DIR / 'ventas'))
DESCARGAS_INVENTARIO_DIR = Path(os.getenv('DESCARGAS_INVENTARIO_DIR', DESCARGAS_DIR / 'inventario'))
DESCARGAS_OTROS_DIR = Path(os.getenv('DESCARGAS_OTROS_DIR', DESCARGAS_DIR / 'otros'))

# Rutas de archivos ya procesados
PROCESADOS_VENTAS_DIR = Path(os.getenv('PROCESADOS_VENTAS_DIR', DESCARGAS_DIR / 'procesados' / 'ventas'))
PROCESADOS_INVENTARIO_DIR = Path(os.getenv('PROCESADOS_INVENTARIO_DIR', DESCARGAS_DIR / 'procesados' / 'inventario'))

# Rutas de logs
LOGS_DIR = Path(os.getenv('LOGS_DIR', DESCARGAS_DIR / 'logs'))

# Crear directorios si no existen
for directorio in [
    DESCARGAS_VENTAS_DIR,
    DESCARGAS_INVENTARIO_DIR,
    DESCARGAS_OTROS_DIR,
    PROCESADOS_VENTAS_DIR,
    PROCESADOS_INVENTARIO_DIR,
    LOGS_DIR,
]:
    try:
        directorio.mkdir(parents=True, exist_ok=True)
        print(f"   📁 Directorio verificado: {directorio}")
    except Exception as e:
        print(f"   ❌ Error creando directorio {directorio}: {e}")

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================
LOGGING_CONFIG = {
    'general': LOGS_DIR / 'general.log',
    'descargas': LOGS_DIR / 'descargas.log',
    'ventas': LOGS_DIR / 'procesamiento_ventas.log',
    'inventario': LOGS_DIR / 'procesamiento_inventario.log',
    'errores': LOGS_DIR / 'errores.log',
    'api': LOGS_DIR / 'api.log',
}

# ============================================================================
# SEGURIDAD Y AUTENTICACIÓN
# ============================================================================
# Secreto para firmar tokens JWT (Cambiar en producción vía .env)
SECRET_KEY = os.getenv('SECRET_KEY', '09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 60 * 24)) # 24 horas por defecto

# Credenciales para integración con Odoo (Definir en .env)
ODOO_API_USER = os.getenv('ODOO_API_USER', 'odoo_integration')
ODOO_API_PASSWORD = os.getenv('ODOO_API_PASSWORD', 'C@rvaj@l_Odoo_2026')

# ============================================================================
# CONFIGURACIÓN DE API
# ============================================================================
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '8000'))
API_RELOAD = DEBUG  # Auto-reload en desarrollo

print(f"🌐 API: http://{API_HOST}:{API_PORT}")

# ============================================================================
# CONFIGURACIÓN DE POOL (Para conexiones BD)
# ============================================================================
if DATABASE_TYPE == 'sqlite':
    # SQLite: Sin pooling
    SQLALCHEMY_POOL_CONFIG = {
        "connect_args": {"check_same_thread": False},
        "poolclass": "NullPool"
    }
else:
    # PostgreSQL: Con pooling
    SQLALCHEMY_POOL_CONFIG = {
        "pool_size": int(os.getenv('POOL_SIZE', '10')),
        "max_overflow": int(os.getenv('MAX_OVERFLOW', '20')),
        "pool_pre_ping": True,  # Verificar conexión antes de usar
        "pool_recycle": 3600,    # Reciclar conexión cada hora
    }

# ============================================================================
# PROCESAMIENTO DE REPORTES
# ============================================================================
# Tamaño máximo de archivo (MB)
MAX_FILE_SIZE_MB = 50

# Extensiones permitidas
ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}

# Fila donde comienzan los datos en Excel
EXCEL_DATA_START_ROW_VENTAS = 10
EXCEL_DATA_START_ROW_INVENTARIO = 10

# Fila de cabeceras en Excel
EXCEL_HEADER_ROW_VENTAS = 9
EXCEL_HEADER_ROW_INVENTARIO = 9

# ============================================================================
# VALIDACIÓN
# ============================================================================
# Cantidad mínima de columnas esperadas
MIN_COLUMNS_VENTAS = 14
MIN_COLUMNS_INVENTARIO = 13

# ============================================================================
# INTEGRACIÓN ODOO
# ============================================================================
ODOO_ENABLED = os.getenv('ODOO_ENABLED', 'False').lower() == 'true'
ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'production')
ODOO_USER = os.getenv('ODOO_USER', 'admin')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')

# ============================================================================
# SEGURIDAD
# ============================================================================
API_KEY_REQUIRED = os.getenv('API_KEY_REQUIRED', 'False').lower() == 'true'
API_KEYS = os.getenv('API_KEYS', '').split(',') if os.getenv('API_KEYS') else []

# ============================================================================
# RESUMEN DE CONFIGURACIÓN
# ============================================================================
CONFIG_SUMMARY = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                      ⚙️ CONFIGURACIÓN CARGADA                             ║
╠════════════════════════════════════════════════════════════════════════════╣
║ Entorno:              {ENVIRONMENT.upper():50} ║
║ Debug:                {str(DEBUG):50} ║
║ Base de Datos:        {DATABASE_TYPE.upper():50} ║
║ API:                  {f'http://{API_HOST}:{API_PORT}':50} ║
║                                                                            ║
║ Directorios:                                                              ║
║   Descargas Ventas:   {str(DESCARGAS_VENTAS_DIR.relative_to(BASE_DIR)):46} ║
║   Descargas Invtar:   {str(DESCARGAS_INVENTARIO_DIR.relative_to(BASE_DIR)):46} ║
║   Logs:               {str(LOGS_DIR.relative_to(BASE_DIR)):46} ║
║                                                                            ║
║ Base de Datos:                                                            ║
║   Tipo:               {DATABASE_TYPE.upper():50} ║
║   Echo:               {str(DB_ECHO):50} ║
║                                                                            ║
║ (Configuración completa cargada desde .env)                               ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

if ENVIRONMENT == 'development':
    print(CONFIG_SUMMARY)

# ============================================================================
# EXPORTAR CONFIGURACIÓN
# ============================================================================
__all__ = [
    'ENVIRONMENT',
    'DEBUG',
    'DATABASE_TYPE',
    'DATABASE_URL',
    'DESCARGAS_VENTAS_DIR',
    'DESCARGAS_INVENTARIO_DIR',
    'PROCESADOS_VENTAS_DIR',
    'PROCESADOS_INVENTARIO_DIR',
    'LOGS_DIR',
    'LOGGING_CONFIG',
    'API_HOST',
    'API_PORT',
    'API_RELOAD',
]
