#!/usr/bin/env python
"""
🚀 EJECUTOR DEL SERVIDOR API
Inicia servidor FastAPI con Uvicorn
"""

import sys
import logging
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from src.api import app
from src.config import API_HOST, API_PORT, ENVIRONMENT, DEBUG

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Inicia el servidor API"""
    
    print("\n" + "=" * 80)
    print("🚀 CARVAJAL VENTAS API SERVER")
    print("=" * 80)
    print(f"\n📌 Configuración:")
    print(f"   Entorno: {ENVIRONMENT}")
    print(f"   Host: {API_HOST}")
    print(f"   Puerto: {API_PORT}")
    print(f"   Debug: {DEBUG}")
    print(f"   URL: http://{API_HOST}:{API_PORT}")
    print(f"   Docs: http://{API_HOST}:{API_PORT}/docs")
    
    print("\n📊 Componentes cargados:")
    print(f"   ✅ Config")
    print(f"   ✅ Database")
    print(f"   ✅ Parsers (VENTAS, INVENTARIO)")
    print(f"   ✅ API Routes")
    
    print("\n" + "=" * 80)
    print("⏳ Iniciando servidor...\n")
    
    try:
        uvicorn.run(
            app,
            host=API_HOST,
            port=API_PORT,
            reload=DEBUG,
            log_level="debug" if DEBUG else "info"
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error iniciando servidor: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
